"""Some low level routines for (mainly parsing) the FCC tables"""

def cell2text(cell, munge=False):
    result = [p.text for p in cell.paragraphs]
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
