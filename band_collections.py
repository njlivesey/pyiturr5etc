"""Code for handling collections of bands"""

import astropy.units as units
from intervaltree import IntervalTree
import copy
import numpy as np

__all__ = [ "Collection" ]

class BandCollection:
    """A collection of bands corresponding to one or more jurisdictions"""
    # This is basically a wrapper around IntervalTree, but not a subclass

    def __init__(self, *args):
        """Create a band collection and possibly fill it with bands supplied"""
        self.data = IntervalTree()
        self.metadata = dict()
        for a in args:
            for b in a:
                self.append(b)
    
    def __getitem__(self, key):
        """Get a specific item/range from the collection"""
        # Something of a wrapper around IntervalTree.__getitem__.
        # However, while the former returns a set of Intervals, we
        # want to return a list of bands.
        try:
            key = round(key.to(units.Hz).value)
        except AttributeError:
            key = slice(
                round(key.start.to(units.Hz).value),
                round(key.stop.to(units.Hz).value))
        intervals = self.data.__getitem__(key)
        result = []
        for i in intervals:
            result.append(i.data)
        return sorted(result)

    def __iter__(self):
        """Generate an iterable over the collected bands"""
        bands = self.tolist()
        for b in bands:
            yield b

    def __len__(self):
        """Return number of bands"""
        return len(self.data)
        
    def append(self, band):
        """Append a band to the collection"""
        # This just invokes the addi method from IntervalTree.  Use
        # integer Hertz as the indexing.  This is to avoid rounding
        # issues and lack of clarity when mixing MHz, GHz, etc.
        self.data.addi(
            round(band.bounds[0].to(units.Hz).value),
            round(band.bounds[1].to(units.Hz).value),
            band)

    def union(self, other):
        """Merge two sets of band collections without regard to their content"""
        result = BandCollection()
        result.data = self.data | other.data
        return result
        
    def merge(self, other, single_jurisdiction=None):
        """Merge band collections, paying attention to quasi-duplicates (i.e., jurisdictions)"""
        # Build a raw lists that is the brain-dead merge of both
        interim = self.union(other)
        # If we're doing a single jurisdiction, just go through them all and add them if appropriate
        # Now go through and join bands together if they're the same
        # in all but region.
        result = BandCollection()
        for interim_band in interim:
            # Do a deep copy because today's new_band becomes
            # tomorrow's recorded_band, so if we don't the input lists
            # will get trampled on.  Don't deep copy footnote
            # definitions though.            
            new_band = interim_band.deepcopy()
            add_band = True
            if single_jurisdiction:
                if not new_band.has_jurisdiction(single_jurisdiction):
                    continue
                new_band.jurisdictions = [single_jurisdiction]
            else:
                # See if we already have an entry that's identical in
                # all but the jurisdiction.  If so, just note the
                # additional jurisdiction, in the already-recorded
                # band, if not, add this one.
                recorded_bands = result[new_band.bounds[0]:new_band.bounds[1]]
                add_band = True
                for recorded_band in recorded_bands:
                    if recorded_band.equal(new_band, ignore_jurisdictions=True):
                        recorded_band.jurisdictions = sorted(list(
                            set(recorded_band.jurisdictions +
                                new_band.jurisdictions)))
                        add_band = False
            if add_band:
                result.append(new_band)
        return result

    def get_boundaries(self):
        """Return an array that gives all the band edges, in order"""
        return sorted(self.data.boundary_table)*units.Hz

    def flatten(self):
        """Where bands overlap, split them, then merge contents of bands with same spans"""
        # First loop over the bands and slice at overlap boundaries, so
        # all overlaps are complete rather than partial.  This
        # functionality is taken from intervaltree's own splitoverlaps
        # method.
        bounds = self.get_boundaries()
        interim = BandCollection()
        for lbound, ubound in zip(bounds[:-1], bounds[1:]):
            if ubound-lbound < 10*units.Hz:
                raise ValueError(f"Tiny or negative band: {lbound} to {ubound} ({ubound-lbound})")
            relevant_bands = self[0.5*(lbound+ubound)]
            for band in relevant_bands:
                new_band = band.deepcopy()
                new_band.bounds[0] = np.around(lbound.to(band.bounds[0].unit), 5)
                new_band.bounds[1] = np.around(ubound.to(band.bounds[0].unit), 5)
                interim.append(new_band)
        # Now find the exactly overlapping bands that have resulted and merge them.
        result = BandCollection()
        for band in interim:
            overlapping_bands = interim[band.center]
            if len(overlapping_bands) == 1:
                # If there's only one band, this one, then add to result
                if overlapping_bands[0] is not band:
                    raise ValueError("Confused flatten")
                result.append(band)
            else:
                # Otherwise, merge the bands
                merged_band = band.deepcopy()
                for overlapping_band in overlapping_bands:
                    if overlapping_band is band:
                        continue
                    if not overlapping_band.has_same_bounds_as(merged_band):
                        print (merged_band.compact_str())
                        print (overlapping_band.compact_str())
                        raise ValueError(f"Inappropriate overlap")
                    merged_band = merged_band.combine_with(overlapping_band, skip_bounds=True)
                result.append(merged_band)
            pass
        return result

    def get_bands(self, f0, f1=None, condition=None, adjacent=False, margin=None, oobe=False):
        """Return the bands within f0-f1 (or enclosing f0).  Optionally return from a wider range"""
        # Do some error checking
        if oobe:
            if margin is not None:
                raise ValueError("Cannot set oobe and select a margin")
            else:
                margin = 2.5
        # First get the band(s) that are explictly in the range discussed
        if f1 is None:
            core = self[f0]
        else:
            core = self[f0:f1]
        if len(core) == 0:
            return []
        # Apply the conditions if supplied
        if condition:
            core = [band for band in core if condition(band)]
        # Work out what the core range is.
        core_min = min(b.bounds[0] for b in core)
        core_max = max(b.bounds[1] for b in core)
        core_bandwidth = core_max - core_min
        # Now add any bands within a given margin of the core band(s).
        if margin is not None:
            # Can supply as fraction of bandwidth or in frequency
            margin_fraction = None
            # Think about cases where margin has units of some kind
            if hasattr(margin,"to"):
                try:
                    margin_frequency = margin.to(units.Hz)
                except units.UnitConversionError:
                    pass
                # Now the case where margin is a fraction
                try:
                    margin_fraction = margin.to(units.dimensionless_unscaled)
                except units.UnitConversionError:
                    pass
            else:
                # If margin is unitless, it must be fractional
                margin_fraction = margin    
            if margin_fraction is not None:
                margin_frequency = (margin_fraction-0.5)*core_bandwidth
            full_min = core_min - margin_frequency
            full_max = core_max + margin_frequency
            marginal_bands = self[full_min:full_max]
        else:
            marginal_bands = []
        # Apply condition to the marginal bands if supplied
        if condition:
            marginal_bands = [band for band in marginal_bands if condition(band)]

        # Now add any adjacent bands
        if adjacent:
            deltaF = 1.0*units.kHz
            # Identify all the bands that are truely adjacent
            truly_adjacent_bands = []
            for f in [core_min-deltaF, core_max+deltaF]:
                truly_adjacent_bands += self[f]
            # Now make the span of this collection the span of what we're after.
            adjacent_min = min(b.bounds[0] for b in truly_adjacent_bands)
            adjacent_max = max(b.bounds[1] for b in truly_adjacent_bands)
            adjacent_bands = self[adjacent_min:adjacent_max]
        else:
            adjacent_bands = []
        # Apply condition to the adjacent bands if supplied
        if condition:
            adjacent_bands = [band for band in adjacent_bands if condition(band)]
        # Now combine all the bands found, remove duplicates and sort
        combined = core+marginal_bands+adjacent_bands
        return sorted(list(set(combined)))

    def tolist(self):
        """Convert band collection to sorted list"""
        return sorted([b.data for b in self.data])

    def stitch(self, condition=None):
        """Group adjacent/overlapping bands together in ever-larger groups provided condition is met"""
        # Keep a list of the bands we've got thus far
        bands_claimed = set()
        # Create an empty result
        result = BandCollection()
        # Create a place to store the ongoing band
        accumulator = None
        # Get all the band edges
        bounds = self.get_boundaries()
        # Loop over all the intervals
        for lbound, ubound in zip(bounds[:-1], bounds[1:]):
            # Find all the bands that overlap the midpoint of this little span
            center = 0.5*(lbound+ubound)
            bands = self.get_bands(center)
            # Keep track of whether we added bands to the accumulator
            accumulator_updated = False
            # Loop over these bands
            for band in bands:
                # If this band has already been claimed, then move on
                if band in bands_claimed:
                    continue
                # If this band does not meet the condition, then move on
                if condition is not None:
                    if not condition(band):
                        continue
                # OK, so this is a new band that meets our condition
                if accumulator is not None:
                    # If we're accumulating a band, add to it
                    assert accumulator.overlaps(band) or accumulator.is_adjacent(band), \
                        "Confused aboue band adjecency/overlap"
                    accumulator = accumulator.combine_with(band)
                    accumulator_updated = True
                else:
                    # Otherwise this band is our new accumulator
                    accumulator = band
                    accumulator_updated = True
            # If we didn't grow the accumualtor, or start a new one,
            # and the accumulator doesn't fully cover this band then
            # we're done with this accumulation.
            if accumulator is not None:
                if not accumulator_updated and not accumulator.covers(ubound):
                    result.append(accumulator)
                    accumulator = None
        # When done with the loop, add the accumulator
        if accumulator is not None:
            result.append(accumulator)
        return result
