"""First attempt at Python code to handle FCC tables"""

from IPython.display import display, HTML
import astropy.units as units
import bisect
import copy
import docx
import docx
import numpy as np
import pandas as pd

from .bands import NotBandError, Band
from .versions import Version
from .utils import cell2text, first_line, last_line, pretty_print
from .cells import FCCCell
from .band_collections import BandCollection

class OtherTable(Exception):
    pass
class FCCTableError(Exception):
    pass

n_logical_columns = 6

def _parse_table(table, unit, version=Version("20200818"), dump_raw=False, dump_ordered=False):
    """Go through one table in the document and return a guess as to its contents"""
    # First get the first row and work out if this is a table with headers or not
    header = first_line(table.rows[0].cells[0])
    n_rows = len(table.rows)
    header_prefix = "Table of Frequency Allocations"
    has_header = header[0:len(header_prefix)] == header_prefix
    page = None
    if has_header:
        page = last_line(table.rows[0].cells[-1])
        first_useful_row = 3
        # Get the units from the remainder of the header
        words = header[len(header_prefix):].split()
        unit = units.Unit(words[1])        
    else:
        first_useful_row = 0
    # Get the last row and check it's not just full of page numbers
    try:
        footer = first_line(table.rows[-1].cells[0])
    except IndexError:
        footer = ""
    footer_prefix = "Page"
    has_footer = footer[0:len(footer_prefix)] == footer_prefix
    if has_footer:
        last_useful_row = n_rows-2
    else:
        last_useful_row = n_rows-1
    # Also, get the page number if it's in the last row/column (or thereabouts)
    last_working_row = -1
    if not has_header:
        for ir in [-1,-2,-3]:
            try:
                page = last_line(table.rows[ir].cells[-1])
                last_working_row = ir
                break
            except IndexError:
                pass
    # Some page numbers are hard to deduce, these we patch
    page = version.patch_page(page)
    # Check to see if the table ends with a page number
    entry = first_line(table.rows[last_working_row].cells[-1])
    ends_with_page_number = entry[0:len(footer_prefix)] == footer_prefix

    # Possibly dump the raw table
    if dump_raw:
        frame = pd.DataFrame()
        for r in table.rows:
            entries = []
            for c in r.cells:
                try:
                    this_bottom = c._element.bottom
                except (ValueError):
                    this_bottom = None
                entries.append(
                    c.text +
                    f"<{c._element.left},{c._element.right}>, <{c._element.top},{this_bottom}>")
            frame = frame.append(pd.Series(entries), ignore_index=True)
        print(page)
        pretty_print(frame)

    n_cols_per_row = [len(r.cells) for r in table.rows]
    max_cols = max(n_cols_per_row)

    # Look at how each cell spans the grid (left and right information)
    left, right, top, bottom = [
        np.zeros(shape=[n_rows, max_cols], dtype=int)
        for i in range(4)]
    for ir, r in enumerate(table.rows):
        for ic, c in enumerate(r.cells):
            left[ir, ic] = c._element.left
            right[ir, ic] = c._element.right
            top[ir, ic] = c._element.top
            try:
                bottom[ir, ic] = c._element.bottom
            except ValueError:
                bottom[ir, ic] = top[ir, ic]+1
    assert np.max(bottom)==n_rows, "Confused about the number of rows"
    
    # Build up a new data structure for the cells in the proper order
    max_boxes = np.max(right)
    n_boxes_per_row = np.max(right, axis=1)
    ordered = []
    for ir in range(n_rows):
        boxes = [None]*max_boxes
        ordered.append(boxes)
    for rIn, r in enumerate(table.rows):
        for cIn, c in enumerate(r.cells):
            for rOut in range(top[rIn,cIn], bottom[rIn,cIn]):
                for cOut in range(left[rIn,cIn], right[rIn,cIn]):
                    new_value = cell2text(c)
                    current_value =  ordered[rOut][cOut]
                    if current_value != None and current_value != new_value:
                        raise FCCTableError(f"Trampled unexpectedly {rOut},{cOut} from {rIn},{cIn}")
                    else:
                        ordered[rOut][cOut] = new_value

    # Possibly dump the ordered table
    if dump_ordered:
        frame = pd.DataFrame(columns=range(max_boxes))
        for boxes in ordered:
            frame = frame.append(pd.Series(boxes), ignore_index=True)
        print(page)
        pretty_print(frame)

    # Now go through and cut out the header row
    ordered = ordered[first_useful_row:last_useful_row+1]
    n_rows = n_rows - first_useful_row
    # Create a list of lists to hold the result
    collections = [list() for i in range(n_logical_columns)]
    for ir, boxes in enumerate(ordered):
        # OK, get the layout for this page/row
        layout = version.get_layout(page, ir)
        assert layout[n_logical_columns] == "/", f"Bad layout: {layout}"
        if int(layout[n_logical_columns+1:]) != max_boxes:
            raise ValueError("Supplied layout does not match table")
        sources = [int(l,16) for l in layout[0:n_logical_columns]]
        for i in range(n_logical_columns):
            collections[i].append(FCCCell(
                boxes[sources[i]],
                unit=unit, logical_column=i,
                ordered_row=ir, ordered_column=sources[i],
                page=page))
    # Finish off
    diagnostics = {
        "page": page,
        "has_header": has_header}
    return collections, unit, diagnostics

class DigestError(Exception):
    """Error raised when collection can't be digested"""
    pass

def _digest_collection(cells, fcc_rules_cells=None, jurisdictions=None, debug=False):
    """Go through a column of cells, merge what needs to be merged and parse into bands"""
    # Set up some defaults
    if fcc_rules_cells is None:
        rules = [None]*len(cells)
    else:
        rules = fcc_rules_cells
    assert len(rules) == len(cells), "Mismatch between entries and rules"
    # Generate iterators for the cells and the rules
    iter_cells = iter(cells)
    iter_rules = iter(rules)
    # Set up defaults
    result = BandCollection()
    accumulator = None
    rules_accumulator = None
    previous_band = None
    exhausted = False
    while not exhausted:
        # Get the next cell and rule
        try:
            cell = next(iter_cells)
            rule = next(iter_rules)
            finished_accumulating = cell.is_band_start()
        except StopIteration:
            cell = None
            rule = None
            finished_accumulating = True
            exhausted = True
        if debug:
            print (f"---------------- finished_accumulating: {finished_accumulating}, exhausted: {exhausted}")
            diagnostics = {
                "cell": cell,
                "rule": rule,
                "accumulator": accumulator,
                "rules_accumulator": rules_accumulator}
            for key, item in diagnostics.items():
                try:
                    print (f"{key}={'/'.join(item.lines)}")
                except (AttributeError,TypeError):
                    print (f"{key} is None (or {key}.lines is None)")
        if finished_accumulating and accumulator is not None:
            # We've got to the start of a new band (or the end of the
            # list).  Convert the accumulator into a band.
            if debug:
                print (f"Parsing {'/'.join(accumulator.lines)}")
            new_band = Band.parse(
                accumulator, fcc_rules=rules_accumulator,
                jurisdictions=jurisdictions)
            if debug:
                print (f"Gives: {new_band.compact_str()}")
            # OK, this might genuinely be a new band, or it might be
            # the same band with additional information.
            try:
                if new_band.bounds != previous_band.bounds:
                    genuinely_new = True
                else:
                    genuinely_new = False
            except AttributeError:
                genuinely_new = True
            if debug:
                print (f"genuinely_new={genuinely_new}")
            if genuinely_new:
                # If it's genuinely new (new frequency range) then append it
                if debug:
                    print (f"Appending {new_band.compact_str()}")
                result.append(new_band)
                previous_band = new_band
            # If it's not genuinely new, we'll finish it off on later iterations
            # else:
            #     # Otherwise, it must be an update to the previously
            #     # recorded one, so update the record.
            #     if debug:
            #         print (f"Replacing {previous_band.compact_str()}")
            #         print (f"with {new_band.compact_str()}")
        if finished_accumulating or accumulator is None:
            # Either the accumulator is empty (first iteration) or
            # needs to be reset, do so.
            accumulator = copy.deepcopy(cell)
            rules_accumulator = copy.deepcopy(rule)
        else:
            if not cell.is_empty():
                accumulator.append(cell)
                if rule is not None:
                    rules_accumulator.append(rule)
    return result

def parse_all_tables(fccfile, table_range=None, **kwargs):
    """Go through tables in fcc file and parse them"""
    
    version = Version("20200818")
    tables = fccfile.tables
    unit = units.dimensionless_unscaled
    collections_list = [list() for i in range(n_logical_columns)]
    if table_range is None:
        table_range=range(0,65)
    print ("Reading tables: ", end="")
    for it in table_range:
        print (f"{it}, ", end="")
        table = tables[it]
        new_columns, new_unit, diagnostics = _parse_table(
            table, unit, version, **kwargs)
        unit = new_unit
        for collection, new_entries in zip(collections_list, new_columns):
            collection += new_entries
    # Now go through and convert these into band collections
    print ("done.")
    collections = dict()
    print ("Digesting: ", end="")
    for name, i in zip(["R1","R2","R3"], range(3)):
        print (f"{name}, ", end="")
        collections[name] = _digest_collection(
            collections_list[i], jurisdictions=[name])
    for name, i in zip(["F","NF"], range(3,5)):
        print (f"{name}, ", end="")
        collections[name] = _digest_collection(
            collections_list[i], collections_list[5],
            jurisdictions=[name])
    print ("done.")
    return collections
            
