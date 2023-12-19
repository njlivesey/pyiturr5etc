"""User level routines for the pyfcctab suite, including main table class"""

import copy
import docx
import numpy as np
import pickle
import pint

from IPython.display import display, HTML
from .ingest_tables import parse_all_tables
from .additional_allocations import all_additions
from .band_collections import BandCollection
from .footnotes import ingest_footnote_definitions, footnotedef2html
from .jurisdictions import Jurisdiction
from .fccpint import ureg



class FCCTables(object):
    """Class that holds all information in the FCC tables document"""

    @property
    def r1(self):
        return self.collections["R1"]

    @property
    def r2(self):
        return self.collections["R2"]

    @property
    def r3(self):
        return self.collections["R3"]

    @property
    def f(self):
        return self.collections["F"]

    @property
    def nf(self):
        return self.collections["NF"]

    @property
    def itu(self):
        return self.collections["ITU"]

    @property
    def usa(self):
        return self.collections["USA"]

    @property
    def all(self):
        return self.collections["all"]


default_path = "/users/livesey/corf/"


def read(
    filename=default_path + "fcctable.docx",
    skip_additionals=False,
    skip_footnote_definitions=False,
    **kwargs,
):
    """Reader routine for FCC tables file"""

    # Open the FCC file
    docx_data = docx.Document(filename)
    # Read all the tables
    collections, version = parse_all_tables(docx_data, **kwargs)
    result = FCCTables()
    result.version = version
    result.collections = collections
    # Now possibly insert the additional bands.
    if not skip_additionals:
        # We'll create an interim result for the collections we have.
        print(f"Injecting additions in: ", end="")
        for jname in result.collections.keys():
            jurisdiction = Jurisdiction.parse(jname)
            print(f"{jurisdiction.name}, ", end="")
            for new_band in all_additions:
                if jurisdiction in new_band.jurisdictions:
                    inserted_band = copy.deepcopy(new_band)
                    inserted_band.jurisdictions = [jurisdiction]
                    result.collections[jname].append(inserted_band)
            result.collections[jname] = result.collections[jname].flatten()
        print("done.")
    # Now we'll merge everything we have
    itu_regions = ["R1", "R2", "R3"]
    usa_regions = ["F", "NF"]
    all_regions = itu_regions + usa_regions
    print("Merging: ITU, ", end="")
    itu_all = BandCollection()
    for tag in itu_regions:
        itu_all = itu_all.merge(result.collections[tag])
    print("USA, ", end="")
    usa_all = BandCollection()
    for tag in usa_regions:
        usa_all = usa_all.merge(result.collections[tag])
    # Now add these merges to the results
    result.collections = {**result.collections, "ITU": itu_all, "USA": usa_all}
    # Now do a merge on literally everything
    print("all, ", end="")
    all_all = BandCollection()
    for tag in ["ITU", "USA"]:
        all_all = all_all.merge(result.collections[tag])
    result.collections = {**result.collections, "all": all_all}
    print("done.")
    # Now go through all the bands we have and add the relevant
    # footnote definitions to them.  First read the footnote
    # definitions, and store them in the result
    if not skip_footnote_definitions:
        print("Footnote definitions: reading, ", end="")
        footnote_definitions = ingest_footnote_definitions(docx_data)
        result.footnote_definitions = footnote_definitions
        print("appending, ", end="")
        for collection in result.collections.values():
            for b in collection:
                footnotes = b.all_footnotes()
                b._footnote_definitions = {}
                for f in footnotes:
                    if f[-1] == "#":
                        f = f[:-1]
                    if f in footnote_definitions:
                        b._footnote_definitions[f] = footnote_definitions[f]
        print("done.")
    return result


def save(tables, filename=default_path + "fcctable.pickle"):
    """Write tables to a pickle file"""
    outfile = open(filename, "wb")
    pickle.dump(tables, outfile)
    outfile.close()


def load(filename=default_path + "fcctable.pickle"):
    """Read tables from a pickle file"""
    infile = open(filename, "rb")
    result = pickle.load(infile)
    infile.close()
    return result


def htmlcolumn(bands, append_footnotes=False):
    """Produce an HTML table corresponding to a set of bands"""
    # First loop over the bands and work out how many rows and columns
    # we'll need
    # text = '<link rel="stylesheet" href="fcc.css">'
    text = '<table id="fcc-table">'
    for b in bands:
        text += '<tr><td id="fcc-td">'
        text += b.to_html(highlight_allocations=True, skip_jurisdictions=True)
        text += "</td></tr>\n"
    text += "</table>"

    # Now possibly append a description of all the footnotes
    if append_footnotes:
        footnotes = []
        definitions = {}
        for b in bands:
            footnotes += b.all_footnotes()
            definitions.update(b._footnote_definitions)
        footnotes = list(set(footnotes))
        footnotes.sort()

        for f in footnotes:
            text += footnotedef2html(f, definitions)

    # Now output the HTML
    display(HTML(text))
    return text


def htmltable(bands, append_footnotes=False, tooltips=True, filename=None):
    """Produce an HTML table corresponding to a set of bands"""
    # First loop over the bands and work out how many rows (frequency
    # spans) and columns (jurisdictions) we'll need.
    jurisdictions = []
    edges = []
    # Build up data
    for b in bands:
        jurisdictions += b.jurisdictions
        edges += b.bounds
    # Make this information unique and sorted
    edges = list(set(edges))
    edges.sort()
    edges = pint.Quantity.from_sequence(edges)
    jurisdictions = list(set(jurisdictions))
    jurisdictions.sort()
    # OK, so how many rows and columns?
    nColumns = len(jurisdictions)
    nRows = len(edges) - 1

    # Now set up some data structures to define the table.  First its
    # contents (None initially)
    table = list()
    for r in range(nRows):
        table.append([None for c in range(nColumns)])
    # Now some arrays that define the span of each cell, 1x1 to start with
    rSpan = np.ones(shape=[nRows, nColumns], dtype=np.int_)
    cSpan = np.ones(shape=[nRows, nColumns], dtype=np.int_)

    # Now loop over the bands and put them in cells
    for b in bands:
        # Identify which rows this band spans.
        row_span = np.searchsorted(edges, b.bounds)
        # Identify which columns this band should be listed in
        column_flags = [j in b.jurisdictions for j in jurisdictions]
        for r in range(row_span[0], row_span[1]):
            for c in range(nColumns):
                if column_flags[c]:
                    if table[r][c] is not None:
                        raise ValueError(f"Overlapping bands for {r}, {c}")
                    else:
                        table[r][c] = b
    # Now go through the cells and work out which ones should be aggolomorated
    Overlapped = "overlapped"
    for r in range(nRows):
        for c in range(nColumns):
            band = table[r][c]
            if band is None or band is Overlapped:
                continue
            # Now search forward in columns and see how many bands are the same
            column_flags = [
                band.equal(other_band, ignore_jurisdictions=True)
                for other_band in table[r][c:]
            ]
            try:
                column_span = column_flags.index(False)
            except (ValueError, AttributeError):
                column_span = len(column_flags)
            # Now search forward in rows and see how many bands are the same
            row_flags = [
                band.equal(other_row[c], ignore_jurisdictions=True)
                for other_row in table[r:]
            ]
            try:
                row_span = row_flags.index(False)
            except ValueError:
                row_span = len(row_flags)
            # Now make our data structures reflect that. First blow away the entire rectangle
            for rr in range(r, r + row_span):
                table[rr][c : c + column_span] = [Overlapped] * column_span
            cSpan[r : r + row_span, c : c + column_span] = 0
            rSpan[r : r + row_span, c : c + column_span] = 0
            # Now put the top left corner back
            table[r][c] = band
            cSpan[r, c] = column_span
            rSpan[r, c] = row_span

    # print (f"cSpan:\n{cSpan}")
    # print (f"rSpan:\n{rSpan}")
    # for row in table:
    #     for cell in row:
    #         if cell is None:
    #             word = "None"
    #         elif cell is Overlapped:
    #             word = "Ovlp"
    #         else:
    #             word = "Band"
    #         print (word+" ", end="")
    #     print ()

    # Start the HTML for the table
    text = ['<-- HTML output from pyfcctab package by Nathaniel.J.Livesey@jpl.nasa.gov-->']
    text += ['<link rel="stylesheet" href="fcc.css">']
    # with open("fcc.css", "r") as css_file:
    #    text = css_file.readlines()
    text += ['<table id="fcc-table">']
    text += ["<tr>"]
    # Add the header row
    for j in jurisdictions:
        text += ['<th id="fcc-th">' + str(j) + "</th>"]
    text += ["</tr>"]
    # Go through our arrays populate the HTML table
    for r, row in enumerate(table):
        text += ["<tr>"]
        for c, cell in enumerate(row):
            if cell is not Overlapped and cell is not None:
                text += [
                    f'<td id="fcc-td"; colspan="{cSpan[r,c]}"; rowspan="{rSpan[r,c]}">'
                ]
                text += [cell.to_html(
                    highlight_allocations=True,
                    tooltips=tooltips,
                    skip_jurisdictions=True,
                )]
                text += ["</td>"]
            if cell is None:
                text += [
                    f'<td id="fcc-td"; colspan="{cSpan[r,c]}"; rowspan="{rSpan[r,c]}">'
                    + "&nbsp;" + "</td>"]
        text += ["</tr>"]
    text += ["</table>"]

    # Now possibly append a description of all the footnotes
    if append_footnotes:
        footnotes = []
        definitions = {}
        for b in bands:
            footnotes += b.all_footnotes()
            definitions.update(b._footnote_definitions)
        footnotes = list(set(footnotes))
        footnotes.sort()

        for f in footnotes:
            text += [footnotedef2html(f, definitions)]

    # Now output the HTML
    return text
    if filename is None:
        display(HTML("\n".join(text)))
    else:
        with open(filename, "w") as file:
            file.writelines(text)
    return text
