"""A master class for containing all the allocation table information"""

from dataclasses import dataclass

from .band_collections import BandCollection


@dataclass
class AllocationDatabase:
    """Contains all the information on a set of frequency allocations"""

    source: str
    collections: dict[BandCollection]
    footnote_definitions: dict[str]

    @property
    def r1(self) -> BandCollection:
        """Return the Region 1 information"""
        return self.collections["ITU-R1"]

    @property
    def r2(self) -> BandCollection:
        """Return the Region 2 information"""
        return self.collections["ITU-R2"]

    @property
    def r3(self) -> BandCollection:
        """Return the Region 1 information"""
        return self.collections["ITU-R3"]

    def itu(self) -> BandCollection:
        """Return the combined ITU information"""
        return self.collections["ITU"]
