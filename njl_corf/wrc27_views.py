"""Generates plots etc. in WRC-27 views report"""

import re
import textwrap
import pathlib
import shutil
import warnings
from dataclasses import dataclass
from typing import Optional

import matplotlib.pyplot as plt
from intervaltree import IntervalTree
from natsort import natsorted

from njl_corf import band_figure, pyfcctab
from njl_corf.corf_pint import ureg


@dataclass
class _AIKernel:
    """Information about a WRC agenda item

    Attributes
    ----------
    name : str
        Name for the agenda item (e.g., "AI-1.2")
    wrc : str
        "WRC-27" or "WRC-31" (currently)
    text : str
        Text of agenda item
    soundbyte : str
        Summary of threat to passive services
    """

    name: str = None
    wrc: str = None
    text: str = None
    soundbyte: str = None

    def format_soundbyte(
        self,
        first_word_only: bool = False,
        multi_line: bool = False,
        latex: Optional[bool] = False,
    ) -> str:
        """Return a useful string representation of the "soundbyte" attribute

        Parameters
        ----------
        first_word_only : bool, optional
            If set, use only the first "word" (underscores are non-breaking but replaced
            with spaces)
        multi_line : bool, optional
            If set, split into two lines

        Returns
        -------
        str
            String result
        """
        # Get a first cut at the result
        result = self.soundbyte
        if result is None:
            return ""
        # If we only want the first "word", get that
        if first_word_only:
            result = result.split(" ", maxsplit=1)[0]
        # Now replace any underscores with spaces
        result = result.replace("_", " ")
        # Now, possibly split into multiple lines
        if multi_line:
            words = result.split(" ")
            if len(words) == 1:
                pass
            if len(words) == 2:
                result = "\n".join(words)
            if len(words) == 3:
                options = [
                    [words[0], words[1] + "\n" + words[2]],
                    [words[0] + "\n" + words[1], words[2]],
                ]
                lengths = [[len(clause) for clause in option] for option in options]
                deltas = [abs(length[0] - length[1]) for length in lengths]
                i_option = deltas.index(min(deltas))
                result = "\n".join(options[i_option])
        # Now prepare for latex
        if latex:
            result = result.replace(">", r"\textgreater")
        return result


@dataclass
class AgendaItem(_AIKernel):
    """Information about a WRC agenda item

    Attributes
    ----------
    name : str
        Name for the agenda item (e.g., "AI-1.2")
    wrc : str
        "WRC-27" or "WRC-31" (currently)
    frequency_bands : list[range]
        Bands under consideration
    text : str
        Text of agenda item
    soundbyte : str
        Summary of threat to passive services
    """

    frequency_bands: list[range] = None

    def __post_init__(self):
        """Tidy up after creation"""
        if self.frequency_bands is None:
            self.frequency_bands = []

    def split(self):
        """Return subbands of self as list"""
        result = []
        for i_band, frequency_band in enumerate(self.frequency_bands):
            result.append(
                AgendaItemSubBand(
                    name=self.name,
                    wrc=self.wrc,
                    text=self.text,
                    soundbyte=self.soundbyte,
                    i_band=i_band,
                    n_bands=len(self.frequency_bands),
                    frequency_band=frequency_band,
                )
            )
        return result


@dataclass
class AgendaItemSubBand(_AIKernel):
    """One band from an AgendaItem"""

    frequency_band: slice = None
    i_band: int = 0
    n_bands: int = 0


def get_ai_info(grouped: bool = False) -> dict[AgendaItem]:
    """Populate a dictionary detailing the bands in each AI"""
    ai_info = {
        "WRC-27 AI-1.1": AgendaItem(
            frequency_bands=[
                slice(47.2 * ureg.GHz, 50.2 * ureg.GHz),
                slice(50.4 * ureg.GHz, 51.4 * ureg.GHz),
            ],
            soundbyte="ESIMs (aero/marine)",
        ),
        "WRC-27 AI-1.2": AgendaItem(
            frequency_bands=[slice(13.75 * ureg.GHz, 14.0 * ureg.GHz)],
            soundbyte="FSS uplinks",
        ),
        "WRC-27 AI-1.3": AgendaItem(
            frequency_bands=[slice(51.4 * ureg.GHz, 52.4 * ureg.GHz)],
            soundbyte="FSS NGSO uplinks",
        ),
        "WRC-27 AI-1.4": AgendaItem(
            frequency_bands=[slice(17.3 * ureg.GHz, 17.8 * ureg.GHz)],
            soundbyte="FSS NGSO downlinks",
        ),
        "WRC-27 AI-1.5": AgendaItem(
            frequency_bands=None,
            soundbyte="NGSO",
        ),
        "WRC-27 AI-1.6": AgendaItem(
            frequency_bands=[
                slice(37.5 * ureg.GHz, 42.5 * ureg.GHz),
                slice(42.5 * ureg.GHz, 43.5 * ureg.GHz),
                slice(47.2 * ureg.GHz, 50.2 * ureg.GHz),
                slice(50.4 * ureg.GHz, 51.4 * ureg.GHz),
            ],
            soundbyte="FSS up/down",
        ),
        "WRC-27 AI-1.7": AgendaItem(
            frequency_bands=[
                slice(4_400 * ureg.MHz, 4_800 * ureg.MHz),
                slice(7_125 * ureg.MHz, 8_400 * ureg.MHz),
                slice(14.8 * ureg.GHz, 15.35 * ureg.GHz),
            ],
            soundbyte="IMT",
        ),
        "WRC-27 AI-1.8": AgendaItem(
            frequency_bands=[
                slice(231.5 * ureg.GHz, 275 * ureg.GHz),
                slice(275 * ureg.GHz, 700 * ureg.GHz),
            ],
            soundbyte="Radiolocation",
        ),
        "WRC-27 AI-1.9": AgendaItem(
            frequency_bands=[
                slice(3_025 * ureg.kHz, 3_155 * ureg.kHz),
                slice(3_900 * ureg.kHz, 3_950 * ureg.kHz),
                slice(4_700 * ureg.kHz, 4_750 * ureg.kHz),
                slice(5_680 * ureg.kHz, 5_730 * ureg.kHz),
                slice(6_685 * ureg.kHz, 6_765 * ureg.kHz),
                slice(8_965 * ureg.kHz, 9_040 * ureg.kHz),
                slice(11_175 * ureg.kHz, 11_275 * ureg.kHz),
                slice(13_200 * ureg.kHz, 13_260 * ureg.kHz),
                slice(15_010 * ureg.kHz, 15_100 * ureg.kHz),
                slice(17_970 * ureg.kHz, 18_030 * ureg.kHz),
            ],
            soundbyte="Aeronautical mobile",
        ),
        "WRC-27 AI-1.10": AgendaItem(
            frequency_bands=[
                slice(71 * ureg.GHz, 76 * ureg.GHz),
                slice(81 * ureg.GHz, 86 * ureg.GHz),
            ],
            soundbyte="Satellite PFD/EIRP",
        ),
        "WRC-27 AI-1.11": AgendaItem(
            frequency_bands=[
                slice(1_518 * ureg.MHz, 1_544 * ureg.MHz),
                slice(1_545 * ureg.MHz, 1_559 * ureg.MHz),
                slice(1_610 * ureg.MHz, 1_645.5 * ureg.MHz),
                slice(1_645 * ureg.MHz, 1_660 * ureg.MHz),
                slice(1_670 * ureg.MHz, 1_675 * ureg.MHz),
                slice(2_485.5 * ureg.MHz, 2_500 * ureg.MHz),
            ],
            soundbyte="space-to-space",
        ),
        "WRC-27 AI-1.12": AgendaItem(
            frequency_bands=[
                slice(1_427 * ureg.MHz, 1_432 * ureg.MHz),
                slice(1_645.5 * ureg.MHz, 1_646.5 * ureg.MHz),
                slice(1_880 * ureg.MHz, 1_920 * ureg.MHz),
                slice(2_010 * ureg.MHz, 2_025 * ureg.MHz),
            ],
            soundbyte="MSS",
        ),
        "WRC-27 AI-1.13": AgendaItem(
            frequency_bands=[slice(694 * ureg.MHz, 2.7 * ureg.GHz)],
            soundbyte="MSS/IMT",
        ),
        "WRC-27 AI-1.14": AgendaItem(
            frequency_bands=[
                slice(2_010 * ureg.MHz, 2_025 * ureg.MHz),
                slice(2_160 * ureg.MHz, 2_170 * ureg.MHz),
            ],
            soundbyte="MSS",
        ),
        "WRC-27 AI-1.15": AgendaItem(
            frequency_bands=[
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
            soundbyte="Lunar",
        ),
        "WRC-27 AI-1.16": AgendaItem(
            frequency_bands=[
                slice(10.7 * ureg.GHz, 10.95 * ureg.GHz),
                slice(42.0 * ureg.GHz, 42.5 * ureg.GHz),
                slice(74.0 * ureg.GHz, 76.0 * ureg.GHz),
                slice(95.0 * ureg.GHz, 100.0 * ureg.GHz),
                slice(116 * ureg.GHz, 119.98 * ureg.GHz),
                slice(123 * ureg.GHz, 130.0 * ureg.GHz),
            ],
            soundbyte="Quiet_zones",
        ),
        "WRC-27 AI-1.17": AgendaItem(
            frequency_bands=[
                slice(27.5 * ureg.MHz, 28.0 * ureg.MHz),
                slice(29.7 * ureg.MHz, 30.2 * ureg.MHz),
                slice(32.2 * ureg.MHz, 32.6 * ureg.MHz),
                slice(37.5 * ureg.MHz, 38.325 * ureg.MHz),
                slice(73.0 * ureg.MHz, 74.6 * ureg.MHz),
                slice(608 * ureg.MHz, 614 * ureg.MHz),
            ],
            soundbyte="Space_weather",
        ),
        "WRC-27 AI-1.18": AgendaItem(
            frequency_bands=[
                slice(71.0 * ureg.GHz, 76.0 * ureg.GHz),
                slice(81.0 * ureg.GHz, 86.0 * ureg.GHz),
                slice(92.0 * ureg.GHz, 94.0 * ureg.GHz),
                slice(111.8 * ureg.GHz, 114.25 * ureg.GHz),
                slice(123.0 * ureg.GHz, 130.0 * ureg.GHz),
                slice(158.5 * ureg.GHz, 164 * ureg.GHz),
                slice(167.0 * ureg.GHz, 174.5 * ureg.GHz),
                slice(191.8 * ureg.GHz, 200.0 * ureg.GHz),
                slice(209.0 * ureg.GHz, 217.0 * ureg.GHz),
                slice(232.0 * ureg.GHz, 235.0 * ureg.GHz),
            ],
            soundbyte="EESS/RAS protection",
        ),
        "WRC-27 AI-1.19": AgendaItem(
            frequency_bands=[
                slice(4_200 * ureg.MHz, 4_400 * ureg.MHz),
                slice(8_400 * ureg.MHz, 8_500 * ureg.MHz),
            ],
            soundbyte="EESS_(Passive)",
        ),
        "WRC-31 AI-2.1": AgendaItem(
            frequency_bands=[slice(275.0 * ureg.GHz, 325.0 * ureg.GHz)],
            soundbyte=">275 GHz",
        ),
        "WRC-31 AI-2.2": AgendaItem(
            frequency_bands=[slice(275.0 * ureg.GHz, 325.0 * ureg.GHz)],
            soundbyte="WPT",
        ),
        "WRC-31 AI-2.3": AgendaItem(
            frequency_bands=[slice(12.75 * ureg.GHz, 13.25 * ureg.GHz)],
            soundbyte="ESIMs (aero/marine)",
        ),
        "WRC-31 AI-2.4": AgendaItem(
            frequency_bands=[
                slice(3_700 * ureg.MHz, 4_200 * ureg.MHz),
                slice(5_925 * ureg.MHz, 6_425 * ureg.MHz),
            ],
            soundbyte="space-to-space",
        ),
        "WRC-31 AI-2.5": AgendaItem(
            frequency_bands=[
                slice(694 * ureg.MHz, 960 * ureg.MHz),
                slice(890 * ureg.MHz, 942 * ureg.MHz),
                slice(3_400 * ureg.MHz, 3_700 * ureg.MHz),
            ],
            soundbyte="Aeronautical_IMT",
        ),
        "WRC-31 AI-2.6": AgendaItem(
            frequency_bands=[
                slice(102 * ureg.GHz, 109.5 * ureg.GHz),
                slice(151.5 * ureg.GHz, 164 * ureg.GHz),
                slice(167 * ureg.GHz, 174.8 * ureg.GHz),
                slice(209 * ureg.GHz, 226 * ureg.GHz),
                slice(252 * ureg.GHz, 275 * ureg.GHz),
            ],
            soundbyte="IMT",
        ),
        "WRC-31 AI-2.7": AgendaItem(
            frequency_bands=[
                slice(157.1875 * ureg.MHz, 157.3375 * ureg.MHz),
                slice(161.7875 * ureg.MHz, 161.9375 * ureg.MHz),
            ],
            soundbyte="Marine",
        ),
        "WRC-31 AI-2.8": AgendaItem(
            frequency_bands=[
                slice(415 * ureg.kHz, 26.175 * ureg.MHz),
            ],
            soundbyte="Marine",
        ),
        "WRC-31 AI-2.9": AgendaItem(
            frequency_bands=[
                slice(5_030 * ureg.MHz, 5_150 * ureg.MHz),
                slice(5_150 * ureg.MHz, 5_250 * ureg.MHz),
            ],
            soundbyte="RNSS",
        ),
        "WRC-31 AI-2.10": AgendaItem(
            frequency_bands=[
                slice(22.55 * ureg.GHz, 23.15 * ureg.GHz),
            ],
            soundbyte="EESS (Earth-to-Space)",
        ),
        "WRC-31 AI-2.11": AgendaItem(
            frequency_bands=[
                slice(37.5 * ureg.GHz, 40.5 * ureg.GHz),
                slice(40.5 * ureg.GHz, 52.4 * ureg.GHz),
            ],
            soundbyte="EESS (space-to-Earth)",
        ),
        "WRC-31 AI-2.12": AgendaItem(
            frequency_bands=[
                slice(3_000 * ureg.MHz, 3_100 * ureg.MHz),
                slice(3_300 * ureg.MHz, 3_400 * ureg.MHz),
            ],
            soundbyte="EESS (Active)",
        ),
        "WRC-31 AI-2.13": AgendaItem(
            frequency_bands=[
                slice(9_200 * ureg.MHz, 10_400 * ureg.MHz),
            ],
            soundbyte="EESS (Active)",
        ),
        "WRC-31 AI-2.14": AgendaItem(
            frequency_bands=[
                slice(470 * ureg.MHz, 694 * ureg.MHz),
            ],
            soundbyte="Broadcast/Mobile",
        ),
    }
    # Now go through and properly populate the wrc/name info
    for key, item in ai_info.items():
        item.wrc, item.name = key.split(" ")

    if grouped:
        return ai_info
    else:
        return split_all(ai_info)


def split_all(ai_info: dict[AgendaItem]) -> dict[AgendaItemSubBand]:
    """Split all agenda items into their respective subbands"""
    result = {}
    for key, item in ai_info.items():
        subbands = item.split()
        for subband in subbands:
            new_key = key + chr(ord("a") + subband.i_band)
            result[new_key] = subband
    # Now a set of rules that merge ranges for an AI into adjacent (or nearby) groups
    # for ease of plotting.
    merging_rules = {
        "WRC-27 AI-1.6": ["ab", "cd"],
        "WRC-27 AI-1.11": ["ab", "cde", "f"],
    }
    # Now do the actual merging
    for prefix, combinations in merging_rules.items():
        template = ai_info[prefix]
        for combination in combinations:
            combined_bands = [
                result[prefix + character].frequency_band for character in combination
            ]
            enveloping_band = slice(
                min(this_band.start for this_band in combined_bands),
                max(this_band.stop for this_band in combined_bands),
            )
            subband = AgendaItemSubBand(
                name=template.name,
                wrc=template.wrc,
                text=template.text,
                soundbyte=template.soundbyte,
                i_band=-1,
                n_bands=-1,
                frequency_band=enveloping_band,
            )
            result[prefix + combination] = subband
    sorted_keys = natsorted(result.keys())
    return {key: result[key] for key in sorted_keys}


def ai_html_summary(
    agenda_item: str,
    allocation_database: pyfcctab.FCCTables,
    oscar_database: IntervalTree,
):
    """Produce an HTML file that is the agenda item summary"""
    # Get a filename prefix as the agenda item with spaces changed to underscores
    file_prefix = "outputs/" + "_".join(agenda_item.split(" "))
    # Look up this agenda item
    frequency_range = get_ai_info()[agenda_item].frequency_band
    if frequency_range is None:
        return
    if frequency_range.start is None or frequency_range.stop is None:
        return
    bands = allocation_database.all[frequency_range]
    # Make the plot
    config = band_figure.FigureConfiguration.load()
    fig, ax = plt.subplots(layout="constrained")
    band_figure.views_plot(
        frequency_range=frequency_range,
        allocation_database=allocation_database,
        oscar_database=oscar_database,
        figure_configuration=config,
        ax=ax,
    )
    fig.savefig(file_prefix + ".png", dpi=600)
    plt.close()
    # Create an HTML file for this collection
    contents = []
    contents += textwrap.dedent(
        f"""\
        <!DOCTYPE html>
        <html>
        <head>
        <title>{agenda_item}</title>
        """
    ).split("\n")
    contents += pyfcctab.get_pyfcctab_css_lines()
    # Add some style information to make the images zoomable
    contents += textwrap.dedent(
        """\
        <style>
            img {
                max-width: 100%;
                height: auto;
            }
        </style>
        """
    ).split("\n")
    contents += textwrap.dedent(
        f"""\
        </head>
        <body>
        <h1>{agenda_item}</h1>
        <h2>Basic information</h2>
        <p>Frequency range: {frequency_range.start:~H} to {frequency_range.stop:~H}</p>
        <img src="{file_prefix}.png" width=1200 
          alt="Summary of bands under consideration in {agenda_item}">
        <h2>Band under consideration</h2>
        """
    ).split("\n")
    contents += pyfcctab.htmltable(
        bands=bands,
        append_footnotes=True,
        tooltips=True,
        omit_css=True,
    )
    # Now get the adjacent bands:
    science_services = ["Earth Exploration-Satellite*", "Radio Astronomy*"]
    nearby_science_bands = {}
    core_collection_names = ["R1", "R2", "R3", "F", "NF"]
    for collection_name in core_collection_names:
        these_bands = []
        for science_service in science_services:
            these_bands += [
                allocation_database.collections[
                    collection_name
                ].find_closest_matching_band(
                    start_frequency,
                    direction=direction,
                    condition=lambda band: band.has_allocation(science_service),
                )
                for start_frequency, direction in zip(
                    [frequency_range.start, frequency_range.stop],
                    [-1, 1],
                )
            ]
            these_bands = [
                this_band for this_band in these_bands if this_band is not None
            ]
        nearby_science_bands[collection_name] = pyfcctab.BandCollection(these_bands)
    # Merge them back into "all"
    all_bands = pyfcctab.BandCollection()
    for these_bands in nearby_science_bands.values():
        all_bands = all_bands.merge(these_bands)
    contents.append("<h2>Nearest science bands outside this range</h2>")
    contents += pyfcctab.htmltable(
        bands=all_bands,
        append_footnotes=True,
        tooltips=True,
        omit_css=True,
    )
    # Finish off the file
    contents += ["</body></html>"]
    with open(f"{file_prefix}.html", "w", encoding="utf-8") as html_file:
        for line in contents:
            html_file.write(line + "\n")


def get_ai_prefix_suffix(ai):
    """Split AI string into name and a, b, c, etc. suffix"""
    prefix_regex = r"^WRC-(27|31) AI-\d.\d+"
    match = re.match(prefix_regex, ai)
    prefix = str(match.group())
    suffix = ai[len(prefix) :]
    return prefix, suffix


def generate_index_html():
    """Generate the index.html file with links to the AIs"""
    # Generate the opening material
    contents = []
    contents += textwrap.dedent(
        """\
        <!DOCTYPE html>
        <html>
        <head>
        <title>WRC-27 and WRC-31 agenda items</title>
        """
    ).split("\n")
    contents += textwrap.dedent(
        """\
        </head>
        <body>
        <h1>WRC-23 agenda items and WRC-27 draft agenda items</h1>
        """
    ).split("\n")
    # Get the agenda items
    ai_ranges = get_ai_info()
    # Gather them by agenda item
    index_entries = {}
    for ai in ai_ranges.keys():
        prefix, suffix = get_ai_prefix_suffix(ai)
        if prefix not in index_entries:
            index_entries[prefix] = []
        index_entries[prefix].append(suffix)
    # Sort them into (the wrong, for now) order
    agenda_items = natsorted(index_entries.keys())
    # Create HTML for them, group by WRC
    groups = ["WRC-27", "WRC-31"]
    for group in groups:
        contents.append(f"<h2>{group} agenda items</h2>")
        for ai in agenda_items:
            # Skip over the ones that are in the other group
            if not ai.startswith(group):
                continue
            # Identify which are the available suffixes
            suffixes = index_entries[ai]
            # Sort them into some suitable order, put the multi-character suffixes at the end.
            suffixes = sorted(
                suffixes,
                key=lambda suffix: ord(suffix[0]) + ord("z") * (len(suffix) > 1),
            )
            # Build the url links for these files
            ai_with_underscore = "_".join(ai.split(" "))
            links = [
                f'<a href="{ai_with_underscore}{suffix}.html">{suffix}</a>'
                for suffix in suffixes
            ]
            # Add it all to the HTML file.
            contents.append(f"{ai}: " + ", ".join(links) + "<br>")
    # Finish things up.
    contents.append("</body></html>")
    # Save the file
    with open("index.html", "w", encoding="utf-8") as html_file:
        for line in contents:
            html_file.write(line + "\n")


def push_information(
    source_path: str | pathlib.Path = None,
    destination_path: str | pathlib.Path = None,
):
    """Copy all the html and png files to a given path"""
    # Set up the source path
    if source_path is None:
        source_path = "."
    if isinstance(source_path, str):
        source_path = pathlib.Path(source_path)
    # Set up the destination path
    if destination_path is None:
        destination_path = (
            "/Users/livesey/corf/wrc-27-views-google-drive/preliminary-information/"
        )
    if isinstance(destination_path, str):
        destination_path = pathlib.Path(destination_path)
    # Get a list of all the files we want to copy
    files_to_copy = (
        list(source_path.glob("WRC-??_AI-*.html"))
        + list(source_path.glob("WRC-??_AI-*.png"))
        + list(source_path.glob("index.html"))
    )
    # Perform the copy
    for file_to_copy in files_to_copy:
        shutil.copy(file_to_copy, destination_path)
    # Check that there are no extraneous files in the destination directory
    filename_strings = [file.name for file in files_to_copy]
    for file in destination_path.iterdir():
        if file.name not in filename_strings:
            warnings.warn(f"Unexpected file in destination: {file.name}")
