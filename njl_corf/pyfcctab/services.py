"""Defines and tracks information related to specific radio communications services"""

__all__ = ["Service"]


class Service:
    """A service that can be allocated to a band"""

    def __init__(
        self,
        name: str,
        abbreviation: str = None,
        science: bool = False,
        science_support: bool = False,
        aliases: list[str] = None,
    ):
        """Set up a new service based on information provided.

        Parameters
        ----------
        name : str
            Name for the service (e.g., "Aeronautical Mobile")
        abbreviation : str, optional
            Optional abbreviation for it (e.g., RAS for Radio Astronomy Service)
        science : bool, optional
            If true, this is a science service
        science_support : bool, optional
            If true, this service supports science
        aliases : list[str], optional
            Potential string aliases for the service.
        """
        self.name = name.lower().strip()
        if abbreviation is None:
            self.abbreviation = self.name
        self.science = science
        self.science_support = science_support
        if aliases is None:
            aliases = []
        self.aliases = [alias.lower().strip() for alias in aliases]
        # Create a local copy of all the potential lower-case names/aliases for this type
        self._potential_matches = [
            match.lower() for match in [self.name] + self.aliases
        ]

    @classmethod
    def identify(cls: type, line: str) -> "Service":
        """Work out what service is requested in a string.

        This method will pick the service that has the longest matching to the start of the string.

        Parameters
        ----------
        line : str
            String that identifies a service (either it's name or an alias to it)

        Returns
        -------
        Service:
            The radiocommunication service that matches that name.
        """
        # Convert input to lower case and not its lenth
        line_lower = line.lower()
        # Loop over candidate services
        result = None
        for service in _services:
            # Loop over potential matches to this service (the name and its aliases, all
            # converted to lower case)
            for candidate in service._potential_matches:
                if line_lower[: len(candidate)] == candidate:
                    # If the candidate is a match for the start of the string, then,
                    # assuming we don't already have a match then pick this one.
                    if result is None:
                        result = service
                    else:
                        # If do already have a match, pick this one instead if it is
                        # longer than the match we have already.
                        if len(candidate) > len(result.name):
                            result = service
        return result


# Now we define all our services and store them in a local database.
_services = [
    Service("AERONAUTICAL MOBILE"),
    Service("AERONAUTICAL MOBILE-SATELLITE"),
    Service("AERONAUTICAL RADIONAVIGATION", aliases=["AERONAUTICAL RADIONAVI-GATION"]),
    Service("AMATEUR"),
    Service("AMATEUR-SATELLITE"),
    Service("BROADCASTING"),
    Service("BROADCASTING-SATELLITE"),
    Service("EARTH EXPLORATION-SATELLITE", abbreviation="EESS", science=True),
    Service("FIXED"),
    Service("FIXED-SATELLITE"),
    Service("INTER-SATELLITE"),
    Service("LAND MOBILE"),
    Service("MARITIME MOBILE"),
    Service("MARITIME MOBILE-SATELLITE"),
    Service("MARITIME RADIONAVIGATION"),
    Service("METEOROLOGICAL AIDS", science_support=True),
    Service("METEOROLOGICAL-SATELLITE", science_support=True),
    Service("MOBILE except aeronautical mobile"),
    Service("MOBILE"),
    Service("MOBILE-SATELLITE except aeronautical mobile-satellite"),
    Service("MOBILE-SATELLITE except maritime mobile-satellite"),
    Service("MOBILE-SATELLITE"),
    Service("RADIO ASTRONOMY", abbreviation="RAS", science=True),
    Service("RADIODETERMINATION-SATELLITE", aliases=["RADIODETERMINATION-SATEL-LITE"]),
    Service("RADIOLOCATION"),
    Service("RADIOLOCATION-SATELLITE"),
    Service("RADIONAVIGATION"),
    Service("RADIONAVIGATION-SATELLITE"),
    Service("SPACE OPERATION"),
    Service("SPACE RESEARCH", science_support=True),
    Service(
        "STANDARD FREQUENCY AND TIME SIGNAL",
        abbreviation="Time",
        science_support=True,
    ),
    Service(
        "STANDARD FREQUENCY AND TIME SIGNAL-SATELLITE",
        abbreviation="Time",
        science_support=True,
    ),
]
