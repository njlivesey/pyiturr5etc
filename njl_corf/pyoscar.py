"""A module for reading and handling the WMO OSCAR frequency database

The input is the CSV file generated from the OSCAR website
"""

import pandas as pd

import intervaltree


def read(filename: str = None) -> intervaltree.IntervalTree:
    """Read the data in the OSCAR CSV file and store in IntervalTree

    Parameters
    ----------
    filename : str, optional
        File to read

    Returns
    -------
    intervaltree.IntervalTree
        Result
    """
    if filename is None:
        filename = (
            "/Users/livesey/corf/data/"
            "Oscar-Satellite-Frequencies-Earth-observation-MW-frequencies-2023-11-14.xlsx"
        )
    data = pd.read_excel(filename)
