"""Code for handling collections of bands"""

import copy
from typing import Callable, Optional
import pint
import numpy as np

from intervaltree import IntervalTree

from .bands import Band

from pyiturr5etc.corf_pint import ureg

__all__ = ["BandCollection"]


class BandCollection:
    """A collection of bands corresponding to one or more jurisdictions"""

    # This is basically a wrapper a IntervalTree, but not a subclass

    def __init__(self, *args):
        """Create a band collection and possibly fill it with bands supplied"""
        self.data: IntervalTree[Band] = IntervalTree()
        self.metadata = {}
        for a in args:
            for b in a:
                self.append(b)

    def __getitem__(self, key) -> list[Band]:
        """Get a specific item/range from the collection"""
        # Something of a wrapper around IntervalTree.__getitem__.
        # However, while the former returns a set of Intervals, we
        # want to return a list of bands.
        return sorted([item.data for item in self.data[key]])

    def __iter__(self):
        """Generate an iterable over the collected bands"""
        bands = self.tolist()
        for b in bands:
            yield b

    def __len__(self):
        """Return number of bands"""
        return len(self.data)

    def begin(self):
        """Return lowest frequency"""
        return self.data.begin()

    def end(self):
        """Return lowest frequency"""
        return self.data.end()

    def append(self, band):
        """Append a band to the collection"""
        # This just invokes the addi method from IntervalTree.
        self.data.addi(band.bounds[0], band.bounds[1], band)

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
            # Do a deep copy because today's new_band becomes tomorrow's recorded_band,
            # so if we don't the input lists will get trampled on.  Don't deep copy
            # footnote definitions though (DOES IT DO THAT? DOESN'T SEEM TO SPEED UP IF
            # WE STASH).
            new_band = copy.deepcopy(interim_band)
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
                recorded_bands = result[new_band.bounds[0] : new_band.bounds[1]]
                add_band = True
                for recorded_band in recorded_bands:
                    if recorded_band.equal(new_band, ignore_jurisdictions=True):
                        recorded_band.jurisdictions = sorted(
                            list(
                                set(
                                    recorded_band.jurisdictions + new_band.jurisdictions
                                )
                            )
                        )
                        add_band = False
            if add_band:
                result.append(new_band)
        return result

    def get_boundaries(self):
        """Return an array that gives all the band edges, in order"""
        return sorted(self.data.boundary_table)

    def flatten(self):
        """Where bands overlap, split them, then merge contents of bands with same spans"""
        # First loop over the bands and slice at overlap boundaries, so all overlaps are
        # complete rather than partial.  This functionality is taken from intervaltree's
        # own splitoverlaps method.  First get all the starts and stops of each band
        bounds = self.get_boundaries()
        # Create an interim result
        interim = BandCollection()
        # Loop over all the frequency ranges
        for lbound, ubound in zip(bounds[:-1], bounds[1:]):
            # Check this range isn't too narrow
            if ubound - lbound < 10 * ureg.Hz:
                raise ValueError(
                    f"Tiny or negative band: {lbound} to {ubound} ({ubound-lbound})"
                )
            # Find the band(s) encompassing the midpoint of the current range
            relevant_bands = self[0.5 * (lbound + ubound)]
            # Loop over these and make them have the bounds of the current range we're
            # interested in, then append to our interim result
            for band in relevant_bands:
                new_band = copy.deepcopy(band)
                new_band.bounds[0] = lbound
                new_band.bounds[1] = ubound
                interim.append(new_band)
        # Now find the exactly overlapping bands that have resulted and merge them.
        result = BandCollection()
        for band in interim:
            # Find the bands overlapping the current one.
            overlapping_bands = interim[band.center]
            if len(overlapping_bands) == 1:
                # If there's only one band, presumably this one, then add to result
                if overlapping_bands[0] is not band:
                    raise ValueError("Confused flatten")
                result.append(band)
            else:
                # Otherwise, merge the bands
                merged_band = copy.deepcopy(band)
                for overlapping_band in overlapping_bands:
                    if overlapping_band is band:
                        continue
                    if not overlapping_band.has_same_bounds_as(merged_band):
                        raise ValueError(
                            f"Inappropriate overlap <{merged_band.compact_str()}> vs. "
                            f"<{overlapping_band.compact_str()}>"
                        )
                    merged_band = merged_band.combine_with(
                        overlapping_band, skip_bounds=True
                    )
                result.append(merged_band)
        return result

    def get_bands(
        self,
        f0: pint.Quantity,
        f1: Optional[pint.Quantity] = None,
        condition: Optional[Callable] = None,
        adjacent: Optional[bool] = False,
        recursively_adjacent: Optional[bool] = False,
    ) -> list[Band]:
        """Return the bands within f0-f1 (or enclosing f0).  Optionally return from a wider range"""
        # First get the band(s) that are explictly in the range discussed
        if f1 is None:
            bands = self[f0]
            f1 = f0
        else:
            bands = self[f0:f1]
        # Apply the conditions if supplied
        if condition:
            bands = [band for band in bands if condition(band)]
        # Now add any adjacent bands, possibly recursively.  The logic for this is a
        # little contorted but should be clear enough on careful reading.
        adjacency_pass = 0
        band_collection = BandCollection(bands)
        previous_collection_length = None
        if adjacent or recursively_adjacent:
            while (adjacent and adjacency_pass == 0) or (
                recursively_adjacent
                and (
                    len(band_collection) != previous_collection_length
                    or adjacency_pass == 0
                )
            ):
                adjacency_pass += 1
                previous_collection_length = len(band_collection)
                # If we've got some bands already, get the range from them, otherwise
                # resort to getting them from the inputs.
                if len(band_collection) != 0:
                    f_min = band_collection.begin()
                    f_max = band_collection.end()
                else:
                    f_min = f0
                    f_max = f1
                # Look slightly above/blow this range to find adjacent bands
                epsilon = 1e-5
                band_collection = BandCollection(
                    self[f_min * (1 - epsilon) : f_max * (1 + epsilon)]
                )
                # Make sure that the bands we found comply with our condition
                if condition:
                    band_collection = BandCollection(
                        band for band in band_collection if condition(band)
                    )
            result = list(band_collection)
        else:
            result = bands

        return sorted(list(set(result)))

    def tolist(self) -> list[Band]:
        """Convert band collection to sorted list"""
        return sorted([b.data for b in self.data])

    def stitch(self, condition=None) -> "BandCollection":
        """Group adjacent/overlapping bands together in ever-larger groups provided
        condition is met"""
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
            center = 0.5 * (lbound + ubound)
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
                    assert accumulator.overlaps(band) or accumulator.is_adjacent(
                        band
                    ), "Confused aboue band adjecency/overlap"
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

    def find_closest_matching_band(
        self,
        frequency: pint.Quantity,
        direction: int,
        condition: Callable[[Band], bool],
        include_band_in_this_frequency: bool = False,
    ) -> Band:
        """Iterate through the collection to find the nearest band matching conditions
        Parameters
        ----------
        frequency : pint.Quantity
            The frequency to start the search from (defaults to ignoring the band that
            includes this frequency)
        direction : int
            +1 for looking in above supplied frequency, -1 for looking below
        condition : Callable[[Band], bool]
            Callable that, when supplied a band, returns True if the band meets the
            user's condition, False if not.
        include_band_in_this_frequency : bool
            If set, then, if a band encompasing a supplied frequency meets the condition
            return it.
        Returns
        -------
        Band
            Return the closest band matching the condition
        """
        if direction not in [-1, 1]:
            raise ValueError(
                f"Invalid value for direction, must be -1 or +1, got {direction}"
            )
        # First work out the boundaries for all the bands and the midpoints of all the
        # associated panels
        boundaries = pint.Quantity.from_sequence(self.get_boundaries())
        mid_points = 0.5 * (boundaries[:-1] + boundaries[1:])
        # Now work out where we are in that setup.  We're above the boundary given by
        # np.searchsorted - 1, so in the panel given by np.searchsorted - 1
        i_panel = np.searchsorted(boundaries, frequency) - 1
        starting_panel = i_panel
        while 0 < i_panel < len(mid_points):
            # Identify bands(s) that overlap this mid_point
            candidate_bands = self[mid_points[i_panel]]
            # Now loop over those bands and return the first one we find that matches
            for candidate_band in candidate_bands:
                # If this band matches our condition, then we're done, so just return
                # this band (unless it's the one we started at, unless that's OK.)
                if condition(candidate_band) and (
                    (i_panel != starting_panel) or include_band_in_this_frequency
                ):
                    return candidate_band
            # Move the pointer to the next panel
            i_panel += direction
        # We got to the end of this list without finding a match, return None
        return None
