"""Code to provide additional alocations"""

from njl_corf.corf_pint import ureg
from .bands import Band
from .band_collections import BandCollection

NOTES = """
5.149 adds RAS at 6650-6675.2 MHz (see 5.458A), possibly others
"""

# ------------------------------------------------------- Allocation-adding footnotes.


# Footnote 5.149 is particularly complicated.  Text is more or less copy and pasted from
# the FCC tables
def footnote_5_149():
    """Return band or bands corresponding to footnote 5.149:

    In making assignments to stations of other services to which the bands: [TABLE]
    [Cell:] 13 360-13 410 kHz, 25 550-25 670 kHz, 37.5-38.25 MHz, 73-74.6 MHz in Regions
    1 and 3, 150.05-153 MHz in Region 1, 322-328.6 MHz, 406.1-410 MHz, 608-614 MHz in
    Regions 1 and 3, 1330-1400 MHz, 1610.6-1613.8 MHz, 1660-1670 MHz, 1718.8-1722.2 MHz,
    2655-2690 MHz, 3260-3267 MHz, 3332-3339 MHz, 3345.8-3352.5 MHz, 4825-4835 MHz,
    4950-4990 MHz, 4990-5000 MHz, 6650-6675.2 MHz, 10.6-10.68 GHz, 14.47-14.5 GHz,
    22.01-22.21 GHz, 22.21-22.5 GHz, 22.81-22.86 GHz, [Cell:] 23.07-23.12 GHz, 31.2-31.3
    GHz, 31.5-31.8 GHz in Regions 1 and 3, 36.43-36.5 GHz, 42.5-43.5 GHz, 48.94-49.04
    GHz, 76-86 GHz, 92-94 GHz, 94.1-100 GHz, 102-109.5 GHz, 111.8-114.25 GHz,
    128.33-128.59 GHz, 129.23-129.49 GHz, 130-134 GHz, 136-148.5 GHz, 151.5-158.5 GHz,
    168.59-168.93 GHz, 171.11-171.45 GHz, 172.31-172.65 GHz, 173.52-173.85 GHz,
    195.75-196.15 GHz, 209-226 GHz, 241-250 GHz, 252-275 GHz are allocated,
    administrations are urged to take all practicable steps to protect the radio
    astronomy service from harmful interference.  Emissions from spaceborne or airborne
    stations can be particularly serious sources of interference to the radio astronomy
    service (see Nos. 4.5 and 4.6 and Article 29).  (WRC-07)
    """
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
        # The first pair of words is the bounds and units
        bounds_str = " ".join(words[:2])
        # Now the remainder
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
            Band.create_band_from_footnote(
                bounds=bounds_str,
                allocations="Radio astronomy 5.149#",
                jurisdictions=jurisdictions,
            )
        )
    return bands


def footnote_5_225():
    """Return band or bands corresponding to footnote 5.225

    Additional allocation:  in Australia and India, the band 150.05-153 MHz is also
    allocated to the radio astronomy service on a primary basis.
    """
    return [
        Band.create_band_from_footnote(
            bounds="150.05-153 MHz",
            allocations="RADIO ASTRONOMY 5.225# (Australia and India only)",
            jurisdictions=["R3"],
        )
    ]


def footnote_5_250():
    """Return band or bands corresponding to footnote 5.250

    Additional allocation:  in China, the band 225-235 MHz is also allocated to the
    radio astronomy service on a secondary basis.
    """
    return [
        Band.create_band_from_footnote(
            bounds="225-235 MHz",
            allocations="Radio astronomy 5.250# (China only)",
            jurisdictions=["R3"],
        )
    ]


def footnote_5_304():
    """Return band or bands corresponding to footnote 5.304

    Additional allocation:  in the African Broadcasting Area (see Nos. 5.10 to 5.13),
    the band 606-614 MHz is also allocated to the radio astronomy service on a primary
    basis.
    """
    return [
        Band.create_band_from_footnote(
            bounds="606-614 MHz",
            allocations="RADIO ASTRONOMY 5.304# (African broadcasting area)",
            jurisdictions=["R1"],
        )
    ]


def footnote_5_305():
    """Return band or bands corresponding to footnote 5.305

    Additional allocation:  in China, the band 606-614 MHz is also allocated to the
    radio astronomy service on a primary basis. basis.
    """
    return [
        Band.create_band_from_footnote(
            bounds="606-614 MHz",
            allocations="RADIO ASTRONOMY 5.305# (China)",
            jurisdictions=["R3"],
        )
    ]


def footnote_5_306():
    """Return band or bands corresponding to footnote 5.306

    Additional allocation:  in Region 1, except in the African Broadcasting Area (see
    Nos. 5.10 to 5.13), and in Region 3, the band 608-614 MHz is also allocated to the
    radio astronomy service on a secondary basis.
    """
    return [
        Band.create_band_from_footnote(
            bounds="608-614 MHz",
            allocations="Radio astronomy 5.306# (Not Africa)",
            jurisdictions=["R1"],
        )
    ]


def footnote_5_307():
    """Return band or bands corresponding to footnote 5.307

    Additional allocation:  in India, the band 608-614 MHz is also allocated to the
    radio astronomy service on a primary basis.
    """
    return [
        Band.create_band_from_footnote(
            bounds="608-614 MHz",
            allocations="Radio astronomy 5.307# (India)",
            jurisdictions=["R1"],
        )
    ]


def footnote_5_339():
    """Return band or bands corresponding to footnote 5.339

    The bands 1370-1400 MHz, 2640-2655 MHz, 4950-4990 MHz and 15.20-15.35 GHz are also
    allocated to the space research (passive) and Earth exploration-satellite (passive)
    services on a secondary basis.
    """
    added_ranges = [
        "1370-1400 MHz",
        "2640-2655 MHz",
        "4950-4990 MHz",
        "15.20-15.35 GHz",
    ]
    bands = []
    for this_range in added_ranges:
        bands.append(
            Band.create_band_from_footnote(
                bounds=this_range,
                allocations=[
                    "Earth exploration-satellite (passive) 5.339#",
                    "Space research (passive) 5.339#",
                ],
                jurisdictions=["R1", "R2", "R3"],
            )
        )
    return bands


def footnote_5_385():
    """Return band or bands corresponding to footnote 5.385

    Additional allocation:  the band 1718.8-1722.2 MHz is also allocated to the radio
    astronomy service on a secondary basis for spectral line observations.
    """
    return [
        Band.create_band_from_footnote(
            bounds="1718.8-1722.2 MHz",
            allocations="Radio astronomy 5.385#",
            jurisdictions=["R1", "R2", "R3"],
        )
    ]


def footnote_5_437():
    """Return band or bands corresponding to footnote 5.437

    Passive sensing in the Earth exploration-satellite and space research services may
    be authorized in the frequency band 4200-4400 MHz on a secondary basis.  (WRC-15)
    """
    return [
        Band.create_band_from_footnote(
            bounds="4200-4400 MHz",
            allocations="Earth exploration-satellite (passive) 5.437#",
            jurisdictions=["R1", "R2", "R3"],
        )
    ]


def footnote_5_443():
    """Return band or bands corresponding to footnote 5.443:

    Different category of service:  in Argentina, Australia and Canada, the allocation
    of the bands 4825-4835 MHz and 4950-4990 MHz to the radio astronomy service is on a
    primary basis (see No. 5.33).
    """
    added_ranges = [
        "4825-4835 MHz",
        "4950-4990 MHz",
    ]
    bands = []
    for this_range in added_ranges:
        bands.append(
            Band.create_band_from_footnote(
                bounds=this_range,
                allocations="RADIO ASTRONOMY 5.443# (Argentina, Australia, Canada only)",
                jurisdictions=["R2", "R3"],
            )
        )
    return bands


def footnote_5_458():
    """Return band or bands corresponding to footnote 5.458:

    In the band 6425-7075 MHz, passive microwave sensor measurements are carried out
    over the oceans.  In the band 7075-7250 MHz, passive microwave sensor measurements
    are carried out.  Administrations should bear in mind the needs of the Earth
    exploration-satellite (passive) and space research (passive) services in their
    future planning of the bands 6425-7075 MHz and 7075-7250 MHz.
    """
    added_ranges = [
        "6425-7075 MHz",
        "7075-7250 MHz",
    ]
    bands = []
    for this_range in added_ranges:
        bands.append(
            Band.create_band_from_footnote(
                bounds=this_range,
                allocations="Earth exploration-satellite (passive) 5.458#",
                jurisdictions=["R1", "R2", "R3"],
            )
        )
    return bands


def footnote_5_479():
    """Return band or bands corresponding to footnote 5.479:

    The band 9975-10 025 MHz is also allocated to the meteorological-satellite service
    on a secondary basis for use by weather radars.
    """
    return [
        Band.create_band_from_footnote(
            bounds="9.975-10.025 GHz",
            allocations="Earth exploration-satellite (active) 5.479#",
            jurisdictions=["R1", "R2", "R3"],
        )
    ]


def footnote_5_543():
    """Return band or bands corresponding to footnote 5.543:

    The band 29.95-30 GHz may be used for space-to-space links in the Earth
    exploration-satellite service for telemetry, tracking, and control purposes, on a
    secondary basis.
    """
    return [
        Band.create_band_from_footnote(
            bounds="29.95-30 GHz",
            allocations="Earth exploration-satellite (space-to-space, comms.) 5.543#",
            jurisdictions=["R1", "R2", "R3"],
        )
    ]


def footnote_5_555():
    """Return band or bands corresponding to footnote 5.555:

    Additional allocation:  the band 48.94-49.04 GHz is also allocated to the radio
    astronomy service on a primary basis.
    """
    return [
        Band.create_band_from_footnote(
            bounds="48.94-49.05 GHz",
            allocations="RADIO ASTRONOMY 5.555#",
            jurisdictions=["R1", "R2", "R3"],
        )
    ]


def footnote_5_556():
    """Return band or bands corresponding to footnote 5.556:

    In the bands 51.4-54.25 GHz, 58.2-59 GHz and 64-65 GHz, radio astronomy observations
    may be carried out under national arrangements.
    """
    added_ranges = [
        "51.4-54.25 GHz",
        "58.2-59 GHz",
        "64-65 GHz",
    ]
    bands = []
    for this_range in added_ranges:
        bands.append(
            Band.create_band_from_footnote(
                bounds=this_range,
                allocations="radio astronomy 5.556# (On a nation-by-nation basis)",
                jurisdictions=["R1", "R2", "R3"],
            )
        )
    return bands


def footnote_5_562d():
    """Return band or bands corresponding to footnote 5.562D

    Additional allocation:  In Korea (Rep. of), the frequency bands 128-130 GHz,
    171-171.6 GHz, 172.2172.8 GHz and 173.3174 GHz are also allocated to the radio
    astronomy service on a primary basis.  Radio astronomy stations in Korea (Rep. of)
    operating in the frequency bands referred to in this footnote shall not claim
    protection from, or constrain the use and development of, services in other
    countries operating in accordance with the Radio Regulations.  (WRC-15)"""
    added_ranges = [
        "128-130 GHz",
        "171-171.6 GHz",
        "172.2-172.8 GHz",
        "173.3-174 GHz",
    ]
    bands = []
    for this_range in added_ranges:
        bands.append(
            Band.create_band_from_footnote(
                bounds=this_range,
                allocations="RADIO ASTRONOMY 5.562D# (Korea, Rep. of, only)",
                jurisdictions=["R3"],
            )
        )
    return bands


def footnote_5_563b():
    """Return band or bands corresponding to footnote 5.563b:

    The band 237.9-238 GHz is also allocated to the Earth
    exploration-satellite service (active) and the space research service (active) for
    spaceborne cloud radars only.
    """
    return [
        Band.create_band_from_footnote(
            bounds="237.9-238 GHz",
            allocations="Earth exploration-satellite (active) 5.563B#",
            jurisdictions=["R1", "R2", "R3"],
        )
    ]


def footnote_5_565():
    """Return band or bands corresponding to footnote 5.565:

    The following frequency bands in the range 275-1000 GHz are identified for use by
    administrations for passive service applications: radio astronomy service: 275-323
    GHz, 327-371 GHz, 388-424 GHz, 426-442 GHz, 453510 GHz, 623711 GHz, 795-909 GHz and
    926-945 GHz; â€“ Earth exploration-satellite service (passive) and space research
    service (passive): 275286 GHz, 296306 GHz, 313-356 GHz, 361-365 GHz, 369-392 GHz,
    397-399 GHz, 409-411 GHz, 416434 GHz, 439-467 GHz, 477-502 GHz, 523-527 GHz, 538-581
    GHz, 611-630 GHz, 634-654 GHz, 657692 GHz, 713-718 GHz, 729-733 GHz, 750-754 GHz,
    771-776 GHz, 823-846 GHz, 850-854 GHz, 857-862 GHz, 866-882 GHz, 905-928 GHz,
    951-956 GHz, 968-973 GHz and 985-990 GHz. The use of the range 275-1000 GHz by the
    passive services does not preclude use of this range by active services.
    Administrations wishing to make frequencies in the 275-1000 GHz range available for
    active service applications are urged to take all practicable steps to protect these
    passive services from harmful interference until the date when the Table of
    Frequency Allocations is established in the above-mentioned 275-1000 GHz frequency
    range. All frequencies in the range 1000-3000 GHz may be used by both active and
    passive services. (WRC12)
    """
    ras_ranges = [
        "275-323 GHz",
        "327-371 GHz",
        "388-424 GHz",
        "426-442 GHz",
        "453-510 GHz",
        "623-711 GHz",
        "795-909 GHz",
        "926-945 GHz",
    ]
    eess_ranges = [
        "275-286 GHz",
        "296-306 GHz",
        "313-356 GHz",
        "361-365 GHz",
        "369-392 GHz",
        "397-399 GHz",
        "409-411 GHz",
        "416-434 GHz",
        "439-467 GHz",
        "477-502 GHz",
        "523-527 GHz",
        "538-581 GHz",
        "611-630 GHz",
        "634-654 GHz",
        "657-692 GHz",
        "713-718 GHz",
        "729-733 GHz",
        "750-754 GHz",
        "771-776 GHz",
        "823-846 GHz",
        "850-854 GHz",
        "857-862 GHz",
        "866-882 GHz",
        "905-928 GHz",
        "951-956 GHz",
        "968-973 GHz",
        "985-990 GHz",
    ]
    bands = []
    for ranges, allocations in zip(
        [ras_ranges, eess_ranges],
        [
            "radio astronomy 5.565#",
            "earth exploration-satellite (passive) 5.565#",
        ],
    ):
        for this_range in ranges:
            bands.append(
                Band.create_band_from_footnote(
                    bounds=this_range,
                    allocations=allocations,
                    jurisdictions=["R1", "R2", "R3"],
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
        footnote_5_563b,
        footnote_5_565,
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
                this_protected_band = Band.create_band_from_footnote(
                    bounds=range_str, jurisdictions=[jurisdiction]
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
