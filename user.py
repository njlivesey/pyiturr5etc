"""User level routines for the pyfcctab suite, including main table class"""

from intervaltree import Interval, IntervalTree
import astropy.units as units
import copy
import docx
import numpy as np
import pickle

from IPython.display import display, HTML
from .ingest_tables import parse_all_tables
from .additional_allocations import all_additions
from .band_collections import BandCollection
from .footnotes import ingest_footnote_definitions, footnotedef2html
    
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

def read(filename=default_path+"fcctable.docx",
         skip_additionals=False, **kwargs):
    """Reader routine for FCC tables file"""
    
    # Open the FCC file
    docx_data = docx.Document(filename)
    # Read all the tables
    collections = parse_all_tables(docx_data, **kwargs)
    result = FCCTables()
    result.collections = collections
    # Now possibly insert the additional bands.
    if not skip_additionals:
        # We'll create an interim result for the collections we have.
        print (f"Injecting additions in: ", end="")
        for jurisdiction, collection in result.collections.items():
            print(f"{jurisdiction}, ", end="")
            for new_band in all_additions:
                if jurisdiction in new_band.jurisdictions:
                    new_band = copy.deepcopy(new_band)
                    new_band.jurisdictions = [jurisdiction]
                    result.collections[jurisdiction].append(new_band)
        print ("done.")
    # Now we'll merge everything we have
    itu_regions = ["R1", "R2", "R3"]
    usa_regions = ["F", "NF"]
    all_regions = itu_regions + usa_regions
    print ("Merging: ITU, ", end="")
    itu_all = BandCollection()
    for tag in itu_regions:
        itu_all = itu_all.merge(result.collections[tag])
    print ("USA, ", end="")
    usa_all = BandCollection()
    for tag in usa_regions:
        usa_all = usa_all.merge(result.collections[tag])
    # Now add these merges to the results
    result.collections = {**result.collections, "ITU": itu_all,
                          "USA": usa_all}
    # Now do a merge on literally everything
    print ("all, ", end="")
    all_all = BandCollection()
    for tag in ["ITU", "USA"]:
        all_all = all_all.merge(result.collections[tag])
    result.collections = {**result.collections, "all": all_all}
    print ("done.")
    # Now go through all the bands we have and add the relevant
    # footnote definitions to them.  First read the footnote
    # definitions, and store them in the result
    print ("Footnote definitions: reading, ", end="")
    footnote_definitions = ingest_footnote_definitions(docx_data)
    result.footnote_definitions = footnote_definitions
    print ("appending, ", end="")
    for collection in result.collections.values():
        for b in collection:
            footnotes = b.all_footnotes()
            b._footnote_definitions = {}
            for f in footnotes:
                if f[-1] == "#":
                    f = f[:-1]
                if f in footnote_definitions:
                    b._footnote_definitions[f] = footnote_definitions[f]
    print ("done.")
    return result

def save(tables, filename=default_path+"fcctable.pickle"):
    """Write tables to a pickle file"""
    outfile = open(filename, 'wb')
    pickle.dump(tables, outfile)
    outfile.close()

def load(filename=default_path+"fcctable.pickle"):
    """Read tables from a pickle file"""
    infile = open(filename, 'rb')
    result = pickle.load(infile)
    infile.close()
    return result

def htmlcolumn(bands, append_footnotes=False):
    """Produce an HTML table corresponding to a set of bands"""
    # First loop over the bands and work out how many rows and columns
    # we'll need
    text = '<link rel="stylesheet" href="fcc.css">'
    text += '<table id="fcc-table">'
    for b in bands:
        text += '<tr><td id="fcc-td">'
        text += b.to_html(highlight_allocations=True, skip_jurisdictions=True)
        text += '</td></tr>\n'
    text += '</table>'

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

def htmltable(bands, append_footnotes=False):
    """Produce an HTML table corresponding to a set of bands"""
    # First loop over the bands and work out how many rows and columns
    # we'll need
    jurisdictions = []
    edges = []
    for b in bands:
        jurisdictions += b.jurisdictions
        edges += b.bounds
    edges = list(set(edges))
    edges.sort()
    edges = units.Quantity(edges)
    jurisdictions = list(set(jurisdictions))
    print (edges)

    text = '<link rel="stylesheet" href="fcc.css">'
    text += '<table id="fcc-table">'
    for b in bands:
        text += '<tr><td id="fcc-td">'
        text += b.to_html(highlight_allocations=True, skip_jurisdictions=False)
        text += '</td></tr>\n'
    text += '</table>'

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
