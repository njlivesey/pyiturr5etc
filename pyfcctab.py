"""First attempt at Python code to handle FCC tables"""

import docx
import re
import numpy as np
import astropy.units as units

# --------------------------------------------------------------------- Services
class Service:
    """A service that can be allocated to a band"""
    def __init__(self, name, abbreviation=None, science=False, science_support=False):
        self.name = name.lower()
        if abbreviation is None:
            self.abbreviation = self.name
        self.science = science
        self.science_support = science_support

services_list = [
    Service("AERONAUTICAL-RADIOMAVIGATION"),
    Service("AMATEUR"),
    Service("BROADCASTING-SATELLITE"),
    Service("EARTH EXPLORATION-SATELLITE", abbreviation="EESS", science=True),
    Service("FIXED"),
    Service("FIXED-SATELLITE"),
    Service("INTER-SATELLITE"),
    Service("MARTINE MOBILE"),
    Service("MARTINE MOBILE-SATELLITE"),
    Service("METEOROLOGICAL-SATELLITE", science_support=True),
    Service("MOBILE"),
    Service("MOBILE-SATELLITE"),
    Service("RADIO ASTRONOMY", abbreviation="RAS", science=True),
    Service("RADIOLOCATION"),
    Service("RADIONAVIGATION"),
    Service("SPACE RESEARCH", science_support=True),
    Service("STANDARD FREQUENCY AND TIME SIGNAL-SATELLITE", abbreviation="Time", science_support=True),
]

services = {service.name: service for service in services_list}

# --------------------------------------------------------------------- Bounds
class Bounds:
    """A frequeny bounds"""
    def __init__(self, low, high):
        self.bounds = (low, high)
        self.bandwidth = self.bounds[1] - self.bounds[0]
        self.center = 0.5*(self.bounds[0] + self.bounds[1])

    def __str__(self):
        return f"{self.bounds[0]}-{self.bounds[1]} [{np.round(self.bandwidth,3)}]"

    def __eq__(self, a):
        return self.bounds == a.bounds

    def __ne__(self, a):
        return not (self == a)

    @classmethod
    def parse(cls, text, unit):
        """Turn a string giving a frequency range into a bounds object"""
        re_float = r"[0-9]+(?:\.[0-9]+)?"
        re_bounds = f"^({re_float})-({re_float})$"
        match = re.match(re_bounds, text)
        if match is None:
            raise ValueError(f"Text does not describe a frequency range: {text}")
        return cls(
            float(match.group(1))*unit,
            float(match.group(2))*unit)
    
# --------------------------------------------------------------------- Allocations
class Allocation:
    """An entry allocating a service to a band"""
    def __str__(self):
        """Return a string representation of an Allocation"""
        if self.primary:
            result = self.service.upper()
        else:
            result = self.service.capitalize()
        if self.qualification != "":
            result += f" ({self.qualification})"
        if self.footnotes != "":
            result += " " + " ".join(self.footnotes)
        return (result)

    def __eq__(self,a):
        if self.primary != a.primary:
            return False
        if self.qualification != a.qualification:
            return False
        if self.footnotes != a.footnotes:
            return False
        if self.co_primary != a.co_primary:
            return False
        if self.exclusive != a.exclusive:
            return False
        return True

    def __ne__(self, a):
        return not (self == a)

    @classmethod
    def parse(cls, line):
        """Take a complete line of text and turn into an Allocation"""
        # Work out which service this is.
        service = None
        ll = line.lower()
        for s in services.keys():
            if ll[0:len(s)] == s:
                service = s
        # If not a service then quit
        if service is None:
            return None
        # Look at the remainder of the line
        invocation = line[0:len(service)]
        primary = invocation.isupper()
        remainder = line[len(service):].strip()
        # Anyting in parentheses becomes a qualification
        qualification = ""
        if len(remainder) > 0:
            if remainder[0] == r"(":
                qualification = remainder[1:remainder.index(r")")]
                remainder = remainder[len(qualification)+2:].strip()
        # Now the remainder (if anything) must be footnotes
        footnotes = remainder.split()
        # Create the result
        result = cls()
        result.service = service
        result.qualification = qualification
        result.footnotes = footnotes
        result.primary = primary
        return result
            
# --------------------------------------------------------------------- Bands
class Band:
    """A frequency bounds and the allocations thereto (i.e., contents of a cell in the FCC tables)"""
    def __str__(self):
        """Return a string representation of a Band"""
        result = str(self.bounds) + "\n"
        for a in self.allocations:
            result = result + str(a) + "\n"
        if self.footnotes != "":
            result = result + "\n" + " ".join(self.footnotes) + "\n"
        return (result)

    def __eq__(self,a):
        """Compare two sets of Band information"""
        if self.bounds != a.bounds:
            return False
        if len(self.allocations) != len(a.allocations):
            return False
        for sa, aa in zip(self.allocations, a.allocations):
            if sa != aa:
                return False
        return self.footnotes == a.footnotes
        
    def __ne__(self, a):
        return not (self == a)

    @classmethod
    def parse(cls, cell, unit):
        # Make a string array with the lines of text
        text = [p.text for p in cell.paragraphs]
        # Now work out which lines are continuations of other lines and string them together
        lines = []
        line = None
        for t in text:
            t = t.strip()
            if len(t) == 0:
                continue
            if t[0] == " ":
                if line[-1] != '-':
                    line = line + " " + t.strip()
                else:
                    line = line + t.strip()
            else:
                if line is not None:
                    lines.append(line)
                line = t
        lines.append(line.strip())
        # Now the first line should be a frequency range
        bounds = Bounds.parse(lines[0], unit)
        # Now the remainder will either be allocations, blanks or collections of footnotes
        service_names = services.keys()
        footnotes = None
        allocations = []
        primary_allocations = []
        secondary_allocations = []
        for l in lines[1:]:
            if footnotes is not None:
                raise ValueError("Gone past footnotes and cell not empty")
            if l == "":
                continue
            # See if this line conveys an allocation
            allocation = Allocation.parse(l)
            if allocation is not None:
                if allocation.primary:
                    primary_allocations.append(allocation)
                else:
                    secondary_allocations.append(allocation)
                allocations.append(allocation)
            else:
                footnotes=l.split()
                print (f"***** Footnotes: {footnotes}")
        # Done looping over the lines, so tidy things up.
        if footnotes is None:
            footnotes = []
        for a in allocations:
            if a.primary:
                a.co_primary = len(primary_allocations) > 1
            else:
                a.co_primary = False
            a.exclusive = len(allocations) == 1
            a.bounds = bounds
        # Now create a Band to hold the result
        result = cls()
        result.bounds = bounds
        result.allocations = allocations
        result.primary_allocations = primary_allocations
        result.secondary_allocations = secondary_allocations
        result.footnotes = footnotes
        result._lines = lines
        result._text = text
        return result

def cell2text(cell):
    return [p.text for p in cell.paragraphs]
def first_line(cell):
    return cell2text(cell)[0].strip()
        
def nextRow(fcc_file, n_tables=50, group_len=2):
    """A generator to work through rows of the table"""
    tables = fcc_file.tables
    header_prefix = "Table of Frequency Allocations"
    header_close = "Non-Federal Table"
    for table_index, table in enumerate(tables):
        cells = table._cells
        n_cells = len(cells)
        for n_columns in range(6,12):
            if n_cells % n_columns == 0:
                break
        if n_cells % n_columns != 0:
            raise ValueError(f"Unable to work out number of column in table {table_index} with {n_cells} cells")

        n_rows = n_cells // n_columns
        print (f"============================================================ Table {table_index}")
        print (f"Guessing this is a {n_rows} row table with {n_columns} columns")
        if table_index % group_len == 0:
            # The first table in each group has three header rows
            header = first_line(cells[0])
            if header[0:len(header_prefix)] != header_prefix:
                raise ValueError(f"Unexpected header cell: {header}")
            remainder = header[len(header_prefix):]
            words = remainder.split()
            frequency_unit = units.Unit(words[1])
            # Now find the start of the table proper.
            # To do this get to the last "Non-Federal Table"
            cell_index = 0
            while (first_line(cells[cell_index]) != header_close):
                cell_index += 1
            while (first_line(cells[cell_index]) == header_close):
                cell_index += 1
            # Then skip the final "FCC Rule Part(s)" that follow
            cell_index += 1
            # For the very first table, skip the bit about the lowermost range being unallocted
            if table_index == 0:
                cell_index += n_columns + 1
            # print ("======================================= HEADER")
            # for i, c in enumerate(cells[0:cell_index]):
            #     print (f"------------------ Cell {i}")
            #     print (cell2text(c))
            # print ("======================================= HEADER END")
        else:
            frequency_unit = units.kHz
            cell_index = 0
        # Now go through the rows in this table
        n_data_cells = len(cells) - cell_index
        remainder = n_data_cells % n_columns
        # if remainder != 0:
        #     raise ValueError(f"Remainder of table is of unexpected size ({n_data_cells} cells, a remainder of {remainder}")
        print (f"First cell {cell_index}: {cell2text(cells[cell_index])}")
        if cell_index > 0:
            print (f"Preceding cell {cell_index-1}: {cell2text(cells[cell_index-1])}")
        while cell_index < len(cells):
            row = cells[cell_index:cell_index+n_columns]
            row = [cell2text(r) for r in row]
            yield row, frequency_unit
            cell_index += n_columns
