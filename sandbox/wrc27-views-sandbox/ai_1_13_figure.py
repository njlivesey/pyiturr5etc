"""Figure for WRC-27 AI-1.13"""

import functools
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from matplotlib.patches import Rectangle
from dataclasses import dataclass
from typing import Optional

import pint
from pyiturr5etc import ureg
from pyiturr5etc.wrc27_figure_support import (
    set_nas_graphic_style,
    major_frequency_formatter_with_units,
)


def bandwidth_factor(reference_bandwidth):
    """Give the dB correction to go from reference bandwidth to 1 Hz"""
    return 10.0 * np.log10(reference_bandwidth / ureg.Hz)


def box2rect(x_span, y_span, **kwargs):
    """Return a rectangle for a given x/y span"""
    return Rectangle(
        [x_span[0], y_span[0]],
        width=x_span[1] - x_span[0],
        height=y_span[1] - y_span[0],
        **kwargs,
    )


def get_next_color(ax):
    """Get the next color from the prop cycler and advance it"""
    # pylint: disable-next=protected-access
    return next(ax.get_prop_cycle)["color"]
    return next(ax._get_lines.prop_cycler)["color"]


def table_rr_22_4():
    """Return frequencies, power limits, and services for entries from Table RR 21-4"""
    kHz = ureg.kHz
    MHz = ureg.MHz
    GHz = ureg.GHz
    #
    buffer = [
        [0.5 * (1670 + 1700) * MHz, -133 - bandwidth_factor(1.5 * MHz)],
        #
        [0.5 * (1518 + 1525) * MHz, -150 - bandwidth_factor(4 * kHz)],
        #
        [0.5 * (1525 + 1530) * MHz, -144 - bandwidth_factor(4 * kHz)],
        [0.5 * (1670 + 1710) * MHz, -144 - bandwidth_factor(4 * kHz)],
        [0.5 * (2025 + 2100) * MHz, -144 - bandwidth_factor(4 * kHz)],
        [0.5 * (2200 + 2300) * MHz, -144 - bandwidth_factor(4 * kHz)],
        #
        [0.5 * (2500 + 2690) * MHz, -125 - bandwidth_factor(1 * MHz)],
        #
        [0.5 * (3400 + 4200) * MHz, -142 - bandwidth_factor(4 * kHz)],
        #
        [0.5 * (3400 + 4200) * MHz, -126 - bandwidth_factor(1 * MHz)],
        #
        [0.5 * (4500 + 4800) * MHz, -142 - bandwidth_factor(4 * kHz)],
        [0.5 * (5760 + 5725) * MHz, -142 - bandwidth_factor(4 * kHz)],
        [0.5 * (7250 + 7900) * MHz, -142 - bandwidth_factor(4 * kHz)],
        #
        [0.5 * (5150 + 5216) * MHz, -164 - bandwidth_factor(4 * kHz)],
        #
        [0.5 * (6700 + 6825) * MHz, -127 - bandwidth_factor(1 * MHz)],
        #
        [0.5 * (6825 + 7075) * MHz, -144 - bandwidth_factor(4 * kHz)],
        [0.5 * (6825 + 7075) * MHz, -124 - bandwidth_factor(1 * MHz)],
        #
        [0.5 * (8025 + 8500) * MHz, -140 - bandwidth_factor(4 * kHz)],
        #
        [0.5 * (9900 + 10400) * MHz, -66 - bandwidth_factor(1 * MHz)],
        #
        [0.5 * (10.7 + 11.7) * GHz, -140 - bandwidth_factor(4 * kHz)],
        #
        [0.5 * (10.7 + 11.7) * GHz, -116 - bandwidth_factor(1 * MHz)],
        #
        [0.5 * (10.7 + 11.7) * GHz, -116 - bandwidth_factor(1 * MHz)],
        [0.5 * (11.7 + 12.75) * GHz, -114 - bandwidth_factor(1 * MHz)],
        #
        [0.5 * (12.5 + 12.75) * GHz, -138 - bandwidth_factor(4 * kHz)],
        #
        [0.5 * (13.4 + 13.65) * GHz, -149 - bandwidth_factor(4 * kHz)],
        #
        [0.5 * (17.7 + 19.3) * GHz, -105 - bandwidth_factor(1 * MHz)],
        #
        [0.5 * (17.7 + 19.3) * GHz, -112 - bandwidth_factor(1 * MHz)],
        #
        [0.5 * (19.3 + 19.7) * GHz, -105 - bandwidth_factor(1 * MHz)],
        #
        [0.5 * (21.4 + 22.0) * GHz, -105 - bandwidth_factor(1 * MHz)],
        #
        [0.5 * (22.55 + 23.55) * GHz, -105 - bandwidth_factor(1 * MHz)],
        #
        [0.5 * (24.45 + 24.75) * GHz, -105 - bandwidth_factor(1 * MHz)],
        #
        [0.5 * (24.45 + 24.75) * GHz, -105 - bandwidth_factor(1 * MHz)],
        #
        [0.5 * (25.25 + 27.5) * GHz, -105 - bandwidth_factor(1 * MHz)],
        #
        [0.5 * (27.5 + 30.0) * GHz, -110 - bandwidth_factor(1 * MHz)],
        #
        [0.5 * (31.0 + 31.3) * GHz, -105 - bandwidth_factor(1 * MHz)],
        #
        [0.5 * (34.7 + 35.2) * GHz, -105 - bandwidth_factor(1 * MHz)],
        #
        [0.5 * (31.8 + 32.3) * GHz, -105 - bandwidth_factor(1 * MHz)],
        #
        [0.5 * (32.3 + 33.0) * GHz, -115 - bandwidth_factor(1 * MHz)],
        #
        [0.5 * (37 + 38) * GHz, -105 - bandwidth_factor(1 * MHz)],
        #
        [0.5 * (37.5 + 40) * GHz, -105 - bandwidth_factor(1 * MHz)],
        #
        [0.5 * (40 + 40.5) * GHz, -105 - bandwidth_factor(1 * MHz)],
        #
        [0.5 * (40.5 + 42) * GHz, -105 - bandwidth_factor(1 * MHz)],
        #
        [0.5 * (42 + 42.5) * GHz, -105 - bandwidth_factor(1 * MHz)],
        #
        [0.5 * (47.5 + 47.9) * GHz, -105 - bandwidth_factor(1 * MHz)],
        [0.5 * (48.2 + 48.54) * GHz, -105 - bandwidth_factor(1 * MHz)],
        [0.5 * (49.44 + 50.2) * GHz, -105 - bandwidth_factor(1 * MHz)],
    ]
    #
    f, pfd = zip(*buffer)
    return pint.Quantity.from_list(f), pint.Quantity.from_list(pfd)


def ai_1_13(for_poster: Optional[bool] = False):
    """Generate the figure for WRC-27 AI-1.13"""
    # ---------------------------------------------------- Data
    # RA-769 Table 1
    # fmt: off
    ra769_t1_f = np.array([
        13.385, 25.610, 73.8, 151.525, 325.3, 408.05, 611, 1_413.5,
        1_665, 2_695, 4_995, 10_650, 15_375, 22_355, 23_800, 31_550,
        43_000, 89_000, 150_000, 224_000,270_000,
    ]) * ureg.MHz
    ra769_t1_pfd = np.array([
        -248, -249, -258, -259, -258, -255, -253, -255, -251, -247,
        -241, -240, -233, -231, -233, -228, -227, -228, -223, -218, -216,
    ])
    # RA-769 Table 3
    ra769_t3_f = np.array([
        325.3, 611, 1_413.5, 2_695, 4_995, 10_650, 15_375, 23_800,
        43_000, 86_000,
    ]) * ureg.MHz
    ra769_t3_pfd = np.array([
     -217, -212, -211, -205, -200, -193, -189, -183, -175, -172,
    ])
    # fmt: on
    # NRQZ
    f_end = 1 * ureg.THz
    nrqz_f_boundaries = pint.Quantity.from_list(
        [
            1e-3 * ureg.Hz,
            54 * ureg.MHz,
            108 * ureg.MHz,
            470 * ureg.MHz,
            1000 * ureg.MHz,
            f_end,
        ]
    )
    nrqz_panel_pfds = (
        np.array(
            [1e-8, 1e-12, 1e-14, 1e-17, (f_end.to(ureg.GHz).magnitude) ** 2 * 1e-17]
        )
        * ureg.W
        / ureg.m**2
    )
    nrqz_f = []
    nrqz_pfd = []
    Wm2Hz = ureg.W / ureg.m**2 / ureg.Hz
    delta_f = 20 * ureg.kHz
    for i in range(len(nrqz_f_boundaries) - 1):
        pfd = (nrqz_panel_pfds[i] / delta_f).to(Wm2Hz)
        nrqz_f += [nrqz_f_boundaries[i], nrqz_f_boundaries[i + 1]]
        nrqz_pfd += [10.0 * np.log10(pfd / Wm2Hz)] * 2
    # Delete the penultimate point to get the diagonal line
    del nrqz_f[-2]
    del nrqz_pfd[-2]
    nrqz_f = pint.Quantity.from_list(nrqz_f)
    nrqz_pfd = pint.Quantity.from_list(nrqz_pfd)
    # AI
    ai_f = [694 * ureg.MHz, 2.7 * ureg.GHz]
    # SCS, numbers from Harvey's filing, but subtract 60 dB to go from dB(W/m2/MHz) to
    # dB(W/m2/Hz)
    scs_f = ai_f
    scs_pfd = np.array([-89, -80]) - 60.0
    # Do some FSS numbers, taken from Table RR 21-4
    trr214_f, trr214_pfd = table_rr_22_4()
    # fss_f = pint.Quantity.from_list([10.7 * ureg.GHz, 11.7 * ureg.GHz])
    # fss_pfd = -114 - bandwidth_factor(1 * ureg.MHz)

    # ---------------------------------------------------- Figure
    # Define the figure style
    set_nas_graphic_style()
    fig, ax = plt.subplots(figsize=[10.6 / 2.54, 4], layout="constrained")
    # x-axis scale etc.
    # Set up the x-axis ticks
    ax.set_xscale("log")
    ax.set_xlim((10 * ureg.MHz).to(ureg.Hz), (275 * ureg.GHz).to(ureg.Hz))
    unit_formatter = FuncFormatter(
        functools.partial(
            major_frequency_formatter_with_units,
            supplied_unit=None,
        )
    )
    ax.xaxis.set_major_formatter(unit_formatter)
    ax.set_xlabel("")
    # y-axis scale etc.
    ax.set_ylabel(r"Spectral power flux density / dB(W/(m$^2$ Hz))")
    #
    # Show the lines
    ax.plot(ra769_t1_f, ra769_t1_pfd, ".", label="RA-769 Table 1")
    ax.plot(ra769_t3_f, ra769_t3_pfd, ".", label="RA-769 Table 3")
    ax.plot(nrqz_f, nrqz_pfd, label="NRQZ")
    # Shade the AI-1.13 region
    ax.axvspan(*ai_f, color="lightgrey", label="AI-1.13")
    # SCS
    patch = box2rect(
        scs_f,
        scs_pfd,
        label="Spaceborne IMT",
        facecolor="tab:Red",
        edgecolor="none",
    )
    ax.add_patch(patch)
    # Table RR 21-4
    ax.plot(
        trr214_f,
        trr214_pfd,
        marker=".",
        color="tab:purple",
        linestyle="none",
        label="RR Table 21-4",
    )
    # Add the legend
    ax.legend(loc="center", bbox_to_anchor=(0.5, -0.15), ncol=3, frameon=False)
    # --------------------------------- Any specifics for posters
    if for_poster:
        # Set axis facecolor to opaque white
        ax.set_facecolor("white")
        # Set figure transparency by adjusting the facecolor alpha
        fig.patch.set_alpha(0.0)  # Fully transparent figure background
