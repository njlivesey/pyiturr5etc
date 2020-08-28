"""Code for handling bands (i.e., cells in the FCC tables)"""

import re
import docx
import fnmatch

from .allocations import Allocation
from .services import services
from .utils import cell2text

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

    @classmethod
    def parse(cls, text, unit):
        """Turn a string giving a frequency range into a bounds object"""
        re_float = r"[0-9]+(?:\.[0-9]+)?"
        re_bounds = f"^({re_float})-({re_float})$"
        match = re.match(re_bounds, text)
        if match is not None:
            return cls(
                float(match.group(1))*unit,
                float(match.group(2))*unit)
        # Perhaps this is the "below the bottom" case.
        re_bottom = f"^Below ({re_float}) \(Not Allocated\)$"
        match = re.match(re_bottom, text)
        if match is None:
            raise NotBoundsError(f"Not a valid range: {text}")
        return cls(
            0.0*unit, float(match.group(1))*unit)

# --------------------------------------------------------------------- Bands

def _text2lines(text):
    if text is None:
        return None
    lines = []
    line = None
    for t in text:
        if len(t) == 0:
            continue
        # if len(t) != 0:
        #     t0 = t[0]
        # else:
        #     t0 = ""
        is_continuation = (t0 == " ")
        if line is None:
            is_continuation = False
        else:
            if len(line) == 0:
                is_continuation = False
        if is_continuation:
            if line[-1] != '-':
                line = line + " " + t.strip()
            else:
                line = line + t.strip()
        else:
            if line is not None:
                lines.append(line)
            line = t.strip()
    if line is not None:
        lines.append(line.strip())
    return lines

class NotBandError(Exception):
    """Exception used to indicate failed parse of band"""
    pass

class Band:
    """A frequency bounds and the allocations thereto (i.e., contents of a cell in the FCC tables)"""
    def __str__(self, separator="\n"):
        """Return a string representation of a Band"""
        result = str(self.bounds) + separator
        for a in self.allocations:
            result = result + str(a) + separator
        if self.footnotes != "":
            result = result + separator + " ".join(self.footnotes)
        if self.fcc_rules is not None:
            result = result + separator + '[' + '; '.join(self.fcc_rules) + ']'
        return (result)

    def compact_str(self):
        return self.__str__(separator="/")

    def __eq__(self,a):
        """Compare two sets of Band information"""
        if self.bounds != a.bounds:
            return False
        if len(self.allocations) != len(a.allocations):
            return False
        for sa, aa in zip(self.allocations, a.allocations):
            if sa != aa:
                return False
        return self.footnotes == a.footnotes
        
    def __ne__(self, a):
        return not (self == a)

    def all_footnotes(self):
        result = self.footnotes
        for a in self.allocations:
            result = result + a.footnotes
        return list(set(result))

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

    @classmethod
    def parse(cls, cell, unit, fcc_rules=None):
        """Parse a table cell into a Band"""
        if cell is None:
            raise NotBandError("Cell is None")
        if type(cell) == docx.table._Cell:
            text = cell2text(cell)
        else:
            text = cell
        # Now work out which lines are continuations of other lines and string them together
        lines = _text2lines(text)
        # Now the first line should be a frequency range
        if len(lines) == 0:
            return None
        try:
            bounds = Bounds.parse(lines[0], unit)
        except NotBoundsError:
            raise NotBandError("Text doesn't start with bounds, so not a band")
        # Now the remainder will either be allocations, blanks or collections of footnotes
        service_names = services.keys()
        footnotes = []
        allocations = []
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
                allocations.append(allocation)
            else:
                footnotes += l.split()
        # Done looping over the lines, so tidy things up.
        if footnotes is None:
            footnotes = []
        for a in allocations:
            if a.primary:
                a.co_primary = len(primary_allocations) > 1
            else:
                a.co_primary = False
            a.exclusive = len(allocations) == 1
            a.bounds = bounds
        # Now create a Band to hold the result
        result = cls()
        result.bounds = bounds
        result.allocations = allocations
        result.primary_allocations = primary_allocations
        result.secondary_allocations = secondary_allocations
        result.footnotes = footnotes
        result.fcc_rules = _text2lines(fcc_rules)
        result._lines = lines
        result._text = text
        return result
