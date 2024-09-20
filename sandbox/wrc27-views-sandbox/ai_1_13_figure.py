"""Figure for WRC-27 AI-1.13"""

import numpy as np
import matplotlib.pyplot as plt

import pint
from njl_corf import ureg
from njl_corf.wrc27_figures import set_nas_graphic_style


def ai_1_13():
    """Generate the figure for WRC-27 AI-1.13"""
    set_nas_graphic_style()

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
    #
    ra769_t3_f = np.array([
        325.3, 611, 1_413.5, 2_695, 4_995, 10_650, 15_375, 23_800,
        43_000, 86_000,
    ]) * ureg.MHz
    ra769_t3_pfd = np.array([
     -217, -212, -211, -205, -200, -193, -189, -183, -175, -172,
    ])
    # fmt: on
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
    #
    nrqz_f = pint.Quantity.from_list(nrqz_f)
    nrqz_pfd = pint.Quantity.from_list(nrqz_pfd)
    fig, ax = plt.subplots(figsize=[10.6 / 2.54, 4])
    ax.set_xscale("log")
    ax.set_xlim(10 * ureg.MHz, 275 * ureg.GHz)

    ax.plot(ra769_t1_f, ra769_t1_pfd, ".", label="RA-769 Table 1")
    ax.plot(ra769_t3_f, ra769_t3_pfd, ".", label="RA-769 Table 3")
    ax.plot(nrqz_f, nrqz_pfd, label="NRQZ")
    ax.legend()
