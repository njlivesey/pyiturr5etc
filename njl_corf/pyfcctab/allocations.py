"""Handling of allocations of services to bands"""

import fnmatch

__all__ = ["Allocation"]

from .services import Service
from .footnotes import footnote2html


class Allocation:
    """An entry allocating a service to a band"""

    def __init__(
        self,
        service: Service,
        modifiers: list[str],
        footnotes: list[str],
        primary: bool,
        user_annotations: dict = None,
    ):
        """Create an allocation from inputs

        Parameters
        ----------
        service : Service
            The ITU-R service for this allocation
        modifiers : list[str]
            List of any modifiers for this allocation
        footnotes : list[str]
            List of any footnotes for this allocation
        primary : bool
            True if this allocation is primary
        user_annotations : dict
            Additional information that can be supplied by user.  Note that the parent
            Band instance has its own user_annotations attribute.
        """
        self.service = service
        self.modifiers = modifiers
        self.footnotes = footnotes
        self.primary = primary
        if user_annotations is None:
            user_annotations = {}
        self.user_annotations = user_annotations

    def to_str(
        self,
        html: bool = False,
        omit_footnotes: bool = False,
        omit_modifiers: bool = False,
        tooltips: bool = True,
        footnote_definitions: dict[str] = None,
    ):
        """String representation of Allocation, possibly with HTML/tooltips"""
        if self.primary:
            result = self.service.name.upper()
        else:
            result = self.service.name.capitalize()
        if self.modifiers and not omit_modifiers:
            result += " " + " ".join([f"({m})" for m in self.modifiers])
        if self.footnotes and not omit_footnotes:
            if html:
                result = (
                    result
                    + " "
                    + " ".join(
                        [
                            footnote2html(f, footnote_definitions, tooltips=tooltips)
                            for f in self.footnotes
                        ]
                    )
                )
            else:
                result = result + " " + " ".join(self.footnotes)
        # if html:
        #     result = '<p><span id="fcc-allocation">' + result + '</span></p>'
        return result

    def __str__(self):
        """Return a string representation of an allocations"""
        return self.to_str()

    def __eq__(self, a):
        if self.service != a.service:
            return False
        if self.modifiers != a.modifiers:
            return False
        if self.footnotes != a.footnotes:
            return False
        if self.primary != a.primary:
            return False
        return True

    def __ne__(self, a):
        return not self == a

    def __hash__(self):
        return hash(str(self))

    def __gt__(self, a):
        return str(self) > str(a)

    def __lt__(self, a):
        return str(self) < str(a)

    def __ge__(self, a):
        return str(self) >= str(a)

    def __le__(self, a):
        return str(self) <= str(a)

    def matches(
        self,
        line: str,
        case_sensitive: bool = False,
        omit_footnotes: bool = False,
        omit_modifiers: bool = False,
    ):
        """Return true if an allocation matches a given string"""
        self_str = self.to_str(
            omit_footnotes=omit_footnotes,
            omit_modifiers=omit_modifiers,
        )
        if case_sensitive:
            return fnmatch.fnmatchcase(self_str, line)
        else:
            return fnmatch.fnmatchcase(self_str.lower(), line.lower())

    @classmethod
    def parse(cls, line):
        """Take a complete line of text and turn into an Allocation"""
        # Work out which service this is.
        service = Service.identify(line)
        # If not a service then quit
        if service is None:
            return None
        # Look at the remainder of the line
        invocation = line[0 : len(service.name)]
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
                modifier = remainder[1 : remainder.index(r")")]
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
