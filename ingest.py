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

class OtherTable(Exception):
    pass
class FCCTableError(Exception):
    pass

def harvest_footnotes(fccfile, n_tables=64):
    """Go through the file and try to collect all the footnotes"""
    footnotes = []
    for table in fccfile.tables[0:n_tables]:
        for row in table.rows:
            for cell in row.cells:
                try:
                    band = Band.parse(cell, units.kHz)
                    footnotes += band.all_footnotes()
                except NotBandError:
                    pass
    return list(set(footnotes))

def _get_empty_collections():
    """Return a pair of lists each containing three empty lists"""
    itu_collections = []
    for i in range(3):
        itu_collections.append(list())
    fcc_collections = []
    for i in range(3):
        fcc_collections.append(list())
    return itu_collections, fcc_collections

    
def parse_table(table, unit, version=Version("20200818"), dump_raw=False, dump_ordered=False):
    """Go through one table in the document and return a guess as to its contents"""
    # Check that this is the kind of table we can cope with
    pass
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
    # print(left)
    # print(right)
    # print(top)
    # print(bottom)
    # print(np.max(bottom), n_rows)
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
    left = left[first_useful_row:last_useful_row+1,:]
    right = right[first_useful_row:last_useful_row+1,:]
    top = top[first_useful_row:last_useful_row+1,:]
    bottom = bottom[first_useful_row:last_useful_row+1,:]
    n_rows = n_rows - first_useful_row

    # Create a pair of lists to hold the results
    itu_collections, fcc_collections = _get_empty_collections()
    for ir, boxes in enumerate(ordered):
        # OK, get the layout for this page/row
        layout = version.get_layout(page, ir+first_useful_row)
        assert layout[6] == "/", f"Bad layout: {layout}"
        if int(layout[7:]) != max_boxes:
            raise ValueError("Supplied layout does not match table")
        sources = [int(l,16) for l in layout[0:6]]
        # First the ITU entries
        entries = []
        for i in range(3):
            itu_collections[i].append(boxes[sources[i]])
        for i in range(3):
            fcc_collections[i].append(boxes[sources[i+3]])

    # Finish off
    diagnostics = {
        "page": page,
        "has_header": has_header}
    return itu_collections, fcc_collections, unit, diagnostics

class DigestError(Exception):
    """Error raised when collection can't be digested"""
    pass

def _digest_collection(entries, unit, fcc_rules=None):
    """Go through a collection column, merge what needs to be merged and parse into bands"""
    output_collection = []
    accumulator = None
    rules_accumulator = None
    previous = None
    previous_rule = None
    if fcc_rules is None:
        rules = [None]*len(entries)
    else:
        rules = fcc_rules
    for entry, rule in zip(entries, rules):
        # See if this one is at least the start of a band
        try:
            if entry is not None:
                test = Band.parse(entry, unit)
            # OK, it worked (or it's not none), so dispatch the one
            # we've been working on thus far.  However, be careful,
            # there are circmstances in which this can simply be a
            # repeat of the previous one.
            if entry != previous and accumulator is not None:
                new_band = Band.parse(accumulator, unit, rules_accumulator)
                if len(output_collection) > 0:
                    if new_band != output_collection[-1]:
                        output_collection.append(new_band)
                else:
                    output_collection.append(new_band)
            accumulator = entry
            rules_accumulator = rule
        except NotBandError:
            # The current entry isn't a band, it must be finishing the
            # band in the accumulator.  Check it's not just a repeat.
            if entry != previous:
                if accumulator is None:
                    accumulator = entry
                else:
                    if entry is not None:
                        accumulator = accumulator + entry
                if rules_accumulator is None:
                    rules_accumulator = rule
                else:
                    if rule is not None:
                        rules_accumulator = rules_accumulator + rule
                previous = entry
                previous_rule = rule
    # OK, now we've got to the end, deal with the final entry
    try:
        new_band = Band.parse(accumulator, unit, rules_accumulator)
        if len(output_collection) > 0:
            if new_band != output_collection[-1]:
                output_collection.append(new_band)
        else:
            output_collection.append(new_band)
    except NotBandError:
        pass
        # raise DigestError("Unable to parse the final entry")
    return output_collection

def parse_all_tables(fccfile, table_range=range(0,65), **kwargs):
    """Go through tables in fcc file and parse them"""

    version = Version("20200818")
    tables = fccfile.tables
    unit = units.dimensionless_unscaled
    # Setup empty result
    itu_accumulators, fcc_accumulators = _get_empty_collections()
    itu_collections, fcc_collections = _get_empty_collections()

    for it in table_range:
        print (f"============================ Table {it}")
        table = tables[it]
        these_itu_entries, these_fcc_entries, new_unit, diagnostics = parse_table(
            table, unit, version, **kwargs)
        # If this table has got a header, then dispatch the previously
        # collected table entries.
        if diagnostics["has_header"]:
            for i in range(3):
                itu_collections[i] += _digest_collection(
                    itu_accumulators[i], unit)
            for i in range(2):
                fcc_collections[i] += _digest_collection(
                    fcc_accumulators[i], unit, fcc_rules=fcc_accumulators[2])
            itu_accumulators, fcc_accumulators = _get_empty_collections()
        unit = new_unit
        # Now add the new entries to the accumulators
        for i in range(3):
            itu_accumulators[i] += these_itu_entries[i]
            fcc_accumulators[i] += these_fcc_entries[i]
    # Now dispatch the final table
    for i in range(3):
        itu_collections[i] += _digest_collection(
            itu_accumulators[i], unit)
    for i in range(2):
        fcc_collections[i] += _digest_collection(
            fcc_accumulators[i], unit, fcc_rules=fcc_accumulators[2])
    itu = {
        "R1": itu_collections[0],
        "R2": itu_collections[1],
        "R3": itu_collections[2]}
    fcc = {
        "F": fcc_collections[0],
        "NF": fcc_collections[1]}
    return itu, fcc

def merge_band_lists(collections):
    """Combine a set of lists of bands into one"""
    interim = []
    # Build the raw list
    for tag, collection in collections.items():
        for band in collection:
            new_band = copy.deepcopy(band)
            if new_band.jurisdictions is not None:
                raise ValueError("Band seems to already have been merged")
            new_band.jurisdictions = [tag]
            interim.append(new_band)
    # Now sort all these bands into order
    interim.sort()
    result = []
    # Now go through and join bands together if they're the same in all but region.
    for band in interim:
        # This is the index of the first entry in the result that
        # starts at this band's frequency
        index = bisect.bisect_left(result, band)
        # Now look for all the bands already stored after this one and
        # see if they are basically the same as this band.
        destination = -1
        for i in range(index, len(result)):
            # Here we take advantage of the fact that the = operator
            # for bands does not pay attention to jurisdiction
            # information.
            if result[i] == band:
                destination = i
        if destination != -1:
            result[destination].jurisdictions.append(band.jurisdictions[0])
        else:
            result.append(band)
                
    return result
        
        
