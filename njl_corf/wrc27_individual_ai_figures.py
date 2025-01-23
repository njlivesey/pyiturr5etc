"""Produces an overview graphic for the WRC 27/31 agenda items"""

from dataclasses import dataclass
from typing import Optional, Callable
import functools

import matplotlib.pyplot as plt
import numpy as np
import pint
from matplotlib.patches import Rectangle
from matplotlib.transforms import blended_transform_factory
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from numpy.typing import ArrayLike

from njl_corf import pyiturr5 as rr, ureg, wrc27_views

from . import wrc27_figure_support as fs


# --------------------------------------------------------------------------------------
#
# The first part of the module is the routine to produce a figure for a specific agenda
# item or multiple specific items.  Support routines for this follow below.


def wrc27_ai_figure(
    ai: str | list[str],
    allocation_database: Optional[rr.AllocationDatabase] = None,
    frequency_range_shown_pre_daylight: Optional[list[pint.Quantity]] = None,
    ax: Optional[plt.Axes] = None,
    no_show: Optional[bool] = False,
    log_axis: Optional[bool] = False,
    include_srs: Optional[bool] = False,
    minimum_bandwidth_points: Optional[float] = None,
    put_units_on_labels: Optional[bool] = False,
    include_all_encompassed_allocations: Optional[bool] = True,
    xticks: Optional[pint.Quantity] = None,
    xminor: Optional[pint.Quantity] = None,
    arrows_included: Optional[ArrayLike] = None,
    custom_annotations: Optional[Callable] = None,
    color_scheme: Optional[str] = None,
    include_5340_legend: Optional[bool] = False,
    include_quilt_y_labels: Optional[bool] = False,
):
    """Figure reviewing WRC agenda items and associated bands

    Parameters
    ----------
    ai : str | list[str], optional
        AI identifier or list thereof (e.g. 1.6)
    allocation_database : rr.AllocationDatabase, optional
        Allocation tables from rr.  If not supplied, these are read in. Having them as
        an optional argument enables faster debugging.
    frequency_range : list[pint.Quantity], optional
        Range of frequencies to cover, expansive default assumed if not given.
    ax : plt.Axes, optional
        If supplied do figure in these axes, otherwise generate our own
    no_show : bool, optional
        If set, skip the plt.show() step.
    log_xaxis : bool, optional
        Force log or linear x-axis
    include_srs : bool, optional
        If set, include the SRS entries.
    minimum_bandwidth_points : float, optional
        If bar is narrower than this, make it wider
    put_units_on_labels : float, optional
        If set, put units on frequency labels
    include_all_encompassed_allocations : bool, optional
        If set, show all the sciencea allocations within the frequency range encompassed
        by the figure, otherwise only show the science/5.340 bands directly adjacent to
        the bands under consideration in the AI.
    xticks : pint.Quantity
        Optional manually supplied major tick locations
    xminor : pint.Quantity
        Optional manually supplied minor tick locations
    arrows_included : pint.Quanity
        If provided, gives band-by-band flags indicating whether show up/down/sideways
        arrows for Earth-to-space, space-to-Earth, space-to-space allocations should be
        shown.
    custom_annotations : Callable
        If supplied, is called with the figure and axes to provide additional
        information.  Other information needed is up to the calling routine to provide
        (e.g., via a closure.)
    color_scheme : Optional[str]
        Name of color scheme to use
    """
    # Read the allocation tables if not supplied
    if allocation_database is None:
        allocation_database = rr.parse_rr_file()
    # Get the agenda items
    ai_info = wrc27_views.get_ai_info(grouped=True)
    # Subset them if/as necessary
    if isinstance(ai, str):
        ai = [ai]
    ai_info = {ai_key: ai_info[ai_key] for ai_key in ai}
    # Get the colormap we like
    figure_colors = fs.get_wrc_color_scheme(color_scheme)
    # Define the science allocations we're interested in.
    science_rows = {
        "RAS": fs.BarType(
            allocation="Radio Astronomy*",
            color=figure_colors["RAS"],
        ),
    }
    # Define the bars we're going to show
    if include_srs:
        science_rows = science_rows | {
            "SRS (Passive)": fs.BarType(
                allocation="Space Research (Passive)*",
                color=figure_colors["SRS (Passive)"],
            ),
            "SRS (Active)": fs.BarType(
                allocation="Space Research (Active)*",
                color=figure_colors["SRS (Active)"],
            ),
        }
    science_rows = science_rows | {
        "EESS (Passive)": fs.BarType(
            allocation="Earth Exploration-Satellite (Passive)*",
            color=figure_colors["EESS (Passive)"],
        ),
        "EESS (Active)": fs.BarType(
            allocation="Earth Exploration-Satellite (Active)*",
            color=figure_colors["EESS (Active)"],
        ),
        "RR 5.340": fs.BarType(
            footnote="5.340",
            slot=3,
            color=[figure_colors["5.340"]],
        ),
    }
    # Identify the bars for each agenda item
    bar_buffers = {row_key: rr.BandCollection() for row_key in science_rows}
    for ai_key, this_ai_info in ai_info.items():
        frequency_bands = this_ai_info.frequency_bands
        if this_ai_info.secondary_bands is not None:
            frequency_bands += this_ai_info.secondary_bands
        for ai_band in frequency_bands:
            for row_key, row_info in science_rows.items():
                relevant_bands = allocation_database.itu.get_bands(
                    ai_band.start,
                    ai_band.stop,
                    condition=row_info.construct_condition(),
                    recursively_adjacent=True,
                )
                bar_buffers[row_key] = bar_buffers[row_key].union(
                    rr.BandCollection(relevant_bands)
                )
    # Set font defaults etc.
    fs.set_nas_graphic_style()
    # Now embark upon the figure, set up the figure itself, start with a default width
    if ax is None:
        ax_supplied = False
        fig, ax = plt.subplots(layout="constrained")
    else:
        ax_supplied = True
        fig = ax.figure

    # -------------------------------- x-axis
    if frequency_range_shown_pre_daylight is None:
        # Identify the frequency range
        f_mins_ai = []
        f_maxs_ai = []
        f_mins_science = []
        f_maxs_science = []
        # Gather mins/maxes for the bands in each AI
        for ai_key, this_ai_info in ai_info.items():
            f_mins_ai += [band.start for band in this_ai_info.frequency_bands]
            f_maxs_ai += [band.stop for band in this_ai_info.frequency_bands]
        # Now do the same for any relevant science bands
        for science_bands in bar_buffers.values():
            f_mins_science += [band.bounds[0] for band in science_bands]
            f_maxs_science += [band.bounds[1] for band in science_bands]
        # Get the full range for both the AI bands and the science bands
        if len(f_mins_ai) != 0:
            frequency_range_shown_pre_daylight = [min(f_mins_ai), max(f_maxs_ai)]
        else:
            frequency_range_shown_pre_daylight = [1.0 * ureg.MHz, 1.0 * ureg.GHz]
        if len(f_mins_science) != 0:
            frequency_range_full = [
                min(f_mins_science + f_mins_ai),
                max(f_maxs_science + f_maxs_ai),
            ]
        else:
            frequency_range_full = frequency_range_shown_pre_daylight
        add_daylight = True
    else:
        add_daylight = False
        frequency_range_full = frequency_range_shown_pre_daylight
    # Setup the frequency axis, labels, etc.
    log_axis = fs.setup_frequency_axis(
        ax=ax,
        frequency_range=frequency_range_shown_pre_daylight,
        add_daylight=add_daylight,
        log_axis=log_axis,
        put_units_on_labels=put_units_on_labels,
        xticks=xticks,
        xminor=xminor,
    )

    # OK, despite having gone to the lengths of carefully identifying the science (and
    # 5.340) bands that overlap or are directly adjacent to the bands under
    # consideration, we're going to kind of throw all that away, and just get all the
    # bands of interest in the range, but only if we identified a case for their
    # inclusion (by virtue of being adjacent or overlapping) before.
    new_bar_buffers = {row_key: rr.BandCollection() for row_key in science_rows}
    for row_key, row_info in science_rows.items():
        if bar_buffers[row_key] or include_all_encompassed_allocations:
            new_bar_buffers[row_key] = allocation_database.itu.get_bands(
                frequency_range_full[0],
                frequency_range_full[1],
                condition=row_info.construct_condition(),
                recursively_adjacent=True,
            )
    bar_buffers = new_bar_buffers
    # -------------------------------- Actual figure
    # OK, loop over the agenda items
    y_labels = []
    for ai_key, this_ai_info in ai_info.items():
        # If there are no specific bands for this AI, then we're done at this point
        if ai_info is None:
            continue
        # Show either the frequency bands, or the detailed bands (if present) as solid boxes
        if this_ai_info.detailed_bands is None:
            solid_frequency_bands = this_ai_info.frequency_bands
            facecolor = figure_colors["AI"]
        else:
            solid_frequency_bands = this_ai_info.detailed_bands
            facecolor = figure_colors["AI-extra"]
        for i_band, ai_band in enumerate(solid_frequency_bands):
            direction = ai_band.step
            if arrows_included is not None:
                if not arrows_included[i_band]:
                    direction = None
            # Draw this particular band
            show_band_for_individual(
                ai_band.start,
                ai_band.stop,
                row=len(y_labels),
                facecolor=facecolor,
                ax=ax,
                minimum_bandwidth_points=minimum_bandwidth_points,
                edgecolor="none",
                direction=direction,
            )
        # If detailed bands are present, show the frequency bands as a hollow box
        if this_ai_info.detailed_bands is not None:
            for ai_band in this_ai_info.frequency_bands:
                # Draw this particular band
                show_band_for_individual(
                    ai_band.start,
                    ai_band.stop,
                    row=len(y_labels),
                    facecolor="none",
                    edgecolor=figure_colors["AI"],
                    ax=ax,
                    minimum_bandwidth_points=minimum_bandwidth_points,
                    direction=ai_band.step,
                )
        # Now do any secondary bands
        if this_ai_info.secondary_bands is not None:
            for ai_band in this_ai_info.secondary_bands:
                # Draw this particular band
                show_band_for_individual(
                    ai_band.start,
                    ai_band.stop,
                    row=len(y_labels),
                    facecolor=figure_colors["AI-extra"],
                    ax=ax,
                    minimum_bandwidth_points=minimum_bandwidth_points,
                    edgecolor="none",
                    direction=ai_band.step,
                )

        y_labels.append(r"\textbf{" + ai_key + r"}")
    # Now loop over the science bands
    for row_key, science_bands in bar_buffers.items():
        if len(science_bands) == 0:
            continue
        row_info = science_rows[row_key]
        for science_band in science_bands:
            # Work out what the status of this band is
            status = 3
            for allocation in science_band.allocations:
                if row_info.allocation is None:
                    status = 0
                if allocation.matches(row_info.allocation):
                    if allocation.primary:
                        status = min(status, 0)
                    if allocation.secondary:
                        status = min(status, 1)
                    if allocation.footnote_mention:
                        status = min(status, 2)
            show_band_for_individual(
                science_band.bounds[0],
                science_band.bounds[1],
                row=len(y_labels),
                ax=ax,
                minimum_bandwidth_points=minimum_bandwidth_points,
                facecolor=row_info.color[status],
            )
        y_labels.append(row_key)
    # -------------------------------- y-axis
    # Note the y-axis is upside down to facilitate indexing etc.
    tick_space_height = 0.4
    y_range = [len(y_labels) - 0.5 + tick_space_height, -0.5 - tick_space_height]
    ax.set_ylim(y_range[0], y_range[1])
    y_tick_locations = np.arange(len(y_labels))
    ax.set_yticks(y_tick_locations, labels=y_labels)
    ax.yaxis.set_minor_locator(plt.NullLocator())
    # Suppress the y ticks.
    ax.tick_params(axis="y", which="both", left=False, right=False)
    # --------------------------------- Legend
    wrc_ai_figure_legend(
        fig=fig,
        ax=ax,
        n_rows=len(y_labels),
        figure_colors=figure_colors,
        include_quilt_y_labels=include_quilt_y_labels,
        include_5340_legend=include_5340_legend,
    )
    # --------------------------------- Sizing
    if not ax_supplied:
        # Now work out the size.
        row_size_inches = 0.15
        # Take a stab at the figure size
        figure_width_inches = 10.6 / 2.54
        bar_area_height_inches = (
            len(y_labels) + 2 * tick_space_height
        ) * row_size_inches
        notional_extra_height_inches = 0.25595 + 0.18 * (not put_units_on_labels)
        initial_height = bar_area_height_inches + notional_extra_height_inches
        fig.set_size_inches(
            figure_width_inches, bar_area_height_inches + notional_extra_height_inches
        )
        # Do a first pass to get the size
        fig.canvas.draw()
        # Work out the actual size of the axes in inches, the remainder is the space taken
        # up by the extra stuff
        actual_bar_area_height_inches = ax.get_position().height * initial_height
        print(f"{bar_area_height_inches=}, {actual_bar_area_height_inches=}")
        actual_extra_height_inches = initial_height - actual_bar_area_height_inches
        print(
            f"{actual_extra_height_inches=}, "
            f"correction={actual_extra_height_inches-notional_extra_height_inches}"
        )
        # Redraw at corrected height
        final_height_inches = bar_area_height_inches + actual_extra_height_inches
        fig.set_size_inches(figure_width_inches, final_height_inches)
        fig.canvas.draw()
    # --------------------------------- Any custom annotation
    if custom_annotations:
        custom_annotations(ax=ax)
    # --------------------------------- Done
    if not no_show:
        plt.show()


def show_band_for_individual(
    start: pint.Quantity,
    stop: pint.Quantity,
    row: int,
    ax: plt.Axes,
    minimum_bandwidth_points: Optional[float] = None,
    direction: Optional[float] = None,
    **kwargs,
):
    """Show a band as a rectangle patch"""
    vertical_width = 0.8
    y_bottom = row - 0.5 * vertical_width
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
        height=vertical_width,
        **kwargs,
    )
    ax.add_patch(patch)
    if direction is not None:
        # Get a sense of how big this bar will be, show the direction arrow within or
        # beside the bar, accordingly
        bandwidth_points = fs.get_bandwidth_points(start, stop)
        if bandwidth_points > 6.0:
            x_anchor = 0.5 * (start + stop)
            color = "white"
        else:
            x_anchor = stop
            color = "black"
            x_anchor += fs.shift_x_by_points(x_anchor, 3.0 + (5.0 * (direction == 1j)))
        y_center = row + 0.03 * vertical_width
        # Now work out what symbol to show
        if direction == -1:
            symbol = r"{\boldmath$\downarrow$}"
        elif direction == 1:
            symbol = r"{\boldmath$\uparrow$}"
        elif direction == 1j:
            symbol = r"{\boldmath$\leftrightarrow$}"
        elif direction == 0:
            symbol = r"{\boldmath$\updownarrow$}"
        else:
            raise ValueError("Do not know what symbol to use")
        ax.annotate(
            symbol,
            (x_anchor, y_center),
            color=color,
            ha="center",
            va="center",
        )
        # Now, if we put the annotation in the center, put some thin white lines at the
        # edges so that distinct bands are separated.
        if color == "white":
            for x in [start, stop]:
                ax.plot(
                    pint.Quantity.from_list([x, x]),
                    [y_bottom, y_bottom + vertical_width],
                    color="white",
                    linewidth=0.5,
                )


def rr5_340_49_ghz_annotation(
    ax: Axes,
    side: str,
):
    """A specific annotation for one of the 5.340 bands in AI-1.1"""
    # We want to annotate the bottom row (5.340), work out where that is and move up a
    # little.
    y, _ = ax.get_ylim()
    y = y - 0.85
    if side == "left":
        x = 48.94 * ureg.GHz
        ha = "right"
        margin_sign = -1
    elif side == "right":
        x = 49.04 * ureg.GHz
        ha = "left"
        margin_sign = 1
    else:
        raise ValueError(f"Argument 'side' must be 'left', or 'right', not '{side}")
    ax.annotate(
        "No airborne\nemissions",
        xy=(x, y),
        xycoords="data",
        xytext=(3 * margin_sign, 0),
        textcoords="offset points",
        ha=ha,
        va="center",
        fontsize="small",
        linespacing=0.9,
    )


def wrc_ai_figure_legend(
    fig: Figure,
    ax: Axes,
    n_rows: int,
    figure_colors: dict,
    include_quilt_y_labels: bool,
    include_5340_legend: bool,
):
    """Generates legend for the individual AI figure"""
    # Combine figure transform (for x-axis) and data transform (for y-axis)
    legend_transform = blended_transform_factory(fig.transFigure, ax.transData)
    # Rectangle parameters
    if include_quilt_y_labels:
        x_rail_left = 0.07
    else:
        x_rail_left = 0.00
    box_pitch_x = 0.05
    box_pitch_y = 1.0
    box_width = box_pitch_x * 0.9
    box_height = box_pitch_y * 0.8
    box_x = np.arange(4) * box_pitch_x + x_rail_left
    box_y = np.arange(5) * box_pitch_y + n_rows + 1.2
    quilt_colors = [figure_colors["RAS"], figure_colors["EESS (Passive)"]]
    for i_service in range(2):
        for i_type in range(3):
            rect = Rectangle(
                (box_x[i_type], box_y[i_service]),
                width=box_width,
                height=box_height,
                transform=legend_transform,
                facecolor=quilt_colors[i_service][i_type],
                edgecolor="none",
                clip_on=False,
            )
            fig.patches.append(rect)
    # Now some labels
    labels = ["Pri.", "Sec.", "Fn."]
    for i_label, label in enumerate(labels):
        fig.text(
            box_x[i_label] + (0.5 * box_pitch_x) * 0.9,
            box_y[2],
            label,
            ha="center",
            va="top",
            transform=legend_transform,
            fontsize="small",
        )
    if include_quilt_y_labels:
        labels = ["RAS", "EESS"]
        y_legend_nudge = 0.005
        for i_label, label in enumerate(labels):
            fig.text(
                x_rail_left - y_legend_nudge,
                box_y[i_label] + 0.5,
                label,
                ha="right",
                va="center",
                transform=legend_transform,
                fontsize="small",
            )
    # Now the 5.340 legend
    if include_5340_legend:
        x_rail_right = 0.99
        y_5350_daylight = 0.5
        rect = Rectangle(
            # (x_rail_right - box_width, box_y[1] + y_5350_daylight),
            (box_x[0], box_y[3]),
            width=box_width,
            height=box_height,
            transform=legend_transform,
            facecolor=figure_colors["5.340"],
            edgecolor="none",
            clip_on=False,
        )
        fig.patches.append(rect)
        fig.text(
            x_rail_right - box_width - y_legend_nudge,
            box_y[1] + 0.5 + y_5350_daylight,
            "5.340",
            ha="right",
            va="center",
            transform=legend_transform,
            fontsize="small",
        )


# --------------------------------------------------------------------------------------
#
# The next part of the module does the work of generating multiple such figures, one for
# each agenda item or agenda item grouping.


@dataclass
class AIPlotConfiguration:
    """Defines the configuration of a specific Agenda Item plot"""

    ai: str | list[str]
    log_axis: Optional[bool] = None
    put_units_on_labels: Optional[bool] = False
    frequency_range: Optional[list[pint.Quantity]] = None
    include_all_encompassed_allocations: Optional[bool] = True
    xticks: Optional[pint.Quantity] = None
    xminor: Optional[pint.Quantity] = None
    arrows_included: Optional[ArrayLike] = None
    custom_annotations: Optional[Callable] = None


def all_individual_figures(
    allocation_database: Optional[rr.AllocationDatabase] = None,
    only: Optional[list[str]] = None,
    skip_pdf: Optional[bool] = False,
    skip_png: Optional[bool] = False,
    **kwargs,
):
    """Generate all the figures for the agenda items"""
    # Setup a placeholder for the configurations
    plot_configurations: dict[AIPlotConfiguration] = {}
    # Make a bunch of plots for the WRC-27 items
    # fmt: on
    plot_configurations["WRC-27 AI-1.1"] = AIPlotConfiguration(
        "WRC-27 AI-1.1",
        custom_annotations=functools.partial(rr5_340_49_ghz_annotation, side="left"),
    )
    plot_configurations["WRC-27 AI-1.2"] = AIPlotConfiguration(
        "WRC-27 AI-1.2", frequency_range=[13.20 * ureg.GHz, 14.05 * ureg.GHz]
    )
    plot_configurations["WRC-27 AI-1.3"] = AIPlotConfiguration(
        "WRC-27 AI-1.3", frequency_range=[50.0 * ureg.GHz, 54.4 * ureg.GHz]
    )
    plot_configurations["WRC-27 AI-1.4"] = AIPlotConfiguration(
        "WRC-27 AI-1.4", frequency_range=[17.1 * ureg.GHz, 17.9 * ureg.GHz]
    )
    plot_configurations["WRC-27 AI-1.5"] = AIPlotConfiguration("WRC-27 AI-1.5")
    plot_configurations["WRC-27 AI-1.6"] = AIPlotConfiguration(
        "WRC-27 AI-1.6",
        custom_annotations=functools.partial(rr5_340_49_ghz_annotation, side="left"),
    )
    plot_configurations["WRC-27 AI-1.7"] = AIPlotConfiguration(
        "WRC-27 AI-1.7",
        # put_units_on_labels=True,
        # log_axis=True,
        # xticks=[5 * ureg.GHz, 10 * ureg.GHz, 15 * ureg.GHz, 20 * ureg.GHz],
    )
    plot_configurations["WRC-27 AI-1.8"] = AIPlotConfiguration(
        "WRC-27 AI-1.8",
        # log_axis=True,
        # xticks=[200 * ureg.GHz, 300 * ureg.GHz, 500 * ureg.GHz, 700 * ureg.GHz],
        # put_units_on_labels=True,
    )
    plot_configurations["WRC-27 AI-1.9"] = AIPlotConfiguration(
        "WRC-27 AI-1.9",
        log_axis=False,
        frequency_range=[2 * ureg.MHz, 18 * ureg.MHz],
        # xticks=[3 * ureg.MHz, 6 * ureg.MHz, 10 * ureg.MHz, 20 * ureg.MHz],
    )
    plot_configurations["WRC-27 AI-1.10"] = AIPlotConfiguration(
        "WRC-27 AI-1.10",
        frequency_range=[70.0 * ureg.GHz, 90 * ureg.GHz],
        xticks=np.linspace(70 * ureg.GHz, 90 * ureg.GHz, 11),
    )
    plot_configurations["WRC-27 AI-1.11"] = AIPlotConfiguration(
        "WRC-27 AI-1.11", arrows_included=[False, True, False, False, True, True]
    )
    plot_configurations["WRC-27 AI-1.12"] = AIPlotConfiguration("WRC-27 AI-1.12")
    plot_configurations["WRC-27 AI-1.13"] = AIPlotConfiguration(
        "WRC-27 AI-1.13",
        # log_axis=True,
    )
    plot_configurations["WRC-27 AI-1.14"] = AIPlotConfiguration("WRC-27 AI-1.14")
    plot_configurations["WRC-27 AI-1.15"] = AIPlotConfiguration(
        "WRC-27 AI-1.15",
        put_units_on_labels=True,
        log_axis=True,
        xticks=[
            0.3 * ureg.GHz,
            1 * ureg.GHz,
            3 * ureg.GHz,
            10 * ureg.GHz,
            30 * ureg.GHz,
        ],
        xminor=np.array([0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 2, 4, 5, 6, 7, 8, 9, 20])
        * ureg.GHz,
    )
    plot_configurations["WRC-27 AI-1.16"] = AIPlotConfiguration(
        "WRC-27 AI-1.16",
        frequency_range=[5 * ureg.GHz, 140 * ureg.GHz],
        log_axis=True,
        xticks=[
            5 * ureg.GHz,
            10 * ureg.GHz,
            30 * ureg.GHz,
            60 * ureg.GHz,
            100 * ureg.GHz,
            160 * ureg.GHz,
        ],
        xminor=np.array([20, 40, 50, 70, 80, 90, 110, 120, 130, 140, 150]) * ureg.GHz,
    )
    plot_configurations["WRC-27 AI-1.17"] = AIPlotConfiguration(
        "WRC-27 AI-1.17",
        put_units_on_labels=True,
        log_axis=True,
        xticks=[30 * ureg.MHz, 100 * ureg.MHz, 300 * ureg.MHz, 600 * ureg.MHz],
    )
    plot_configurations["WRC-27 AI-1.18"] = AIPlotConfiguration("WRC-27 AI-1.18")
    plot_configurations["WRC-27 AI-1.19"] = AIPlotConfiguration("WRC-27 AI-1.19")
    # Now the simple WRC-31 ones
    plot_configurations["WRC-31 AI-2.2"] = AIPlotConfiguration("WRC-31 AI-2.2")
    plot_configurations["WRC-31 AI-2.3"] = AIPlotConfiguration("WRC-31 AI-2.3")
    plot_configurations["WRC-31 AI-2.4"] = AIPlotConfiguration("WRC-31 AI-2.4")
    plot_configurations["WRC-31 AI-2.5"] = AIPlotConfiguration("WRC-31 AI-2.5")
    plot_configurations["WRC-31 AI-2.7"] = AIPlotConfiguration("WRC-31 AI-2.7")
    plot_configurations["WRC-31 AI-2.8"] = AIPlotConfiguration("WRC-31 AI-2.8")
    plot_configurations["WRC-31 AI-2.9"] = AIPlotConfiguration(
        "WRC-31 AI-2.9",
        frequency_range=[4.80 * ureg.GHz, 5.60 * ureg.GHz],
    )
    plot_configurations["WRC-31 AI-2.14"] = AIPlotConfiguration("WRC-31 AI-2.14")
    # fmt: on
    # Now do those that are in combination
    plot_configurations["WRC-31 AIs-2.1-2.6"] = AIPlotConfiguration(
        ai=[
            "WRC-31 AI-2.1",
            "WRC-31 AI-2.6",
        ]
    )
    plot_configurations["WRC-31 AIs-2.10-2.11"] = AIPlotConfiguration(
        ai=[
            "WRC-31 AI-2.10",
            "WRC-31 AI-2.11",
        ],
        custom_annotations=functools.partial(rr5_340_49_ghz_annotation, side="left"),
    )
    plot_configurations["WRC-31 AIs-2.12-2.13"] = AIPlotConfiguration(
        ai=[
            "WRC-31 AI-2.12",
            "WRC-31 AI-2.13",
        ]
    )
    # Now go through and do them all
    for key, item in plot_configurations.items():
        if only:
            if key not in only:
                continue
        print(key)
        wrc27_ai_figure(
            allocation_database=allocation_database,
            ai=item.ai,
            log_axis=item.log_axis,
            frequency_range_shown_pre_daylight=item.frequency_range,
            include_all_encompassed_allocations=item.include_all_encompassed_allocations,
            put_units_on_labels=item.put_units_on_labels,
            no_show=True,
            xticks=item.xticks,
            xminor=item.xminor,
            minimum_bandwidth_points=1.0,
            arrows_included=item.arrows_included,
            custom_annotations=item.custom_annotations,
            **kwargs,
        )
        if not skip_pdf:
            plt.savefig(
                f"specific-ai-plots/SpecificAI-{key}.pdf",
                bbox_inches="tight",
                pad_inches=2.0 / 72,
            )
        if not skip_png:
            plt.savefig(
                f"specific-ai-plots/SpecificAI-{key}.png",
                dpi=600,
                bbox_inches="tight",
                pad_inches=2.0 / 72,
            )
        if only:
            plt.show()
        plt.close()
