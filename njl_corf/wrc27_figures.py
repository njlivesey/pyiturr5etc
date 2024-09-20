"""Produces an overview graphic for the WRC 27/31 agenda items"""

from dataclasses import dataclass
from typing import Optional, Callable
import functools

import matplotlib
import matplotlib.font_manager
import matplotlib.pyplot as plt
import numpy as np
import pint
from matplotlib.patches import Rectangle
from matplotlib.ticker import FuncFormatter, NullFormatter
from matplotlib.transforms import blended_transform_factory

from njl_corf import pyfcctab, ureg, wrc27_views


def set_nas_graphic_style():
    """Choose fonts etc. to match NAS style"""
    # Set plot defaults
    matplotlib.rcParams["text.usetex"] = True
    matplotlib.rcParams["font.family"] = "serif"
    matplotlib.rcParams["font.serif"] = ["Palatino"]
    matplotlib.rcParams["font.size"] = 9
    matplotlib.rcParams["pdf.fonttype"] = 42
    matplotlib.rcParams["ps.fonttype"] = 42


def discern_ideal_unit(f: pint.Quantity | np.float64) -> pint.Unit:
    """Return the appropriate unit to pick"""
    if isinstance(f, pint.Quantity):
        f = f.to(ureg.Hz).magnitude
    if f < 1e3:
        return ureg.Hz
    if f < 1e6:
        return ureg.kHz
    if f < 1e9:
        return ureg.MHz
    if f < 1e12:
        return ureg.GHz
    else:
        return ureg.THz


# pylint: disable-next=unused-argument
def major_frequency_formatter_with_units(
    x,
    pos,
    supplied_unit: Optional[pint.Unit] = None,
):
    """A nice tick formatter for frequency"""
    assert not isinstance(x, pint.Quantity), "Got a pint Quantity for x"
    if supplied_unit is None:
        # It's up to us to identifty the unit, in which case, we have to assume that we
        # were given the unit in Hz.
        supplied_unit = discern_ideal_unit(x)
        x = (x * ureg.Hz).to(supplied_unit).magnitude
    x = x * supplied_unit
    return f"{x:.4g~}"


def generic_log_formatter(x, pos):
    """A simple formatter for log ticks"""
    assert not isinstance(x, pint.Quantity), "Got a pint Quantity for x"
    if not np.isclose(np.round(x), x):
        return f"{x}"
    else:
        return f"{int(round(x))}"


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
    put_units_on_labels: Optional[bool] = False,
    xticks: Optional[pint.Quantity] = None,
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
    put_units_on_labels : bool, optional
        If set, put the units on the labels (otherwise in a x-axis label)
    xticks : pint.Quantity, optinal
        Locations for xticks
    """
    # Have the tickmarks point outwards
    ax.tick_params(axis="x", which="both", direction="out")
    # Sort out xticks
    if isinstance(xticks, list):
        xticks = pint.Quantity.from_list(xticks)
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
    # Set up the axis type and identify the "center" frequency (which depends on the
    # type of axis)
    if log_axis:
        ax.set_xscale("log")
        orders = np.log10(frequency_range[1] / frequency_range[0])
        center_frequency = np.sqrt(frequency_range[0] * frequency_range[1])
    else:
        center_frequency = 0.5 * (frequency_range[0] + frequency_range[1])
        orders = 0
    # If the plot linear or over a narrow logarithmic range, identify a natural unit
    # (MHz, GHz, etc.)
    if not log_axis or orders < 2:
        typical_unit = discern_ideal_unit(center_frequency)
        # Set the frequency axis to have this range in this unit
        ax.set_xlim(*[f.to(typical_unit) for f in frequency_range])
    else:
        # Otherwise note that we're working over a large logarithmic range by setting
        # typical_unit to None and force range to Hertz.
        ax.set_xlim(*[f.to(ureg.Hz) for f in frequency_range])
        if xticks is not None:
            xticks = [f.to(ureg.Hz) for f in xticks]
        typical_unit = None
    # Otherwise, we're not doing decadal ticks, either pick our own or use the user
    # supplied list.  If the latter, put them in appropriate units
    if xticks is not None and typical_unit is not None:
        # The user suppled specific ticks, convert them to the appropriate value.
        xticks = xticks.to(typical_unit)
    # Work out whether the labels have units on them, deal with that if so
    if put_units_on_labels:
        # Suppress the x-axis label
        ax.set_xlabel("")
        # Reset the x axis range to be in hertz, and note that there is no "typical unit"
        if xticks is not None:
            xticks = [f.to(ureg.Hz) for f in xticks]
        ax.set_xlim(*[f.to(ureg.Hz) for f in frequency_range])
        # Create a tick formatter, note we need to apply to both major and minor ticks
        # with a log axis for it to take effect.
        # if log_axis:
        #   ax.xaxis.set_minor_formatter(FuncFormatter(minor_frequency_formatter))
        unit_formatter = FuncFormatter(
            functools.partial(
                major_frequency_formatter_with_units, supplied_unit=typical_unit
            )
        )
        ax.xaxis.set_major_formatter(unit_formatter)
    else:
        if typical_unit is not None:
            ax.set_xlabel(f"Frequency / {typical_unit:~}")
        else:
            ax.set_xlabel("Frequency")

    # For log axes, pick the scalar formatter
    if log_axis:
        if xticks is not None:
            ax.set_xticks(xticks)
        if put_units_on_labels:
            # Redo the formatter (probably more efficient organizations of this set of
            # if statements, but this one works)
            ax.xaxis.set_major_formatter(unit_formatter)
        else:
            ax.xaxis.set_major_formatter(FuncFormatter(generic_log_formatter))
        ax.xaxis.set_minor_formatter(NullFormatter())
    else:
        # Now pick the specific ticks (do this last, because setting the formatter resets this)
        if xticks is not None:
            ax.set_xticks(xticks)
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
        minimum_bandwidth_points = 1.0
    # Get the current figure and axes, work out if we're on a log-scale
    fig = plt.gcf()
    ax = plt.gca()
    try:
        log_scale = bool(["linear", "log"].index(ax.get_xscale()))
    except ValueError as exception:
        raise ValueError(f"Unrecognized axis x-scale {ax.get_xscale()}") from exception
    # Work out the width of the axes in points (will be subject to minor changes, I
    # think, when final drawing takes place.)
    ax_width_points = 72.0 * fig.get_figwidth() * (ax.get_position().width)
    # Compute the width of the band in axes coordinates
    x_unit = ax.xaxis.get_units()
    current_width_points = 0.0
    for sign, x in zip([-1, 1], [start, stop]):
        if x_unit is not None:
            p_display = ax.transData.transform([x.to(x_unit).magnitude, 0])
        else:
            p_display = ax.transData.transform([x, 0])
        p_axes = ax.transAxes.inverted().transform(p_display)
        current_width_points += sign * p_axes[0] * ax_width_points
    # Work out if a correction is needed
    factor = minimum_bandwidth_points / current_width_points
    if factor > 1.0:
        if not log_scale:
            f_center = 0.5 * (start + stop)
            start = f_center - factor * (f_center - start)
            stop = f_center + factor * (stop - f_center)
        else:
            log_start = np.log10(start.to(x_unit).magnitude)
            log_stop = np.log10(stop.to(x_unit).magnitude)
            log_center = 0.5 * (log_start + log_stop)
            log_start = log_center - factor * (log_center - log_start)
            log_stop = log_center + factor * (log_stop - log_center)
            start = (10.0**log_start) * x_unit
            stop = (10.0**log_stop) * x_unit
    return start, stop


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
    minimum_bandwidth_points: Optional[float] = None,
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
        # decadal_ticks=True,
        put_units_on_labels=True,
        log_axis=True,
    )
    # Put grey lines at major ticks
    for x in list(ax.get_xticks())[1:-1]:
        ax.axvline(x, color="lightgrey", zorder=0, linewidth=0.5)
    # -------------------------------- y-axis
    y_range = [len(ai_info) - 0.5, -0.5]
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
    if not no_show:
        plt.show()


def wrc27_ai_figure(
    ai: str | list[str],
    allocation_tables: Optional[pyfcctab.FCCTables] = None,
    frequency_range_shown_pre_daylight: Optional[list[pint.Quantity]] = None,
    ax: Optional[plt.Axes] = None,
    no_show: Optional[bool] = False,
    log_axis: Optional[bool] = False,
    include_srs: Optional[bool] = False,
    minimum_bandwidth_points: Optional[float] = None,
    put_units_on_labels: Optional[bool] = False,
    include_all_encompassed_allocations: Optional[bool] = True,
    xticks: Optional[pint.Quantity] = None,
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
    include_srs : bool, optional
        If set, include the SRS entries.
    minimum_bandwidth_points : float, optional
        If bar is narrower than this, make it wider
    put_units_on_labels : float, optional
        If set, put units on frequency labels
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
    # Get the colormap we like
    color_map = plt.get_cmap("tab20c").colors
    # Define the science allocations we're interested in.
    science_rows = {
        "RAS": BarType(
            allocation="Radio Astronomy*",
            color=[color_map[0], color_map[1], color_map[3]],
        ),
    }
    # Define the bars we're going to show
    if include_srs:
        science_rows = science_rows | {
            "SRS (Passive)": BarType(
                allocation="Space Research (Passive)*",
                color=[color_map[12], color_map[13], color_map[14]],
            ),
            "SRS (Active)": BarType(
                allocation="Space Research (Active)*",
                color=[color_map[12], color_map[13], color_map[14]],
            ),
        }
    science_rows = science_rows | {
        "EESS (Passive)": BarType(
            allocation="Earth Exploration-Satellite (Passive)*",
            color=[color_map[8], color_map[9], color_map[11]],
        ),
        "EESS (Active)": BarType(
            allocation="Earth Exploration-Satellite (Active)*",
            color=[color_map[8], color_map[9], color_map[11]],
        ),
        "RR 5.340": BarType(
            footnote="5.340",
            slot=3,
            color=["xkcd:melon"],
        ),
    }
    # Identify the bars for each agenda item
    bar_buffers = {row_key: pyfcctab.BandCollection() for row_key in science_rows}
    for ai_key, this_ai_info in ai_info.items():
        for ai_band in this_ai_info.frequency_bands:
            for row_key, row_info in science_rows.items():
                relevant_bands = allocation_tables.itu.get_bands(
                    ai_band.start,
                    ai_band.stop,
                    condition=row_info.construct_condition(),
                    recursively_adjacent=True,
                )
                bar_buffers[row_key] = bar_buffers[row_key].union(
                    pyfcctab.BandCollection(relevant_bands)
                )
    # Set font defaults etc.
    set_nas_graphic_style()
    # Now embark upon the figure, set up the figure itself, start with a default width
    if ax is None:
        ax_supplied = False
        fig, ax = plt.subplots(layout="constrained")
    else:
        ax_supplied = True

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
    log_axis = setup_frequency_axis(
        ax=ax,
        frequency_range=frequency_range_shown_pre_daylight,
        add_daylight=add_daylight,
        log_axis=log_axis,
        put_units_on_labels=put_units_on_labels,
        xticks=xticks,
    )

    # OK, despite having gone to the lengths of carefully identifying the science (and
    # 5.340) bands that overlap or are directly adjacent to the bands under
    # consideration, we're going to kind of throw all that away, and just get all the
    # bands of interest in the range, but only if we identified a case for their
    # inclusion (by virtue of being adjacent or overlapping) before.
    new_bar_buffers = {row_key: pyfcctab.BandCollection() for row_key in science_rows}
    for row_key, row_info in science_rows.items():
        if bar_buffers[row_key] or include_all_encompassed_allocations:
            new_bar_buffers[row_key] = allocation_tables.itu.get_bands(
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
            facecolor = "dimgrey"
        else:
            solid_frequency_bands = this_ai_info.detailed_bands
            facecolor = "lightgrey"
        for ai_band in solid_frequency_bands:
            # Draw this particular band
            show_band_for_individual(
                ai_band.start,
                ai_band.stop,
                row=len(y_labels),
                facecolor=facecolor,
                ax=ax,
                minimum_bandwidth_points=minimum_bandwidth_points,
                edgecolor="none",
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
                    edgecolor="dimgrey",
                    ax=ax,
                    minimum_bandwidth_points=minimum_bandwidth_points,
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
    y_range = [len(y_labels) - 0.5, -0.5]
    y_margin = 0.15
    ax.set_ylim(y_range[0] + y_margin, y_range[1] - y_margin)
    y_tick_locations = np.arange(len(y_labels))
    ax.set_yticks(y_tick_locations, labels=y_labels)
    ax.yaxis.set_minor_locator(plt.NullLocator())
    # Suppress the y ticks.
    ax.tick_params(axis="y", which="both", left=False, right=False)
    # --------------------------------- Legend
    # Combine figure transform (for x-axis) and data transform (for y-axis)
    legend_transform = blended_transform_factory(fig.transFigure, ax.transData)
    # Rectangle parameters
    box_width = 0.05
    box_height = 1.0
    box_x = np.arange(3) * box_width
    box_y = np.arange(3) * box_height + len(y_labels) - 0.25
    i_color = [[0, 1, 3], [8, 9, 11]]
    for i_service in range(2):
        for i_type in range(3):
            rect = Rectangle(
                (box_x[i_type], box_y[i_service]),
                width=box_width * 0.9,
                height=box_height * 0.8,
                transform=legend_transform,
                facecolor=color_map[i_color[i_service][i_type]],
                edgecolor="none",
                clip_on=False,
            )
            fig.patches.append(rect)
    # Now some labels
    labels = ["Pri.", "Sec.", "Fn."]
    for i_label, label in enumerate(labels):
        fig.text(
            box_x[i_label] + (0.5 * box_width) * 0.9,
            box_y[2],
            label,
            ha="center",
            va="top",
            transform=legend_transform,
            fontsize="small",
        )
    # --------------------------------- Sizing
    if not ax_supplied:
        # Now work out the size.
        row_size_inches = 0.15
        # Take a stab at the figure size
        figure_width_inches = 10.6 / 2.54
        bar_area_height_inches = (len(y_labels) + 2 * y_margin) * row_size_inches
        notional_extra_height_inches = 0.3533 + 0.18 * (not put_units_on_labels)
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
    put_units_on_labels: Optional[bool] = False
    frequency_range: Optional[list[pint.Quantity]] = None
    include_all_encompassed_allocations: Optional[bool] = True
    xticks: Optional[pint.Quantity] = None


def all_individual_figures(
    allocation_tables: Optional[pyfcctab.FCCTables] = None,
    only: Optional[list[str]] = None,
):
    """Generate all the figures for the agenda items"""
    # Get the agenda items
    ai_info = wrc27_views.get_ai_info(grouped=True)
    # Setup a placeholder for the configurations
    plot_configurations: dict[AIPlotConfiguration] = {}
    # Make a bunch of plots for the WRC-27 items
    # fmt: on
    plot_configurations["WRC-27 AI-1.1"] = AIPlotConfiguration("WRC-27 AI-1.1")
    plot_configurations["WRC-27 AI-1.2"] = AIPlotConfiguration("WRC-27 AI-1.2")
    plot_configurations["WRC-27 AI-1.3"] = AIPlotConfiguration(
        "WRC-27 AI-1.3", frequency_range=[50.2 * ureg.GHz, 53.0 * ureg.GHz]
    )
    plot_configurations["WRC-27 AI-1.4"] = AIPlotConfiguration("WRC-27 AI-1.4")
    plot_configurations["WRC-27 AI-1.5"] = AIPlotConfiguration("WRC-27 AI-1.5")
    plot_configurations["WRC-27 AI-1.6"] = AIPlotConfiguration("WRC-27 AI-1.6")
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
        log_axis=True,
        xticks=[3 * ureg.MHz, 6 * ureg.MHz, 10 * ureg.MHz, 20 * ureg.MHz],
    )
    plot_configurations["WRC-27 AI-1.10"] = AIPlotConfiguration("WRC-27 AI-1.10")
    plot_configurations["WRC-27 AI-1.11"] = AIPlotConfiguration("WRC-27 AI-1.11")
    plot_configurations["WRC-27 AI-1.12"] = AIPlotConfiguration("WRC-27 AI-1.12")
    plot_configurations["WRC-27 AI-1.13"] = AIPlotConfiguration(
        "WRC-27 AI-1.13",
        # log_axis=True,
    )
    plot_configurations["WRC-27 AI-1.14"] = AIPlotConfiguration("WRC-27 AI-1.14")
    plot_configurations["WRC-27 AI-1.15"] = AIPlotConfiguration(
        "WRC-27 AI-1.15", put_units_on_labels=True, log_axis=True
    )
    plot_configurations["WRC-27 AI-1.16"] = AIPlotConfiguration(
        "WRC-27 AI-1.16",
        log_axis=True,
        xticks=[10 * ureg.GHz, 30 * ureg.GHz, 60 * ureg.GHz, 100 * ureg.GHz],
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
    plot_configurations["WRC-31 AI-2.9"] = AIPlotConfiguration("WRC-31 AI-2.9")
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
        ]
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
            allocation_tables=allocation_tables,
            ai=item.ai,
            log_axis=item.log_axis,
            frequency_range_shown_pre_daylight=item.frequency_range,
            include_all_encompassed_allocations=item.include_all_encompassed_allocations,
            put_units_on_labels=item.put_units_on_labels,
            no_show=True,
            xticks=item.xticks,
            minimum_bandwidth_points=1.0,
        )
        plt.savefig(
            f"specific-ai-plots/SpecificAI-{key}.pdf",
            bbox_inches="tight",
            pad_inches=2.0 / 72,
        )
        plt.savefig(
            f"specific-ai-plots/SpecificAI-{key}.png",
            dpi=600,
            bbox_inches="tight",
            pad_inches=2.0 / 72,
        )
        if only:
            plt.show()
        plt.close()
