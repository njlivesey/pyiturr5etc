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

def _parse_bounds(text, unit):
    """Turn a string giving a frequency range into a bounds object"""
    re_float = r"[0-9_]+(?:\.[0-9_]+)?"
    re_bounds = f"^({re_float})-({re_float})[\w]*(\(Not allocated\))?$"
    match = re.match(re_bounds, text)
    if match is not None:
        return [
            float(match.group(1))*unit,
            float(match.group(2))*unit,
            ]
    # Perhaps this is the "below the bottom" case.
    re_bottom = f"^Below ({re_float}) \(Not Allocated\)$"        
    match = re.match(re_bottom, text)
    if match is not None:
        return [0.0*unit, float(match.group(1))*unit]
    # Otherwise, this is not a bound
    raise NotBoundsError(f"Not a valid range: {text}")
            
# --------------------------------------------------------------------- Band

class NotBandError(Exception):
    """Exception used to indicate failed parse of band"""
    pass

class Band:
    """A frequency bounds and the allocations thereto (i.e., contents of a table cell)"""
    def __str__(self, separator="\n", skip_footnotes=False, specific_allocations=None, skip_rules=False):
        """Return a string representation of a Band"""
        # Do the frequency range
        result = self.range_str()
        # Add jurisdiction information and annotation information if any
        for extra in [self.jurisdictions_str(), self.annotations_str()]:
            if extra != "":
                result = result + ' ' + extra
        # Next line
        result = result + separator
        # Do allocations
        if specific_allocations is None:
            clauses = [str(a) for a in self.allocations]
        else:
            clauses = []
            for a in self.allocations:
                for sa in specific_allocations:
                    if a.matches(sa):
                        clauses.append(str(a))
        result = result + separator.join(clauses)
        # Do footnotes
        if not skip_footnotes and self.footnotes != "":
            result = result + separator + " ".join(self.footnotes)
        # Do rules
        rules_str = self.fcc_rules_str()
        if rules_str != "" and not skip_rules:
            result = result + separator + rules_str
        return (result)

    def range_str(self):
        return f"{self.bounds[0]}-{self.bounds[1]}"
        
    def compact_str(self, **kwargs):
        return self.__str__(separator="/", **kwargs)

    def jurisdictions_str(self):
        if self.jurisdictions is not None:
            result =  '[' + ','.join(self.jurisdictions) + ']'
        else:
            result = ""
        return result

    def fcc_rules_str(self):
        result = ""
        if self.fcc_rules is not None:
            if len(self.fcc_rules) > 0:
                result = '{' + '; '.join(self.fcc_rules) + '}'
        return result

    def annotations_str(self):
        result = ""
        try:
            if len(self.annotations) > 0:
                result = '<' + ','.join(self.annotations) + '>'
        except TypeError:
            pass
        return result

    def finalize(self):
        """Make sure all the various pieces of information for a band are correct"""
        self.allocations = []
        self.bandwidth = self.bounds[1] - self.bounds[0]
        assert self.bandwidth>0.0, f"Non-positive bandwidth for {self}"
        self.center = self.bounds[0] + 0.5*self.bandwidth
        n_allocations = len(self.primary_allocations) + len(self.secondary_allocations)
        for a in self.primary_allocations:
            assert a.primary, "A secondary allocation ended up in the primary list somehow"
            a.co_primary = len(self.primary_allocations) > 1
            a.exclusive = n_allocations == 1
            self.allocations.append(a)
        for a in self.secondary_allocations:
            assert not a.primary, "A primary allocation ended up in the secondary list somehow"
            a.co_primary = False
            a.exclusive = n_allocations == 1
            self.allocations.append(a)

    def __eq__(self,a):
        """Compare two sets of Band information"""
        if a is None:
            return False
        if self.bounds != a.bounds:
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
        return self.bounds[0] > a.bounds[0]

    def __lt__(self, a):
        return self.bounds[0] < a.bounds[0]

    def __ge__(self, a):
        return self.bounds[0] >= a.bounds[0]

    def __le__(self, a):
        return self.bounds[0] <= a.bounds[0]

    def __add__(self, a):
        return self.combine_with(a)

    def all_footnotes(self):
        result = self.footnotes
        for a in self.allocations:
            result = result + a.footnotes
        return list(set(result))

    def combine_with(self, a, force=False, skip_bounds=False):
        """Merge the contents of two different bands"""

        def _combine_elements(a,b):
            result = []
            if a is not None:
                result += a
            if b is not None:
                result += b
            return list(set(result))
            
        if ((not force) and
            (not self.overlaps(a) and not self.is_adjacent(a))):
            raise ValueError("Two bands not overlapping/adjacent, set force=True")
        result = Band()
        # Merge the bounds
        if not skip_bounds:
            result.bounds = [
                min(self.bounds[0], a.bounds[0]),
                max(self.bounds[1], a.bounds[1]),
                ]
        else:
            result.bounds = self.bounds
        # Merge the allocations
        result.primary_allocations = list(set(
            self.primary_allocations + a.primary_allocations))
        result.primary_allocations.sort()
        result.secondary_allocations = list(set(
            self.secondary_allocations + a.secondary_allocations))
        result.secondary_allocations.sort()
        # Merge the footnotes
        result.footnotes = _combine_elements(self.footnotes, a.footnotes)
        result.footnotes.sort()
        # Merge the FCC rules and the jurisdictions
        result.fcc_rules = _combine_elements(
            self.fcc_rules, a.fcc_rules)
        result.jurisdictions = _combine_elements(
            self.jurisdictions, a.jurisdictions)
        result.jurisdictions.sort()
        result.annotations = _combine_elements(
            self.annotations, a.annotations)
        # Use the finalize routine to sort out all the metadata
        result.finalize()
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

    @classmethod
    def parse(cls, cell, fcc_rules=None, unit=None, jurisdictions=None, annotations=None):
        """Parse a table cell into a Band"""
        from .cells import FCCCell
        # Now the first line should be a frequency range
        if cell is None:
            raise NotBandError("Cell is None")
        proper_cell = isinstance(cell, FCCCell)
        if proper_cell:
            if cell.lines is None:
                raise NotBandError("Cell.lines is None")
            if len(cell.lines) == 0:
                raise NotBandError("Cell has no useful text")
            lines = cell.lines
            if unit is not None:
                raise ValueError("Potentially conflicting unit information")
            unit = cell.unit
        else:
            lines = cell
        try:
            bounds = _parse_bounds(lines[0], unit)
        except NotBoundsError:
            raise NotBandError("Text doesn't start with bounds, so not a band")
        # Now the remainder will either be allocations, blanks or collections of footnotes
        footnotes = []
        primary_allocations = []
        secondary_allocations = []
        for l in lines[1:]:
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
        result.bounds = bounds
        result.primary_allocations = primary_allocations
        result.secondary_allocations = secondary_allocations
        result.footnotes = footnotes
        result.fcc_rules = fcc_rules
        result.jurisdictions = jurisdictions
        result._lines = lines
        result.annotations = annotations
        if proper_cell:
            result._text = cell.text
            result._page = cell.page
            result._logical_column = cell.logical_column
            result._ordered_row = cell.ordered_row
            result._ordered_column = cell.ordered_row
        else:
            result._text = None
            result._page = None
            result._logical_column = None
            result._ordered_row = None
            result._ordered_column = None
        result.finalize()
        return result
