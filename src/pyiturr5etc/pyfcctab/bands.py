"""Code for handling bands (i.e., cells in the FCC tables)"""

import re
import fnmatch
import numpy as np
from termcolor import colored

import pint

from .allocations import Allocation
from .footnotes import footnote2html
from .jurisdictions import Jurisdiction
from .cells import FCCCell
from njl_corf.corf_pint import ureg


__all__ = ["NotBoundsError", "NotBandError", "Band"]

_FREQUENCY_ATOL = 10 * ureg.Hz
_FREQUENCY_RTOL = 1e-6


# First define some exceptions we'll be using/raising
class NotBoundsError(Exception):
    """Exception used to flag failed parse of Bounds"""


class NotBandError(Exception):
    """Exception used to indicate failed parse of band"""


# Now a support routine.
def _parse_bounds(text, units: pint.Unit = None) -> list[pint.Quantity]:
    """Turn a string giving a frequency range into a bounds object"""
    re_float = r"[0-9_]+(?:\.[0-9_]+)?"
    re_bounds = (
        f"^({re_float})-({re_float})" r"[\s]*([kMG]Hz)?" r"[\s]*(\(Not allocated\))?$"
    )
    match = re.match(re_bounds, text)
    if match is not None:
        # OK, we match this rather complex wildcard
        if match.group(3):
            new_units = ureg.parse_expression(match.group(3))
            if units is not None and new_units != units:
                raise ValueError("Units mismatch")
            units = new_units
        else:
            if units is None:
                raise ValueError("No units given in string or separately")
        return [
            float(match.group(1)) * units,
            float(match.group(2)) * units,
        ]
    # Perhaps this is the "below the bottom" case.
    re_bottom = f"^Below ({re_float})" r" \(Not Allocated\)$"
    match = re.match(re_bottom, text)
    if match is not None:
        return [0.0 * units, float(match.group(1)) * units]
    # Otherwise, this is not a bound
    raise NotBoundsError(f"Not a valid range: {text}")


# --------------------------------------------------------------------- Band


class Band:
    """A frequency bound and allocations thereto (i.e., contents of a table cell)"""

    def __init__(
        self,
        bounds: list[pint.Quantity],
        jurisdictions: list[Jurisdiction],
        primary_allocations: list[Allocation] = None,
        secondary_allocations: list[Allocation] = None,
        footnote_mentions: list[Allocation] = None,
        footnotes: list[str] = None,
        fcc_rules: list[str] = None,
        annotations: list[str] = None,
        footnote_definitions: dict[str] = None,
        metadata: dict = None,
        user_annotations: dict = None,
    ):
        """Generate a Band based on inputs

        Parameters
        ----------
        bounds : list[pint.Quantity]
            start and stop frequency for the band
        jurisdictions : list[Jurisdiction]
            Which jurisdiction(s) does this band fall under
        primary_allocations : list[Allocation], optional
            List of the primary allocations
        secondary_allocations : list[Allocation], optional
            List of the secondary allocations
        footnotes : list[str], optional
            List of the associated footnotes
        fcc_rules : list[str], optional
            List of any associated fcc rules
        annotations : list[str], optional
            Any annotations from the FCC table
        footnote_mentions : list[str], optional
            Any quasi-allocations that are introduced by a footnote (e.g., 5.149)
        footnote_definitions: dict[str], optional
            Information for defining the footnotes.
        metadata : dict, optional
            Collection of other data (typically referring back to Word document)
        user_annotations : dict, optional
            Collection of user supplied annotations specific to the band (note that the
            individual Allocations within the band can carry user_annotations also.)
        """
        self.bounds = bounds
        self.jurisdictions = jurisdictions
        if primary_allocations is None:
            primary_allocations = []
        self.primary_allocations = primary_allocations
        if secondary_allocations is None:
            secondary_allocations = []
        self.secondary_allocations = secondary_allocations
        if footnote_mentions is None:
            footnote_mentions = []
        self.footnote_mentions = footnote_mentions
        if footnotes is None:
            footnotes = []
        self.footnotes = footnotes
        if fcc_rules is None:
            fcc_rules = []
        self.fcc_rules = fcc_rules
        if annotations is None:
            annotations = []
        self.annotations = annotations
        if metadata is None:
            metadata = {}
        self.metadata = metadata
        if footnote_definitions is None:
            footnote_definitions = {}
        self.footnote_definitions = footnote_definitions
        if user_annotations is None:
            user_annotations = {}
        self.user_annotations = user_annotations
        # Finalize to deal with all the internals
        self.finalize()

    def __str__(self):
        """Return a string representation 66 a Band"""
        return self.to_str()

    def __repr__(self):
        """Return a string representation of a Band"""
        return "<Band " + self.to_str(separator=";") + ">"

    def to_str(
        self,
        separator: str = None,
        skip_footnotes: bool = False,
        specific_allocations: list[Allocation] = None,
        skip_rules: bool = False,
        skip_jurisdictions: bool = False,
        skip_annotations: bool = False,
        highlight_allocations: list[Allocation] = None,
        html: bool = False,
        tooltips: bool = True,
    ):
        """Get string representation of band with various options

        Parameters
        ----------
        separator : str, optional
            String used to speparate clauses (defaults to line break, either string or HTML)
        skip_footnotes : bool, optional
            If set, omit any footnote information
        specific_allocations : list[Allocation], optional
            If set, only list specific allocations
        skip_rules : bool, optional
            _description_, by default False
        skip_jurisdictions : bool, optional
            _description_, by default False
        skip_annotations : bool, optional
            _description_, by default False
        highlight_allocations : list[Allocation], optional
            _description_, by default None
        html : bool, optional
            _description_, by default False
        tooltips : bool, optional
            _description_, by default True

        Returns
        -------
        _type_
            _description_

        Raises
        ------
        ValueError
            _description_
        """  # Deal with setting defaults etc.
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
            allocations = self.allocations
        else:
            allocations = list(
                set(self.allocations).intersection(set(specific_allocations))
            )
        # Start to build the result
        clauses = []
        if highlight_allocations is not None:
            for a in allocations:
                a_str = a.to_str(
                    html=html,
                    footnote_definitions=self.footnote_definitions,
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
                                f, self.footnote_definitions, tooltips=tooltips
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
        """Generate string describing frequency range

        Parameters
        ----------
        html : bool, optional
            If true, return in HTML-compatible form

        Returns
        -------
        str : result
        """
        values = [f"{np.around(value,5):~H}" for value in self.bounds]
        if html:
            return "&ndash;".join(values)
        else:
            return "-".join(values)

    def compact_str(self, **kwargs):
        """Return a compact string representation of band"""
        return self.to_str(separator="/", **kwargs)

    def __hash__(self):
        return hash(str(self))

    def jurisdictions_str(self):
        """Return string representation of band's jurisdictions"""
        if self.jurisdictions is not None:
            clauses = [str(j) for j in self.jurisdictions]
            result = "[" + ", ".join(clauses) + "]"
        else:
            result = ""
        return result

    def fcc_rules_str(self):
        """Return string representation of band's fcc rules"""
        result = ""
        if self.fcc_rules is not None:
            if len(self.fcc_rules) > 0:
                result = "{" + "; ".join(self.fcc_rules) + "}"
        return result

    def annotations_str(self):
        """Return string representation of band's annotations"""
        result = ""
        try:
            if len(self.annotations) > 0:
                result = "<" + ",".join(self.annotations) + ">"
        except TypeError:
            pass
        return result

    def finalize(self):
        """Make sure all the various pieces of information for a band are correct"""
        # Get a list of all the allocations
        self.allocations = []
        # Work out whether which ever allocation we have will be exclusive (ignore
        # quasi-allocations introduced by footnotes such as 5.140)
        single_allocation = (
            len(self.primary_allocations) + len(self.secondary_allocations)
        ) == 1
        for a in self.primary_allocations:
            assert (
                a.primary and not a.secondary
            ), "A secondary allocation ended up in the primary list somehow"
            a.co_primary = len(self.primary_allocations) > 1
            a.exclusive = single_allocation
            self.allocations.append(a)
        for a in self.secondary_allocations:
            assert (
                a.secondary and not a.primary
            ), "A primary allocation ended up in the secondary list somehow"
            a.co_primary = False
            a.exclusive = single_allocation
            self.allocations.append(a)
        for a in self.footnote_mentions:
            a.co_primary = False
            a.exclusive = False
            self.allocations.append(a)

    def equal(
        self,
        a: "Band",
        ignore_jurisdictions: bool = False,
        ignore_annotations: bool = False,
        ignore_fcc_rules: bool = False,
        ignore_user_annotations: bool = True,
    ) -> bool:
        """Return true if two bands are appropriately equal

        Parameters
        ----------
        a : Band
            Other band to compare with self
        ignore_jurisdictions : bool, optional
            If set, ignore juridiction information in comparison. Default False
        ignore_annotations : bool, optional
            If set, ignore annotation information in comparison. Default False
        ignore_fcc_rules : bool, optional
            If set, ignore fcc_rules information in comparison.  Default False
        ignore_user_annotations : bool, optional
            If set, ignore the information in user_annotations.  Default True

        Returns
        -------
        _type_
            _description_
        """
        if not isinstance(a, Band):
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
        if not ignore_user_annotations and self.user_annotations != a.user_annotations:
            return False
        return True

    def __eq__(self, a):
        """Return true if two bands equal"""
        return self.equal(a)

    def __ne__(self, a):
        """Return true if two bands not eqal"""
        return not self == a

    def __gt__(self, a):
        """Compare bands based on frequency bounds and jurisdictions"""
        if self.bounds[0] != a.bounds[0]:
            return self.bounds[0] > a.bounds[0]
        else:
            return self.jurisdictions > a.jurisdictions

    def __lt__(self, a):
        """Compare bands based on frequency bounds and jurisdictions"""
        if self.bounds[0] != a.bounds[0]:
            return self.bounds[0] < a.bounds[0]
        else:
            return self.jurisdictions < a.jurisdictions

    def __ge__(self, a):
        """Compare bands based on frequency bounds and jurisdictions"""
        return self.bounds[0] >= a.bounds[0]

    def __le__(self, a):
        """Compare bands based on frequency bounds and jurisdictions"""
        return self.bounds[0] <= a.bounds[0]

    def __add__(self, a):
        """Combine two bands together"""
        return self.combine_with(a)

    def all_footnotes(self):
        """Combine all the footnotes referred to in a band

        Both those that apply across the band and those applying to specific allocations
        """
        result = self.footnotes
        for a in self.allocations:
            result = result + a.footnotes
        return list(set(result))

    def footnote_definition(self, footnote):
        """Return text defining a given footnote"""
        if footnote[-1] == r"#":
            footnote = footnote[0:-1]
        return self.footnote_definitions[footnote]

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
        # Merge the bounds
        if not skip_bounds:
            bounds = [
                min(self.bounds[0], a.bounds[0]),
                max(self.bounds[1], a.bounds[1]),
            ]
        else:
            bounds = self.bounds
        # Merge the allocations
        primary_allocations = sorted(
            list(set(self.primary_allocations + a.primary_allocations))
        )
        secondary_allocations = sorted(
            list(set(self.secondary_allocations + a.secondary_allocations))
        )
        footnote_mentions = sorted(
            list(set(self.footnote_mentions + a.footnote_mentions))
        )
        # Merge the footnotes
        footnotes = sorted(_combine_elements(self.footnotes, a.footnotes))
        # Merge the FCC rules and the jurisdictions
        fcc_rules = _combine_elements(self.fcc_rules, a.fcc_rules)
        jurisdictions = sorted(_combine_elements(self.jurisdictions, a.jurisdictions))
        annotations = _combine_elements(self.annotations, a.annotations)
        # Think about the footnote definitions
        footnote_definitions = dict()
        for band in [self, a]:
            if hasattr(band, "footnote_definitions"):
                footnote_definitions = footnote_definitions | band.footnote_definitions
        # Think about the user annotations
        user_annotations = self.user_annotations | a.user_annotations
        # Use the finalize routine to sort out all the metadata
        return Band(
            bounds=bounds,
            primary_allocations=primary_allocations,
            secondary_allocations=secondary_allocations,
            footnote_mentions=footnote_mentions,
            footnotes=footnotes,
            fcc_rules=fcc_rules,
            jurisdictions=jurisdictions,
            annotations=annotations,
            footnote_definitions=footnote_definitions,
            user_annotations=user_annotations,
        )

    def definitely_usa(self):
        """Return true if the band includes USA footnotes"""
        for f in self.all_footnotes():
            if f[0] != "5" and f[0] != "(":
                return True
        return False

    def has_footnote(
        self,
        footnote: str,
        band_level_only: bool = False,
    ):
        """Return true if band includes a given footnote

        Parameters
        ----------
        footnote : str
            Specific footnote queried
        band_level_only : bool, optional
            If set, only consider footnotes that apply across the band, not those
            associated with a specific allocation.

        Returns
        -------
        boolean : reslut
        """
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
        allocation: str,
        but_not: str = None,
        primary: bool = None,
        secondary: bool = None,
        footnote_mention: bool = None,
        co_primary: bool = None,
        exclusive: bool = None,
        case_sensitive: bool = False,
        user_annotations: dict = None,
        return_allocation: bool = False,
    ) -> bool | tuple[bool, Allocation]:
        """Returns true if band has a given allocation

        Parameters
        ----------
        allocation : str
            The allocation being queried
        but_not : str, optional
            If supplied return false if the band includes this allocation
        primary : bool, optional
            If provided, require allocation's primary flag to match this value
        secondary : bool, optional
            If provided, require allocation's secondary flag to match this value
        co_primary : bool, optional
            If provided, require allocation's co_primary flag to match this value
        footnote_mention : bool, optional
            If provided, require allocation's footnote_mention flag to match this value
        exclusive : bool, optional
            If provided, require allocation's exclusive flag to match this value
        case_sensitive : bool, optional
            If set, force a case-sensitive comparison, default False
        user_annotations : dict, optional
            If provided, all the user_annotations in the allocation must match those
            supplied
        return_allocation : bool, optional
            If set, then the routine returns the actual allocation as well as the flag
            (or None if there is no matching allocation)

        Returns
        -------
        bool : result (optionally plus allocation : Allocation)
        """
        for a in self.allocations:
            if a.matches(
                allocation, case_sensitive=case_sensitive, omit_footnotes=True
            ):
                if primary is not None:
                    if a.primary != primary:
                        continue
                if secondary is not None:
                    if a.secondary != secondary:
                        continue
                if footnote_mention is not None:
                    if a.footnote_mention != footnote_mention:
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
                if user_annotations:
                    for key, item in user_annotations.items():
                        if key not in a.user_annotations:
                            continue
                        if item != a.user_annotations[key]:
                            continue
                # Return the result (optionally including the allocation itself)
                if return_allocation:
                    return True, a
                return True
        # Return the result (optinonally including None, to indicate no allocation
        # found)
        if return_allocation:
            return False, None
        return False

    def applies_in(self, jurisdiction):
        """Return true if this band applies in a give jurisdiction"""
        if self.jurisdictions is None:
            return None
        return jurisdiction in self.jurisdictions

    def covers(self, frequency):
        """Return true if band overlaps a given frequency"""
        return self.bounds[0] <= frequency and self.bounds[1] > frequency

    def overlaps(self, a: "Band"):
        """Return true if a band overlaps another band"""
        return max(a.bounds[0], self.bounds[0]) < min(a.bounds[1], self.bounds[1])

    def has_same_bounds_as(self, a: "Band"):
        """Return True if band has same bounds as another band"""
        for s, a in zip(self.bounds, a.bounds):
            if not np.isclose(s, a, atol=_FREQUENCY_ATOL, rtol=_FREQUENCY_RTOL):
                return False
        return True

    def is_adjacent(self, a: "Band"):
        """Return true if a band is directly adjacent to another"""
        return np.allclose(
            a.bounds[1],
            self.bounds[0],
            atol=_FREQUENCY_ATOL,
            rtol=_FREQUENCY_RTOL,
        ) or np.allclose(
            a.bounds[0],
            self.bounds[1],
            atol=_FREQUENCY_ATOL,
            rtol=_FREQUENCY_RTOL,
        )

    @property
    def frequency_range(self):
        """Return the frequency range for a band"""
        return pint.Quantity([self.bounds[0], self.bounds[1].to(self.bounds[0].units)])

    @property
    def bandwidth(self):
        """Return the bandwidth for a band"""
        return self.bounds[1] - self.bounds[0]

    @property
    def center(self):
        """Return the center frequency for a band"""
        return 0.5 * sum(self.bounds)

    @classmethod
    def parse(
        cls: type,
        cell: FCCCell | list[str],
        fcc_rules: FCCCell | list[str],
        units: pint.Unit = None,
        jurisdictions: list[Jurisdiction] = None,
        annotations: list[str] = None,
    ):
        """Parse a table cell into a Band

        Can take either an FCCCell class from the table or a list of strings.

        Parameters
        ----------
        cell : FCCCell | list[str]
            The entry in the FCC table that describes the band (or can be a list of
            strings)
        fcc_rules : FCCCell | list[str]
            The entry in the FCC table that gives the FCC rules (right most column in
            the table)
        units : pint.Unit, optional
            The units in action for this table page (MHz, GHz, etc.)
        jurisdictions : list[Jurisdiction], optional
            Which jurisdiction(s) this band applies to
        annotations : list[str], optional
            Any annotations associated with this band
        is_from_footnote : bool, optional
            If set, this band is being introduced by a footnote, not as such in the
            result

        Returns
        -------
        result : Band
            A parsed band

        Raises
        ------
        NotBandError
            Raised if the text does not parse correctly into a band
        ValueError
            Raised if the is scope for confusion about which units are in action.
        """
        # Work out what type of input we've been give, an FCCCell type
        # or just a set of strings.
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
        except NotBoundsError as exception:
            raise NotBandError(
                "Text doesn't start with bounds, so not a band"
            ) from exception

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
        # Bundle up all the metadata
        if proper_cell:
            metadata = {
                "lines": lines,
                "text": cell.text,
                "page": cell.page,
                "logical_column": cell.logical_column,
                "ordered_row": cell.ordered_row,
                "ordered_column": cell.ordered_column,
            }
        else:
            metadata = {}
        # Now create and return the result
        return Band(
            bounds=bounds,
            primary_allocations=primary_allocations,
            secondary_allocations=secondary_allocations,
            footnotes=footnotes,
            fcc_rules=fcc_rules,
            jurisdictions=jurisdictions,
            annotations=annotations,
            metadata=metadata,
        )

    @classmethod
    def create_band_from_footnote(
        cls: type,
        bounds: str | slice | list[pint.Quantity],
        allocations: str | list[str] = None,
        jurisdictions: list[Jurisdiction] = None,
        annotations: list[str] = None,
    ):
        """Creates a new band per rules given in a footnote

        Parameters
        ----------
        cls : type
            Presumably Band
        bounds : str | slice | list[pint.Quantity]
            Frequency range (can be supplied as a string)
        allocations : str | list[str], optional
            Sring or list thereof giving the [quasi-]allocations(s) for this band
        jurisdictions : list[Jurisdiction], optional
            List of jurisdictions in which this quasi-allocation applies
        annotations : list[str], optional
            Any annotations associated with this quasi-allocation

        Returns
        -------
        result : Band
            The newly-created band to include in a BandCollection
        """
        # Process the bounds
        bounds = _parse_bounds(bounds)
        # Preprocess the allocations if supplied
        if isinstance(allocations, str):
            allocations = [allocations]
        if allocations:
            allocations = [Allocation.parse(allocation) for allocation in allocations]
        if jurisdictions is not None:
            jurisdictions = [Jurisdiction.parse(j) for j in jurisdictions]
        # Create and return the result
        if allocations:
            for allocation in allocations:
                # allocation.secondary = False
                allocation.footnote_mention = True
        return cls(
            bounds=bounds,
            footnote_mentions=allocations,
            jurisdictions=jurisdictions,
            annotations=annotations,
        )
