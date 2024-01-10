"""Creates a "standard" figure illustrating band allocations/usage"""

import itertools
import fnmatch
import pathlib
import json
from dataclasses import dataclass
import copy
import re

from intervaltree import IntervalTree
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
import pint

from njl_corf import pyfcctab
from njl_corf.pyfcctab.allocations import Allocation
from njl_corf.pyoscar import OscarEntry
from njl_corf.corf_pint import ureg


def _capitalize_service_name(service_name: str | None) -> str | None:
    """Capitalize with caveats.

    Thus far, just capitalize the first letter, plus any occruances of "Earth".
    Also, pass None's through as is (in case that's useful)
    """
    if service_name is None:
        return None
    return service_name.capitalize().replace("earth", "Earth")


def _simplify_service_name(service_name: str) -> str:
    """Remove parentheticals and excess whitespace"""
    return " ".join(re.sub("\(.*?\)", "", service_name).split()).strip()


@dataclass
class FigureConfiguration:
    """Holds the configuration information for the figure"""

    service_colors: {}
    service_ranks: {}
    allocation_height: float = 1.0
    usage_height: float = 1.0

    @classmethod
    def load(cls, filename=None):
        """Load the configuration from a json file"""
        if filename is None:
            filename = pathlib.Path(__file__).parent / "default-band-figure-style.json"
        with open(filename, "r", encoding="utf-8") as config_file:
            defaults = json.load(config_file)
        return cls(
            service_colors=defaults["service_colors"],
            service_ranks=defaults["service_ranks"],
            allocation_height=defaults["allocation_height"],
            usage_height=defaults["usage_height"],
        )

    def get_service_color(self, service: str) -> str:
        """Get color for the given service

        Tries to simplify the service name if not directly matched.
        """
        service = service.lower()
        try:
            return self.service_colors[service]
        except KeyError:
            return self.service_colors[_simplify_service_name(service)]

    def get_service_rank(self, service: str) -> int:
        """Get rank fo the given service

        Tries to simplify the service name if not directly matched
        """
        service = service.lower()
        try:
            return self.service_ranks[service]
        except KeyError:
            return self.service_ranks[_simplify_service_name(service)]


class FigureRow:
    """Contains information describing a row of the figure"""

    def __init__(self):
        pass


def gather_relevant_allocation_data(
    frequency_range: slice,
    band_database: pyfcctab.BandCollection,
) -> (IntervalTree, list[Allocation]):
    """Gather all the information about allocations for a plot"""
    # Identify all the bands in the frequency range
    bands = band_database[frequency_range]
    # Gather all the primary and secondary allocations in those bands
    primary_allocations = itertools.chain.from_iterable(
        [band.primary_allocations for band in bands]
    )
    secondary_allocations = itertools.chain.from_iterable(
        [band.secondary_allocations for band in bands]
    )
    footnote_mentions = itertools.chain.from_iterable(
        [band.footnote_mentions for band in bands]
    )
    allocations = (
        list(primary_allocations)
        + list(secondary_allocations)
        + list(footnote_mentions)
    )
    # Now identify all the unique services that they embody
    allocations = sorted(
        list(
            set(
                _capitalize_service_name(allocation.to_str(omit_footnotes=True))
                for allocation in allocations
            )
        )
    )
    return bands, allocations


def gather_relevant_oscar_data(
    frequency_range: slice,
    oscar_database: IntervalTree,
) -> dict[list[OscarEntry]]:
    """Get OSCAR entries for a frequency range and collate them by service

    Parameters
    ----------
    frequency_range : slice
        Frequency range under consideration
    oscar_database : IntervalTree
        IntervalTree of OscarDatabase entries.

    Returns
    -------
    dict[list[OscarEntry]]:
        Collection of entries corresponding to each relevant service
    """
    # Identify all the OSCAR entries in the frequency range
    entries = oscar_database[frequency_range]
    # Get the unique names of all the missions (aka services) in those entries
    service_names = list(set(entry.data.service for entry in entries))
    # Now make a dictionary of all those entries
    result = {service_name: [] for service_name in service_names}
    for entry in entries:
        result[entry.data.service].append(entry.data)
    return result


def collate_and_sort_allocations(
    # bands: list[pyfcctab.Band],
    allocations: list[str],
    figure_configuration: FigureConfiguration,
    collation_rules: dict = None,
) -> tuple[dict, dict]:
    """Organize allocation material for inclusion in figures.

    Parameters
    ----------
    bands : list[pyfcctab.Band]
        The bands of interest in the plot (typically output from
        gather_relevant_allocation_data)
    allocations : list[str]
        The unique list of allocations of interest for this plot (again, typically
        output from gather_relevant_allocation_data)
    collation_rules : dict, optional
        Provides mapings of the form <new-row-title>: <squence of existing row titles>
        Note that the sequences can include unix-style widcards. However, a subtlety is
        that the wildcards are matched after the non-wildcard matches are considered.
        This allows the user to have specific allocations in one group and use wild
        cards to collect various "also rans".

    Returns
    -------
    list[FigureRow]
        _description_
    """
    if collation_rules is None:
        collation_rules = {}
    # Loop over all the collation rules and gather all the matches they describe.  We'll
    # capture those directly matched separately from those matched by wildcards.  After
    # that we'll pick and choose between them.  First the variables we'll collect the
    # results in.
    direct_matches = {}
    wildcard_matches = {}
    allocation_matched_flags = {key: False for key in allocations}
    directly_matched_allocations = []
    # Now loop over the user-supplied collection rules
    for new_row_title, included_row_specifiers in collation_rules.items():
        # Make sure the included_row_specfiers is a list of strings
        if isinstance(included_row_specifiers, str):
            included_row_specifiers = [included_row_specifiers]
        # Start list of the direct and wildcard matches they imply
        direct_matches[new_row_title] = []
        wildcard_matches[new_row_title] = []
        # Loop over their entries
        for included_row_specifier in included_row_specifiers:
            # Note any direct matches
            if included_row_specifier in allocations:
                direct_matches[new_row_title].append(included_row_specifier)
                directly_matched_allocations.append(included_row_specifier)
                allocation_matched_flags[included_row_specifier] = True
            # Note any wildcard-based matches
            for allocation in allocations:
                if fnmatch.fnmatchcase(
                    allocation.lower(), included_row_specifier.lower()
                ):
                    wildcard_matches[new_row_title].append(allocation)
                    allocation_matched_flags[allocation] = True
    # Now start building the results, which is a dict where the key is the title of the
    # row, and the contents is a list of all the allocations to be represented in that
    # row.  First do the direct ones.
    interim_result = copy.deepcopy(direct_matches)
    # Now the indirect ones, but not if the're already directly matched, and append onto
    # anything existing, don't overwrite.
    for new_row_title, included_rows in wildcard_matches.items():
        included_rows = list(
            filter(
                lambda row_name: row_name not in directly_matched_allocations,
                included_rows,
            )
        )
        interim_result[new_row_title] += included_rows
    # Finally, add those not claimed by any of the collations
    unclaimed_row_titles = list(
        filter(lambda row_name: not allocation_matched_flags[row_name], allocations)
    )
    # Append the unclaimed entries to the interim result. Make sure each entry is a
    # single-element list, for compatibility with the other collections.
    interim_result |= {row_title: [row_title] for row_title in unclaimed_row_titles}
    # Go through and eliminate any empty rows
    interim_result = {key: item for key, item in interim_result.items() if item}
    # Now we need to go through and get the colors and ranks for each of these
    row_ranks = {}
    row_colors = {}
    for row_title, row_services in interim_result.items():
        row_ranks[row_title] = min(
            figure_configuration.get_service_rank(row_service)
            for row_service in row_services
        )
        row_colors[row_title] = figure_configuration.get_service_color(row_services[0])

    # Now sort the rows into their rank order
    row_order = dict(sorted(row_ranks.items(), key=lambda x: x[1])).keys()
    row_allocations = {row_title: interim_result[row_title] for row_title in row_order}
    # Sort the colors for consistency
    row_colors = {row_title: row_colors[row_title] for row_title in row_order}
    return row_allocations, row_colors


def views_plot(
    frequency_range: slice,
    allocation_database: pyfcctab.FCCTables,
    oscar_database: IntervalTree,
    figure_configuration: FigureConfiguration,
    collation_rules: dict = None,
    ax: matplotlib.pyplot.Axes = None,
    frequency_margin: float | pint.Quantity = None,
    omit_band_borders: bool = False,
    filename: str = None,
):
    """_summary_

    Parameters
    ----------
    frequency_range : slice
        The frequency range to show
    allocation_database : pyfcctab.FCCTables
        The FCCTables (a collection of BandCollections)
    oscar_database : IntervalTree
        The database of EESS missions
    figure_configuration : FigureConfiguration
        Configuration for the figure (colors, ordering, etc.), see the
        FigureConfiguration class.
    collation_rules : dict, optional
        A dict describing how to collate the rows for different allocations.  See
        collate_and_sort_allocations for more information (someday I should make a
        better comment here.)
    ax : matplotlib.pyplot.Axes, optional
        Axes to show the figure in
    frequency_margin : float | pint.Quantity, optional
        How much margin to add either side of the frquency range.  Behavior depends on
        the type/sign of the argument:
            - frequency suppled (e.g., 200 MHz): use this frequency as the margin
            - positive dimensionless number supplied (e.g., 0.2): increase the bandwidth
              by this fraction
            - negative dimensionless number supplied (e.g., -0.05): increase the
              bandwidth by this fraction of the band center frequency
    omit_band_borders : bool, optional
        If set, omit the vertical grey lines dividing bands
    """
    if collation_rules is None:
        collation_rules = {}
    if ax is None:
        ax = plt.gca()
    # Increase the range if/as needed
    if frequency_margin is None:
        frequency_margin = 0.20
    # First try to handle the margin as if it was a fixed frequency
    if isinstance(frequency_margin, pint.Quantity):
        pass
    elif frequency_margin > 0:
        formal_bandwidth = frequency_range.stop - frequency_range.start
        frequency_margin = formal_bandwidth * frequency_margin
    else:
        center_frequency = 0.5 * (frequency_range.start + frequency_range.stop)
        frequency_margin = center_frequency * abs(frequency_margin)
    # Now apply this margin.  Ensure we don't go below zero Hz
    examined_frequency_range = slice(
        max(
            frequency_range.start - frequency_margin,
            0.0 * frequency_range.start.units,
        ),
        frequency_range.stop + frequency_margin,
    )

    # ----------------------------------------------- Allocations
    bands, allocations = gather_relevant_allocation_data(
        examined_frequency_range, allocation_database.itu
    )
    row_allocations, row_colors = collate_and_sort_allocations(
        allocations=allocations,
        collation_rules=collation_rules,
        figure_configuration=figure_configuration,
    )
    # Loop over the services we found and include them in the plot
    y_labels = {}
    band_bounds = []
    for band in bands:
        band_bounds += [band.bounds[0], band.bounds[1]]
    for i_row, row_title in enumerate(row_allocations.keys()):
        y_labels[i_row] = row_title
        # Need to think a bit about whether to show it. If we have an exact match
        # then we definately include it.  If it's a wildcard match, then include it
        # only if case it matches to isn't among the list of allocations we're
        # showing
        for band in bands:
            for allocation in row_allocations[row_title]:
                has_allocation, this_allocation = band.has_allocation(
                    allocation,
                    return_allocation=True,
                    case_sensitive=False,
                )
                if has_allocation:
                    # Draw the band in solid (hatch over it as needed later for
                    # secondary etc.,)
                    x_bounds = (
                        pint.Quantity.from_sequence(band.bounds)
                        .to(frequency_range.start.units)
                        .magnitude
                    )
                    thickness = 0.2
                    y_bounds = np.array([i_row - thickness, i_row + thickness])
                    xy = [x_bounds[[0, 1, 1, 0]], y_bounds[[0, 0, 1, 1]]]
                    this_patch = matplotlib.patches.Polygon(
                        np.stack(xy, axis=1),
                        color=row_colors[row_title],
                        linewidth=0,
                    )
                    ax.add_patch(this_patch)
                    # Now consider non-primary allocation cases
                    hatch = None
                    hatch = ""
                    if this_allocation.secondary:
                        hatch = "/////"
                    elif this_allocation.footnote_mention:
                        hatch = "xxx"
                    if hatch:
                        this_hatch_patch = matplotlib.patches.Polygon(
                            np.stack(xy, axis=1),
                            color="white",
                            fill=None,
                            hatch=hatch,
                            linewidth=0,
                        )
                        ax.add_patch(this_hatch_patch)
    # ----------------------------------------------- Oscar
    # Now do all the things found in OSCAR
    eess_usage = gather_relevant_oscar_data(examined_frequency_range, oscar_database)
    # Draw bars for each band usage
    for i, eess_user in enumerate(eess_usage.keys()):
        y_value = i + len(row_allocations)
        y_labels[y_value] = eess_user
        channels = eess_usage[eess_user]
        for channel in channels:
            x_bounds = (
                pint.Quantity.from_sequence([channel.bounds.start, channel.bounds.stop])
                .to(frequency_range.start.units)
                .magnitude
            )
            if x_bounds[1] > x_bounds[0] + 1e-6:
                ax.plot(
                    x_bounds,
                    [y_value] * 2,
                    color="black",
                    linewidth=2.0,
                )
            else:
                ax.plot(x_bounds[0], y_value, color="black", marker="*")
    # ------- Remainder
    # Now set up the rest of the plot information
    n_bars = len(row_allocations) + len(eess_usage)
    ax.set_xlim(examined_frequency_range.start, examined_frequency_range.stop)
    ax.set_ylim(-0.5, n_bars - 0.5)
    ax.set_yticks(np.array(list(y_labels.keys())), y_labels.values())
    if not omit_band_borders:
        band_bounds = list(set(band_bounds))
        for b in band_bounds:
            ax.axvline(b, color="darkgrey", zorder=-10, linewidth=0.5)
    # ------- 5.340
    # Hatch out all the areas that are 5.340
    for band in bands:
        if band.has_footnote("5.340"):
            x_bounds = (
                pint.Quantity.from_sequence(band.bounds)
                .to(frequency_range.start.units)
                .magnitude
            )
            y_bounds = np.array(ax.get_ylim())
            xy = [x_bounds[[0, 1, 1, 0]], y_bounds[[0, 0, 1, 1]]]
            this_patch = matplotlib.patches.Polygon(
                np.stack(xy, axis=1),
                linewidth=0,
                facecolor="lightgrey",
                zorder=-10,
            )
            ax.add_patch(this_patch)
    # Final tidy ups
    ax.invert_yaxis()
    ax.tick_params(axis="y", which="minor", left=False, right=False)
    if filename:
        plt.gcf().savefig(filename)
        plt.close()
