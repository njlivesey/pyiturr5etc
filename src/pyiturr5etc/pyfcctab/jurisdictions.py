"""Support for the different jurisdictions in the FCC tables"""

__all__ = ["Jurisdiction"]


class Jurisdiction(object):
    """Defines an ITU jurisdiction"""

    def __init__(
        self,
        name: str,
        aliases: list[str],
        international: bool = False,
        index: int = None,
    ):
        """Generate a Jurisdiction from inputs

        Parameters
        ----------
        name : str
            The name for the jurisdiction
        aliases : list[str]
            Potential alises for this jurisdiction
        international : bool, optional
            True if this is an ITU jurisdiction
        index : int, optional
            Index number used for tracking rank of jurisdiction
        """
        self.name = name
        self.aliases = aliases
        self.international = international
        self.index = index

    @classmethod
    def parse(cls, line: str, index: bool = False):
        """Parse the string definition of a jurisdiction

        Parameters
        ----------
        line : str
            The input string describing the jurisdiction
        index : bool, optional
            A potential index number for the jurisdiction

        Returns
        -------
        _type_
            _description_

        Raises
        ------
        ValueError
            _description_
        """
        ll = line.lower()
        for i, jurisdiction in enumerate(_jurisdictions):
            candidates = [jurisdiction.name] + jurisdiction.aliases
            for candidate in candidates:
                cl = candidate.lower()
                if ll == cl:
                    if index:
                        return i
                    else:
                        return jurisdiction
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
        return not self == a

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


# Now define a database of jurisdictions.
_jurisdictions = [
    Jurisdiction(
        name="ITU-R1",
        aliases=["ITU Region 1", "ITU R1", "R1", "Region 1"],
        international=True,
        index=0,
    ),
    Jurisdiction(
        name="ITU-R2",
        aliases=["ITU Region 2", "ITU R2", "R2", "Region 2"],
        international=True,
        index=1,
    ),
    Jurisdiction(
        name="ITU-R3",
        aliases=["ITU Region 3", "ITU R3", "R3", "Region 3"],
        international=True,
        index=2,
    ),
    Jurisdiction(
        name="F",
        aliases=["USA Federal", "Fed"],
        index=3,
    ),
    Jurisdiction(
        name="NF",
        aliases=["USA Non-Federal", "Non-Fed"],
        index=4,
    ),
]
