"""Code for handling bands (i.e., cells in the FCC tables)"""

import copy
import re
import fnmatch
import numpy as np
from .fccpint import ureg
from termcolor import colored

from .allocations import Allocation
from .footnotes import footnote2html
from .jurisdictions import Jurisdiction


__all__ = ["NotBoundsError", "NotBandError", "Band"]


# First define some exceptions we'll be using/raising
class NotBoundsError(Exception):
    """Exception used to flag failed parse of Bounds"""


class NotBandError(Exception):
    """Exception used to indicate failed parse of band"""


# Now a support routine.
def _parse_bounds(text, units):
    """Turn a string giving a frequency range into a bounds object"""
    re_float = r"[0-9_]+(?:\.[0-9_]+)?"
    re_bounds = f"^({re_float})-({re_float})[\\w]*(\\(Not allocated\\))?$"
    # print (f"Matching {re_bounds} to {text}")
    match = re.match(re_bounds, text)
    if match is not None:
        return [
            float(match.group(1)) * units,
            float(match.group(2)) * units,
        ]
    # Perhaps this is the "below the bottom" case.
    re_bottom = f"^Below ({re_float}) \\(Not Allocated\\)$"
    match = re.match(re_bottom, text)
    if match is not None:
        return [0.0 * units, float(match.group(1)) * units]
    # Otherwise, this is not a bound
    raise NotBoundsError(f"Not a valid range: {text}")


# --------------------------------------------------------------------- Band


class Band:
    """A frequency bound and allocations thereto (i.e., contents of a table cell)"""

    def __str__(self):
        """Return a string representation of a Band"""
        return self.to_str()

    def __repr__(self):
        """Return a string representation of a Band"""
        return "<Band " + self.to_str(separator=";") + ">"

    def to_str(
        self,
        separator=None,
        skip_footnotes=False,
        specific_allocations=None,
        skip_rules=False,
        skip_jurisdictions=False,
        skip_annotations=False,
        highlight_allocations=None,
        html=False,
        tooltips=True,
    ):
        """Return a string representation of a Band"""
        # Deal with setting defaults etc.
        if html:
            if separator is not None:
                raise ValueError("Cannot select HTML and supply separator")
            separator = "<br>"
        if separator is None:
            separator = "\n"
        highlight_colors = ["red", "green", "blue", "orange"]
        if highlight_allocations is True:
            highlight_allocations = [
                "Earth Exploration-Satellite*",
                "Radio Astronomy*",
                "Space Research*",
            ]
        # Do the frequency range
        if html:
            result = r'<p id="fcc"><b>' + self.range_str(html=True) + "</b>"
        else:
            result = self.range_str()
        # Add jurisdiction information and annotation information if any
        if not skip_jurisdictions:
            result = result + " " + self.jurisdictions_str()
        if not skip_annotations:
            result = result + " " + self.annotations_str()
        # Next line
        result = result + separator
        # Do allocations
        if specific_allocations is None:
            allocations = [a for a in self.allocations]
        else:
            allocations = []
            for a in self.allocations:
                for sa in specific_allocations:
                    if a.matches(sa):
                        allocations.append(a)
        clauses = []
        if highlight_allocations is not None:
            for a in allocations:
                a_str = a.to_str(
                    html=html,
                    footnote_definitions=self._footnote_definitions,
                    tooltips=tooltips,
                )
                try:
                    i = [a.matches(ha) for ha in highlight_allocations].index(True)
                except ValueError:
                    i = None
                if i is None:
                    clauses.append(a_str)
                else:
                    if html:
                        clauses.append('<span id="fcc-highlight">' + a_str + "</span>")
                    else:
                        clauses.append(
                            colored(a_str, highlight_colors[i % len(highlight_colors)])
                        )
        else:
            for a in allocations:
                clauses.append(str(a))
        result = result + separator.join(clauses)
        # Do footnotes
        if not skip_footnotes and self.footnotes != "":
            if html:
                result = (
                    result
                    + separator
                    + separator
                    + " ".join(
                        [
                            footnote2html(
                                f, self._footnote_definitions, tooltips=tooltips
                            )
                            for f in self.footnotes
                        ]
                    )
                )
            else:
                result = result + separator + separator + " ".join(self.footnotes)
        # Do rules
        rules_str = self.fcc_rules_str()
        if rules_str != "" and not skip_rules:
            result = result + separator + rules_str
        if html:
            result = result + r"</p>"
        return result

    def to_html(self, **kwargs):
        """Produce html representation of a band"""
        result = r"<p><fcc>" + self.to_str(html=True, **kwargs) + r"</fcc></p>"
        return result

    def range_str(self, html=False):
        values = [f"{np.around(value,5):~H}" for value in self.bounds]
        if html:
            return "&ndash;".join(values)
        else:
            return "-".join(values)

    def compact_str(self, **kwargs):
        return self.to_str(separator="/", **kwargs)

    def __hash__(self):
        return hash(str(self))

    def jurisdictions_str(self):
        if self.jurisdictions is not None:
            clauses = [str(j) for j in self.jurisdictions]
            result = "[" + ", ".join(clauses) + "]"
        else:
            result = ""
        return result

    def fcc_rules_str(self):
        result = ""
        if self.fcc_rules is not None:
            if len(self.fcc_rules) > 0:
                result = "{" + "; ".join(self.fcc_rules) + "}"
        return result

    def annotations_str(self):
        result = ""
        try:
            if len(self.annotations) > 0:
                result = "<" + ",".join(self.annotations) + ">"
        except TypeError:
            pass
        return result

    def finalize(self):
        """Make sure all the various pieces of information for a band are correct"""
        self.allocations = []
        n_allocations = len(self.primary_allocations) + len(self.secondary_allocations)
        for a in self.primary_allocations:
            assert (
                a.primary
            ), "A secondary allocation ended up in the primary list somehow"
            a.co_primary = len(self.primary_allocations) > 1
            a.exclusive = n_allocations == 1
            self.allocations.append(a)
        for a in self.secondary_allocations:
            assert (
                not a.primary
            ), "A primary allocation ended up in the secondary list somehow"
            a.co_primary = False
            a.exclusive = n_allocations == 1
            self.allocations.append(a)

    def equal(
        self,
        a,
        ignore_jurisdictions=False,
        ignore_annotations=False,
        ignore_fcc_rules=False,
    ):
        """Compare two sets of band information"""
        if type(self) != type(a):
            return False
        if self.bounds != a.bounds:
            return False
        if len(self.allocations) != len(a.allocations):
            return False
        for sa, aa in zip(self.allocations, a.allocations):
            if sa != aa:
                return False
        if not ignore_fcc_rules:
            if (self.fcc_rules is None) != (a.fcc_rules is None):
                return False
            try:
                if len(self.fcc_rules) != len(a.fcc_rules):
                    return False
                for sr, ar in zip(self.fcc_rules, a.fcc_rules):
                    if sr != ar:
                        return False
            except TypeError:
                pass
        if self.footnotes != a.footnotes:
            return False
        if not ignore_jurisdictions and self.jurisdictions != a.jurisdictions:
            return False
        if not ignore_annotations and self.annotations != a.annotations:
            return False
        return True

    def __eq__(self, a):
        """Compare two sets of Band information"""
        return self.equal(a)

    def __ne__(self, a):
        return not (self == a)

    def __gt__(self, a):
        if self.bounds[0] != a.bounds[0]:
            return self.bounds[0] > a.bounds[0]
        else:
            return self.jurisdictions > a.jurisdictions

    def __lt__(self, a):
        if self.bounds[0] != a.bounds[0]:
            return self.bounds[0] < a.bounds[0]
        else:
            return self.jurisdictions < a.jurisdictions

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

    def footnote_definition(self, footnote):
        """Return text defining a given footnote"""
        if footnote[-1] == r"#":
            footnote = footnote[0:-1]
        return self._footnote_definitions[footnote]

    def combine_with(self, a, force=False, skip_bounds=False):
        """Merge the contents of two different bands"""

        def _combine_elements(a, b):
            result = []
            if a is not None:
                result += a
            if b is not None:
                result += b
            return list(set(result))

        if (not force) and (not self.overlaps(a) and not self.is_adjacent(a)):
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
        result.primary_allocations = sorted(
            list(set(self.primary_allocations + a.primary_allocations))
        )
        result.secondary_allocations = sorted(
            list(set(self.secondary_allocations + a.secondary_allocations))
        )
        # Merge the footnotes
        result.footnotes = sorted(_combine_elements(self.footnotes, a.footnotes))
        # Merge the FCC rules and the jurisdictions
        result.fcc_rules = _combine_elements(self.fcc_rules, a.fcc_rules)
        result.jurisdictions = sorted(
            _combine_elements(self.jurisdictions, a.jurisdictions)
        )
        result.annotations = _combine_elements(self.annotations, a.annotations)
        # Think about the footnote definitions
        _footnote_definitions = dict()
        for band in [self, a]:
            if hasattr(band, "_footnote_definitions"):
                _footnote_definitions = {
                    **_footnote_definitions,
                    **band._footnote_definitions,
                }
        if _footnote_definitions:
            result._footnote_definitions = _footnote_definitions
        # Use the finalize routine to sort out all the metadata
        result.finalize()
        return result

    def copy(self):
        """Return a shallow copy of the band"""
        return copy.copy(self)

    def deepcopy(self):
        """Return a deep copy of the band

        (_footnote_definitions is shallow copy, if present)"""
        result = copy.deepcopy(self)
        try:
            result._footnote_definitions = self._footnote_definitions
        except AttributeError:
            pass
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
        self,
        allocation,
        but_not=None,
        primary=None,
        secondary=None,
        co_primary=None,
        exclusive=None,
        case_sensitive=False,
    ):
        for a in self.allocations:
            if a.matches(allocation, case_sensitive=case_sensitive):
                if primary is not None:
                    if a.primary != primary:
                        continue
                if secondary is not None:
                    if (not a.primary) != secondary:
                        continue
                if co_primary is not None:
                    if a.co_primary != co_primary:
                        continue
                if exclusive is not None:
                    if a.exclusive != exclusive:
                        continue
                if but_not is not None:
                    if a.matches(but_not, case_sensitive=case_sensitive):
                        continue
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
        return max(a.bounds[0], self.bounds[0]) < min(a.bounds[1], self.bounds[1])

    def has_same_bounds_as(self, a):
        for s, a in zip(self.bounds, a.bounds):
            if round(s.to(ureg.Hz).magnitude) != round(a.to(ureg.Hz).magnitude):
                return False
        return True

    def is_adjacent(self, a):
        return np.allclose(a.bounds[1], self.bounds[0]) or np.allclose(
            a.bounds[0], self.bounds[1]
        )

    @property
    def frequency_range(self):
        return pint.Quantity([self.bounds[0], self.bounds[1].to(self.bounds[0].units)])

    @property
    def bandwidth(self):
        return self.bounds[1] - self.bounds[0]

    @property
    def center(self):
        return 0.5 * sum(self.bounds)

    @classmethod
    def parse(
        cls, cell, fcc_rules=None, units=None, jurisdictions=None, annotations=None
    ):
        """Parse a table cell into a Band"""
        # Work out what type of input we've been give, an FCCCell type
        # or just a set of strings.
        from .cells import FCCCell

        if cell is None:
            raise NotBandError("Cell is None")
        proper_cell = isinstance(cell, FCCCell)
        if proper_cell:
            if cell.lines is None:
                raise NotBandError("Cell.lines is None")
            if len(cell.lines) == 0:
                raise NotBandError("Cell has no useful text")
            lines = cell.lines
            if units is not None:
                raise ValueError("Potentially conflicting unit information")
            units = cell.units
        else:
            lines = cell

        # Now the first line should be a frequency range
        try:
            bounds = _parse_bounds(lines[0], units)
        except NotBoundsError:
            raise NotBandError("Text doesn't start with bounds, so not a band")

        # Now the remainder will either be allocations, blanks or
        # collections of footnotes
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
        # Make sure the footnotes are unique (and sort them)
        footnotes = sorted(list(set(footnotes)))
        # Do the fcc rules
        try:
            rules_lines = fcc_rules.lines
        except AttributeError:
            rules_lines = fcc_rules
        try:
            fcc_rules = [entry for entry in rules_lines if entry != ""]
            if len(fcc_rules) == 0:
                fcc_rules = None
        except TypeError:
            fcc_rules = None
        # Deal with the jurisdictions
        if jurisdictions is not None:
            jurisdictions = [Jurisdiction.parse(j) for j in jurisdictions]
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
