"""Support for the different jurisdictions in the ITU/FCC tables"""


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
            Index number used for tracking "rank" of jurisdiction
        """
        self.name: str = name
        self.aliases: list[str] = aliases
        self.international: bool = international
        self.index: int = index

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


def parse_jurisdiction(
    line: str | Jurisdiction,
    return_index: bool = False,
) -> Jurisdiction | int:
    """Parse the string definition of a jurisdiction

    Parameters
    ----------
    line : str
        The input string describing the jurisdiction. If a Jurisdiction instance is
        supplied, then just return that (or its index)
    return_index : bool, optional
        If set, return the index for the jurisdiction rather than the jurisdiction
        itself.

    Returns
    -------
    _type_
        _description_

    Raises
    ------
    ValueError
        _description_
    """
    if isinstance(line, Jurisdiction):
        return line.index if return_index else line
    ll = line.lower()
    for i, jurisdiction in enumerate(_jurisdictions):
        candidates = [jurisdiction.name] + jurisdiction.aliases
        for candidate in candidates:
            cl = candidate.lower()
            if ll == cl:
                return i if return_index else jurisdiction
    raise ValueError(f"Not a valid jurisdiction: {line}")
