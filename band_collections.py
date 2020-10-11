"""Code for handling collections of bands"""

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
