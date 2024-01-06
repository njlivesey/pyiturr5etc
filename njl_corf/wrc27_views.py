"""Generates plots etc. in WRC-27 views report"""

from njl_corf.corf_pint import ureg


def get_ai_info() -> dict:
    """Populate a dictionary detailing the bands in each AI"""
    raw_ranges = {
        "WRC-23 AI-1.1": [slice(47.2 * ureg.GHz, 51.4 * ureg.GHz)],
        "WRC-23 AI-1.2": [slice(13.75 * ureg.GHz, 14.0 * ureg.GHz)],
        "WRC-23 AI-1.3": [slice(51.4 * ureg.GHz, 52.4 * ureg.GHz)],
        "WRC-23 AI-1.4": [slice(17.3 * ureg.GHz, 17.7 * ureg.GHz)],
        "WRC-23 AI-1.5": None,
        "WRC-23 AI-1.6": [
            slice(37.5 * ureg.GHz, 42.5 * ureg.GHz),
            slice(42.5 * ureg.GHz, 43.5 * ureg.GHz),
            slice(47.2 * ureg.GHz, 50.2 * ureg.GHz),
            slice(50.4 * ureg.GHz, 51.4 * ureg.GHz),
        ],
        "WRC-23 AI-1.7": [
            slice(4_400 * ureg.MHz, 4_800 * ureg.MHz),
            slice(7_125 * ureg.MHz, 8_400 * ureg.MHz),
            slice(14.8 * ureg.GHz, 15.35 * ureg.GHz),
        ],
        "WRC-23 AI-1.8": [
            slice(231.5 * ureg.GHz, 275 * ureg.GHz),
            slice(275 * ureg.GHz, 700 * ureg.GHz),
        ],
        "WRC-23 AI-1.9": [slice(3_025 * ureg.MHz, 18.030 * ureg.GHz)],
        "WRC-23 AI-1.10": [
            slice(71 * ureg.GHz, 76 * ureg.GHz),
            slice(81 * ureg.GHz, 86 * ureg.GHz),
        ],
        "WRC-23 AI-1.11": [
            slice(1_518 * ureg.MHz, 1_544 * ureg.MHz),
            slice(1_545 * ureg.MHz, 1_559 * ureg.MHz),
            slice(1_610 * ureg.MHz, 1_6455 * ureg.MHz),
            slice(1_645 * ureg.MHz, 1_660 * ureg.MHz),
            slice(1_670 * ureg.MHz, 1_675 * ureg.MHz),
            slice(2_485.5 * ureg.MHz, 2_500 * ureg.MHz),
        ],
        "WRC-23 AI-1.12": [
            slice(1_427 * ureg.MHz, 1_432 * ureg.MHz),
            slice(1_645.5 * ureg.MHz, 1_646.5 * ureg.MHz),
            slice(1_880 * ureg.MHz, 1_920 * ureg.MHz),
            slice(2_010 * ureg.MHz, 2_025 * ureg.MHz),
        ],
        "WRC-23 AI-1.13": [slice(694 * ureg.MHz, 2.7 * ureg.GHz)],
        "WRC-23 AI-1.14": None,
        "WRC-23 AI-1.15": [
            slice(390 * ureg.MHz, 406.1 * ureg.MHz),
            slice(420 * ureg.MHz, 430 * ureg.MHz),
            slice(440 * ureg.MHz, 450 * ureg.MHz),
            slice(2.4 * ureg.GHz, 2.69 * ureg.GHz),
            slice(3.5 * ureg.GHz, 3.8 * ureg.GHz),
            slice(5.15 * ureg.GHz, 5.57 * ureg.GHz),
            slice(5.57 * ureg.GHz, 5.725 * ureg.GHz),
            slice(5.775 * ureg.GHz, 5.925 * ureg.GHz),
            slice(7.190 * ureg.GHz, 7.235 * ureg.GHz),
            slice(8.45 * ureg.GHz, 8.5 * ureg.GHz),
            slice(25.25 * ureg.GHz, 28.35 * ureg.GHz),
        ],
        "WRC-23 AI-1.16": None,
        "WRC-23 AI-1.17": [
            slice(27.5 * ureg.MHz, 28.0 * ureg.MHz),
            slice(29.7 * ureg.MHz, 30.2 * ureg.MHz),
            slice(32.2 * ureg.MHz, 32.6 * ureg.MHz),
            slice(37.5 * ureg.MHz, 38.325 * ureg.MHz),
            slice(73.0 * ureg.MHz, 74.6 * ureg.MHz),
            slice(608 * ureg.MHz, 614 * ureg.MHz),
        ],
        "WRC-23 AI-1.18": None,
        "WRC-23 AI-1.19": [
            slice(4_200 * ureg.MHz, 4_400 * ureg.MHz),
            slice(8_400 * ureg.MHz, 8_500 * ureg.MHz),
        ],
        "WRC-27 AI-2.1": None,
        "WRC-27 AI-2.2": [slice(275 * ureg.GHz, 325 * ureg.GHz)],
        "WRC-27 AI-2.3": [slice(12.75, 13.25 * ureg.GHz)],
        "WRC-27 AI-2.4": [
            slice(3_700 * ureg.MHz, 4_200 * ureg.MHz),
            slice(5_925 * ureg.MHz, 6_425 * ureg.MHz),
        ],
        "WRC-27 AI-2.5": None,
        "WRC-27 AI-2.6": None,
        "WRC-27 AI-2.7": None,
        "WRC-27 AI-2.8": None,
        "WRC-27 AI-2.9": None,
        "WRC-27 AI-2.10": None,
        "WRC-27 AI-2.11": None,
        "WRC-27 AI-2.12": None,
        "WRC-27 AI-2.13": None,
        "WRC-27 AI-2.14": None,
    }
    # Start creating our result, which, for now, is just the AI prefixes with a, b, c,
    # etc. for each slice
    result = {}
    for prefix, slices in raw_ranges.items():
        if slices is None:
            result[prefix + "a"] = slice(None)
        else:
            for i_slice, this_slice in enumerate(slices):
                result[prefix + chr(ord("a") + i_slice)] = this_slice
    # Now a set of rules that merge ranges for an AI into adjacent (or nearby) groups
    # for ease of plotting.
    merging_rules = {
        "WRC-23 AI-1.6": ["ab", "cd"],
        "WRC-23 AI-1.11": ["abcde", "f"],
    }
    # Now do the actual merging
    for prefix, combinations in merging_rules.items():
        for combination in combinations:
            combined_slices = [result[prefix + character] for character in combination]
            enveloping_slice = slice(
                min(this_slice.start for this_slice in combined_slices),
                max(this_slice.stop for this_slice in combined_slices),
            )
            result[prefix + combination] = enveloping_slice
    return result
