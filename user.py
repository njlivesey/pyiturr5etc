"""User level routines for the pyfcctab suite, including main table class"""

import astropy.units as units
import numpy as np
import docx
from intervaltree import Interval, IntervalTree

from .ingest import parse_all_tables, merge_band_lists

def read(filename="/users/livesey/corf/fcctable.docx", **kwargs):
    """Reader routine for FCC tables file"""
    return FCCTables.import_docx_file(filename, **kwargs)

class BandIndex(object):
    """A class for holding indices for a band list"""

    def find_bands(self, r0, r1=None, adjacent=False):
        """Find bands that fall in a range, possibly adjacent bands also"""
        try:
            n0 = len(r0)
        except TypeError:
            n0 = 1
        if n0 < 1 or n0 > 2:
            raise ValueError("Inappropriate size for range")
        if n0 == 2:
            if r1 is not None:
                raise ValueError("Conflicting requests for range")
            r1 = r0[1]
            r0 = r0[0]
        # Now find the bands.
        if r1 is None:
            intervals = self.tree.at(r0)
            if adjacent:
                raise ValueError("Cannot set adjacent for single valued searches")
        else:
            if adjacent:
                epsilon = 1e-10
            else:
                epslion = 0.0
            intervals = self.tree.overlap(r0*(1-epsilon), r1*(1+epsilon))
            
        return [i.data for i in intervals]
    
    @classmethod
    def generate(cls, collection, allow_overlaps=False):
        """Generate a set of indices for a band list"""
        # Create and fill a local copy of the bands bounds
        bounds = np.ndarray(shape=[len(collection),2]) << units.Hz
        for i, band in enumerate(collection):
            bounds[i,0] = band.bounds[0]
            bounds[i,1] = band.bounds[1]
        # Do some checks
        bandwidth = bounds[:,1] - bounds[:,0]
        # Check that all the bands have a positive bandwidth
        if np.any(bandwidth <= 0.0):
            raise ValueError("One or more bands has non-positive bandwidth")
        # Check that the bands are in the correct order
        step = bounds[1:,0] - bounds[0:-1,0]
        if np.any(step < 0.0):
            raise ValueError("One or more bands are in the wrong order")
        # Check for gaps
        if not allow_overlaps:
            gap = bounds[1:,0] - bounds[0:-1,1]
            for i, g in enumerate(gap):
                if g != 0:
                    print ("===================")
                    print (f"Gap = {g}")
                    print (collection[i])
                    print ("-------------------")
                    print (collection[i+1])
            if not np.all(np.isclose(gap, 0.0*units.Hz)):
                raise ValueError("One or more bands have gaps between them")
        # Now store things in an intervaltree
        tree = IntervalTree()
        for i in range(len(collection)):
            tree.addi(bounds[i,0], bounds[i,1], i)
        result = cls()
        result.bounds = bounds
        result.bandwidth = bandwidth
        result.tree = tree
        return result

class FCCTables(object):
    """Class that holds all information in the FCC tables document"""

    def find_bands(self, name, r0, r1=None, adjacent=False):
        band_indices = self.indices[name].find_bands(r0, r1, adjacent)
        return [self.collections[name][i] for i in band_indices]
    
    @classmethod
    def import_docx_file(cls, filename, **kwargs):
        """Read entire contents of FCC tables file"""

        # Open the FCC file
        docx_data = docx.Document(filename)
        # Read all the tables
        collections = parse_all_tables(docx_data, **kwargs)
        # Generate merged tables
        itu_all = merge_band_lists({tag: collections[tag] for tag in ["R1","R2","R3"]})
        usa_all = merge_band_lists({tag: collections[tag] for tag in ["F","NF"]})
        full = merge_band_lists({tag: collections[tag] for tag in ["R1","R2","R3","F","NF"]})
        # Now generate all the bands
        collections = {**collections, "ITU":itu_all, "USA":usa_all, "ALL": full}
        # Now generate all the indices
        indices = {}
        for jurisdiction, bands in collections.items():
            allow_overlaps = jurisdiction in ["ITU", "USA", "ALL"]
            print (f"for {jurisdiction} allow_overlaps is {allow_overlaps}")
            indices[jurisdiction] = BandIndex.generate(bands, allow_overlaps)
        # Generate the result
        result = cls()
        result.collections = collections
        result.indices = indices
        return result
