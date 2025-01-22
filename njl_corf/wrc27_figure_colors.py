"""Provides a set of colors for the WRC figures"""

import numpy as np
from numpy.typing import ArrayLike, NDArray
from typing import Optional

import matplotlib.pyplot as plt
from matplotlib.colors import hsv_to_rgb


def colors(
    hue: ArrayLike,
    sat: ArrayLike,
    val: ArrayLike,
) -> NDArray:
    """Get RGB array from hue/sat/val"""
    hue = np.array(hue)
    sat = np.array(sat)
    val = np.array(val)
    hue, sat, val = np.broadcast_arrays(hue, sat, val)
    hsv = np.stack([hue, sat, val], axis=-1)
    print(hsv.shape)
    return hsv_to_rgb(hsv)


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
            "SRS (Passive)": [color_map[12], color_map[13], color_map[14]],
            "SRS (Active)": [color_map[12], color_map[13], color_map[14]],
            "EESS (Passive)": [color_map[8], color_map[9], color_map[11]],
            "EESS (Active)": [color_map[8], color_map[9], color_map[11]],
        }
    elif name == "R&S-a":
        figure_colors = {
            "RAS Overview": "#31437e",
            "EESS Overview": "317e34",
            "5.340": "xkcd:melon",
            "AI": "dimgrey",
            "AI-extra": "lightgrey",
            "RAS": ["#31437e", "#03a1bf", "#96d1de"],
            "EESS (Passive)": ["#317e43", "#03bfa1", "#96ded1"],
            "EESS (Active)": ["#317e43", "#03bfa1", "#96ded1"],
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
            "EESS (Passive)": [
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
            "EESS (Passive)": [
                "xkcd:pine green",
                "xkcd:grass green",
                "xkcd:very light green",
            ],
        }
    else:
        raise ValueError(f"Unrecognized color scheme: {name}")
    # Clean up
    if "EESS (Active)" not in figure_colors:
        figure_colors["EESS (Active)"] = figure_colors["EESS (Passive)"]
    if "SRS (Active)" not in figure_colors:
        figure_colors["SRS (Active)"] = figure_colors["RAS"]
    if "SRS (Passive)" not in figure_colors:
        figure_colors["SRS (Passive)"] = figure_colors["RAS"]
    return figure_colors
