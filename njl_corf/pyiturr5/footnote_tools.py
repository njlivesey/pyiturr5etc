"""Import definitions of the ITU and US footnotes from FCC tables"""

from typing import Optional


def sanitize_footnote_name(footnote: str) -> str:
    """Remove any trailing # symbols from footnote

    These symbols denote an artificial "band" created in a BandCollection that flags
    that the band is purely a result of the footnote (see additional_allocations
    module)

    Parameters
    ----------
    footnote : str
        The footnote name

    Returns
    -------
    str
        Footnote name with any trailing # characters removed
    """
    if footnote.endswith("#"):
        return footnote[:-1]
    return footnote


def footnote2html(
    footnote: str,
    tooltips: Optional[bool] = True,
    definitions: Optional[dict[str]] = None,
) -> str:
    """Convert a footnote to html text, possibly including tooltips

    Parameters
    ----------
    footnote : str
        The footnote name (e.g., 5.340, US241)
    tooltips : Optional[bool], optional
        If set, add tooltips giving the footnote definitions, in which case the
        "definitions" argument must be supplied. By default True
    definitions : Optional[dict[str]], optional
        A dictionary containing the definitions of all the footnotes, indexed by the
        footnote name.

    Returns
    -------
    str
        HTML text for the foonote, including code for the tooltips if requested.
    """
    # Strip any internal decorations off the footnote key (to enable definition lookup)
    key = sanitize_footnote_name(footnote)
    # If there are no tooltips, then just return the sanitized name
    if not tooltips:
        return footnote
    # OK, we've been asked for tooltips.  Can we provide them?
    if definitions is None:
        raise ValueError("If tooltips requested, footnote defintions must be supplied")
    if key not in definitions:
        raise ValueError(f"No definition found for {footnote}")
    return (
        r'<span id="fcc"><span class="tooltip">'
        + footnote
        + r'<span class="tooltiptext">'
        + r"<b>"
        + key
        + r":</b>&nbsp"
        + definitions[key]
        + r"</span></span></span>"
    )


def footnotedef2html(footnote: str, definitions: dict[str]) -> str:
    """Convert footnote definition to html text

    Parameters
    ----------
    footnote : str
        The name of the footnote (e.g., 5.430, US241)
    definitions : dict[str]
        Footnote definitions, indexed by footnote name

    Returns
    -------
    str
        HTML text for the footnote definition.
    """
    key = sanitize_footnote_name(footnote)
    try:
        return (
            r'<p id="fcc"><b>' + key + ":</b>&nbsp" + definitions[key] + "</span></p>"
        )
    except KeyError as exception:
        raise ValueError(f"Unable to find definition for {footnote}") from exception
