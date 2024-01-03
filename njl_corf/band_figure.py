"""Creates a "standard" figure illustrating band allocations/usage"""

import itertools

import intervaltree
import matplotlib
import numpy as np
import pint

from njl_corf import pyfcctab


def views_plot(
    frequency_range: slice,
    allocation_database: pyfcctab.FCCTables,
    oscar_database: intervaltree.IntervalTree,
    ax: matplotlib.pyplot.Axes,
    frequency_margin: float = None,
):
    """Does one views report plot"""
    # Increate the range if/as needed
    if frequency_margin is None:
        frequency_margin = 0.20
    formal_bandwidth = frequency_range.stop - frequency_range.start
    examined_frequency_range = slice(
        frequency_range.start - formal_bandwidth * frequency_margin,
        frequency_range.stop + formal_bandwidth * frequency_margin,
    )
    # ------ Allocations
    bands = allocation_database.itu[examined_frequency_range]
    # Work out how many services are in use
    primary_allocations = itertools.chain.from_iterable(
        [band.primary_allocations for band in bands]
    )
    secondary_allocations = itertools.chain.from_iterable(
        [band.secondary_allocations for band in bands]
    )
    allocations = list(primary_allocations) + list(secondary_allocations)
    services = sorted(list(set(allocation.service.name for allocation in allocations)))
    n_services = len(services)
    # Loop over the services we found and include them in the plot
    y_labels = {}
    colors = matplotlib.colormaps["tab10"].colors
    band_bounds = []
    for i_service, service in enumerate(services):
        y_labels[i_service] = service
        for band in bands:
            band_bounds += [band.bounds[0], band.bounds[1]]
            if band.has_allocation(service + "*"):
                x_bounds = (
                    pint.Quantity.from_sequence(band.bounds)
                    .to(frequency_range.start.units)
                    .magnitude
                )
                thickness = 0.2
                y_bounds = np.array([i_service - thickness, i_service + thickness])
                xy = [x_bounds[[0, 1, 1, 0]], y_bounds[[0, 0, 1, 1]]]
                this_patch = matplotlib.patches.Polygon(
                    np.stack(xy, axis=1),
                    color=colors[i_service % len(colors)],
                    linewidth=0,
                )
                ax.add_patch(this_patch)
                if band.has_allocation(service + "*", secondary=True):
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
        y_value = i + n_services
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
    n_bars = n_services + len(eess_usage)
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
