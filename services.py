"""Details of ITU Radio services"""

__all__ = ["Service"]


class Service:
    """A service that can be allocated to a band"""

    def __init__(
        self, name, abbreviation=None, science=False, science_support=False, aliases=[]
    ):
        self.name = name.lower().strip()
        if abbreviation is None:
            self.abbreviation = self.name
        self.science = science
        self.science_support = science_support
        self.aliases = [alias.lower().strip() for alias in aliases]

    @classmethod
    def identify(cls, line):
        result = None
        ll = line.lower()
        for service in _services:
            candidates = [service.name] + service.aliases
            for candidate in candidates:
                cl = candidate.lower()
                if ll[0 : len(cl)] == cl:
                    if result is None:
                        result = service
                    else:
                        if len(cl) > len(result.name):
                            result = service
        return result


_services = [
    #    Service(""),
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
        "STANDARD FREQUENCY AND TIME SIGNAL", abbreviation="Time", science_support=True
    ),
    Service(
        "STANDARD FREQUENCY AND TIME SIGNAL-SATELLITE",
        abbreviation="Time",
        science_support=True,
    ),
]
