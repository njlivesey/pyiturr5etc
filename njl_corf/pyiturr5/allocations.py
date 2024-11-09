"""Define and track information related to radicommunication service allocations"""

from typing import Optional
import fnmatch

from .services import identify_service, Service
from .footnote_tools import footnote2html


class NotAllocationError(Exception):
    """Raised if a string cannot be parsed as an allocation"""


class Allocation:
    """An entry allocating a service to a band"""

    def __init__(
        self,
        service: Service,
        modifiers: list[str],
        footnotes: list[str],
        primary: bool,
        secondary: Optional[bool] = None,
        footnote_mention: Optional[bool] = False,
        user_annotations: Optional[dict] = None,
    ):
        """Create an allocation from inputs

        To first order, allocations are either "Primary" or "Secondary", at least that's
        how the ITU/FCC designates things.  However, this sofware can also track things
        incorporated (only) by footnote mentions (e.g., the 5.149 "all pracitcal steps")
        designation.  Some of these footnote mentions are accompanied by (mostly
        secondary) allocations, others are not. Hence, while an allocation can only be
        either primary or secondary (or neither) not both, it can be one of those and
        have footnote_mention set true.


        Parameters
        ----------
        service : Service
            The ITU-R service for this allocation
        modifiers : list[str]
            List of any modifiers for this allocation
        footnotes : list[str]
            List of any footnotes for this allocation
        primary : bool
            True if this allocation is a primary allocation
        secondary : bool
            True if this allocation is a secondary allocation
        footnote_mention : bool
            True if this alloction derives from a footnote, see above.  Default False
        user_annotations : dict
            Additional information that can be supplied by user.  Note that the parent
            Band instance has its own user_annotations attribute.
        """
        self.service: Service = service
        self.modifiers: list[str] = modifiers
        self.footnotes: list[str] = footnotes
        self.primary: bool = primary
        if footnote_mention is None:
            footnote_mention: bool = False
        if secondary is None:
            secondary: bool = (not primary) and (not footnote_mention)
        self.secondary: bool = secondary
        self.footnote_mention: bool = footnote_mention
        if user_annotations is None:
            user_annotations = {}
        self.user_annotations: dict = user_annotations
        # Do some checking
        if self.primary and self.secondary:
            raise ValueError("Allocation cannot be both primary and secondary")

    def to_str(
        self,
        html: bool = False,
        omit_footnotes: bool = False,
        omit_modifiers: bool = False,
        tooltips: bool = True,
        footnote_definitions: dict[str] = None,
    ):
        """String representation of Allocation, possibly with HTML/tooltips"""
        suffix = ""
        if self.primary:
            result = self.service.name.upper()
        elif self.secondary:
            result = self.service.name.capitalize()
        elif self.footnote_mention:
            result = self.service.name.lower()
            suffix = " (by footnote)"
        else:
            raise ValueError("Confused by this allocation")
        if self.modifiers and not omit_modifiers:
            result += " " + " ".join([f"({m})" for m in self.modifiers])
        result += suffix
        if self.footnotes and not omit_footnotes:
            if html:
                result = (
                    result
                    + " "
                    + " ".join(
                        [
                            footnote2html(
                                f, tooltips=tooltips, definitions=footnote_definitions
                            )
                            for f in self.footnotes
                        ]
                    )
                )
            else:
                result = result + " " + " ".join(self.footnotes)
        # if html:
        #     result = '<p><span id="fcc-allocation">' + result + '</span></p>'
        return result

    def __format__(self, format_spec: str) -> str:
        """Custom format method for allocation

        Parameter
        ---------
        format_spec: str
            The format string.  Keywords are: nofn, nomod corresponding to omitting
            footnotes and modifiers, respectively, separated by commas

        Result
        ------
            Formatted string for allocation
        """
        format_spec = format_spec.split(",")
        return self.to_str(
            omit_footnotes="nofn" in format_spec,
            omit_modifiers="nomod" in format_spec,
        )

    def __str__(self) -> str:
        """Return a string representation of an allocations"""
        return self.to_str()

    def __repr__(self) -> str:
        return str(self)

    def __eq__(self, a) -> bool:
        if self.service != a.service:
            return False
        if self.modifiers != a.modifiers:
            return False
        if self.footnotes != a.footnotes:
            return False
        if self.primary != a.primary:
            return False
        if self.secondary != a.secondary:
            return False
        if self.footnote_mention != a.footnote_mention:
            return False
        return True

    def __ne__(self, a) -> bool:
        return not self == a

    def __hash__(self) -> int:
        return hash(str(self))

    def __gt__(self, a) -> bool:
        return str(self) > str(a)

    def __lt__(self, a) -> bool:
        return str(self) < str(a)

    def __ge__(self, a) -> bool:
        return str(self) >= str(a)

    def __le__(self, a) -> bool:
        return str(self) <= str(a)

    def matches(
        self,
        line: str,
        case_sensitive: bool = False,
        omit_footnotes: bool = False,
        omit_modifiers: bool = False,
    ) -> bool:
        """Return true if an allocation matches a given string"""
        self_str = self.to_str(
            omit_footnotes=omit_footnotes,
            omit_modifiers=omit_modifiers,
        )
        if case_sensitive:
            return fnmatch.fnmatchcase(self_str, line)
        else:
            try:
                return fnmatch.fnmatchcase(self_str.lower(), line.lower())
            except AttributeError:
                # One of the arguments was not a string.
                return False


def parse_allocation(line) -> Allocation:
    """Take a complete line of text and turn into an Allocation"""
    # Work out which service this is. Special case for no allocation
    if line == "(Not allocated)":
        return None
    service = identify_service(line)
    # If not a service then quit
    if service is None:
        raise NotAllocationError(f"Unable to identify allocation: {line}")
    # Look at the remainder of the line
    invocation = line[: len(service.name)]
    if len(invocation) > 0:
        first_word = invocation.split()[0]
    else:
        first_word = invocation
    primary = first_word.isupper()
    remainder = line[len(service.name) :].strip()
    # Anyting in parentheses becomes a modifiers
    modifiers = []
    while len(remainder) > 0:
        if remainder[0] == r"(":
            try:
                modifier = remainder[1 : remainder.index(r")")]
            except ValueError:
                raise NotAllocationError(f"Corrupted allocation: {line}")
            modifiers.append(modifier)
            remainder = remainder[len(modifier) + 2 :].strip()
        else:
            break
    # Now the remainder (if anything) must be footnotes
    footnotes = remainder.split()
    # Create and return the result
    return Allocation(
        service=service,
        modifiers=modifiers,
        footnotes=footnotes,
        primary=primary,
    )
