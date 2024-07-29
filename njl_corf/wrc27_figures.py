"""Produces an overview graphic for the WRC 27/31 agenda items"""

from dataclasses import dataclass
from typing import Optional, Callable

import matplotlib
import matplotlib.font_manager
import matplotlib.pyplot as plt
import numpy as np
import pint
from matplotlib.patches import Rectangle
from matplotlib.ticker import FuncFormatter, MaxNLocator

from njl_corf import pyfcctab, ureg, wrc27_views

from fontTools.ttLib import TTFont, TTLibError


def set_nas_graphic_style():
    """Choose fonts etc. to match NAS style"""
    # Set plot defaults
    matplotlib.rcParams["text.usetex"] = True
    matplotlib.rcParams["font.family"] = "serif"
    matplotlib.rcParams["font.serif"] = ["Palatino"]
    matplotlib.rcParams["font.size"] = 9
    matplotlib.rcParams["pdf.fonttype"] = 42
    matplotlib.rcParams["ps.fonttype"] = 42


# pylint: disable-next=unused-argument
def major_frequency_formatter(x, pos):
    """A nice tick formatter for frequency"""
    if x < 1e3:
        return f"{x:.3g} Hz"
    elif x < 1e6:
        return f"{x / 1e3:.3g} kHz"
    elif x < 1e9:
        return f"{x / 1e6:.3g} MHz"
    elif x < 1e12:
        return f"{x / 1e9:.3g} GHz"
    else:
        return f"{x / 1e12:.3g} THz"


# pylint: disable-next=unused-argument
def minor_frequency_formatter(x, pos):
    """A formatter that returns an empty string each time"""
    return ""


def setup_frequency_axis(
    ax: plt.Axes,
    frequency_range: list[pint.Quantity],
    decadal_ticks: Optional[bool] = False,
    add_daylight: Optional[bool] = False,
    log_axis: Optional[bool] = None,
    daylight_factor: Optional[float] = None,
):
    """Configure the frequency axis

    Parameters
    ----------
    ax : plt.Axes
        The axes under consideration
    frequency_range : list[pint.Quantity]
        The frequency range to cover
    decadal_ticks : bool, optional
        If set, force major ticks to be on the decades of frequency
    add_daylight : bool, optional
        If set, add some daylight either side of the frequency range
    log_axis : bool, optional
        Chose log vs. linear axis
    daylight_factor : float, optional
        Amount of daylight to add
    """
    # Work out whether we want to have a logarithmic axis or not.
    orders = frequency_range[1] / frequency_range[0]
    if log_axis is None:
        log_axis = orders > 5.0
    # Make the frequency range a little larger
    if add_daylight:
        if daylight_factor is None:
            daylight_factor = 0.1
        if log_axis:
            frequency_range = [
                frequency_range[0] * (1.0 - daylight_factor),
                frequency_range[1] * (1.0 + daylight_factor),
            ]
        else:
            frequency_span = frequency_range[1] - frequency_range[0]
            frequency_range = [
                frequency_range[0] - frequency_span * daylight_factor,
                frequency_range[1] + frequency_span * daylight_factor,
            ]
            frequency_range[0] = max(frequency_range[0], 0.0 * ureg.Hz)
    # Choose a default for the minimum fractional bandwidth
    ax.set_xlim(*[f.to(ureg.Hz) for f in frequency_range])
    if log_axis:
        ax.set_xscale("log")
    if decadal_ticks:
        # Work out potential ticks
        x_ticks = [
            1.0 * ureg.kHz,
            10.0 * ureg.kHz,
            100.0 * ureg.kHz,
            1.0 * ureg.MHz,
            10.0 * ureg.MHz,
            100.0 * ureg.MHz,
            1.0 * ureg.GHz,
            10.0 * ureg.GHz,
            100.0 * ureg.GHz,
            1.0 * ureg.THz,
        ]
        x_ticks = [
            x_tick
            for x_tick in x_ticks
            if x_tick >= frequency_range[0] and x_tick <= frequency_range[1]
        ]
        x_tick_labels = [f"{f:.0f~H}" for f in x_ticks]
        ax.set_xticks(x_ticks, labels=x_tick_labels)
        # Add thin vertical lines at major tick lines
        for f_line in x_ticks:
            # Skip if we're right at the left/right edge (not the confusing meaning of "in"
            # below, it's the range as a list, not a true range.
            if f_line not in frequency_range:
                ax.axvline(f_line, color="grey", linewidth=0.5)
    else:
        # Create a formatter, note we need to apply to both major and minor ticks with a
        # log axis for it to take effect.
        ax.xaxis.set_major_formatter(FuncFormatter(major_frequency_formatter))
        if log_axis:
            ax.xaxis.set_minor_formatter(FuncFormatter(minor_frequency_formatter))
        else:
            # For linear axes, the number of ticks could be reduced
            pass
            # ax.xaxis.set_major_locator(MaxNLocator(prune="both", nbins=4))
    # Have the tickmarks point outwards
    ax.tick_params(axis="x", which="both", direction="out")
    # Suppress the x-axis label
    ax.set_xlabel("")
    return log_axis


def ensure_visible_bandwidth(
    start: pint.Quantity,
    stop: pint.Quantity,
    minimum_bandwidth_points: Optional[float] = None,
) -> tuple[pint.Quantity, pint.Quantity]:
    """Broadens a spectral range to ensure visibility in a plot if it's too narrow

    Note, the presumption is that frequency is shown on a logarithmic scale (at least
    for now), and broadening etc. is done with that in mind.

    Parameters
    ----------
    start : pint.Quantity
        Starting frequency
    stop : pint.Quantity
        Ending frequency
    mimimum_graphical_bandwidth : float, optional
        Minimum fractional bandwidth to ensure.  If a band is narrower than that, then
        the code will move start and stop outwards from the center to meet this minimum
        fractional bandwidth.

    Returns
    -------
    tuple[pint.Quantity, pint.Quantity] - start, stop
        start and stop frequencies adjusted if/as needed.
    """
    # Set defaults
    if minimum_bandwidth_points is None:
        minimum_bandwidth_points = 0.5
    # Get the current figure and axes, work out if we're on a log-scale
    fig = plt.gcf()
    ax = plt.gca()
    try:
        log_scale = bool(["linear", "log"].index(ax.get_xscale()))
    except ValueError as exception:
        raise ValueError(f"Unrecognized axis x-scale {ax.get_xscale()}") from exception
    # Work out the width of the axes in points (will be subject to minor changes, I
    # think, when final drawing takes place.)
    ax_width_pt = 72.0 * fig.get_figwidth() * (ax.get_position().width)
    # Compute the width in data coordinates
    xlim = ax.get_xlim()
    ax_width_data = xlim[1] - xlim[0]
    if log_scale:
        ax_width_data = np.log10(ax_width_data)
    # Compute the scaling ratio
    points_per_data = ax_width_pt / ax_width_data
    # Convert start/end to Hz for now
    start = start.to(ureg.Hz).magnitude
    stop = stop.to(ureg.Hz).magnitude
    # Compute the current width of the bar
    if log_scale:
        current_width_data = np.log10(stop) - np.log10(start)
    else:
        current_width_data = stop - start
    # Compute the current width in points
    current_width_points = current_width_data * points_per_data
    # Work out if a correction is needed
    factor = minimum_bandwidth_points / current_width_points
    # print(minimum_bandwidth_points, current_width_points)
    if factor > 1.0:
        new_width = factor * current_width_data
        if log_scale:
            f_center = 0.5 * (np.log10(start) + np.log10(stop))
        else:
            f_center = 0.5 * (start + stop)
        start = f_center - 0.5 * new_width
        stop = f_center + 0.5 * new_width
        if log_scale:
            start = 10.0**start
            stop = 10.0**stop
    return start * ureg.Hz, stop * ureg.Hz


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
    start, stop = ensure_visible_bandwidth(
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


def show_band_for_individual(
    start: pint.Quantity,
    stop: pint.Quantity,
    row: int,
    ax: plt.Axes,
    status: int,
    minimum_bandwidth_points: Optional[float] = None,
    **kwargs,
):
    """Show a band as a rectangle patch"""
    vertical_width = 0.8
    y_bottom = row - 0.5 * vertical_width
    # For really small bands, make them bigger
    start, stop = ensure_visible_bandwidth(
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
    # Possibly hatch it
    hatches = {1: "///////", 2: "xxxxx"}
    if status > 0:
        patch = Rectangle(
            [start, y_bottom],
            width=(stop - start),
            height=vertical_width,
            hatch=hatches[status],
            color="white",
            fill=None,
            linewidth=0,
        )
        ax.add_patch(patch)


@dataclass
class BarType:
    """Contains the information describing a family of bars"""

    color: str
    slot: int = None
    allocation: Optional[str] = None
    footnote: Optional[str] = None
    condition: Optional[Callable] = None

    def construct_condition(self):
        """A condition to pass to get_bands"""
        if self.allocation and self.footnote:
            return lambda band: band.has_allocation(
                self.allocation
            ) and band.has_footnote(self.footnote)
        elif self.allocation:
            return lambda band: band.has_allocation(self.allocation)
        elif self.footnote:
            return lambda band: band.has_footnote(self.footnote)
        else:
            raise ValueError("No way to subset bands for this BarType")


def wrc27_overview_figure(
    allocation_tables: Optional[pyfcctab.FCCTables] = None,
    frequency_range: Optional[list[pint.Quantity]] = None,
    wrc: str = None,
    ax: Optional[plt.Axes] = None,
    no_show: bool = False,
    include_soundbytes: bool = False,
    first_word_only: bool = False,
    multi_line: bool = False,
    include_srs: bool = False,
    minimum_bandwidth_points: Optional[float] = False,
):
    """Figure reviewing WRC agenda items and associated bands

    Parameters
    ----------
    allocation_tables : pyfcctab.FCCTables, optional
        FCC allocation tables from pyfcctab.  If not supplied, these are read in.
        Having them as an optional argument enables faster debugging.
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
    if allocation_tables is None:
        allocation_tables = pyfcctab.read()
    # Get the agenda items
    ai_info = wrc27_views.get_ai_info(grouped=True)
    # Subset them if/as necessary
    if wrc is not None:
        if wrc not in ["WRC-27", "WRC-31"]:
            raise ValueError(
                f"Ivalid WRC specification ({wrc}), must be WRC-27 or WRC-31"
            )
        ai_info = {key: item for key, item in ai_info.items() if key.startswith(wrc)}
    # Define the science allocations we're interested in.
    bars = {
        "RAS": BarType(
            condition=lambda band: band.has_allocation("Radio Astronomy*")
            or (
                include_srs
                and (
                    band.has_allocation("Space Research (Passive)*")
                    or band.has_allocation("Space Research (Active)*")
                )
            ),
            slot=1,
            color="xkcd:dark sky blue",
        ),
        "EESS": BarType(
            condition=lambda band: band.has_allocation(
                "Earth Exploration-Satellite (Passive)*"
            )
            or band.has_allocation("Earth Exploration-Satellite (Active)*"),
            slot=2,
            color="xkcd:soft green",
        ),
        "5.340": BarType(
            condition=lambda band: band.has_footnote("5.340"),
            slot=3,
            color="xkcd:melon",
        ),
    }
    # Set font defaults etc.
    set_nas_graphic_style()
    # Now embark upon the figure, set up the figure itself
    if ax is None:
        _, ax = plt.subplots(figsize=[6, len(ai_info) * 0.18], layout="constrained")
    # -------------------------------- x-axis
    if frequency_range is None:
        frequency_range = [1_000_000 * ureg.Hz, 1_000_000_000_000 * ureg.Hz]
    _ = setup_frequency_axis(
        ax=ax,
        frequency_range=frequency_range,
        decadal_ticks=True,
    )
    # -------------------------------- y-axis
    y_range = [len(ai_info) - 0.5, -0.5]
    ax.set_ylim(y_range[0], y_range[1])
    y_labels = [key.split(" ")[1][3:] for key in ai_info.keys()]
    y_tick_locations = np.arange(len(ai_info))
    ax.set_yticks(y_tick_locations, labels=y_labels)
    ax.yaxis.set_minor_locator(plt.NullLocator())
    # Potentially the soundbyte labels
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
        bar_buffer = {key: pyfcctab.BandCollection() for key in bars}
        for ai_band in this_ai.frequency_bands:
            # Draw the bands addressed by the Agenda Item
            show_band_for_overview(
                ai_band.start,
                ai_band.stop,
                row=i_y,
                slot=0,
                facecolor="dimgrey",
                ax=ax,
                edgecolor="none",
                minimum_bandwidth_points=minimum_bandwidth_points,
            )
            # Draw all the science bands we found
            for key, bar_info in bars.items():
                relevant_bands = allocation_tables.itu.get_bands(
                    ai_band.start,
                    ai_band.stop,
                    condition=bar_info.condition,
                    adjacent=True,
                )
                bar_buffer[key] = bar_buffer[key].union(
                    pyfcctab.BandCollection(relevant_bands)
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
    if not no_show:
        plt.show()


def wrc27_ai_figure(
    ai: str | list[str],
    allocation_tables: Optional[pyfcctab.FCCTables] = None,
    frequency_range: Optional[list[pint.Quantity]] = None,
    ax: Optional[plt.Axes] = None,
    no_show: Optional[bool] = False,
    log_axis: Optional[bool] = False,
    comprehensive_overview: Optional[bool] = False,
    include_srs: Optional[bool] = False,
    minimum_bandwidth_points: Optional[float] = None,
):
    """Figure reviewing WRC agenda items and associated bands

    Parameters
    ----------
    ai : str | list[str], optional
        AI identifier or list thereof (e.g. 1.6)
    allocation_tables : pyfcctab.FCCTables, optional
        FCC allocation tables from pyfcctab.  If not supplied, these are read in.
        Having them as an optional argument enables faster debugging.
    frequency_range : list[pint.Quantity], optional
        Range of frequencies to cover, expansive default assumed if not given.
    ax : plt.Axes, optional
        If supplied do figure in these axes, otherwise generate our own
    no_show : bool, optional
        If set, skip the plt.show() step.
    log_xaxis : bool, optional
        Force log or linear x-axis
    comprehensive_overview : bool, optional
        If set, show all the science bands, regardless of distance, and increase the range a bit.
    include_srs : bool, optional
        If set, include the SRS entries.
    minimum_bandwidth_points : float, optional
        If bar is narrower than this, make it wider
    """
    # Read the allocation tables if not supplied
    if allocation_tables is None:
        allocation_tables = pyfcctab.read()
    # Get the agenda items
    ai_info = wrc27_views.get_ai_info(grouped=True)
    # Subset them if/as necessary
    if isinstance(ai, str):
        ai = [ai]
    ai_info = {ai_key: ai_info[ai_key] for ai_key in ai}
    # Define the science allocations we're interested in.
    science_rows = {
        "RAS": BarType(
            allocation="Radio Astronomy*",
            color="xkcd:dark sky blue",
        ),
    }
    if include_srs:
        science_rows = science_rows | {
            "SRS (Passive)": BarType(
                allocation="Space Research (Passive)*",
                color="xkcd:royal purple",
            ),
            "SRS (Active)": BarType(
                allocation="Space Research (Active)*",
                color="xkcd:pale purple",
            ),
        }
    science_rows = science_rows | {
        "EESS (Passive)": BarType(
            allocation="Earth Exploration-Satellite (Passive)*",
            color="xkcd:soft green",
        ),
        "EESS (Active)": BarType(
            allocation="Earth Exploration-Satellite (Active)*",
            color="xkcd:easter green",
        ),
        "5.340": BarType(
            footnote="5.340",
            slot=3,
            color="xkcd:melon",
        ),
    }
    # Identify the bars for each agenda item
    bar_buffers = {}
    for ai_key, this_ai_info in ai_info.items():
        bar_buffers[ai_key] = {
            row_key: pyfcctab.BandCollection() for row_key in science_rows
        }
        for band in this_ai_info.frequency_bands:
            for row_key, row_info in science_rows.items():
                relevant_bands = allocation_tables.itu.get_bands(
                    band.start,
                    band.stop,
                    condition=row_info.construct_condition(),
                    recursively_adjacent=True,
                )
                bar_buffers[ai_key][row_key] = bar_buffers[ai_key][row_key].union(
                    pyfcctab.BandCollection(relevant_bands)
                )
    # Set font defaults etc.
    set_nas_graphic_style()
    # Now embark upon the figure, set up the figure itself, start with a default width
    if ax is None:
        fig, ax = plt.subplots(layout="constrained")

    # -------------------------------- x-axis
    if frequency_range is None:
        # Identify the frequency range
        f_mins = []
        f_maxs = []
        for ai_key, this_ai_info in ai_info.items():
            # Gather mins/maxes for the bands in this AI
            f_mins += [band.start for band in this_ai_info.frequency_bands]
            f_maxs += [band.stop for band in this_ai_info.frequency_bands]
            # Now do the same for any relevant science bands
            for science_bands in bar_buffers[ai_key].values():
                f_mins += [band.bounds[0] for band in science_bands]
                f_maxs += [band.bounds[1] for band in science_bands]
        if len(f_mins) != 0:
            frequency_range = [min(f_mins), max(f_maxs)]
        else:
            frequency_range = [1.0 * ureg.MHz, 1.0 * ureg.GHz]
        add_daylight = True
    else:
        add_daylight = False
    # For a comprehensive overview, have a larger range
    if comprehensive_overview:
        add_daylight = True
        daylight_factor = 0.3
    else:
        daylight_factor = None
    # Also for a comprehensive overview, we include all the bands regardless of adjacency
    if comprehensive_overview:
        new_bar_buffers = {}
        for row_key, row_info in science_rows.items():
            new_bar_buffers[row_key] = allocation_tables.itu.get_bands(
                frequency_range[0],
                frequency_range[1],
                condition=row_info.construct_condition(),
                recursively_adjacent=True,
            )
        for ai_key in ai_info:
            bar_buffers[ai_key] = new_bar_buffers
    # Setup the frequency axis, labels, etc.
    log_axis = setup_frequency_axis(
        ax=ax,
        frequency_range=frequency_range,
        add_daylight=add_daylight,
        log_axis=log_axis,
        daylight_factor=daylight_factor,
    )
    # -------------------------------- Actual figure
    # OK, loop over the agenda items
    y_labels = []
    for ai_key, this_ai_info in ai_info.items():
        # If there are no specific bands for this AI, then we're done at this point
        if ai_info is None:
            continue
        # If we're not on the first one, then put a dividing line in
        if len(y_labels) > 0:
            ax.axhline(len(y_labels) - 0.5, linewidth=1.0, color="black")
        for band in this_ai_info.frequency_bands:
            # Draw this particular band
            show_band_for_individual(
                band.start,
                band.stop,
                row=len(y_labels),
                facecolor="dimgrey",
                ax=ax,
                minimum_bandwidth_points=minimum_bandwidth_points,
                edgecolor="none",
                status=0,
            )
        y_labels.append(r"\textbf{" + ai_key + r"}")
        for row_key, science_bands in bar_buffers[ai_key].items():
            if len(science_bands) == 0:
                continue
            row_info = science_rows[row_key]
            for band in science_bands:
                # Work out what the status of this band is
                status = 3
                for allocation in band.allocations:
                    if row_info.allocation is None:
                        continue
                    if allocation.matches(row_info.allocation):
                        if allocation.primary:
                            status = min(status, 0)
                        if allocation.secondary:
                            status = min(status, 1)
                        if allocation.footnote_mention:
                            status = min(status, 2)
                if status == 3:
                    status = 0
                show_band_for_individual(
                    band.bounds[0],
                    band.bounds[1],
                    row=len(y_labels),
                    ax=ax,
                    minimum_bandwidth_points=minimum_bandwidth_points,
                    facecolor=row_info.color,
                    status=status,
                )
            y_labels.append(row_key)
    # -------------------------------- y-axis
    y_range = [len(y_labels) - 0.5, -0.5]
    ax.set_ylim(y_range[0], y_range[1])
    y_tick_locations = np.arange(len(y_labels))
    ax.set_yticks(y_tick_locations, labels=y_labels)
    ax.yaxis.set_minor_locator(plt.NullLocator())
    # Suppress the y ticks.
    ax.tick_params(axis="y", which="both", left=False, right=False)
    # --------------------------------- Sizing
    # Now work out the size.
    row_size_inches = 0.15
    # Take a stab at the figure size
    figure_width_inches = 10.6 / 2.54
    bar_area_height_inches = len(y_labels) * row_size_inches
    notional_extra_height_inches = 0.3533
    initial_height = bar_area_height_inches + notional_extra_height_inches
    fig.set_size_inches(
        figure_width_inches, bar_area_height_inches + notional_extra_height_inches
    )
    # Do a first pass to get the size
    fig.canvas.draw()
    # Work out the actual size of the axes in inches, the remainder is the space taken
    # up by the extra stuff
    actual_bar_area_height_inchdes = ax.get_position().height * initial_height
    actual_extra_height_inches = initial_height - actual_bar_area_height_inchdes
    # Redraw at corrected height
    final_height_inches = bar_area_height_inches + actual_extra_height_inches
    fig.set_size_inches(figure_width_inches, final_height_inches)
    fig.canvas.draw()
    # --------------------------------- Done
    if not no_show:
        plt.show()


@dataclass
class AIPlotConfiguration:
    """Defines the configuration of a specific Agenda Item plot"""

    ai: str | list[str]
    log_axis: Optional[bool] = None
    frequency_range: Optional[list[pint.Quantity]] = None


def all_individual_figures(
    allocation_tables: Optional[pyfcctab.FCCTables] = None,
    comprehensive_overview: Optional[bool] = False,
):
    """Generate all the figures for the agenda items"""
    # Get the agenda items
    ai_info = wrc27_views.get_ai_info(grouped=True)
    # Make a bunch of plots for the WRC-27 items
    plot_configurations: dict[AIPlotConfiguration] = {}
    solo_wrc31_items = [
        "WRC-31 AI-2.3",
        "WRC-31 AI-2.4",
        "WRC-31 AI-2.8",
        "WRC-31 AI-2.14",
    ]
    for key, item in ai_info.items():
        if key.startswith("WRC-27") or key in solo_wrc31_items:
            plot_configurations[key] = AIPlotConfiguration(key)
    # Now do those that are in combination
    plot_configurations["WRC-31 AIs-2.1-2.2-2.6"] = AIPlotConfiguration(
        ai=[
            "WRC-31 AI-2.1",
            "WRC-31 AI-2.2",
            "WRC-31 AI-2.6",
        ]
    )
    plot_configurations["WRC-31 AIs-2.10-2.11"] = AIPlotConfiguration(
        ai=[
            "WRC-31 AI-2.10",
            "WRC-31 AI-2.11",
        ]
    )
    plot_configurations["WRC-31 AIs-2.12-2.13"] = AIPlotConfiguration(
        ai=[
            "WRC-31 AI-2.12",
            "WRC-31 AI-2.13",
        ]
    )
    if comprehensive_overview:
        file_suffix = "-overview"
    else:
        file_suffix = ""
    for key, item in plot_configurations.items():
        print(key)
        wrc27_ai_figure(
            allocation_tables=allocation_tables,
            ai=item.ai,
            log_axis=item.log_axis,
            frequency_range=item.frequency_range,
            no_show=True,
            comprehensive_overview=comprehensive_overview,
        )
        plt.savefig(f"specific-ai-plots/SpecificAI-{key}{file_suffix}.pdf")
        plt.close()
