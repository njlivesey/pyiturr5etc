"""First attempt at Python code to handle FCC tables"""

import numpy as np
import pandas as pd
import pathlib

import pint
from docx.document import Document
from docx.table import Table

from .bands import NotBandError, Band
from .versions import Version
from .utils import cell2text, first_line, last_line, pretty_print
from .cells import FCCCell
from .band_collections import BandCollection
from pyiturr5etc.corf_pint import ureg


class FCCTableError(Exception):
    """Exception raised when there is a problem with this table"""


N_LOGICAL_COLUMNS = 6


def _parse_table(
    table: Table,
    units: pint.Unit,
    version: Version,
    dump_raw: bool = False,
    dump_ordered: bool = False,
) -> (dict[BandCollection], pint.Unit, dict):
    """Go through one table in the document and return a guess as to its contents

    Parameters
    ----------
    table : docx.table.Table
        Table entry from Word FCC tables file
    units : pint.Unit
        Current frequency unit
    version : Version
        Version-specific information
    dump_raw : bool, optional
        Dump the raw information for debugging purposes
    dump_ordered : bool, optional
        Dump the ordered information for debugging purposes.

    Returns
    -------
    collections : dict[BandCollections]
        The information in this table
    units : pint.Unit
        Potentially updated frquency unit information
    diagnostics : dict
        Various sources of information

    Raises
    ------
    FCCTableError
        Raised if there is some problem with the table itself
    ValueError
        _description_
    """

    # First get the first row and work out if this is a table with headers or not
    header = first_line(table.rows[0].cells[0])
    n_rows = len(table.rows)
    header_prefix = "Table of Frequency Allocations"
    has_header = header[0 : len(header_prefix)] == header_prefix
    page = None
    if has_header:
        page = last_line(table.rows[0].cells[-1])
        first_useful_row = 3
        # Get the units from the remainder of the header
        words = header[len(header_prefix) :].split()
        units = pint.Unit(words[1])
    else:
        first_useful_row = 0
    # Get the last row and check it's not just full of page numbers
    try:
        footer = first_line(table.rows[-1].cells[0])
    except IndexError:
        footer = ""
    footer_prefix = "Page"
    has_footer = footer[0 : len(footer_prefix)] == footer_prefix
    if has_footer:
        last_useful_row = n_rows - 1
    else:
        last_useful_row = n_rows - 1
    # Also, get the page number if it's in the last row/column (or thereabouts)
    if not has_header:
        for i_row in [-1, -2, -3]:
            try:
                page = last_line(table.rows[i_row].cells[-1])
                break
            except IndexError:
                pass
    # Some page numbers are hard to deduce, these we patch
    page = version.patch_page(page)

    # Possibly dump the raw table
    if dump_raw:
        frame = pd.DataFrame()
        for row in table.rows:
            entries = []
            for column in row.cells:
                # pylint: disable=protected-access
                try:
                    this_bottom = column._element.bottom
                except ValueError:
                    this_bottom = None
                entries.append(
                    column.text
                    + f"<{column._element.left},{column._element.right}>, "
                    + f"<{column._element.top},{this_bottom}>"
                )
                # pylint: enable=protected-access
            frame = pd.concat([frame, pd.DataFrame([entries])], ignore_index=True)
        print(page)
        pretty_print(frame)

    n_cols_per_row = [len(r.cells) for r in table.rows]
    max_cols = max(n_cols_per_row)

    # Look at how each cell spans the grid (left and right information)
    left, right, top, bottom = [
        np.zeros(shape=[n_rows, max_cols], dtype=int) for i in range(4)
    ]
    for i_row, row in enumerate(table.rows):
        for i_column, column in enumerate(row.cells):
            # pylint: disable=protected-access
            left[i_row, i_column] = column._element.left
            right[i_row, i_column] = column._element.right
            top[i_row, i_column] = column._element.top
            try:
                bottom[i_row, i_column] = column._element.bottom
            except ValueError:
                bottom[i_row, i_column] = top[i_row, i_column] + 1
            # pylint: enable=protected-access
    assert np.max(bottom) == n_rows, "Confused about the number of rows"

    # Build up a new data structure for the cells in the proper order
    max_boxes = np.max(right)
    ordered = []
    for i_row in range(n_rows):
        boxes = [None] * max_boxes
        ordered.append(boxes)
    for r_in, row in enumerate(table.rows):
        for c_in, column in enumerate(row.cells):
            for r_out in range(top[r_in, c_in], bottom[r_in, c_in]):
                for c_out in range(left[r_in, c_in], right[r_in, c_in]):
                    new_value = cell2text(column)
                    current_value = ordered[r_out][c_out]
                    if current_value is not None and current_value != new_value:
                        raise FCCTableError(
                            f"Trampled unexpectedly {r_out},{c_out} from {r_in},{c_in}"
                        )
                    else:
                        ordered[r_out][c_out] = new_value

    # Possibly dump the ordered table
    if dump_ordered:
        frame = pd.DataFrame(columns=range(max_boxes))
        for boxes in ordered:
            frame = pd.concat(
                [frame, pd.DataFrame([boxes])],
                ignore_index=True,
            )
        print(page)
        pretty_print(frame)

    # Now go through and cut out the header row
    ordered = ordered[first_useful_row : last_useful_row + 1]
    n_rows = n_rows - first_useful_row
    # Create a list of lists to hold the result
    collections = [list() for i in range(N_LOGICAL_COLUMNS)]
    for i_row, boxes in enumerate(ordered):
        # OK, get the layout for this page/row
        layout = version.get_layout(page, i_row)
        assert layout[N_LOGICAL_COLUMNS] == "/", f"Bad layout: {layout}"
        if int(layout[N_LOGICAL_COLUMNS + 1 :]) != max_boxes:
            raise ValueError("Supplied layout does not match table")
        sources = [int(l, 16) for l in layout[0:N_LOGICAL_COLUMNS]]
        for i in range(N_LOGICAL_COLUMNS):
            collections[i].append(
                FCCCell(
                    boxes[sources[i]],
                    units=units,
                    logical_column=i,
                    ordered_row=i_row,
                    ordered_column=sources[i],
                    page=page,
                )
            )
    # Finish off
    diagnostics = {"page": page, "has_header": has_header}
    return collections, units, diagnostics


class DigestError(Exception):
    """Error raised when collection can't be digested"""


# pylint: disable-next=too-many-locals, too-many-branches, too-many-statements
def _digest_collection(cells, fcc_rules_cells=None, jurisdictions=None, debug=False):
    """Go through column of cells, merge and parse as needed"""
    # Set up some defaults
    if fcc_rules_cells is None:
        rules = [None] * len(cells)
    else:
        rules = fcc_rules_cells
    assert len(rules) == len(cells), "Mismatch between entries and rules"
    # Set up defaults
    result = BandCollection()
    accumulator = []
    rules_accumulator = []
    accumulator_as_band = None
    for cell_orig, rule_orig in zip(cells, rules):
        # See if this cell marks the start of band
        if cell_orig is not None:
            cell = cell_orig.clean()
        else:
            cell = None
        if rule_orig is not None:
            rule = rule_orig.clean()
        else:
            rule = None
        if debug:
            print("-----------------------------------------------------")
            print(f"Cell is: {cell.lines}")
        try:
            cell_as_band = Band.parse(cell, fcc_rules=rule, jurisdictions=jurisdictions)
            cell_is_band_start = True
        except NotBandError:
            cell_is_band_start = False
            cell_as_band = None
        # If this cell is the start of a band, see if it's the start of a new band
        if cell_is_band_start:
            try:
                cell_is_new_band = accumulator_as_band.bounds != cell_as_band.bounds
            except AttributeError:
                cell_is_new_band = True
        else:
            cell_is_new_band = False
        if debug:
            print(
                f"    cell_is_band_start={cell_is_band_start}, "
                f"cell_is_new_band={cell_is_new_band}"
            )
            print("    cell_as_band=", end="")
            try:
                print(cell_as_band.compact_str())
            except AttributeError:
                print(cell_as_band)

        accumulate_cell = True
        if cell_is_new_band:
            # If the cell is a new band, then store the accumulated
            # band, and start a new accumulator
            if accumulator_as_band is not None:
                if debug:
                    print(f"*** Storing: {accumulator_as_band.compact_str()}")
                result.append(accumulator_as_band)
            else:
                if debug:
                    print("    nothing in accumulator to store.")
            accumulator = []
            rules_accumulator = []
        elif cell_is_band_start:
            # If the cell is the start of a band, but not the
            # start of a new band, then presumably it's a repeat
            # of the information we have thus far.  Check that
            # that's the case, and mark it as not to be accumulated
            accumulate_cell = False
            try:
                if not cell_as_band.equal(accumulator_as_band, ignore_fcc_rules=True):
                    print(cell_as_band.compact_str())
                    print("----------")
                    print(accumulator_as_band.compact_str())
                    raise ValueError("Confused about bands")
            except AttributeError:
                pass
        # Now accumulate the cell contents if appropriate
        if accumulate_cell:
            try:
                if cell.lines is not None:
                    accumulator += cell.lines
            except AttributeError:
                pass
            try:
                if rule.lines is not None:
                    rules_accumulator += rule.lines
            except AttributeError:
                pass
            try:
                accumulator_as_band = Band.parse(
                    accumulator,
                    fcc_rules=rules_accumulator,
                    units=cell.units,
                    jurisdictions=jurisdictions,
                )
            except NotBandError:
                accumulator_as_band = None
        if debug:
            print(f"    accumulator={accumulator}")
            if accumulator_as_band is not None:
                print(f"    accumulator_as_band={accumulator_as_band.compact_str()}")
            else:
                print("    accumulator_as_band=None")
    # Once we're done with the loop, add the final band
    if accumulator_as_band is not None:
        result.append(accumulator_as_band)
    return result


def parse_all_tables(
    fccfile: Document,
    filename: str,
    table_range: range = None,
    **kwargs,
) -> tuple[dict[BandCollection], Version]:
    """Go through all the tables in the FCC Word file and parse them

    Parameters
    ----------
    fccfile : Document
        The Word document as read by docx
    filename : str
        Used to extract the version information
    table_range : range
        Which tables in the files are the ones to consider

    Returns
    -------
    collections : dict[BandCollection]
        All the parsed information

    version : Version
        Version related information
    """
    # Get the version as the suffix to the filename
    version_words = pathlib.Path(filename).stem.split("-")[1:]
    # Convert it to a set of version information
    version = Version("-".join(version_words))
    tables = fccfile.tables
    unit = ureg.dimensionless
    collections_list = [list() for i in range(N_LOGICAL_COLUMNS)]
    if table_range is None:
        table_range = range(0, 65)
    print("Reading tables: ", end="")
    for it in table_range:
        print(f"{it}, ", end="")
        table = tables[it]
        # pylint: disable-next=unused-variable
        new_columns, new_unit, diagnostics = _parse_table(
            table, unit, version, **kwargs
        )
        unit = new_unit
        for collection, new_entries in zip(collections_list, new_columns):
            collection += new_entries
    # Now go through and convert these into band collections
    print("done.")
    collections = dict()
    print("Digesting: ", end="")
    for name, i in zip(["R1", "R2", "R3"], range(3)):
        print(f"{name}, ", end="")
        collections[name] = _digest_collection(
            collections_list[i], jurisdictions=[name], debug=False
        )
    for name, i in zip(["F", "NF"], range(3, 5)):
        print(f"{name}, ", end="")
        collections[name] = _digest_collection(
            collections_list[i], collections_list[5], jurisdictions=[name]
        )
    print("done.")
    return collections, version
