"""Some low level routines for (mainly parsing) the FCC tables"""

from IPython.display import display, HTML
import pandas as pd

from docx.table import _Cell as DocxCell


def cell2text(cell: DocxCell, munge: bool = False):
    """Convert an FCC cell to ttext for debugging

    Parameters
    ----------
    cell : FCCCell
        Input from Word document
    munge : bool, optional
        Return result as single string (otherwise list)

    Returns
    -------
    result : str or list[str]
    """
    result = []
    for p in cell.paragraphs:
        entry = p.text
        # Possibly strip \n's off the start
        if len(result) == 0:
            try:
                while entry[0] == "\n":
                    entry = entry[1:]
            except IndexError:
                pass
        # Also possibly strip \n's off the end
        try:
            while entry[-1] == "\n":
                entry = entry[:-1]
        except IndexError:
            pass
        result.append(entry)
    if munge:
        return "\n".join(result)
    return result


def first_line(cell: DocxCell):
    """Return the first line of text corresponding to a cell"""
    return cell2text(cell)[0].strip()


def last_line(cell: DocxCell):
    """Return the last line of text corresponding to a cell"""
    return cell2text(cell)[-1].strip()


def text2lines(text):
    """Handle continuation lines for text (ending hyphens I think)"""
    if text is None:
        return None
    lines = []
    line = None
    for t in text:
        if len(t) != 0:
            t0 = t[0]
        else:
            t0 = ""
        is_continuation = t0 == " "
        if line is None:
            is_continuation = False
        else:
            if len(line) == 0:
                is_continuation = False
        if is_continuation:
            # pylint: disable-next=unsubscriptable-object
            if line[-1] != "-":
                line = line + " " + t.strip()
            else:
                line = line + t.strip()
        else:
            if line is not None:
                lines.append(line)
            line = t.strip()
    if line is not None:
        lines.append(line.strip())
    return lines


def dump_cells(cells: list[DocxCell]):
    """Simply dump all the cells as text"""
    for i, c in enumerate(cells):
        print(f"-------------- Cell {i}")
        print(cell2text(c))


def pretty_print(df: pd.DataFrame):
    """Get nice text version of dataframe"""
    return display(HTML(df.to_html().replace(r"\n", "<br>")))
