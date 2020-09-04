"""Some low level routines for (mainly parsing) the FCC tables"""

from IPython.display import display, HTML

def cell2text(cell, munge=False):
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
        result.append(entry)
    if munge:
        return "\n".join(result)
    else:
        return result
    
def first_line(cell):
    return cell2text(cell)[0].strip()

def last_line(cell):
    return cell2text(cell)[-1].strip()

def dump_cells(cells):
    for i, c in enumerate(cells):
        print (f"-------------- Cell {c}")
        print (cell2text(c))

def pretty_print(df):
    return display(HTML(df.to_html().replace(r"\n","<br>")))
