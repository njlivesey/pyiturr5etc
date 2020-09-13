"""User level routines for the pyfcctab suite, including main table class"""

from intervaltree import Interval, IntervalTree
import astropy.units as units
import copy
import docx
import numpy as np

from .ingest import parse_all_tables, merge_band_lists
from .additional_allocations import all_additions


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
                raise ValueError(
                    "Cannot set adjacent for single valued searches")
        else:
            if adjacent:
                epsilon = 1e-6
            else:
                epsilon = 0.0
            intervals = self.tree.overlap(r0*(1-epsilon), r1*(1+epsilon))
        return [i.data for i in intervals]

    @classmethod
    def generate(cls, collection, allow_overlaps=False):
        """Generate a set of indices for a band list"""
        # Create and fill a local copy of the bands bounds
        bounds = np.ndarray(shape=[len(collection), 2]) << units.Hz
        for i, band in enumerate(collection):
            bounds[i, 0] = band.bounds[0]
            bounds[i, 1] = band.bounds[1]
        # Do some checks
        bandwidth = bounds[:, 1] - bounds[:, 0]
        # Check that all the bands have a positive bandwidth
        if np.any(bandwidth <= 0.0):
            raise ValueError("One or more bands has non-positive bandwidth")
        # Check that the bands are in the correct order
        step = bounds[1:, 0] - bounds[0:-1, 0]
        if np.any(step < 0.0):
            raise ValueError("One or more bands are in the wrong order")
        # Check for gaps
        if not allow_overlaps:
            gap = bounds[1:, 0] - bounds[0:-1, 1]
            for i, g in enumerate(gap):
                if g != 0:
                    print("===================")
                    print(f"Gap = {g}")
                    print(collection[i])
                    print("-------------------")
                    print(collection[i+1])
            if not np.all(np.isclose(gap, 0.0*units.Hz)):
                raise ValueError("One or more bands have gaps between them")
        # Now store things in an intervaltree
        tree = IntervalTree()
        for i in range(len(collection)):
            tree.addi(bounds[i, 0], bounds[i, 1], i)
        result = cls()
        result.bounds = bounds
        result.bandwidth = bandwidth
        result.tree = tree
        return result


class FCCTables(object):
    """Class that holds all information in the FCC tables document"""

    def find_bands(self, name, r0, r1=None, adjacent=False):
        band_indices = self.indices[name].find_bands(r0, r1, adjacent)
        bands = [self.collections[name][i] for i in band_indices]
        bands.sort()
        return bands

    def inject_band(self, name, new_band):
        """Insert/merge new band into list as appropriate"""
        # We'll build up lists of bands to add and remove, then do
        # them all at once at the end.  First find the indices of
        indices_to_delete = []
        bands_to_add = []
        # bands that impinge on the new one.
        affected_band_indices = self.indices[name].find_bands(
            new_band.bounds)
        working_new_band = copy.deepcopy(new_band)
        for ai in affected_band_indices:
            affected_band = copy.deepcopy(self.collections[name][ai])
            if affected_band.bounds[0] < new_band.bounds[0]:
                # We need to split the affected band because it starts
                # before the new band does.  Create the lower part and
                # log it for addition.                
                additional_band = copy.deepcopy(affected_band)
                additional_band.bounds[1] = new_band.bounds[0]
                bands_to_add.append(additional_band)
                # Tweak the working copy of the affected band such
                # that it starts at the same place as the new band
                # does.
                print (f"Here: {affected_band.range} -> {new_band.range}")
                affected_band.bounds[0] = new_band.bounds[0]
                print (f"Gives: {affected_band.range}")
            if affected_band.bounds[1] > new_band.bounds[1]:
                # We need to split the affected band because it ends
                # after the new band does.  Create an upper part and
                # log it for additon.
                additional_band = copy.deepcopy(affected_band)
                additional_band.bounds[0] = new_band.bounds[1]
                bands_to_add.append(additional_band)
                # Tweak the working copy of the affected band such
                # that it finishes at the same place as the new band
                # does.
                print (f"Here: {affected_band.range} -> {new_band.range}")
                affected_band.bounds[1] = new_band.bounds[1]
                print (f"Gives: {affected_band.range}")
            # Now, while there may well be other bands affected by the
            # new band, at this point we don't care about them, all we
            # need to do is add the allocations/footnotes/etc. from
            # the new band to a working copy of the affected one.
            affected_band = affected_band.combine_with(
                new_band, skip_bounds=True)
            bands_to_add.append(affected_band)
            # Mark the old copy of the affected band for deletion.
            indices_to_delete.append(ai)
        # Now do all the deletions
        for i in sorted(indices_to_delete, reverse=True):
            del self.collections[name][i]
        # Now the additions.
        self.collections[name] += bands_to_add
        self.collections[name].sort()
        # Now make a new index for this collection
        self.indices[name] = BandIndex.generate(
            self.collections[name])
         

def read(filename="/users/livesey/corf/fcctable.docx",
         skip_additionals=False, **kwargs):
    """Reader routine for FCC tables file"""
    
    # Open the FCC file
    docx_data = docx.Document(filename)
    # Read all the tables
    collections = parse_all_tables(docx_data, **kwargs)
    result = FCCTables()
    result.collections = collections
    # Index the collections thus far
    result.indices = {}
    for jurisdiction, bands in result.collections.items():
        result.indices[jurisdiction] = BandIndex.generate(bands)
    # Now possibly insert the additional bands.
    if not skip_additionals:
        # We'll create an interim result for the collections we have.
        for jurisdiction, collection in result.collections.items():
            for new_band in all_additions:
                if jurisdiction in new_band.jurisdictions:
                    result.inject_band(jurisdiction, new_band)
    # Now we'll merge everything we have
    itu_regions = ["R1", "R2", "R3"]
    usa_regions = ["F", "NF"]
    all_regions = itu_regions + usa_regions
    itu_all = merge_band_lists(
        {tag: result.collections[tag] for tag in itu_regions})
    usa_all = merge_band_lists(
        {tag: result.collections[tag] for tag in usa_regions})
    full = merge_band_lists(
        {tag: result.collections[tag] for tag in all_regions})
    # Now add these merges to the results
    result.collections = {**result.collections, "ITU": itu_all,
                   "USA": usa_all, "ALL": full}
    # Now generate all the indices
    indices = {}
    for jurisdiction, bands in result.collections.items():
        result.indices[jurisdiction] = BandIndex.generate(
            bands, allow_overlaps = jurisdiction not in all_regions)

    return result
