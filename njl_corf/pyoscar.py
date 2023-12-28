"""A module for reading and handling the WMO OSCAR frequency database

The input is the CSV file generated from the OSCAR website
"""

import math
from dataclasses import dataclass

import intervaltree
import numpy as np
import pandas as pd

from .pyfcctab.fccpint import ureg


@dataclass
class OscarEntry:
    """Contains one entry from the OSCAR database"""

    bounds: slice
    oscar_id: int
    satellite: str
    space_agency: str
    launch: str
    eol: str
    service: str
    sensing_mode: str
    nominal_frequency: str
    bandwidth: str
    polarization: str
    comment: str

    def __post_init__(self):
        """Just some tidying up after definition"""
        if self.bounds.stop == self.bounds.start:
            # pylint: disable-next=no-member
            delta = (
                math.sqrt(math.ulp(self.bounds.stop.magnitude)) * self.bounds.stop.units
            )
            self.bounds = slice(self.bounds.start, self.bounds.stop + delta)


def read_data(filename: str = None) -> intervaltree.IntervalTree:
    """Read the OSCAR database from Excel and ingest"""
    if filename is None:
        filename = (
            "/users/livesey/corf/data/"
            "Oscar-Satellite-Frequencies-Earth-observation-MW-frequencies-2023-11-14.xlsx"
        )
    data = pd.read_excel(filename)
    # Parse the frequency range information
    frequency_ranges = data["Frequency (GHz)"].str.split("-", expand=True)
    lower_limit = (
        frequency_ranges[0]
        .str.strip()
        .str.split(" ", expand=True)[0]
        .str.strip()
        .astype(float)
    )
    upper_limit = (
        frequency_ranges[1]
        .str.strip()
        .str.split(" ", expand=True)[0]
        .str.strip()
        .astype(float)
    )
    # Insert this new information into the table
    data["Frequency start"] = lower_limit
    data["Frequency stop"] = upper_limit
    data.loc[data["Frequency stop"].isnull(), "Frequency stop"] = data[
        "Frequency start"
    ]
    # Think about the bandwidth, first compute the one from the frequency ranges we
    # have.
    range_based_bandwidth = np.abs(upper_limit - lower_limit)
    # Now get the one in the able, if any
    bandwidth = data["Bandwidth (MHz)"].copy().astype(str).str.strip()
    bandwidth.loc[
        (bandwidth == "N/R") | (bandwidth == "-") | (bandwidth == "nan")
    ] = "0 MHz"
    # Convert it to GHz to match the frequency range information
    bandwidth_value = (
        bandwidth.str.split(" ", expand=True)[0].str.strip().astype(float) / 1e3
    )
    # Check that there is no confusion between the two versions of bandwidth
    questionable_row_flags = (bandwidth_value != 0) & (range_based_bandwidth > 1e-4)
    # In the cases where there is, then go with the bandwidth column as the definitive
    # source of information. (ACTUALLY, THIS IS WRONG!)
    data.loc[~questionable_row_flags, "Frequency start"] -= (
        0.5 * bandwidth_value[~questionable_row_flags]
    )
    data.loc[~questionable_row_flags, "Frequency stop"] += (
        0.5 * bandwidth_value[~questionable_row_flags]
    )
    # Now create the result and store in an IntervalTree
    result = intervaltree.IntervalTree()
    for row in data.to_dict("records"):
        entry = OscarEntry(
            bounds=slice(
                row["Frequency start"] * ureg.GHz, row["Frequency stop"] * ureg.GHz
            ),
            oscar_id=int(row["Id"]),
            satellite=row["Satellite"],
            space_agency=row["Space Agency"],
            launch=row["Launch "],
            eol=row["Eol"],
            service=row["Service"],
            sensing_mode=row["Sensing mode"],
            nominal_frequency=row["Frequency (GHz)"],
            bandwidth=row["Bandwidth (MHz)"],
            polarization=row["Polarisation"],
            comment=row["Comment"],
        )
        result[entry.bounds] = entry
    return result
