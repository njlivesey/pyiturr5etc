"""Code to provide additional alocations"""

import astropy.units as units
from .bands import Band
    
def footnote_5_225():
    return [Band.parse(
        ["150.05-153", "Radio astronomy 5.225#"],
        unit=units.MHz, jurisdictions=["R3"],
        annotations=["Australia and India only"])]


def footnote_5_250():
    return [Band.parse(
        ["225-235", "Radio astronomy 5.250#"],
        unit=units.MHz, jurisdictions=["R3"],
        annotations=["China only"])]


def footnote_5_304():
    return [Band.parse(
        ["606-614", "RADIO ASTRONOMY 5.304#"],
        unit=units.MHz, annotations=["African broadcasting area"],
        jurisdictions=["R1"])]


def footnote_5_305():
    return [Band.parse(
        ["606-614", "RADIO ASTRONOMY 5.305#"],
        unit=units.MHz, annotations=["China"],
        jurisdictions=["R3"])]


def footnote_5_306():
    return [Band.parse(
        ["608-614", "Radio astronomy 5.306#"],
        unit=units.MHz, annotations=["Not Africa"],
        jurisdictions=["R1"])]


def footnote_5_307():
    return [Band.parse(
        ["608-614", "Radio astronomy 5.307#"],
        unit=units.MHz, annotations=["India"],
        jurisdictions=["R1"])]

def footnote_5_339():
    added_ranges = [
        "1370-1400",
        "2640-2655",
        "4950-4990",
        "15.20-15.35",
    ]
    added_units = [
        units.MHz,
        units.MHz,
        units.MHz,
        units.GHz,
    ]
    bands = []
    for r, u in zip(added_ranges, added_units):
        bands.append(
            Band.parse([
                r,
                "Earth exploration-satellite (passive) 5.339#",
                "Space research (passive) 5.339#",
            ], unit=u, jurisdictions=["R1", "R2", "R3"]))
    return bands


def footnote_5_385():
    return [Band.parse(
        ["1718.8-1722.2", "Radio astronomy 5.385#"],
        unit=units.MHz, jurisdictions=["R1", "R2", "R3"])]


def footnote_5_437():
    return [Band.parse(
        ["4200-4400", "Earth exploration-satellite (passive) 5.437#"],
        unit=units.MHz, jurisdictions=["R1", "R2", "R3"])]


def footnote_5_443():
    added_ranges = [
        "4825-4835",
        "4950-4990",
    ]
    bands = []
    for r in added_ranges:
        bands.append(
            Band.parse([r, "RADIO ASTRONOMY 5.443#"],
                       unit=units.MHz, jurisdictions=["R2", "R3"],
                       annotations=["Argentina, Australia, Canada only"]))
    return bands


def footnote_5_479():
    return [Band.parse(
        ["9975-10025", "Earth exploration-satellite (active) 5.479#"],
        unit=units.MHz, jurisdictions=["R1", "R2", "R3"])]

def footnote_5_458():
    added_ranges = [
        "6425-7075",
        "7075-7250",
    ]
    bands = []
    for r in added_ranges:
        bands.append(
            Band.parse([r,
                        "Earth exploration-satellite (passive) 5.458#"],
                       unit=units.MHz, jurisdictions=["R1", "R2", "R3"]))
    return bands

def footnote_5_543():
    return [Band.parse(
        ["29.95-30",
            "Earth exploration-satellite (space-to-space, comms.) 5.543#"],
        unit=units.GHz, jurisdictions=["R1", "R2", "R3"])]

def footnote_5_555():
    return [Band.parse(
        ["48.94-49.05", "RADIO ASTRONOMY 5.555#"],
        unit=units.GHz, jurisdictions=["R1", "R2", "R3"])]

def footnote_5_556():
    added_ranges = [
        "51.4-54.25",
        "58.2-59",
        "64-65",
    ]
    bands = []
    for r in added_ranges:
        bands.append(
            Band.parse([r, "RADIO ASTRONOMY 5.556#"],
                       unit=units.GHz, jurisdictions=["R1","R2","R3"],
                       annotations=["On a nation-by-nation basis"]))
    return bands
    

def footnote_5_562D():
    added_ranges = [
        "128-130",
        "171-171.6",
        "172.2-172.8",
        "173.3-174",
    ]
    bands = []
    for r in added_ranges:
        bands.append(
            Band.parse([r, "RADIO ASTRONOMY 5.562D#"],
                       unit=units.GHz, jurisdictions=["R3"],
                       annotations=["Korea (Rep. of) only"]))
    return bands


# ---------------------------------------------------------------------

# Footnote 5.149 is particularly complicated.  Text is more or less copy and pasted from the FCC tables
def footnote_5_149():
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
        "252-275 GHz"]
    bands = []
    for i in entries:
        words = i.split()
        # The first word is the bounds
        bounds = words[0]
        # The second is the units
        unit = units.Unit(words[1])
        if len(words) > 2:
            if words[2] != "in":
                raise ValueError("'in' expected.")
            if words[3] == "Region":
                jurisdictions = ["R"+words[4]]
            elif words[3] == "Regions":
                jurisdictions = [
                    "R"+words[4],
                    "R"+words[6],
                    ]
            else:
                raise ValueError(f"Unexpected word '{words[3]}'")
        else:
            jurisdictions = ["R1","R2","R3"]
        bands.append(
            Band.parse([bounds,"Radio astronomy 5.149#"],
                       unit=unit, jurisdictions=jurisdictions))
    return bands
        

# ---------------------------------------------------------------------

all_additions = []
routines = [
    footnote_5_149,
    footnote_5_225, footnote_5_250, footnote_5_304, footnote_5_305, footnote_5_306,
    footnote_5_307, footnote_5_339, footnote_5_385, footnote_5_437, footnote_5_443,
    footnote_5_479, footnote_5_543, footnote_5_458, footnote_5_555, footnote_5_556,
    footnote_5_562D ]
for r in routines:
    all_additions += r()

notes="""
5.149 adds RAS at 6650-6675.2 MHz (see 5.458A), possibly others
"""
