"""Produces an overview graphic for the WRC 27/31 agenda items"""

from typing import Optional

import matplotlib.pyplot as plt
import numpy as np
import pint
from matplotlib.patches import Rectangle
from matplotlib.axes import Axes
from matplotlib.lines import Line2D

from njl_corf import pyiturr5 as rr
from njl_corf import ureg, wrc27_views

from . import wrc27_figure_support as fs


def wrc27_overview_figure(
    allocation_database: Optional[rr.AllocationDatabase] = None,
    frequency_range: Optional[list[pint.Quantity]] = None,
    wrc: str = None,
    ax: Optional[plt.Axes] = None,
    no_show: bool = False,
    include_soundbytes: bool = False,
    first_word_only: bool = False,
    multi_line: bool = False,
    include_srs: bool = False,
    minimum_bandwidth_points: Optional[float] = None,
    color_scheme: Optional[str] = None,
):
    """Figure reviewing WRC agenda items and associated bands

    Parameters
    ----------
    allocation_database : rr.AllocationDatabase, optional
        Allocation tables from RR. If not supplied, these are read in. Having them as an
        optional argument enables faster debugging.
    frequency_range : list[pint.Quantity], optional
        Range of frequencies to cover, expansive default assumed if not given.
    wrc : str, optional
        If supplied, must be either WRC-27 or WRC-31, otherwise, figure shows both.
    ax : plt.Axes, optional
        If supplied do figure in these axes, otherwise generate our own
    no_show : bool, optional
        If set, skip the plt.show() step.
    include_soundbyte : bool, optional
        If set, show the soundbyte as a right-hand x-axis
    first_word_only : bool, optional
        If set, only show the first "word" of the soundbyte
    multi-line : bool, optional
        If set, split the soundbyte into two separate lines
    include_srs : bool, optional
        If set, include SRS allocations as part of RAS.
    minimum_bandwidth_points : float, optional
        If bar is narrower than this, make it wider
    """
    # Read the allocation tables if not supplied
    if allocation_database is None:
        allocation_database = rr.parse_rr_file()
    # Get the agenda items
    ai_info = wrc27_views.get_ai_info(grouped=True)
    # Subset them if/as necessary
    if wrc is not None:
        if wrc not in ["WRC-27", "WRC-31"]:
            raise ValueError(
                f"Ivalid WRC specification ({wrc}), must be WRC-27 or WRC-31"
            )
        ai_info = {key: item for key, item in ai_info.items() if key.startswith(wrc)}
    # Get the color information
    figure_colors = fs.get_wrc_color_scheme(color_scheme)
    # Define the science allocations we're interested in.
    bars = {
        "RAS": fs.BarType(
            condition=lambda band: band.has_allocation("Radio Astronomy*")
            or (
                include_srs
                and (
                    band.has_allocation("Space Research (passive)*")
                    or band.has_allocation("Space Research (active)*")
                )
            ),
            slot=1,
            color=figure_colors["RAS Overview"],
        ),
        "EESS": fs.BarType(
            condition=lambda band: band.has_allocation(
                "Earth Exploration-Satellite (passive)*"
            )
            or band.has_allocation("Earth Exploration-Satellite (active)*"),
            slot=2,
            color=figure_colors["EESS Overview"],
        ),
        "5.340": fs.BarType(
            condition=lambda band: band.has_footnote("5.340"),
            slot=3,
            color=figure_colors["5.340"],
        ),
    }
    # Set font defaults etc.
    fs.set_nas_graphic_style()
    # Now embark upon the figure, set up the figure itself
    if ax is None:
        _, ax = plt.subplots(figsize=[6, len(ai_info) * 0.18], layout="constrained")
    # -------------------------------- x-axis
    if frequency_range is None:
        frequency_range = [1_000_000 * ureg.Hz, 1_000_000_000_000 * ureg.Hz]
    _ = fs.setup_frequency_axis(
        ax=ax,
        frequency_range=frequency_range,
        # decadal_ticks=True,
        put_units_on_labels=True,
        log_axis=True,
    )
    # Put grey lines at major ticks
    for x in list(ax.get_xticks())[1:-1]:
        ax.axvline(x, color="lightgrey", zorder=0, linewidth=0.5)
    # -------------------------------- y-axis
    tick_space_height = 0.2
    y_range = [len(ai_info) - 0.5 + tick_space_height, -0.5 - tick_space_height]
    ax.set_ylim(y_range[0], y_range[1])
    y_labels = [key.split(" ")[1][3:] for key in ai_info.keys()]
    y_tick_locations = np.arange(len(ai_info))
    ax.set_yticks(y_tick_locations, labels=y_labels)
    ax.yaxis.set_minor_locator(plt.NullLocator())
    #
    # -------------------------------- Actual figure
    # OK, loop over the agenda items
    for i_y, (ai, this_ai) in enumerate(ai_info.items()):
        # Draw the horiztonal separator lines, a thicker one to separate the two WRCs
        if i_y > 0:
            if ai == "WRC-31 AI-2.1":
                linewidth = 1.5
            else:
                linewidth = 0.5
            ax.axhline(i_y - 0.5, linewidth=linewidth, color="lightgrey")
        # If there are no specific bands for this AI, then we're done at this point
        if ai_info is None:
            continue
        # Create a buffer to hold the impacted science bands
        bar_buffer = {key: rr.BandCollection() for key in bars}
        for ai_band in this_ai.frequency_bands:
            # Draw the bands addressed by the Agenda Item
            show_band_for_overview(
                ai_band.start,
                ai_band.stop,
                row=i_y,
                slot=0,
                facecolor=figure_colors["AI"],
                ax=ax,
                edgecolor="none",
                minimum_bandwidth_points=minimum_bandwidth_points,
            )
            # Draw all the science bands we found
            for key, bar_info in bars.items():
                relevant_bands = allocation_database.itu.get_bands(
                    ai_band.start,
                    ai_band.stop,
                    condition=bar_info.condition,
                    adjacent=True,
                )
                bar_buffer[key] = bar_buffer[key].union(
                    rr.BandCollection(relevant_bands)
                )
        for key, science_bands in bar_buffer.items():
            bar_info = bars[key]
            for ai_band in science_bands:
                show_band_for_overview(
                    ai_band.bounds[0],
                    ai_band.bounds[1],
                    row=i_y,
                    slot=bar_info.slot,
                    ax=ax,
                    minimum_bandwidth_points=minimum_bandwidth_points,
                    facecolor=bar_info.color,
                )
    # -------------------------------------------------- Soundbyte labels
    #
    # Place this after the rest, because we don't want to mislead the plt.gca()
    # invocation in ensure_minimum_bandwidth_points.
    if include_soundbytes:
        ax2 = ax.twinx()
        ax2.set_ylim(y_range[0], y_range[1])
        y2_labels = []
        for this_ai in ai_info.values():
            y2_labels.append(
                this_ai.format_soundbyte(
                    first_word_only=first_word_only,
                    multi_line=multi_line,
                    latex=True,
                )
            )
        ax2.set_yticks(y_tick_locations, labels=y2_labels)
        ax2.yaxis.set_minor_locator(plt.NullLocator())
        ax2.tick_params(axis="y", which="both", left=False, right=False)
    # Suppress the y ticks.
    ax.tick_params(axis="y", which="both", left=False, right=False)
    # But add a title by way of a y-axis title
    ax.text(-0.05, 1.002, "Agenda Item", transform=ax.transAxes, ha="left", va="bottom")
    # -------------------------------------------------- Legend
    wrc_overview_figure_legend(ax=ax, figure_colors=figure_colors)
    # -------------------------------------------------- Finish
    if not no_show:
        plt.show()


def show_band_for_overview(
    start: pint.Quantity,
    stop: pint.Quantity,
    row: int,
    ax: plt.Axes,
    slot: int = None,
    minimum_bandwidth_points: Optional[float] = None,
    **kwargs,
):
    """Show a band as a rectangle patch"""
    n_slots = 4
    slot_centers = np.linspace(0.5, -0.5, n_slots + 2)[1:-1]
    slot_widths = [0.175] * len(slot_centers)
    y_bottom = row - slot_centers[slot] - 0.5 * slot_widths[slot]
    # For really small bands, make them bigger
    start, stop = fs.ensure_visible_bandwidth(
        start,
        stop,
        minimum_bandwidth_points=minimum_bandwidth_points,
    )
    start = start.to(ureg.Hz)
    stop = stop.to(ureg.Hz)
    # Draw the rectangle
    patch = Rectangle(
        [start, y_bottom],
        width=(stop - start),
        height=slot_widths[slot],
        **kwargs,
    )
    ax.add_patch(patch)


def wrc_overview_figure_legend(ax: Axes, figure_colors: dict):
    """Add a legend for the overview figure"""
    # Create custom Line2D objects for the legend
    entries = {
        "AI": figure_colors["AI"],
        "RAS": figure_colors["RAS Overview"],
        "EESS": figure_colors["EESS Overview"],
        "5.340": figure_colors["5.340"],
    }
    legend_elements = [
        Line2D([0], [0], color=color, linewidth=1.5, label=label)
        for label, color in entries.items()
    ]
    # Add the legend to the Axes
    delta_x = 0.022
    delta_y = 0.036
    legend = ax.legend(
        handles=legend_elements,
        loc="upper left",
        frameon=True,
        fontsize="small",
        bbox_to_anchor=(0.0 + delta_x, 1.0 - delta_y),
        borderpad=0.3,
        labelspacing=0.3,
    )
    # Tweak the legend a bit
    frame = legend.get_frame()
    frame.set_alpha(1.0)
    frame.set_linewidth(0.5)
    frame.set_boxstyle("Square")
