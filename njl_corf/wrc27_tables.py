"""A module for generating draft tables for the WRC views document"""

import copy
from dataclasses import dataclass
from dataclasses import fields as dataclass_fields

import docx
from pint import Quantity

from njl_corf import pyoscar, ureg


@dataclass
class TableRow:
    """Contains entries for a single row of the table"""

    sensor: str
    satellite: str
    frequency_polarization: str
    bandwidth: str
    ifov: str


def simplify_table_entries(entries: list[TableRow]) -> list[TableRow]:
    """Unify cases where the same sensor is on mulitple missions

    Parameters
    ----------
    entries : list[OscarEntry]
        The planned table entries

    Returns
    -------
    list[OscarEntry]
        The simplified table entries
    """
    still_relevant_flags = [True] * len(entries)
    result: list[TableRow] = []
    # Loop over entries
    for i_in, input_entry in enumerate(entries):
        print(f"{i_in=}, {input_entry.satellite=}, {still_relevant_flags=}")
        # Skip entries we've already marked as irrelevant
        if not still_relevant_flags[i_in]:
            continue
        # Find entries that are alike in all but mission name, accumulate those mission names
        mission_names = [input_entry.satellite]
        for i_check, check_entry in enumerate(entries):
            # Skip entries already obviated and this entry
            if not still_relevant_flags[i_check] or i_check == i_in:
                continue
            if (
                input_entry.sensor == check_entry.sensor
                and input_entry.frequency_polarization
                == check_entry.frequency_polarization
                and input_entry.bandwidth == check_entry.bandwidth
                and input_entry.ifov == check_entry.ifov
            ):
                # If matches in all but spacecraft name note that
                mission_names.append(check_entry.satellite)
                still_relevant_flags[i_check] = False
        # Now we have a list of mission names, try to simplify them
        prefixes = []
        suffixes = []
        # Split mission names into prefixes and suffixes
        for mission_name in mission_names:
            clauses = mission_name.split("-", maxsplit=1)
            prefixes.append(clauses[0])
            if len(clauses) == 2:
                suffixes.append(clauses[1])
            else:
                suffixes.append("")
        # Identify unique prefixes
        unique_prefixes = set(prefixes)
        combined_satellites = ""
        for prefix in unique_prefixes:
            # Loop over the matching prefixes
            entry = prefix
            got_a_suffix = False
            for test_prefix, test_suffix in zip(prefixes, suffixes):
                if test_prefix != prefix:
                    continue
                # Attempt to concatenate them
                if not got_a_suffix:
                    entry += "-"
                    got_a_suffix = True
                else:
                    entry += "/"
                entry += test_suffix
            # Put a semi colon between different missions
            if combined_satellites:
                combined_satellites += "; "
            combined_satellites += entry
        new_entry = copy.copy(input_entry)
        new_entry.satellite = combined_satellites
        result.append(new_entry)
    return result


def make_table(
    frequency_range: slice | Quantity,
    filename: str,
):
    """Greate a draft table for a given frequency range

    Parameters
    ----------
    frequency_range : slice[Quantity, Quantity, None]
        Frequency range subset to consider
    filename : str
        Filename for docx file
    """
    # Read the data from Oscar
    data = pyoscar.read()
    # Subset the bands of interest
    bands = data[frequency_range]
    # Work out the size of the table
    n_rows = len(bands) + 1
    n_columns = len(dataclass_fields(TableRow))
    # Populate the header row
    header_entry = TableRow(
        sensor="Sensor",
        satellite="Satellite",
        frequency_polarization="Center frequency (GHz), polarization",
        bandwidth="Bandwidth (MHz)",
        ifov="IFOV (km)",
    )
    # Create a table entry for each band
    output_data = []
    for band_entry in bands:
        band: pyoscar.OscarEntry = band_entry.data
        # Construct the center frequency and polarization string
        if band.nominal_frequency.endswith(" GHz"):
            frequency_polarization = (
                f"{band.nominal_frequency[:-4]} {band.polarization}"
            )
        else:
            raise ValueError(
                f"Unexpected suffix on nominal_fequency: '{band.nominal_frequency}'"
            )
        # Construct the bandwidth string
        if band.bandwidth.endswith(" MHz"):
            bandwidth = band.bandwidth[:-4]
        else:
            raise ValueError(f"Unexpected suffix on bandwidth: '{band.bandwidth}'")
        # Construct the rest and append this row
        output_data.append(
            TableRow(
                frequency_polarization=frequency_polarization,
                sensor=band.service,
                satellite=band.satellite,
                bandwidth=bandwidth,
                ifov="?",
            )
        )
    # Simplify this to merge missions
    output_data = simplify_table_entries(output_data)
    # Create the file with the result
    document = docx.Document()
    # Creat the table therein
    table = document.add_table(rows=1, cols=n_columns)
    # Populate the header row
    header_cells = table.rows[0].cells
    for i, field in enumerate(dataclass_fields(header_entry)):
        header_cells[i].text = getattr(header_entry, field.name)
    for entry in output_data:
        row_cells = table.add_row().cells
        for i, field in enumerate(dataclass_fields(entry)):
            row_cells[i].text = getattr(entry, field.name)

    if not filename.endswith(".docx"):
        raise ValueError("Filename must end with .docx")
    document.save(filename)
