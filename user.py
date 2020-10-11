"""User level routines for the pyfcctab suite, including main table class"""

from intervaltree import Interval, IntervalTree
import astropy.units as units
import copy
import docx
import numpy as np
import pickle

from .ingest import parse_all_tables
from .additional_allocations import all_additions
from .band_collections import BandCollection
    
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
    print ("done.")
    # Now add these merges to the results
    result.collections = {**result.collections, "ITU": itu_all,
                   "USA": usa_all}
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

    
