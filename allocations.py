"""Handling of allocations of services to bands"""

import fnmatch

__all__ = [ "Allocation" ]

from .services import Service

class Allocation:
    """An entry allocating a service to a band"""
    def __str__(self):
        """Return a string representation of an Allocation"""
        if self.primary:
            result = self.service.name.upper()
        else:
            result = self.service.name.capitalize()
        if len(self.modifiers) != 0:
            result += " " + " ".join([f"({m})" for m in self.modifiers])
        if len(self.footnotes) != 0:
            result += " " + " ".join(self.footnotes)
        return (result)

    def __eq__(self,a):
        if self.primary != a.primary:
            return False
        if self.modifiers != a.modifiers:
            return False
        if self.footnotes != a.footnotes:
            return False
        return True

    def __ne__(self, a):
        return not (self == a)

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

    def matches(self, line, case_sensitive=False):
        if case_sensitive:
            return fnmatch.fnmatchcase(str(self), line)
        else:
            return fnmatch.fnmatchcase(str(self).lower(), line.lower())

    @classmethod
    def parse(cls, line):
        """Take a complete line of text and turn into an Allocation"""
        # Work out which service this is.
        service = Service.identify(line)
        # If not a service then quit
        if service is None:
            return None
        # Look at the remainder of the line
        invocation = line[0:len(service.name)]
        if len(invocation) > 0:
            first_word = invocation.split()[0]
        else:
            first_word = invocation
        primary = first_word.isupper()
        remainder = line[len(service.name):].strip()
        # Anyting in parentheses becomes a modifiers
        modifiers = []
        while len(remainder) > 0:
            if remainder[0] == r"(":
                modifier = remainder[1:remainder.index(r")")]
                modifiers.append(modifier)
                remainder = remainder[len(modifier)+2:].strip()
            else:
                break
        # Now the remainder (if anything) must be footnotes
        footnotes = remainder.split()
        # Create the result
        result = cls()
        result.service = service #.strip()
        result.modifiers = modifiers
        result.footnotes = footnotes
        result.primary = primary
        return result
