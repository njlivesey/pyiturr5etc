"""Produces an overview graphic for the WRC 27/31 agenda items"""

from dataclasses import dataclass

import matplotlib.pyplot as plt
import numpy as np
import pint
from matplotlib.patches import Rectangle
import matplotlib

from njl_corf import pyfcctab, ureg, wrc27_views


def ensure_visible_bandwidth(
    start: pint.Quantity,
    stop: pint.Quantity,
    minimum_fractional_bandwidth: float = None,
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
    mimimum_fractional_bandwidth : float, optional
        Minimum fractional bandwidth to ensure.  If a band is narrower than that, then
        the code will move start and stop outwards from the center to meet this minimum
        fractional bandwidth.

    Returns
    -------
    tuple[pint.Quantity, pint.Quantity] - start, stop
        start and stop frequencies adjusted if/as needed.
    """
    # Set the default
    if minimum_fractional_bandwidth is None:
        minimum_fractional_bandwidth = 0.02
    # Compute the center, use geometric mean given the log scale
    center = np.sqrt(start * stop)
    # Compute fractional bandwidth
    fractional_bandwidth = (stop - start) / center
    # If we're not meeting the minimum, move start and stop outwards from the center (in
    # a logarithmic sense).
    if fractional_bandwidth < minimum_fractional_bandwidth:
        start = center * (1.0 - 0.5 * minimum_fractional_bandwidth)
        stop = center * (1.0 + 0.5 * minimum_fractional_bandwidth)
    return start, stop


def show_band(
    start: pint.Quantity,
    stop: pint.Quantity,
    row: int,
    slot: int,
    ax: plt.Axes,
    minimum_fractional_bandwidth: float = None,
    **kwargs,
):
    """Show a band as a rectangle patch"""
    slot_centers = np.linspace(0.5, -0.5, 6)[1:-1]
    slot_widths = [0.175] * len(slot_centers)
    y_bottom = row - slot_centers[slot] - 0.5 * slot_widths[slot]
    # For really small bands, make them bigger
    start, stop = ensure_visible_bandwidth(
        start,
        stop,
        minimum_fractional_bandwidth=minimum_fractional_bandwidth,
    )
    # Draw the rectangle
    patch = Rectangle(
        [start, y_bottom],
        width=(stop - start),
        height=slot_widths[slot],
        **kwargs,
    )
    ax.add_patch(patch)


@dataclass
class BarType:
    """Contains the information describing a family of bars"""

    condition: str
    slot: int
    color: str


def wrc27_overview_figure(
    allocation_tables: pyfcctab.FCCTables = None,
    frequency_range: list[pint.Quantity] = None,
    wrc: str = None,
    ax: plt.Axes = None,
    no_show: bool = False,
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
        "EESS": BarType(
            condition=lambda band: band.has_allocation(
                "Earth Exploration-Satellite (Passive)*"
            )
            or band.has_allocation("Earth Exploration-Satellite (Active)*"),
            slot=1,
            color="xkcd:dark sky blue",
        ),
        "RAS": BarType(
            condition=lambda band: band.has_allocation("Radio Astronomy*")
            or band.has_allocation("Space Research (Passive)*")
            or band.has_allocation("Space Research (Active)*"),
            slot=2,
            color="xkcd:soft green",
        ),
        "5.340": BarType(
            condition=lambda band: band.has_footnote("5.340"),
            slot=3,
            color="xkcd:melon",
        ),
    }
    # Set plot defaults
    matplotlib.rcParams["font.family"] = "serif"
    matplotlib.rcParams["font.serif"] = ["Palatino"]
    matplotlib.rcParams["font.size"] = 9
    matplotlib.rcParams["pdf.fonttype"] = 42
    matplotlib.rcParams["ps.fonttype"] = 42
    # Now embark upon the figure, set up the figure itself
    if ax is None:
        fig, ax = plt.subplots(figsize=[6, len(ai_info) * 0.18], layout="constrained")
    # -------------------------------- x-axis
    if frequency_range is None:
        frequency_range = [1_000_000 * ureg.Hz, 1_000_000_000_000 * ureg.Hz]
    # Choose a default for the minimum fractional bandwidth
    minimum_fractional_bandwidth = (
        np.log10(frequency_range[1] / frequency_range[0]) * 0.005
    )
    ax.set_xlim(*frequency_range)
    ax.set_xscale("log")
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
    ax.tick_params(axis="x", which="both", direction="out")
    ax.set_xlabel("")
    # Add vertical grid lines
    for f_line in x_ticks:
        # Skip if we're right at the left/right edge (not the confusing meaning of "in"
        # below, it's the range as a list, not a true range.
        if f_line not in frequency_range:
            ax.axvline(f_line, color="grey", linewidth=0.5)
    # -------------------------------- y-axis
    y_range = [len(ai_info) - 0.5, -0.5]
    ax.set_ylim(y_range[0], y_range[1])
    y_labels = [key.split(" ")[1] for key in ai_info.keys()]
    ax.set_yticks(np.arange(len(ai_info)), labels=y_labels)
    ax.yaxis.set_minor_locator(plt.NullLocator())
    #
    # -------------------------------- Actual figure
    # OK, loop over the agenda items
    for i_y, (ai, bands) in enumerate(ai_info.items()):
        # Draw the horiztonal separator lines, a thicker one to separate the two WRCs
        if i_y > 0:
            if ai == "WRC-31 AI-2.1":
                linewidth = 1.5
            else:
                linewidth = 0.5
            ax.axhline(i_y - 0.5, linewidth=linewidth, color="lightgrey")
        # If there are no specific bands for this AI, then we're done at this point
        if bands is None:
            continue
        # Create a buffer to hold the impacted science bands
        bar_buffer = {key: pyfcctab.BandCollection() for key in bars}
        for band in bands:
            # Draw this particular band
            show_band(
                band.start,
                band.stop,
                row=i_y,
                slot=0,
                facecolor="dimgrey",
                ax=ax,
                minimum_fractional_bandwidth=minimum_fractional_bandwidth,
                edgecolor="none",
            )
            for key, bar_info in bars.items():
                relevant_bands = allocation_tables.itu.get_bands(
                    band.start,
                    band.stop,
                    condition=bar_info.condition,
                    adjacent=True,
                )
                bar_buffer[key] = bar_buffer[key].union(
                    pyfcctab.BandCollection(relevant_bands)
                )
        for key, science_bands in bar_buffer.items():
            bar_info = bars[key]
            for band in science_bands:
                show_band(
                    band.bounds[0],
                    band.bounds[1],
                    row=i_y,
                    slot=bar_info.slot,
                    ax=ax,
                    minimum_fractional_bandwidth=minimum_fractional_bandwidth,
                    facecolor=bar_info.color,
                )
    if not no_show:
        plt.show()
