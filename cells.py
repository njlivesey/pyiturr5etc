"""A python module for handling cells from the main tables"""

import astropy.units as units
import copy
import re

from .utils import cell2text, text2lines


class FCCCell(object):
    """A class for holding cells within the main FCC tables"""

    def __init__(
            self, text, unit=None,
            ordered_row=None, ordered_column=None,
            logical_column=None, page=None):
        """Create an FCCCell object"""
        self.text = text
        self.lines = text2lines(text)
        self.unit = unit
        self.ordered_row = ordered_row
        self.ordered_column = ordered_column
        self.logical_column = logical_column
        self.page = page

    def __eq__(self, a):
        """Compare the text content of two cells, and their logical column"""
        assert self.logical_column == a.logical_column, "Asked to compare two cells from different columns"
        return self.lines == a.lines

    def append(self, a):
        """Append text from one cell into another"""
        def _append_items(a,b):
            if a is None and b is None:
                return []
            elif a is None:
                return b
            elif b is None:
                return a
            else:
                return a + b
        self.text = _append_items(self.text, a.text)
        self.lines = _append_items(self.lines, a.lines)

    def is_band_start(self):
        """Return True if this cell starts a new band"""
        from .bands import Band, NotBandError
        try:
            band = Band.parse(self)
            return True
        except NotBandError:
            return False

    def is_empty(self):
        """Return true if the cell should be ignored for one reason or another"""
        if self.lines is None:
            return True
        if self.lines == ["(See previous page)"]:
            return True
        if self.lines == [""]:
            return True
        return False

    def clean(self):
        """Remove specific detritis from the cells"""
        if self.lines is None:
            return self
        new_lines = []
        re_page = r"^Page +[0-9]+$"
        omissions = [
            "(See previous page)",
            ]
        for line in self.lines:
            # Skip page numbers
            if re.search(re_page, line):
                continue
            if "Page" in line:
                raise ValueError(f"Missed <{line}>")
            if any([line==omission for omission in omissions]):
                continue
            new_lines.append(line)
        result = copy.copy(self)
        result.lines = new_lines
        return result
        
