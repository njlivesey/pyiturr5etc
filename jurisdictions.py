"""Support for the different jurisdictions in the FCC tables"""

__all__ = [ "Jurisdiction" ]

class Jurisdiction(object):
    """Defines an ITU jurisdiction"""
    def __init__(self, name, aliases, international=False):
        self.name = name
        self.aliases = aliases
        self.international = international

    @classmethod
    def parse(cls, line, index=False):
        ll = line.lower()
        for i, j in enumerate(_jurisdictions):
            candidates = [ j.name ] + j.aliases
            for candidate in candidates:
                cl = candidate.lower()
                if ll == cl:
                    if index:
                        return i
                    else:
                        return j
        raise ValueError(f"Not a valid jurisdiction: {line}")

    def __str__(self):
        """Return string describing Jurisdiction"""
        return self.aliases[0]

    def __repr__(self):
        """Return representation of Jurisidiction"""
        return f"<Jurisdiction: {self}>"
    
    def __eq__(self, a):
        try:
            return self.index == a.index
        except AttributeError:
            i = self.parse(a, index=True)
        return self.index == i
    def __ne__(self, a):
        return not self==a
    def __gt__(self, a):
        return self.index > a.index
    def __lt__(self, a):
        return self.index < a.index
    def __ge__(self, a):
        return self.index >= a.index
    def __le__(self, a):
        return self.index <= a.index
    def __hash__(self):
        return hash(self.name)

_jurisdictions = [
    Jurisdiction("ITU-R1", ["ITU Region 1", "ITU R1", "R1", "Region 1"], international=True),
    Jurisdiction("ITU-R2", ["ITU Region 2", "ITU R2", "R2", "Region 2"], international=True),
    Jurisdiction("ITU-R3", ["ITU Region 3", "ITU R3", "R3", "Region 3"], international=True),
    Jurisdiction("F", ["USA Federal", "Fed"]),
    Jurisdiction("NF", ["USA Non-Federal", "Non-Fed"]),
    ]
for i,j in enumerate(_jurisdictions):
    j.index = i
