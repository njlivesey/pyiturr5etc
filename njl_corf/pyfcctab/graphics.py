"""Some graphics routines to visualize spectra"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.collections import PatchCollection
from matplotlib.patches import Rectangle
from astropy.visualization import quantity_support

from .fccpint import ureg


def plot_bands(*args, skip_empty=False):
    """Do the iconic frequncy plot"""

    spans = [
        [30 * ureg.kHz, 300 * ureg.kHz],
        [0.3 * ureg.MHz, 3 * ureg.MHz],
        [3 * ureg.MHz, 30 * ureg.MHz],
        [30 * ureg.MHz, 300 * ureg.MHz],
        [0.3 * ureg.GHz, 3 * ureg.GHz],
        [3 * ureg.GHz, 30 * ureg.GHz],
        [30 * ureg.GHz, 300 * ureg.GHz],
    ]

    if skip_empty:
        relevant_spans = []
        for span in spans:
            span_flag = False
            for collection in args:
                bands = collection[span[0] : span[1]]
                if len(bands) != 0:
                    span_flag = True
            if span_flag:
                relevant_spans.append(span)
        spans = relevant_spans

    # pylint: disable-next=unused-variable
    fig, axes = plt.subplots(len(spans), figsize=(14, 12.0 * len(spans) / 7.0))
    plt.subplots_adjust(hspace=0.4)
    quantity_support()

    for panel, span in enumerate(spans):
        # Identify panel
        span = spans[panel]
        ax = axes[panel]
        # Set up axes
        ax.set_ylim([0, len(args)])
        ax.set_xlim([span[0], span[1]])
        ax.set_xscale("log")
        # Do x ticks
        xticks = (
            np.array([3, 4, 5, 6, 7, 8, 9, 10, 15, 20, 25, 30])
            / 3.0
            * span[0].magnitude
        )
        xticklabels = [
            str(t) + " " + str(span[0].units) for t in np.around(xticks, 1).tolist()
        ]
        for i in [3, 5, 6]:
            xticklabels[i] = ""
        ax.set_xticks(xticks)
        ax.set_xticklabels(xticklabels)
        # Prepare y ticks
        ax.set_yticks(np.arange(len(args)) + 0.5)
        yticklabels = []

        for tier, bands in enumerate(args):
            these_bands = bands[span[0] : span[1]]
            try:
                yticklabels.append(bands.metadata["label"])
            except KeyError:
                yticklabels.append(f"Row {tier}")
            boxes = []
            for b in these_bands:
                x = [v.to(span[0].units).magnitude for v in b.bounds]
                y = tier + 0.1
                rect = Rectangle((x[0], y), x[1] - x[0], 0.8)
                boxes.append(rect)
                patches = PatchCollection(boxes, color=f"C{tier}")
                axes[panel].add_collection(patches)
        ax.set_yticklabels(yticklabels)
