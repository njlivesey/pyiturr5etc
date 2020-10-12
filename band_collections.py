"""Code for handling collections of bands"""

import astropy.units as units
from intervaltree import IntervalTree

__all__ = [ "Collection" ]

class BandCollection:
    """A collection of bands corresponding to one or more jurisdictions"""
    # This is basically a wrapper around IntervalTree, but not a subclass

    def __init__(self):
        self.data = IntervalTree()
    
    def __getitem__(self, key):
        """Get a specific item/range from the collection"""
        # Something of a wrapper around IntervalTree.__getitem__.
        # However, while the former returns a set of Intervals, we
        # want to return a list of bands.
        intervals = self.data.__getitem__(key)
        result = []
        for i in intervals:
            result.append(i.data)
        result.sort()
        return result

    def __iter__(self):
        """Generate an iterable over the collected bands"""
        for interval in self.data:
            yield interval.data
        
    def append(self, band):
        """Append a band to the collection"""
        # This just invokes the addi method from IntervalTree
        self.data.addi(band.bounds[0], band.bounds[1], band)

    def union(self, other):
        """Merge two sets of band collections without regard to their content"""
        result = BandCollection()
        result.data = self.data | other.data
        return result
        
    def merge(self, other):
        """Merge band collections, paying attention to quasi-duplicates (i.e., jurisdictions)"""
        # Build a raw lists that is the brain-dead merge of both
        interim = self.union(other)
        # Now go through and join bands together if they're the same
        # in all but region.
        result = BandCollection()
        for new_band in interim:
            # See if we already have an entry that's identical in
            # all but the jurisdiction.  If so, just note the
            # additional jurisdiction, if not, add this one.
            recorded_bands = result[new_band.bounds[0]:new_band.bounds[1]]
            isunique = True
            for recorded_band in recorded_bands:
                if recorded_band.equal(new_band, ignore_jurisdictions=True):
                    recorded_band.jurisdictions = list(
                        set(recorded_band.jurisdictions +
                            new_band.jurisdictions))
                    recorded_band.jurisdictions.sort()
                    isunique = False
            if isunique:
                result.append(new_band)
        return result

    def get_bands(self, f0, f1=None, adjacent=False, margin=None, oobe=False):
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
        # Now add any adjacent bands
        if adjacent:
            deltaF = 1.0*units.kHz
            adjacent_bands = []
            for f in [core_min-deltaF, core_max+deltaF]:
                adjacent_bands += self[f]
        else:
            adjacent_bands = []
        # Now combine all the bands found, remove duplicates and sort
        combined = core+marginal_bands+adjacent_bands
        result = list(set(combined))
        result.sort()
        return result

