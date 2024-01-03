"""Generates plots etc. in WRC-27 views report"""

from njl_corf.corf_pint import ureg


def get_ai_info() -> dict:
    """Populate a dictionary detailing the bands in each AI"""
    ranges = {
        "1.1": slice(47.2 * ureg.GHz, 51.4 * ureg.GHz),
        "1.2": slice(13.5 * ureg.GHz, 14.6 * ureg.GHz),
        "1.3": slice(51.4 * ureg.GHz, 52.4 * ureg.GHz),
        "1.4": slice(17.3 * ureg.GHz, 17.7 * ureg.GHz),
        "1.5": None,
        "1.6ab": slice(37.5 * ureg.GHz, 43.5 * ureg.GHz),
        "1.6cd": slice(47.2 * ureg.GHz, 51.4 * ureg.GHz),
        "1.7a": slice(4_400 * ureg.MHz, 4_800 * ureg.MHz),
        "1.7b": slice(7_125 * ureg.MHz, 8_400 * ureg.MHz),
        "1.7c": slice(14.8 * ureg.GHz, 15.35 * ureg.GHz),
        "1.8": slice(231.5 * ureg.GHz, 275 * ureg.GHz),
        "1.9": None,
        "1.10a": slice(71 * ureg.GHz, 76 * ureg.GHz),
        "1.10b": slice(81 * ureg.GHz, 86 * ureg.GHz),
        "1.11abcde": slice(1_518 * ureg.MHz, 1_675 * ureg.MHz),
        "1.11f": slice(2_483.5 * ureg.MHz, 2_500 * ureg.MHz),
        "1.12a": slice(1_427 * ureg.MHz, 1_432 * ureg.MHz),
        "1.12b": slice(1_645.5 * ureg.MHz, 1_646.5 * ureg.MHz),
        "1.12c": slice(1_880 * ureg.MHz, 1_920 * ureg.MHz),
        "1.12d": slice(2_010 * ureg.MHz, 2_025 * ureg.MHz),
        "1.13": None,
        "1.14": None,
        "1.15": None,
        "1.16": None,
        "1.17": None,
        "1.18": None,
        "1.19a": slice(4_200 * ureg.MHz, 4_400 * ureg.MHz),
        "1.19b": slice(8_400 * ureg.MHz, 8_500 * ureg.MHz),
    }
    return ranges
