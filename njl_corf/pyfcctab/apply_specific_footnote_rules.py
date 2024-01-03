"""Code to provide additional alocations"""

import copy

from intervaltree import IntervalTree

from njl_corf.corf_pint import ureg
from .bands import Band
from .band_collections import BandCollection

NOTES = """
5.149 adds RAS at 6650-6675.2 MHz (see 5.458A), possibly others
"""

# ------------------------------------------------------- Allocation-adding footnotes.


def footnote_5_225():
    """Return a Band corresponding to an allocation described in a footnote"""
    return [
        Band.parse(
            ["150.05-153", "Radio astronomy 5.225# (Australia and India only)"],
            units=ureg.MHz,
            jurisdictions=["R3"],
            annotations=[""],
        )
    ]


def footnote_5_250():
    """Return a Band corresponding to an allocation described in a footnote"""
    return [
        Band.parse(
            ["225-235", "Radio astronomy 5.250# (China only)"],
            units=ureg.MHz,
            jurisdictions=["R3"],
        )
    ]


def footnote_5_304():
    """Return a Band corresponding to an allocation described in a footnote"""
    return [
        Band.parse(
            ["606-614", "RADIO ASTRONOMY 5.304# (African broadcasting area)"],
            units=ureg.MHz,
            jurisdictions=["R1"],
        )
    ]


def footnote_5_305():
    """Return a Band corresponding to an allocation described in a footnote"""
    return [
        Band.parse(
            ["606-614", "RADIO ASTRONOMY 5.305# (China)"],
            units=ureg.MHz,
            jurisdictions=["R3"],
        )
    ]


def footnote_5_306():
    """Return a Band corresponding to an allocation described in a footnote"""
    return [
        Band.parse(
            ["608-614", "Radio astronomy 5.306# (Not Africa)"],
            units=ureg.MHz,
            jurisdictions=["R1"],
        )
    ]


def footnote_5_307():
    """Return a Band corresponding to an allocation described in a footnote"""
    return [
        Band.parse(
            ["608-614", "Radio astronomy 5.307# (India)"],
            units=ureg.MHz,
            jurisdictions=["R1"],
        )
    ]


def footnote_5_339():
    """Return a Band corresponding to an allocation described in a footnote"""
    added_ranges = [
        "1370-1400",
        "2640-2655",
        "4950-4990",
        "15.20-15.35",
    ]
    added_units = [
        ureg.MHz,
        ureg.MHz,
        ureg.MHz,
        ureg.GHz,
    ]
    bands = []
    for this_range, these_units in zip(added_ranges, added_units):
        bands.append(
            Band.parse(
                [
                    this_range,
                    "Earth exploration-satellite (passive) 5.339#",
                    "Space research (passive) 5.339#",
                ],
                units=these_units,
                jurisdictions=["R1", "R2", "R3"],
            )
        )
    return bands


def footnote_5_385():
    """Return a Band corresponding to an allocation described in a footnote"""
    return [
        Band.parse(
            ["1718.8-1722.2", "Radio astronomy 5.385#"],
            units=ureg.MHz,
            jurisdictions=["R1", "R2", "R3"],
        )
    ]


def footnote_5_437():
    """Return a Band corresponding to an allocation described in a footnote"""
    return [
        Band.parse(
            ["4200-4400", "Earth exploration-satellite (passive) 5.437#"],
            units=ureg.MHz,
            jurisdictions=["R1", "R2", "R3"],
        )
    ]


def footnote_5_443():
    """Return a Band corresponding to an allocation described in a footnote"""
    added_ranges = [
        "4825-4835",
        "4950-4990",
    ]
    bands = []
    for this_range in added_ranges:
        bands.append(
            Band.parse(
                [
                    this_range,
                    "RADIO ASTRONOMY 5.443# (Argentina, Australia, Canada only)",
                ],
                units=ureg.MHz,
                jurisdictions=["R2", "R3"],
            )
        )
    return bands


def footnote_5_479():
    """Return a Band corresponding to an allocation described in a footnote"""
    return [
        Band.parse(
            ["9.975-10.025", "Earth exploration-satellite (active) 5.479#"],
            units=ureg.GHz,
            jurisdictions=["R1", "R2", "R3"],
        )
    ]


def footnote_5_458():
    """Return a Band corresponding to an allocation described in a footnote"""
    added_ranges = [
        "6425-7075",
        "7075-7250",
    ]
    bands = []
    for this_range in added_ranges:
        bands.append(
            Band.parse(
                [this_range, "Earth exploration-satellite (passive) 5.458#"],
                units=ureg.MHz,
                jurisdictions=["R1", "R2", "R3"],
            )
        )
    return bands


def footnote_5_543():
    """Return a Band corresponding to an allocation described in a footnote"""
    return [
        Band.parse(
            ["29.95-30", "Earth exploration-satellite (space-to-space, comms.) 5.543#"],
            units=ureg.GHz,
            jurisdictions=["R1", "R2", "R3"],
        )
    ]


def footnote_5_555():
    """Return a Band corresponding to an allocation described in a footnote"""
    return [
        Band.parse(
            ["48.94-49.05", "RADIO ASTRONOMY 5.555#"],
            units=ureg.GHz,
            jurisdictions=["R1", "R2", "R3"],
        )
    ]


def footnote_5_556():
    """Return a Band corresponding to an allocation described in a footnote"""
    added_ranges = [
        "51.4-54.25",
        "58.2-59",
        "64-65",
    ]
    bands = []
    for this_range in added_ranges:
        bands.append(
            Band.parse(
                [this_range, "Radio astronomy 5.556# (On a nation-by-nation basis)"],
                units=ureg.GHz,
                jurisdictions=["R1", "R2", "R3"],
            )
        )
    return bands


def footnote_5_562d():
    """Return a Band corresponding to an allocation described in a footnote"""
    added_ranges = [
        "128-130",
        "171-171.6",
        "172.2-172.8",
        "173.3-174",
    ]
    bands = []
    for this_range in added_ranges:
        bands.append(
            Band.parse(
                [this_range, "RADIO ASTRONOMY 5.562D# (Korea, Rep. of, only)"],
                units=ureg.GHz,
                jurisdictions=["R3"],
            )
        )
    return bands


# Footnote 5.149 is particularly complicated.  Text is more or less copy and pasted from
# the FCC tables
def footnote_5_149():
    """Return a Band corresponding to an allocation described in a footnote"""
    entries = [
        "13.360-13.410 MHz",
        "25.550-25.670 MHz",
        "37.5-38.25 MHz",
        "73-74.6 MHz in Regions 1 and 3",
        "150.05-153 MHz in Region 1",
        "322-328.6 MHz",
        "406.1-410 MHz",
        "608-614 MHz in Regions 1 and 3",
        "1330-1400 MHz",
        "1610.6-1613.8 MHz",
        "1660-1670 MHz",
        "1718.8-1722.2 MHz",
        "2655-2690 MHz",
        "3260-3267 MHz",
        "3332-3339 MHz",
        "3345.8-3352.5 MHz",
        "4825-4835 MHz",
        "4950-4990 MHz",
        "4990-5000 MHz",
        "6650-6675.2 MHz",
        "10.6-10.68 GHz",
        "14.47-14.5 GHz",
        "22.01-22.21 GHz",
        "22.21-22.5 GHz",
        "22.81-22.86 GHz",
        "23.07-23.12 GHz",
        "31.2-31.3 GHz",
        "31.5-31.8 GHz in Regions 1 and 3",
        "36.43-36.5 GHz",
        "42.5-43.5 GHz",
        "48.94-49.04 GHz",
        "76-86 GHz",
        "92-94 GHz",
        "94.1-100 GHz",
        "102-109.5 GHz",
        "111.8-114.25 GHz",
        "128.33-128.59 GHz",
        "129.23-129.49 GHz",
        "130-134 GHz",
        "136-148.5 GHz",
        "151.5-158.5 GHz",
        "168.59-168.93 GHz",
        "171.11-171.45 GHz",
        "172.31-172.65 GHz",
        "173.52-173.85 GHz",
        "195.75-196.15 GHz",
        "209-226 GHz",
        "241-250 GHz",
        "252-275 GHz",
    ]
    bands = []
    for i in entries:
        words = i.split()
        # The first word is the bounds
        bounds_str = words[0]
        # The second is the units
        units = ureg.Unit(words[1])
        if len(words) > 2:
            if words[2] != "in":
                raise ValueError("'in' expected.")
            if words[3] == "Region":
                jurisdictions = ["R" + words[4]]
            elif words[3] == "Regions":
                jurisdictions = [
                    "R" + words[4],
                    "R" + words[6],
                ]
            else:
                raise ValueError(f"Unexpected word '{words[3]}'")
        else:
            jurisdictions = ["R1", "R2", "R3"]
        bands.append(
            Band.parse(
                [bounds_str, "Radio astronomy 5.149#"],
                units=units,
                jurisdictions=jurisdictions,
            )
        )
    return bands


# ------------------------------------------------------- Master routine


def get_all_itu_footnote_based_additions() -> BandCollection:
    """Creates a bunch of new allocations from footnotes

    Calling code should then insert these allocations into the tables.

    Returns
    -------
    BandCollection
        The various additional allocations.
    """
    all_additions = []
    routines = [
        footnote_5_149,
        footnote_5_225,
        footnote_5_250,
        footnote_5_304,
        footnote_5_305,
        footnote_5_306,
        footnote_5_307,
        footnote_5_339,
        footnote_5_385,
        footnote_5_437,
        footnote_5_443,
        footnote_5_479,
        footnote_5_543,
        footnote_5_458,
        footnote_5_555,
        footnote_5_556,
        footnote_5_562d,
    ]
    all_additions = BandCollection()
    for r in routines:
        these_bands = r()
        for b in these_bands:
            all_additions.append(b)
    return all_additions


# ------------------------------------------------------- 5.340/US246


# pylint: disable-next=too-many-locals
def enact_5_340_us246(
    collections: dict[BandCollection],
    interrupt_other_allocations: bool = True,
):
    """Enact the 5.340 and US-246 protections

    In most cases the bands are already marked as 5.340/US246 protected, however, in a
    couple of them the protection is limited to a small slice within the band.  In those
    cases we will split the existing bands and insert the protected band.

    Parameters
    ----------
    collections : dict[BandCollection]
        The collections of bands that have been read in.
    interrupt_other_allocations : bool, optional
        If set, then any allocations that cover the protected band but are wider than it
        are split in two such that their allocation appears to be interrupted. By
        default True

    Raises
    ------
    ValueError
        In cases where there seem to be multiple bands overlapping a protected band
        (shouldn't happen by construction).
    """
    # These entries are cut and pasted directly from the FCC document (2022-08-23 version).
    entries_5_340 = [
        "1400-1427 MHz",
        "2690-2700 MHz, except those provided for by No. 5.422",
        "10.68-10.7 GHz, except those provided for by No. 5.483",
        "15.35-15.4 GHz, except those provided for by No. 5.511",
        "23.6-24 GHz",
        "31.3-31.5 GHz",
        "31.5-31.8 GHz, in Region 2",
        "48.94-49.04 GHz, from airborne stations",
        "50.2-50.4 GHz",
        "52.6-54.25 GHz",
        "86-92 GHz",
        "100-102 GHz",
        "109.5-111.8 GHz",
        "114.25-116 GHz",
        "148.5-151.5 GHz",
        "164-167 GHz",
        "182-185 GHz",
        "190-191.8 GHz",
        "200-209 GHz",
        "226-231.5 GHz",
        "250-252 GHz",
    ]
    entries_us246 = [
        "73-74.6 MHz",
        "608-614 MHz, except for medical telemetry equipment and white space devices",
        "1400-1427 MHz",
        "1660.5-1668.4 MHz",
        "2690-2700 MHz",
        "4990-5000 MHz",
        "10.68-10.7 GHz",
        "15.35-15.4 GHz",
        "23.6-24 GHz",
        "31.3-31.8 GHz",
        "50.2-50.4 GHz",
        "52.6-54.25 GHz",
        "86-92 GHz",
        "100-102 GHz",
        "109.5-111.8 GHz",
        "114.25-116 GHz",
        "148.5-151.5 GHz",
        "164-167 GHz",
        "182-185 GHz",
        "190-191.8 GHz",
        "200-209 GHz",
        "226-231.5 GHz",
        "250-252 GHz",
    ]
    itu_jurisdictions = ["R1", "R2", "R3"]  # list(collections.keys())
    usa_jurisdictions = ["F", "NF"]

    # pylint: disable-next=too-many-nested-blocks
    for entries, relevant_jurisdictions, trigger_footnote in zip(
        [entries_5_340, entries_us246],
        [itu_jurisdictions, usa_jurisdictions],
        ["5.340", "US246"],
    ):
        for entry in entries:
            try:
                range_str, suffix = entry.split(",")
                suffix = suffix.strip()
            except ValueError:
                range_str = entry
                suffix = ""
            bounds_str, units_str = range_str.split(" ")
            units = ureg.Unit(units_str)
            # Deal with any suffixes
            if suffix == "in Region 2":
                jurisdictions = ["R2"]
            else:
                jurisdictions = relevant_jurisdictions
            # Go through all the jurisdictions and basically do nothing when the
            # protected band spans the full band in the alocation table.  However, when
            # the protected band is a narrow subset of the full band, some extra steps
            # can be taken.
            for jurisdiction in jurisdictions:
                # Create a band to denote this protection
                this_protected_band = Band.parse(
                    [bounds_str], units=units, jurisdictions=[jurisdiction]
                )
                this_protected_band.footnotes.append(trigger_footnote)
                collection = collections[jurisdiction]
                # Find the band that overlaps it (there should be only one per jurisdiction)
                overlapping_bands = collection[
                    this_protected_band.bounds[0] : this_protected_band.bounds[1]
                ]
                if len(overlapping_bands) != 1:
                    raise ValueError(
                        "Incorrect number of overlapping bands "
                        f"{jurisdiction}:\n{overlapping_bands}"
                    )
                overlapping_band = overlapping_bands[0]
                # Now, if the protected band is a narrow subset of the overlapping band,
                # then we potentially take extra steps to "interrupt" the overlapping
                # band.
                if (
                    not overlapping_band.has_same_bounds_as(this_protected_band)
                    and interrupt_other_allocations
                ):
                    # OK, we need to split this and apply the 5.340 to only the actual 5.340
                    # band.  Remove 5.340 from the overlapping band if present
                    try:
                        overlapping_band.footnotes.remove(trigger_footnote)
                    except ValueError:
                        pass
                    # Insert the new "protected" band into the list of bands
                    collection.data[
                        this_protected_band.bounds[0] : this_protected_band.bounds[1]
                    ] = this_protected_band
                    # Invoke split_overlaps so as to interrupt the underlying allocations
                    collection.data.split_overlaps()
                    # But this still leaves the slivers of the underlying wider bands in
                    # place.  Spot and remove these because we removed 5.340 from the wider
                    # bands earlier
                    for candidate_band in collection.data[this_protected_band.center]:
                        if not candidate_band.data.has_footnote(trigger_footnote):
                            collection.data.remove(candidate_band)
                else:
                    # Otherwise, at least check that the overlapping band has the
                    # trigger foonote.
                    if not overlapping_band.has_footnote(trigger_footnote):
                        raise ValueError(
                            f"Band {overlapping_band.compact_str()} "
                            f"does not have footnote {trigger_footnote}"
                        )
