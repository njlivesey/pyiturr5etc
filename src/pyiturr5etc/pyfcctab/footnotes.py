"""Import definitions of the ITU and US footnotes from FCC tables"""

import re
import docx
from docx.table import Table


def _document_iterator(source):
    """Iterator for the word document"""
    # pylint: disable-next=protected-access
    elements = source._element.iter()
    for e in elements:
        if isinstance(e, docx.oxml.text.paragraph.CT_P):
            yield docx.text.paragraph.Paragraph(e, source)
        elif isinstance(e, docx.oxml.table.CT_Tbl):
            yield Table(e, source)
        elif isinstance(e, docx.oxml.table.CT_Tc):
            yield "Cell"


def ingestfootnote_definitions(source):
    """Ingest all the footnote definitions from a source document"""
    # Create a dictionary to store all the footnote definitions
    definitions = {}
    # Setup a data structure that notes the text that introduces each
    # block of footnotes in the document, and the regular expressions
    # that match the prefix for a footnote in the corresponding block
    blocks = {
        "International Footnotes": r"^5\.[0-9]+[A-Z]?\w",
        "United States (US) Footnotes": r"^US[0-9]+[A-Z]?\w",
        "Non-Federal Government (NG) Footnotes": r"^NF[0-9]+[A-Z]?\w",
        "Federal Government (G) Footnotes": r"^G[0-9]+[A-Z]?\w",
    }
    # This variable will keep track of what block we're in, currently None
    current_block = None
    # This variable will accumulate the text for the current footnote
    accumulator = []
    # Loop over all the paragraphs in the document
    eof = False
    element_iterator = _document_iterator(source)
    while not eof:
        # This variable will flag when we've got to the end of an entry
        eoe = False
        # This one will flag when we're at the end of the block
        eob = False
        # Now try to get the next element
        try:
            element = next(element_iterator)
        except StopIteration:
            eof = True
            eoe = True
            eob = True
        if isinstance(element, Table):
            accumulator += ["[TABLE]\n"]
        # if type(element) is type("xx"):
        #     print(f"Element is string: {element}")
        if element == "Cell":
            accumulator += ["[Cell:]"]
        # print (f"Read: {type(element)}")
        if isinstance(element, docx.text.paragraph.Paragraph):
            # If this is the first part of a block, move on to that
            # block
            if any([element.text == k for k in blocks]):
                eoe = True
                eob = True
            # Now check to see if we're starting a fotnote
            if current_block is not None:
                # Use regular expression to see if we're starting a
                # footnote
                if re.match(blocks[current_block], element.text):
                    eoe = True

        # Now, if we're on a new element, store the result of the accumulation
        if eoe:
            if current_block is not None:
                accumulator = " ".join(accumulator)
                accumulator = accumulator.replace("\xa0", " ").strip()
                if accumulator != "":
                    name, content = accumulator.split(None, 1)
                    definitions[name] = content.strip()
                accumulator = []
        if eob:
            current_block = element.text
        else:
            # Otherwise add this contents to the accumulator
            try:
                if current_block is not None:
                    accumulator += [element.text]
            except AttributeError:
                # If it's a table, that's been done already
                pass

    return definitions


def sanitize_footnote_name(footnote):
    """Remove any trailing # symbols from footnote

    These symbols denote an artificial "band" created in a BandCollection that flags
    that the band is purely a result of the footnote (see additional_allocations
    module)
    """
    if footnote[-1] != "#":
        return footnote
    else:
        return footnote[:-1]


def footnote2html(footnote, definitions=None, tooltips=True):
    """Convert a footnote to html text, possibly including tooltips"""
    key = sanitize_footnote_name(footnote)
    if definitions is None or tooltips is False:
        return footnote
    if key not in definitions:
        return footnote
    return (
        r'<span id="fcc"><span class="tooltip">'
        + footnote
        + '<span class="tooltiptext">'
        + "<b>"
        + key
        + ":</b>&nbsp"
        + definitions[key]
        + "</span></span></span>"
    )


def footnotedef2html(footnote, definitions):
    """Convert footnote definition to html text"""
    key = sanitize_footnote_name(footnote)
    try:
        return (
            r'<p id="fcc"><b>' + key + ":</b>&nbsp" + definitions[key] + "</span></p>"
        )
    except KeyError:
        return ""
