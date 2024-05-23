"""A module for reading and handling the WMO OSCAR frequency database

The input is the CSV file generated from the OSCAR website
"""

import math
from dataclasses import dataclass
import fnmatch

from intervaltree import IntervalTree
import numpy as np
import pandas as pd

from njl_corf.corf_pint import ureg


@dataclass
# pylint: disable-next=too-many-instance-attributes
class OscarEntry:
    """Contains one entry from the OSCAR database"""

    bounds: slice
    oscar_id: str
    satellite: str
    space_agency: str
    launch: str
    eol: str
    nominal_frequency: str
    bandwidth: str
    polarization: str
    comment: str
    sensing_mode: str = None
    service: str = None

    def __post_init__(self):
        """Just some tidying up after definition"""
        if self.bounds.stop == self.bounds.start:
            # pylint: disable=no-member
            delta = (
                math.sqrt(math.ulp(self.bounds.stop.magnitude)) * self.bounds.stop.units
            )
            # pylint: enable=no-member
            self.bounds = slice(self.bounds.start, self.bounds.stop + delta)


def read(filename: str = None, communications: bool = False) -> IntervalTree:
    """Read the OSCAR database from Excel and ingest"""
    if filename is None:
        if not communications:
            filename = (
                "/users/livesey/corf/data/"
                "Oscar-Satellite-Frequencies-Earth-observation-MW-frequencies-2023-11-14.xlsx"
            )
        else:
            filename = (
                "/users/livesey/corf/data/"
                "Oscar-Satellite-Frequencies-for-Satellite-management-2024-05-23.xlsx"
            )
    data = pd.read_excel(filename).astype(str)
    # Identify fields to capture
    if not communications:
        frequency_field = "Frequency (GHz)"
        frequency_unit = ureg.GHz
        bandwidth_field = "Bandwidth (MHz)"
    else:
        frequency_field = "Frequency (MHz)"
        frequency_unit = ureg.MHz
        bandwidth_field = "Bandwidth (kHz)"
    # Parse the frequency range information
    frequency_ranges = data[frequency_field].str.split("-", expand=True)
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
    bandwidth = data[bandwidth_field].copy().astype(str).str.strip()
    bandwidth.loc[(bandwidth == "N/R") | (bandwidth == "-") | (bandwidth == "nan")] = (
        "0 MHz"
    )
    # Convert it to GHz to match the frequency range information.
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
    result = IntervalTree()
    for row in data.to_dict("records"):
        if not communications:
            kwargs = dict(
                sensing_mode=row["Sensing mode"].strip(),
                service=row["Service"].strip(),
            )
        else:
            kwargs = dict()
        entry = OscarEntry(
            bounds=slice(
                row["Frequency start"] * frequency_unit,
                row["Frequency stop"] * frequency_unit,
            ),
            oscar_id=str(row["Id"]),
            satellite=row["Satellite"],
            space_agency=row["Space Agency"],
            launch=row["Launch "],
            eol=row["Eol"],
            nominal_frequency=row[frequency_field],
            bandwidth=row[bandwidth_field],
            polarization=row["Polarisation"].strip(),
            comment=row["Comment"],
            **kwargs,
        )
        result[entry.bounds] = entry
    return result


def _merge_entry_strings(a: str, b: str, delimiter: str = None) -> str:
    """Combine entry string from b into a, if not there already

    Parameters
    ----------
    a : str
        One entry string (e.g., NASA)
    b : str
        Another entry string (e.g., ESA)
    delimiter : str, optional
        Character(s) to insert between entries (defaults to "/")

    Returns
    -------
    str
        Combined string
    """
    if delimiter is None:
        delimiter = "/"
    if b not in a:
        return a + delimiter + b
    return a


def _merge_entries(a: OscarEntry, b: OscarEntry, new_service: str = None):
    """Merge the data in two entries, for use by intervaltree"""
    combined_bounds = slice(
        min(a.bounds.start, b.bounds.start),
        max(a.bounds.stop, b.bounds.stop),
    )
    oscar_id = _merge_entry_strings(a.oscar_id, b.oscar_id)
    satellite = _merge_entry_strings(a.satellite, b.satellite)
    space_agency = _merge_entry_strings(a.space_agency, b.space_agency)
    launch = _merge_entry_strings(a.launch, b.launch)
    eol = _merge_entry_strings(a.eol, b.eol)
    service = _merge_entry_strings(a.service, b.service)
    sensing_mode = _merge_entry_strings(a.sensing_mode, b.sensing_mode)
    nominal_frequency = 0.5 * (combined_bounds.start + combined_bounds.stop)
    bandwidth = combined_bounds.start - combined_bounds.start
    polarization = _merge_entry_strings(a.polarization, b.polarization)
    comment = _merge_entry_strings(a.comment, b.comment)
    # Possibly patch the service name
    if new_service is not None:
        service = new_service
    # Build and return result
    return OscarEntry(
        bounds=combined_bounds,
        oscar_id=oscar_id,
        satellite=satellite,
        space_agency=space_agency,
        launch=launch,
        eol=eol,
        service=service,
        sensing_mode=sensing_mode,
        nominal_frequency=nominal_frequency,
        bandwidth=bandwidth,
        polarization=polarization,
        comment=comment,
    )


def merge_sensors(
    database: IntervalTree,
    rules: dict[str | list[str]],
) -> IntervalTree:
    """_summary_

    Parameters
    ----------
    database : IntervalTree
        All or part of the OSCAR database
    rules : dict[str  |  list[str]]
        Named rules giving wildcards which are then merged into a single entry according
        to the name.  For example, {"AMSR":"AMSR*"} will merge all the entries named
        AMSR* into a single AMSR entry.  Multiple wildcards can be given as a list

    Returns
    -------
    IntervalTree
        Result of the merge
    """
    # We'll need to do two passes for this I think, one where we identify all the
    # possible matches, the second when we collate them.  First get all the services (as
    # a unique list).
    all_services = list(set(entry.data.service for entry in database))
    rule_map = {}
    # Now go through all the rules and work out which specific service names match them
    for rule_name, wildcards in rules.items():
        if isinstance(wildcards, str):
            wildcards = [wildcards]
        for wildcard in wildcards:
            matching_services = []
            for service in all_services:
                if fnmatch.fnmatch(service, wildcard):
                    matching_services.append(service)
            for matching_service in matching_services:
                if matching_service in rule_map:
                    raise ValueError(
                        f"Duplicate entries: {matching_service} trying {rule_name}, "
                        f"already have {rule_map[matching_service]}"
                    )
                rule_map[matching_service] = rule_name

    # Now go through all the allocations, divvy them up according to whether they match
    # one of our rules (if not, put it in a default collection).  First create a place
    # to stage these.
    collections = {rule_name: IntervalTree() for rule_name in rules.keys()}
    default_collection = "**Default**"
    collections[default_collection] = IntervalTree()
    # Now loop over the database and place each entry in the right collection
    for entry in database:
        collection = rule_map.get(entry.data.service, default_collection)
        collections[collection].add(entry)
    # Now go through the collections and merge them if appropriate
    result = IntervalTree()
    for collection_name, collection in collections.items():
        if collection_name != default_collection:
            # pylint: disable=cell-var-from-loop
            collection.merge_overlaps(
                data_reducer=lambda a, b: _merge_entries(
                    a, b, new_service=collection_name
                ),
                strict=False,
            )
            # pylint: enable=cell-var-from-loop
        result |= collection
    return result
