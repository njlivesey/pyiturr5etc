"""Provides a set of colors for the WRC figures"""

import functools
from typing import Optional, Callable
from dataclasses import dataclass

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib import ticker as mticker
import numpy as np
import pint
from matplotlib.ticker import FuncFormatter, NullFormatter

from pyiturr5etc import ureg


class LaTeXScalarFormatter(mticker.ScalarFormatter):
    """Custom ScalarFormatter that forces LaTeX typesetting for tick labels."""

    def __init__(self, useOffset=True, useMathText=True):
        super().__init__(useOffset=useOffset, useMathText=useMathText)

    def __call__(self, x, pos=None):
        """Override the default __call__ to return LaTeX-formatted labels."""
        label = super().__call__(x, pos)  # Get the default formatted text
        label = label.replace(r"$\mathdefault{", "").replace(r"}$", "")
        return label
        # return rf"${label}"  # Ensure it's typeset in math mode
        return r"$\text{\fontseries{l}\selectfont{}H" f"{label}" r"}$"

    def format_data(self, value):
        """Ensures that interactive display (cursor hover) uses LaTeX."""
        # return rf"{super().format_data(value)}"
        raise NotImplementedError
        return r"$\text{" rf"{super().format_data(value)}" r"}$"

    def format_data_short(self, value):
        """Ensures shorter formatted data is still LaTeX-wrapped."""
        # return rf"{super().format_data_short(value)}"
        raise NotImplementedError
        return r"$\text{" rf"{super().format_data_short(value)}" r"}$"


def set_nas_graphic_style():
    """Choose fonts etc. to match NAS style"""
    matplotlib.rcParams["text.usetex"] = True
    matplotlib.rcParams[
        "text.latex.preamble"
    ] = r"""
        \usepackage[boldweight=Bold]{fdsymbol}
        % \usepackage[light, sflining, sfdefault]{merriweather}
        % \usepackage{mathastext}
    """
    matplotlib.rcParams["font.family"] = "serif"  # "sans-serif"
    matplotlib.rcParams["font.serif"] = ["Palatino"]
    matplotlib.rcParams["font.size"] = 9


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
    # pylint: disable-next=unused-argument
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


# pylint: disable-next=unused-argument
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
    add_daylight: Optional[bool] = False,
    log_axis: Optional[bool] = None,
    daylight_factor: Optional[float] = None,
    put_units_on_labels: Optional[bool] = False,
    xticks: Optional[pint.Quantity] = None,
    xminor: Optional[pint.Quantity] = None,
):
    """Configure the frequency axis

    Parameters
    ----------
    ax : plt.Axes
        The axes under consideration
    frequency_range : list[pint.Quantity]
        The frequency range to cover
    add_daylight : bool, optional
        If set, add some daylight either side of the frequency range
    log_axis : bool, optional
        Chose log vs. linear axis
    daylight_factor : float, optional
        Amount of daylight to add
    put_units_on_labels : bool, optional
        If set, put the units on the labels (otherwise in a x-axis label)
    xticks : pint.Quantity, optional
        Locations for xticks
    xticks : pint.Quantity, optional
        Locations for x minor ticks
    """
    # Sort out xticks
    if isinstance(xticks, list):
        xticks = pint.Quantity.from_list(xticks)
    if isinstance(xminor, list):
        xminor = pint.Quantity.from_list(xminor)
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
        if xminor is not None:
            xminor = [f.to(ureg.Hz) for f in xminor]
        typical_unit = None
    # Otherwise either pick our own ticks or use the user supplied list.  If the latter,
    # put them in appropriate units
    if xticks is not None and typical_unit is not None:
        # The user suppled specific ticks, convert them to the appropriate value.
        xticks = xticks.to(typical_unit)
    if xminor is not None and typical_unit is not None:
        # The user suppled specific minor ticks, convert them to the appropriate value.
        xminor = xminor.to(typical_unit)
    # Work out whether the labels have units on them, deal with that if so
    if put_units_on_labels:
        # Suppress the x-axis label
        ax.set_xlabel("")
        # Reset the x axis range to be in hertz, and note that there is no "typical unit"
        if xticks is not None:
            xticks = [f.to(ureg.Hz) for f in xticks]
        if xminor is not None:
            xminor = [f.to(ureg.Hz) for f in xminor]
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
        if xminor is not None:
            ax.set_xticks(xminor, minor=True)
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
        if xminor is not None:
            ax.set_xticks(xminor, minor=True)
    if isinstance(ax.xaxis.get_major_formatter(), mticker.ScalarFormatter):
        ax.xaxis.set_major_formatter(LaTeXScalarFormatter())
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
    ax = plt.gca()
    try:
        log_scale = bool(["linear", "log"].index(ax.get_xscale()))
    except ValueError as exception:
        raise ValueError(f"Unrecognized axis x-scale {ax.get_xscale()}") from exception
    # Work out the width of the axes in points (will be subject to minor changes, I
    # think, when final drawing takes place.)
    # Compute the width of the band in axes coordinates
    x_unit = ax.xaxis.get_units()
    current_width_points = get_bandwidth_points(start, stop)
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


def get_bandwidth_points(start: float, stop: float):
    """Get the width of a bar in points"""
    current_width_points = 0.0
    ax = plt.gca()
    fig = plt.gcf()
    ax_width_points = 72.0 * fig.get_figwidth() * (ax.get_position().width)
    x_unit = ax.xaxis.get_units()
    for sign, x in zip([-1, 1], [start, stop]):
        if x_unit is not None:
            p_display = ax.transData.transform([x.to(x_unit).magnitude, 0])
        else:
            p_display = ax.transData.transform([x, 0])
        p_axes = ax.transAxes.inverted().transform(p_display)
        current_width_points += sign * p_axes[0] * ax_width_points
    return current_width_points


def shift_x_by_points(x, points, ax=None):
    """Compute delta x that shifts location by points.

    Parameters
    ----------
    x : float
        The x-coordinate in data units.
    points : The shift amount in points.
    ax : Axes
        The Axes object. If None, uses plt.gca().

    Returns:
    new_x : float
        The adjusted x-coordinate in data units.
    """
    if ax is None:
        ax = plt.gca()

    # Get the figure DPI and convert points to pixels
    points_to_pixels = points * (ax.figure.dpi / 72)  # Points to pixels conversion

    # Get axis x-unit (used by Matplotlib for scaling)
    x_unit = ax.xaxis.get_units() or x.units
    x_in_unit = x.to(x_unit).magnitude  # Convert x to the axis unit

    # Transform x to display coordinates
    point_display_original = ax.transData.transform((x_in_unit, 0))
    x_display_original = point_display_original[0]
    y_display_original = point_display_original[1]

    # Shift in display coordinates
    x_display_moved = x_display_original + points_to_pixels

    # Transform back to data coordinates
    x_data_moved = ax.transData.inverted().transform(
        (x_display_moved, y_display_original)
    )

    # Convert delta x back to original units
    delta_x = pint.Quantity(x_data_moved[0] - x_in_unit, x_unit).to(x.units)
    return delta_x


def get_wrc_color_scheme(name: Optional[str] = None):
    """Return a dictionary of colors"""
    if name is None:
        name = "original"
    if name == "original":
        color_map = plt.get_cmap("tab20c").colors
        figure_colors = {
            "RAS Overview": "xkcd:dark sky blue",
            "EESS Overview": "xkcd:soft green",
            "5.340": "xkcd:melon",
            "AI": "dimgrey",
            "AI-extra": "lightgrey",
            "RAS": [color_map[0], color_map[1], color_map[3]],
            "SRS (passive)": [color_map[12], color_map[13], color_map[14]],
            "SRS (active)": [color_map[12], color_map[13], color_map[14]],
            "EESS (passive)": [color_map[8], color_map[9], color_map[11]],
            "EESS (active)": [color_map[8], color_map[9], color_map[11]],
        }
    elif name == "R&S-a":
        figure_colors = {
            "RAS Overview": "#31437e",
            "EESS Overview": "317e34",
            "5.340": "xkcd:melon",
            "AI": "dimgrey",
            "AI-extra": "lightgrey",
            "RAS": ["#31437e", "#03a1bf", "#96d1de"],
            "EESS (passive)": ["#317e43", "#03bfa1", "#96ded1"],
            "EESS (active)": ["#317e43", "#03bfa1", "#96ded1"],
        }
    elif name == "new-a":
        figure_colors = {
            "RAS Overview": "xkcd:marine blue",
            "EESS Overview": "317e34",
            "5.340": "xkcd:melon",
            "AI": "dimgrey",
            "AI-extra": "lightgrey",
            "RAS": [
                "xkcd:marine blue",
                "xkcd:deep sky blue",
                "xkcd:light sky blue",
            ],
            "EESS (passive)": [
                "xkcd:forest green",
                "xkcd:grass green",
                "xkcd:pale green",
            ],
        }
    elif name == "new-b":
        figure_colors = {
            "RAS Overview": "xkcd:purple",
            "EESS Overview": "xkcd:grass green",
            "5.340": "xkcd:melon",
            "AI": "dimgrey",
            "AI-extra": "lightgrey",
            "RAS": [
                "xkcd:purple",
                "xkcd:light purple",
                "xkcd:light pink",
            ],
            "EESS (passive)": [
                "xkcd:pine green",
                "xkcd:grass green",
                "xkcd:very light green",
            ],
        }
    else:
        raise ValueError(f"Unrecognized color scheme: {name}")
    # Clean up
    if "EESS (active)" not in figure_colors:
        figure_colors["EESS (active)"] = figure_colors["EESS (passive)"]
    if "SRS (active)" not in figure_colors:
        figure_colors["SRS (active)"] = figure_colors["RAS"]
    if "SRS (passive)" not in figure_colors:
        figure_colors["SRS (passive)"] = figure_colors["RAS"]
    return figure_colors


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
