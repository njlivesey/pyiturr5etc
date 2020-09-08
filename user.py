"""User level routines for the pyfcctab suite, including main table class"""

import astropy.units as units
import numpy as np
import docx

from .ingest import parse_all_tables, merge_band_lists

def read(filename="/users/livesey/corf/fcctable.docx", **kwargs):
    """Reader routine for FCC tables file"""
    return FCCTables.import_docx_file(filename, **kwargs)

class BandIndex(object):
    """A class for holding indices for a band list"""

    def find_bands(self, r0, r1=None, adjacent=False):
        """Find bands that fall in a range, possibly adjacent bands also"""
        # First work out what we've been asked for
        if len(r0) == 1:
            pass
        elif len(r0) == 2:
            if r1 is not None:
                raise ValueError("Conflicting arguments")
            r1 = r0[1]
            r0 = r0[0]
        else:
            raise ValueError("In appropriate range argument for band search")
        # Now find the bands.
        if not adjacent:
            # If adjacent is not set, then we look for those that
            # start and end within our range.
            first = np.searchsorted(self.bounds[:,0], r0, side="left")
            if r1 is not None:
                last = np.value_locate(self.bounds[self.upper_order,1], r1, side="right")
            else:
                last = first
        else:
            # If adjacent bands do count, then search a different way
            first = np.searchsorted(self.bounds[self.upper_order,1], r0, side="right")
            last = np.searchsorted(self.bounds[:,0], r1, side="left")
        return first, last
    
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
        # Generate an index for the upper bounds (which might be out of order)
        upper_order = np.argsort(bounds[:,1])
        # OK, now set this up as an index and return it
        result = cls()
        result.bounds = bounds
        result.upper_order = upper_order
        return result

class FCCTables(object):
    """Class that holds all information in the FCC tables document"""
    
    @classmethod
    def import_docx_file(cls, filename, **kwargs):
        """Read entire contents of FCC tables file"""

        # Open the FCC file
        docx_data = docx.Document(filename)
        # Read all the tables
        itu, usa = parse_all_tables(docx_data, **kwargs)
        print (usa["F"]
        # Generate merged tables
        itu_all = merge_band_lists(itu)
        usa_all = merge_band_lists(usa)
        # Now generate all the bands
        collections = {**itu, **usa, "ITU":itu_all, "USA":usa_all}
        # Now generate all the indices
        indices = {}
        for jurisdiction, bands in collections.items():
            allow_overlaps = jurisdiction in ["ITU", "USA"]
            print (f"for {jurisdiction} allow_overlaps is {allow_overlaps}")
            indices[jurisdiction] = BandIndex.generate(bands, allow_overlaps)
        # Generate the result
        result = cls()
        result.collections = collections
        result.indices = indices
        return result
