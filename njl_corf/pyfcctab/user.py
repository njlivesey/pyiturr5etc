"""User level routines for the pyfcctab suite, including main table class"""

import copy
import pickle
import numpy as np
import pathlib

import docx
import pint

from IPython.display import display, HTML
from .ingest_tables import parse_all_tables
from .additional_allocations import all_additions
from .band_collections import BandCollection
from .footnotes import ingestfootnote_definitions, footnotedef2html
from .jurisdictions import Jurisdiction


class FCCTables:
    """Class that holds all information in the FCC tables document"""

    def __init__(
        self,
        version: str,
        collections: dict[BandCollection],
        footnote_definitions: dict = None,
    ):
        """Initialize an FCCTables object

        Parameters
        ----------
        version : str
            The version of the Microsoft Word file from which the data are drawn
        collections : dict[BandCollection]
            The various band collections (international and USA)
        """
        self.version = version
        self.collections = collections
        self.footenote_definitions = (footnote_definitions,)

    @property
    def r1(self):
        """The ITU-R1 collection"""
        return self.collections["R1"]

    @property
    def r2(self):
        """The ITU-R2 collection"""
        return self.collections["R2"]

    @property
    def r3(self):
        """The ITU-R3 collection"""
        return self.collections["R3"]

    @property
    def f(self):
        """The federal collection"""
        return self.collections["F"]

    @property
    def nf(self):
        """The non-federal collection"""
        return self.collections["NF"]

    @property
    def itu(self):
        """The complete set of ITU collections"""
        return self.collections["ITU"]

    @property
    def usa(self):
        """The complete set of USA collections"""
        return self.collections["USA"]

    @property
    def all(self):
        """The complete set of all collections"""
        return self.collections["all"]


DEFAULT_PATH = "/users/livesey/corf/data/"


def read(
    filename: str = None,
    skip_additionals: bool = False,
    skip_footnote_definitions: bool = False,
    **kwargs,
) -> FCCTables:
    """_summary_

    Parameters
    ----------
    filename : str, optional
        The Word file to read (defaults to sensible option if omitted)
    skip_additionals : bool, optional
        If set, do not isert additional footnote-derived bands
    skip_footnote_definitions : bool, optional
        If set, do not bother to read/parse the footnote definitions (for speed)

    Returns
    -------
    FCCTables
        All the information from the FCC tables
    """
    if filename is None:
        filename = DEFAULT_PATH + "fcctable-2022-08-23.docx"
    # Open the FCC file
    docx_data = docx.Document(filename)
    # Read all the tables
    collections, version = parse_all_tables(docx_data, filename, **kwargs)
    # Now possibly insert the additional bands.
    if not skip_additionals:
        # We'll create an interim result for the collections we have.
        print("Injecting additions in: ", end="")
        for jname, collection in collections.items():
            jurisdiction = Jurisdiction.parse(jname)
            print(f"{jurisdiction.name}, ", end="")
            for new_band in all_additions:
                if jurisdiction in new_band.jurisdictions:
                    inserted_band = copy.deepcopy(new_band)
                    inserted_band.jurisdictions = [jurisdiction]
                    collection.append(inserted_band)
            collections[jname] = collection.flatten()
        print("done.")
    # Now we'll merge everything we have
    itu_regions = ["R1", "R2", "R3"]
    usa_regions = ["F", "NF"]
    print("Merging: ITU, ", end="")
    itu_all = BandCollection()
    for tag in itu_regions:
        itu_all = itu_all.merge(collections[tag])
    print("USA, ", end="")
    usa_all = BandCollection()
    for tag in usa_regions:
        usa_all = usa_all.merge(collections[tag])
    # Now add these merges to the results
    collections = collections | {"ITU": itu_all, "USA": usa_all}
    # Now do a merge on literally everything
    print("all, ", end="")
    all_all = BandCollection()
    for tag in ["ITU", "USA"]:
        all_all = all_all.merge(collections[tag])
    collections = collections | {"all": all_all}
    print("done.")
    # Now go through all the bands we have and add the relevant
    # footnote definitions to them.  First read the footnote
    # definitions, and store them in the result
    if not skip_footnote_definitions:
        print("Footnote definitions: reading, ", end="")
        footnote_definitions = ingestfootnote_definitions(docx_data)
        print("appending, ", end="")
        for collection in collections.values():
            for b in collection:
                footnotes = b.all_footnotes()
                b.footnote_definitions = {}
                for f in footnotes:
                    if f[-1] == "#":
                        f = f[:-1]
                    if f in footnote_definitions:
                        b.footnote_definitions[f] = footnote_definitions[f]
        print("done.")
    # Build and return the result
    return FCCTables(
        version=version,
        collections=collections,
        footnote_definitions=footnote_definitions,
    )


def save(tables, filename=DEFAULT_PATH + "fcctable.pickle"):
    """Write tables to a pickle file"""
    outfile = open(filename, "wb")
    pickle.dump(tables, outfile)
    outfile.close()


def load(filename=DEFAULT_PATH + "fcctable.pickle"):
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
            definitions.update(b.footnote_definitions)
        footnotes = list(set(footnotes))
        footnotes.sort()

        for f in footnotes:
            text += footnotedef2html(f, definitions)

    # Now output the HTML
    display(HTML(text))
    return text


# pylint: disable-next=too-many-locals, too-many-branches, too-many-statements
def htmltable(
    bands,
    append_footnotes: bool = False,
    tooltips: bool = True,
    filename: str = None,
):
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
    n_columns = len(jurisdictions)
    n_rows = len(edges) - 1

    # Now set up some data structures to define the table.  First its
    # contents (None initially)
    table = list()
    for r in range(n_rows):
        table.append([None for c in range(n_columns)])
    # Now some arrays that define the span of each cell, 1x1 to start with
    r_span = np.ones(shape=[n_rows, n_columns], dtype=np.int_)
    c_span = np.ones(shape=[n_rows, n_columns], dtype=np.int_)

    # Now loop over the bands and put them in cells
    for b in bands:
        # Identify which rows this band spans.
        row_span = np.searchsorted(edges, b.bounds)
        # Identify which columns this band should be listed in
        column_flags = [j in b.jurisdictions for j in jurisdictions]
        for r in range(row_span[0], row_span[1]):
            for c in range(n_columns):
                if column_flags[c]:
                    if table[r][c] is not None:
                        raise ValueError(f"Overlapping bands for {r}, {c}")
                    else:
                        table[r][c] = b
    # Now go through the cells and work out which ones should be aggolomorated
    for r in range(n_rows):
        for c in range(n_columns):
            band = table[r][c]
            if band is None or band == "overlapped":
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
                table[rr][c : c + column_span] = ["overlapped"] * column_span
            c_span[r : r + row_span, c : c + column_span] = 0
            r_span[r : r + row_span, c : c + column_span] = 0
            # Now put the top left corner back
            table[r][c] = band
            c_span[r, c] = column_span
            r_span[r, c] = row_span

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
    text = [
        "<-- HTML output from pyfcctab package by Nathaniel.J.Livesey@jpl.nasa.gov -->"
    ]
    # Append the style sheet information
    with open(
        pathlib.Path(__file__).parent / "fcc.css", "r", encoding="utf-8"
    ) as css_file:
        style_data = css_file.read().splitlines()
    text += ["<style>"] + style_data + ["</style>"]
    # text += ['<link rel="stylesheet" href="fcc.css">']
    # Now start on the table``
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
            if cell != "overlapped" and cell is not None:
                text += [
                    f'<td id="fcc-td"; colspan="{c_span[r,c]}"; rowspan="{r_span[r,c]}">'
                ]
                text += [
                    cell.to_html(
                        highlight_allocations=True,
                        tooltips=tooltips,
                        skip_jurisdictions=True,
                    )
                ]
                text += ["</td>"]
            if cell is None:
                text += [
                    f'<td id="fcc-td"; colspan="{c_span[r,c]}"; rowspan="{r_span[r,c]}">'
                    + "&nbsp;"
                    + "</td>"
                ]
        text += ["</tr>"]
    text += ["</table>"]

    # Now possibly append a description of all the footnotes
    if append_footnotes:
        footnotes = []
        definitions = {}
        for b in bands:
            footnotes += b.all_footnotes()
            definitions.update(b.footnote_definitions)
        footnotes = list(set(footnotes))
        footnotes.sort()

        for f in footnotes:
            text += [footnotedef2html(f, definitions)]

    # Now output the HTML
    if filename:
        with open(
            filename,
            mode="w",
            encoding="utf-8",
        ) as file:
            file.writelines(text)
    return text
