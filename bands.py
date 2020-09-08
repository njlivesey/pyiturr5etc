"""Code for handling bands (i.e., cells in the FCC tables)"""

import re
import docx
import fnmatch
import numpy as np
import astropy.units as units

from .allocations import Allocation
from .utils import cell2text, text2lines

__all__ = [ "NotBoundsError", "Bounds", "NotBandError", "Band" ]

# First a supporting class
# --------------------------------------------------------------------- Bounds
class NotBoundsError(Exception):
    """Exception used to flag failed parse of Bounds"""
    pass

class Bounds:
    """A frequeny bounds"""
    def __init__(self, low, high):
        self.bounds = (low, high)
        self.bandwidth = self.bounds[1] - self.bounds[0]
        self.center = 0.5*(self.bounds[0] + self.bounds[1])

    def __str__(self):
        result = f"{self.bounds[0]}-{self.bounds[1]}"
        return result

    def __eq__(self, a):
        return self.bounds == a.bounds

    def __ne__(self, a):
        return not (self == a)

    def __gt__(self, a):
        return self.bounds[0] > a.bounds[0]

    def __lt__(self, a):
        return self.bounds[0] < a.bounds[0]

    # For the >= or <= comparison operators, we'll mainly key off the
    # lower bound, but if they are the same, the upper bound wil come
    # into play.
    def __ge__(self, a):
        if self.bounds[0] >= a.bounds[0]:
            return True
        # if np.isclose(self.bounds[0], a.bounds[0]):
        #     return self.bounds[1] > a.bounds[1]
        return False

    def __le__(self, a):
        if self.bounds[0] <= a.bounds[0]:
            return True
        # if np.isclose(self.bounds[0], a.bounds[0]):
        #     return self.bounds[1] > a.bounds[1]
        return False

    @classmethod
    def parse(cls, text, unit):
        """Turn a string giving a frequency range into a bounds object"""
        re_float = r"[0-9]+(?:\.[0-9]+)?"
        re_bounds = f"^({re_float})-({re_float})[\w]*(\(Not allocated\))?$"
        match = re.match(re_bounds, text)
        if match is not None:
            return cls(
                float(match.group(1))*unit,
                float(match.group(2))*unit)
        # Perhaps this is the "below the bottom" case.
        re_bottom = f"^Below ({re_float}) \(Not Allocated\)$"        
        match = re.match(re_bottom, text)
        if match is not None:
            return cls(0.0*unit, float(match.group(1))*unit)
        # Otherwise, this is not a bound
        raise NotBoundsError(f"Not a valid range: {text}")
            
# --------------------------------------------------------------------- Bands

class NotBandError(Exception):
    """Exception used to indicate failed parse of band"""
    pass

class Band:
    """A frequency bounds and the allocations thereto (i.e., contents of a cell in the FCC tables)"""
    def __str__(self, separator="\n"):
        """Return a string representation of a Band"""
        result = str(self._bounds)
        if self.jurisdictions is not None:
            result = result + ' [' + ','.join(self.jurisdictions) + ']'
        result = result + separator
        for a in self.allocations:
            result = result + str(a) + separator
        if self.footnotes != "":
            result = result + separator + " ".join(self.footnotes)
        if self.fcc_rules is not None:
            result = result + separator + '[' + '; '.join(self.fcc_rules) + ']'
        return (result)

    def compact_str(self):
        return self.__str__(separator="/")

    def finalize(self):
        """Make sure all the various pieces of information for a band are correct"""
        self.allocations = []
        n_allocations = len(self.primary_allocations) + len(self.secondary_allocations)
        for a in self.primary_allocations:
            assert a.primary, "A secondary allocation ended up in the primary list somehow"
            a.co_primary = len(self.primary_allocations) > 1
            a.exclusive = n_allocations == 1
            a.bounds = self.bounds
            self.allocations.append(a)
        for a in self.secondary_allocations:
            assert not a.primary, "A primary allocation ended up in the secondary list somehow"
            a.co_primary = False
            a.exclusive = n_allocations == 1
            a.bounds = self.bounds
            self.allocations.append(a)

    def __eq__(self,a):
        """Compare two sets of Band information"""
        if a is None:
            return False
        if self._bounds != a._bounds:
            return False
        if len(self.allocations) != len(a.allocations):
            return False
        for sa, aa in zip(self.allocations, a.allocations):
            if sa != aa:
                return False
        if (self.fcc_rules is None) != (a.fcc_rules is None):
            return False
        try:
            if len(self.fcc_rules) != len(a.fcc_rules):
                return False
            for sr, ar in zip(self.fcc_rules, a.fcc_rules):
                if sr !=ar:
                    return False
        except TypeError:
            pass
        return self.footnotes == a.footnotes
        
    def __ne__(self, a):
        return not (self == a)

    def __gt__(self, a):
        return self.bounds > a.bounds

    def __lt__(self, a):
        return self.bounds < a.bounds

    def __ge__(self, a):
        return self.bounds >= a.bounds

    def __le__(self, a):
        return self.bounds <= a.bounds

    def __add__(self, a):
        return self.combine_bands(a)

    def all_footnotes(self):
        result = self.footnotes
        for a in self.allocations:
            result = result + a.footnotes
        return list(set(result))

    def combine_bands(self, a, force=False):
        """Merge the contents of two different bands"""

        def _combine_elements(a,b):
            result = []
            if a is not None:
                result += a
            if b is not None:
                result += b
            if len(result) == 0:
                return None
            else:
                return list(set(result))
            
        if ((not force) and
            (not self.overlaps(a) and not self.is_adjacent(a))):
            raise ValueError("Two bands not overlapping/adjacent, set force=True")
        result = Band()
        # Merge the bounds
        result._bounds = Bounds(
            min(self.bounds[0], a.bounds[0]),
            max(self.bounds[1], a.bounds[1]))
        # print(f"Merging: {self.range} and {a.range} into {result.range}")
        # Merge the allocations
        result.primary_allocations = list(set(
            self.primary_allocations + a.primary_allocations))
        result.primary_allocations.sort()
        result.secondary_allocations = list(set(
            self.secondary_allocations + a.secondary_allocations))
        result.secondary_allocations.sort()
        result.allocations = result.primary_allocations + result.secondary_allocations
        # Merge the footnotes
        result.footnotes = list(set(self.footnotes + a.footnotes))
        # Merge the FCC rules and the jurisdictions
        result.fcc_rules = _combine_elements(
            self.fcc_rules, a.fcc_rules)
        result.jurisdictions = _combine_elements(
            self.jurisdictions, a.jurisdictions)
        return result
        
    def definitelyUSA(self):
        for f in self.all_footnotes():
            if f[0] != "5" and f[0] != "(":
                return True
        return False

    def has_footnote(self, footnote, band_level_only=False):
        if band_level_only:
            footnotes = self.footnotes
        else:
            footnotes = self.all_footnotes()
        fl = footnote.lower().strip()
        for entry in footnotes:
            if fnmatch.fnmatch(entry.lower(), fl):
                return True
        return False

    def has_allocation(
            self, allocation,
            primary=None, secondary=None,
            co_primary=None, exclusive=None,
            case_sensitive=False):
        for a in self.allocations:
            if a.matches(allocation, case_sensitive=case_sensitive):
                if primary is not None:
                    if a.primary != primary:
                        return False
                if secondary is not None:
                    if (not a.primary) != secondary:
                        return False
                if co_primary is not None:
                    if a.co_primary != co_primary:
                        return False
                if exclusive is not None:
                    if a.exclusive != exclusive:
                        return False
                return True
        return False

    def applies_in(self, jurisdiction):
        if self.jurisdictions is None:
            return None
        for j in self.jurisdictions:
            if j == jurisdiction:
                return True
        return False

    def covers(self, frequency):
        return self.bounds[0] <= frequency and self.bounds[1] > frequency

    def overlaps(self, a):
        return (
            max(a.bounds[0],self.bounds[0]) < min(a.bounds[1],self.bounds[1]))

    def is_adjacent(self, a):
        return (
            np.allclose(a.bounds[1], self.bounds[0]) or
            np.allclose(a.bounds[0], self.bounds[1]))

    @property
    def bounds(self):
        return self._bounds.bounds

    @property
    def bandwidth(self):
        return self._bounds.bandwidth

    @property
    def center(self):
        return self._bounds.center

    @property
    def range(self):
        return str(self._bounds)

    @classmethod
    def parse(cls, cell, fcc_rules=None):
        """Parse a table cell into a Band"""
        # Now the first line should be a frequency range
        if cell is None:
            raise NotBandError("Cell is None")
        if cell.lines is None:
            raise NotBandError("Cell.lines is None")
        if len(cell.lines) == 0:
            raise NotBandError("Cell has no useful text")
        try:
            bounds = Bounds.parse(cell.lines[0], cell.unit)
        except NotBoundsError:
            raise NotBandError("Text doesn't start with bounds, so not a band")
        # Now the remainder will either be allocations, blanks or collections of footnotes
        footnotes = []
        primary_allocations = []
        secondary_allocations = []
        for l in cell.lines[1:]:
            if l.strip() == "":
                continue
            # if footnotes is not None:
            #     raise ValueError("Gone past footnotes and cell not empty")
            # See if this line conveys an allocation
            allocation = Allocation.parse(l)
            if allocation is not None:
                if len(footnotes) != 0:
                    raise NotBandError("Back to allocation after footnotes")
                if allocation.primary:
                    primary_allocations.append(allocation)
                else:
                    secondary_allocations.append(allocation)
            else:
                footnotes += l.split()
        # Done looping over the lines, so tidy things up.
        if footnotes is None:
            footnotes = []
        # Do the fcc rules
        try:
            fcc_rules = [entry for entry in fcc_rules.lines if entry != ""]
        except (TypeError, AttributeError):
            fcc_rules = None
        # Now create a Band to hold the result
        result = cls()
        result._bounds = bounds
        result.primary_allocations = primary_allocations
        result.secondary_allocations = secondary_allocations
        result.footnotes = footnotes
        result.fcc_rules = fcc_rules
        result.jurisdictions = None
        result._lines = cell.lines
        result._text = cell.text
        result._page = cell.page
        result._logical_column = cell.logical_column
        result._ordered_row = cell.ordered_row
        result._ordered_column = cell.ordered_row
        result.finalize()
        return result
