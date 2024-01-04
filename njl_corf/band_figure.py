"""Creates a "standard" figure illustrating band allocations/usage"""

import itertools
import string

from intervaltree import IntervalTree, Interval
import matplotlib
import numpy as np
import pint

from njl_corf import pyfcctab
from njl_corf.pyfcctab.allocations import Allocation



def _capitalize_service_name(service_name: str | None) -> str | None:
    """Capitalize with caveats.

    Thus far, just capitalize the first letter, plus any occruances of "Earth".
    Also, pass None's through as is (in case that's useful)
    """
    if service_name is None:
        return None
    return service_name.capitalize().replace("earth", "Earth")


def gather_relevant_allocation_data(
    frequency_range: slice,
    band_database: pyfcctab.BandCollection,
) -> tuple[IntervalTree, IntervalTree]:
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
    allocations = list(primary_allocations) + list(secondary_allocations)
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

def collate_and_sort_allocations(
    bands: list[pyfcctab.Band],
    allocations: list[str],

)


def views_plot(
    frequency_range: slice,
    allocation_database: pyfcctab.FCCTables,
    oscar_database: IntervalTree,
    ax: matplotlib.pyplot.Axes,
    frequency_margin: float = None,
):
    """Does one views report plot NEEDS BETTER DOCSTRING!"""
    # Increate the range if/as needed
    if frequency_margin is None:
        frequency_margin = 0.20
    formal_bandwidth = frequency_range.stop - frequency_range.start
    examined_frequency_range = slice(
        frequency_range.start - formal_bandwidth * frequency_margin,
        frequency_range.stop + formal_bandwidth * frequency_margin,
    )
    bands, allocations = preprocess_allocations(
        examined_frequency_range, allocation_database.itu
    )
    n_allocations = len(allocations)
    # Loop over the services we found and include them in the plot
    y_labels = {}
    band_bounds = []
    for i_allocation, allocation in enumerate(allocations):
        y_labels[i_allocation] = allocation
        for band in bands:
            band_bounds += [band.bounds[0], band.bounds[1]]
            # Need to think a bit about whether to show it. If we have an exact match
            # then we definately include it.  If it's a wildcard match, then include it
            # only if case it matches to isn't among the list of allocations we're
            # showing
            has_direct_match = band.has_allocation(allocation)
            has_valid_wildcard_match, wildcard_match = band.has_allocation(
                allocation + "*",
                case_sensitive=False,
                return_allocation=True,
            )
            if has_valid_wildcard_match:
                has_valid_wildcard_match = (
                    _capitalize_service_name(wildcard_match.to_str(omit_footnotes=True))
                    not in allocations
                ) and (not has_direct_match)
            if has_valid_wildcard_match and not has_direct_match:
                raise ValueError(f"Found a bad case: {band} for {allocation}")
            # DEBUG
            # debug_key = "Radionavigation"
            # if debug_key in allocation and band.has_allocation(debug_key + "*"):
            #     print(f"-------------------------------- {allocation}")
            #     print(f"{type(allocation)}, '{allocation}'")
            #     test = band.has_allocation(allocation)
            #     if has_direct_match:
            #         print(f"Direct match for {band.compact_str()}")
            #     if has_valid_wildcard_match:
            #         print(f"Wildcard match for {band.compact_str()}")
            #         print(f"Based on {wildcard_match.to_str(omit_footnotes=True)}")
            #     if not has_direct_match and not has_valid_wildcard_match:
            #         try:
            #             print(
            #                 f"No match for: {band.compact_str()}, given {_capitalize_service_name(wildcard_match.to_str(omit_footnotes=True))}"
            #             )
            #         except AttributeError:
            #             print(f"No match for: {band.compact_str()}, given {None}")

            # END DEBUG
            # OK, if we're good then go on to make the plot.
            if has_direct_match:  # or has_valid_wildcard_match:
                x_bounds = (
                    pint.Quantity.from_sequence(band.bounds)
                    .to(frequency_range.start.units)
                    .magnitude
                )
                thickness = 0.2
                y_bounds = np.array(
                    [i_allocation - thickness, i_allocation + thickness]
                )
                xy = [x_bounds[[0, 1, 1, 0]], y_bounds[[0, 0, 1, 1]]]
                color = SERVICE_COLORS[Allocation.parse(allocation).service.name]
                this_patch = matplotlib.patches.Polygon(
                    np.stack(xy, axis=1),
                    color=color,
                    linewidth=0,
                )
                ax.add_patch(this_patch)
                if band.has_allocation(allocation + "*", secondary=True):
                    this_hatch_patch = matplotlib.patches.Polygon(
                        np.stack(xy, axis=1),
                        color="white",
                        fill=None,
                        hatch="/////",
                        linewidth=0,
                    )
                    ax.add_patch(this_hatch_patch)
    # ------- Oscar
    # Now do all the things found in OSCAR
    eess_usage = oscar_database[examined_frequency_range]
    # Draw bars for each band usage
    for i, eess_user in enumerate(eess_usage):
        y_value = i + n_allocations
        y_labels[y_value] = eess_user.data.service
        x_bounds = (
            pint.Quantity.from_sequence(
                [eess_user.data.bounds.start, eess_user.data.bounds.stop]
            )
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
    n_bars = n_allocations + len(eess_usage)
    ax.set_xlim(examined_frequency_range.start, examined_frequency_range.stop)
    ax.set_ylim(-0.5, n_bars - 0.5)
    ax.set_yticks(np.array(list(y_labels.keys())), y_labels.values())
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
