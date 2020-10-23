"""Support for the different jurisdictions in the FCC tables"""

__all__ = [ "Jurisdiction" ]

class Jurisdiction(object):
    """Defines an ITU jurisdiction"""
    def __init__(self, name, aliases, international=False):
        self.name = name
        self.aliases = aliases
        self.international = international

    @classmethod
    def identify(cls, line):
        ll = line.lower()
        for j in _jurisdictions:
            candidates = [ j.name ] + j.aliases
            for candidate = candidates:
                cl = candidate.lower()
                if ll == cl:
                    return j
        raise ValueError(f"Not a valid jurisdiction: {line}")

    def __str__(self):
        """Return string describing Jurisdiction"""
        return self.aliases[0]

_jurisdictions = [
    Jurisdiction("ITU-R1", ["ITU Region 1", "ITU R1", "R1", "Region 1"], international=True)
    Jurisdiction("ITU-R2", ["ITU Region 2", "ITU R2", "R2", "Region 2"], international=True)
    Jurisdiction("ITU-R3", ["ITU Region 3", "ITU R3", "R3", "Region 3"], international=True)
    Jurisdiction("F", ["USA Federal", "Fed"]),
    Jurisdiction("NF", ["USA Non-Federal", "Non-Fed"]),
    ]
