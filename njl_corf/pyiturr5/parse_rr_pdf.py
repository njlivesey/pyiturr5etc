"""Code for parsing the ITU RadioRegulations PDF file"""

import copy
import functools
import hashlib
import itertools
import re
import warnings
from dataclasses import dataclass
from typing import Optional

import pdfplumber
from pdfplumber.page import Page
from pdfplumber.table import Table
from pint import Unit
from unidecode import unidecode

from njl_corf import ureg

from .allocation_database import AllocationDatabase
from .allocations import NotAllocationError, parse_allocation
from .band_collections import BandCollection
from .bands import Band, parse_bounds
from .apply_specific_footnote_rules import get_all_itu_footnote_based_additions


@dataclass
class RRVersionInfo:
    """Contains all the information specific to a PDF file for a given version of the RR"""

    version: str
    pages_with_spurious_tables: list[str]
    page_range: range


_rr_versions = {
    "42a483709d2bdb5c78f55a312e0c720b17a8e72f": RRVersionInfo(
        version="2024a",
        pages_with_spurious_tables=["RR5-64", "RR5-69"],
        page_range=slice(49, 210),
    ),
}


def parse_rr_file(
    filename: Optional[str] = None,
    skip_additionals: Optional[bool] = False,
) -> AllocationDatabase:
    """Parses the ITU RadioRegulations file and populates an AllocationDatabase"""
    if filename is None:
        filename = "/Users/livesey/doc/itu/RadioRegulations-V1.pdf"
    # Get the sha1 hash of the file, check it's one we know
    sha1_hash = compute_sha1(filename)
    if sha1_hash not in _rr_versions:
        raise ValueError(
            "The suppplied PDF file is not one I know how to handle (bad sha1hash)"
        )
    rr_version_info = _rr_versions[sha1_hash]
    # Read the information from the relevant pages
    print("Reading from pdf file: ", end="")
    with pdfplumber.open(filename) as pdf:
        footnote_definitions = {}
        band_sets = []
        for page in pdf.pages[rr_version_info.page_range]:
            these_bands, these_footnote_definitions, page_tag = parse_page(
                page, rr_version_info=rr_version_info
            )
            print(page_tag + ", ", end="")
            if these_bands is not None:
                band_sets.append(these_bands)
            footnote_definitions |= these_footnote_definitions
    print("organizing, ", end="")
    # The "bands" data is now a list of dictionaries (by region) of BandCollections.
    # Combined them together by region
    keys = band_sets[0].keys()
    band_collections = {}
    for key in keys:
        buffer = list(
            itertools.chain.from_iterable(bands[key].to_list() for bands in band_sets)
        )
        buffer = list(itertools.chain(buffer))
        band_collections[key] = BandCollection(buffer)
    # Now possibly add alll the allocations that come in via footnotes
    if not skip_additionals:
        print("footnote-allocations, ", end="")
        additional_bands = get_all_itu_footnote_based_additions()
        for jurisdiction, collection in band_collections.items():
            for new_band in additional_bands:
                if jurisdiction in new_band.jurisdictions:
                    inserted_band = copy.copy(new_band)
                    inserted_band.jurisdictions = [jurisdiction]
                    collection.append(inserted_band)
            band_collections[jurisdiction] = collection.flatten()
    # Now merge all three regions together
    print("merging, ", end="")
    band_collections["ITU"] = functools.reduce(
        lambda a, b: a.merge(b), band_collections.values()
    )
    print("finishing.")
    # Construct and return a result
    return AllocationDatabase(
        source=f"ITU Radio Regulations version {rr_version_info.version}",
        collections=band_collections,
        footnote_definitions=footnote_definitions,
    )


def parse_page(
    page: Page,
    rr_version_info: RRVersionInfo,
) -> tuple[BandCollection, dict[str]]:
    """Parse the contents of an individual page of the RR

    Note that this code explicitly assumes that pages are self-contained. That is to say
    that neither a table or a footenote definition spans multiple pages.  This enables
    each page to be parsed as a unit.

    Parameters
    ----------
    page : pdfplumber.page.Page
        The page from within the RR PDF file
    rr_verion_info : RRVerionInfo
        Information about this specific version of the RRs. Mainly contains special
        cases etc.

    Returns
    -------
    tuple[BandCollection, dict[str]]
        Any Bands given in a table on the page, and any footnotes on the page
    """
    # Work out whether this is an odd/even page
    odd_page = bool(page.page_number % 2)
    # Set a parameter for the text extraction
    x_tolerance = 1.0
    # Get a the page tag (i.e., formal page number) for the page.  We need this to key
    # some special case decisions, including pages that get falsely flagged as having
    # tables.  So we do a straight forward extract_text first.
    lines = page.extract_text(x_tolerance=x_tolerance).split("\n")
    header_words = lines[0].split(" ")
    page_tag = header_words[-1] if odd_page else header_words[0]
    # Find all the tables from the page, unless this is one of the pages that somehow
    # ends up with tables that shouldn't
    if page_tag not in rr_version_info.pages_with_spurious_tables:
        tables = page.find_tables()
    else:
        tables = list()
    if len(tables) > 1:
        raise ValueError("More than one table on the page")
    # Extract all the text from the page that is not within the table
    if tables:
        table_bbox = tables[0].bbox
        table_top, table_bottom = table_bbox[1], table_bbox[3]
        # Extract lines from the page
        all_lines = page.extract_text_lines(x_tolerance=x_tolerance)
        # Filter out lines that overlap with the table's vertical bounds
        lines = []
        for line in all_lines:
            line_top, line_bottom = line["top"], line["bottom"]
            # Keep lines that are either above or below the table
            if line_bottom < table_top or line_top > table_bottom:
                lines.append(line["text"])
    else:
        lines = page.extract_text(x_tolerance=x_tolerance).split("\n")
    # Convert all the text to plain old ascii
    lines = [unidecode(line) for line in lines]
    # Check that this begins with RR5-
    if not page_tag.startswith("RR5-"):
        raise ValueError("This page is not part of Article 5")
    # Check that the last line is a page number
    if not re.match(r"^- \d+ -$", lines[-1]):
        raise ValueError("Page does not end with a page number")
    # Skip it then, skip the first line too, which is the running header, we verified that above
    lines = lines[1:-1]
    # One more special case for the first real page
    if page_tag == "RR5-6":
        # Skip the next two lines
        lines = lines[2:]
    # Get the allocations from the table
    if tables:
        header_line = lines[0]
        allocations_data = parse_table_contents(
            tables[0],
            header_line=header_line,
            page_tag=page_tag,
        )
        # Skip the table header line
        lines = lines[1:]
    else:
        allocations_data = None
    # Get the footnotes from the text
    footnotes = parse_lines_for_footnotes(lines)
    # We're done
    return allocations_data, footnotes, page_tag


def parse_lines_for_footnotes(lines: list[str]) -> dict[str]:
    """Extract footnote definitions from lines"""
    footnotes = {}
    current_footnote_key = None
    current_footnote_buffer = None
    for line in lines:
        if line.startswith("5."):
            # We want to start a new footnote. Store the one we'be been building up to
            # now if there is one.
            if current_footnote_key:
                footnotes[current_footnote_key] = current_footnote_buffer
            # Start accumulating the new one.
            current_footnote_key, current_footnote_buffer = line.split(" ", maxsplit=1)
        elif current_footnote_key:
            # We're not starting a new footnote, but we are continuing a previous one.
            # That said, check we've not come to the last line of the page.
            if line != lines[-1]:
                current_footnote_buffer += " " + line
        else:
            # Just note a line we don't understand
            warnings.warn(f"Ignoring: {line}")
            pass
    # Store any accumulated footnote
    if current_footnote_key:
        footnotes[current_footnote_key] = current_footnote_buffer
    # Return the result
    return footnotes


def parse_table_contents(
    table: Table,
    header_line: str,
    page_tag: str,
) -> BandCollection:
    """Extract the frequency allocations from a table from the RR pdf file

    Parameters
    ----------
    table : Table
        The table from the page of the RRs
    header_line : str
        The line right above the table that gives the frequency range.
    page_tag : str
        Just used for metadata and (potentialy down the road) for special case tracking.
    """
    frequency_range = parse_bounds(header_line)
    rows = table.extract()
    # Check that the table has the expected headers
    if rows[0] != ["Allocation to services", None, None]:
        raise ValueError(f"Unexpected top row: {rows[0]}")
    if rows[1] != ["Region 1", "Region 2", "Region 3"]:
        raise ValueError(f"Unexpected second row: {rows[1]}")
    # Now build the result
    jurisdictions = [f"ITU-R{i_region+1}" for i_region in range(3)]
    band_collections = {key: BandCollection() for key in jurisdictions}
    for cell_strings in rows[2:]:
        bands = []
        for jurisdiction, cell_text in zip(jurisdictions, cell_strings):
            bands.append(
                parse_cell(
                    text=cell_text,
                    jurisdiction=jurisdiction,
                    units=frequency_range[0].units,
                    metadata={"source_page": page_tag},
                )
            )
        # Now we have to work out what to do if a band is missing.  It could mean just
        # to copy in the one to the left, but perhaps not if the start frequency is
        # already covered by an already created band.  First work out the smallest start
        # frequency of the bands in this batch.
        lower_bounds_found_thus_far = [
            band.bounds[0] for band in bands if band is not None
        ]
        if lower_bounds_found_thus_far:
            start_frequency = min(lower_bounds_found_thus_far)
        else:
            start_frequency = 0.0 * ureg.Hz
        complete_bands = []
        stashed_band = None
        for jurisdiction, band in zip(jurisdictions, bands):
            if band is not None:
                complete_bands.append(band)
                # Record this band for potential reuse if others are missing
                stashed_band = band
            else:
                # See if there is a band in this region that already covers the start frequency of this band
                if band_collections[jurisdiction][start_frequency]:
                    # If so, then we keep this entry as None
                    complete_bands.append(None)
                else:
                    # Otherwise, copy in the band to the left, if we can
                    band = copy.copy(stashed_band)
                    if band is None:
                        warnings.warn("Unable to parse table row, missing band")
                        # raise ValueError("Unable to parse table row, missing band"
                    else:
                        band.jurisdictions = [jurisdiction]
                    complete_bands.append(band)
        # Now add these to the band collections
        for jurisdiction, band in zip(jurisdictions, complete_bands):
            if band is not None:
                band_collections[jurisdiction][band.bounds[0] : band.bounds[1]] = band
    return band_collections


def parse_cell(
    text: str | None,
    units: Unit,
    jurisdiction: str,
    metadata: Optional[dict],
) -> Band:
    """Parse the text in a cell to get a band

    Parameters
    ----------

    text : str
        The text from the table cell (as one single string)
    units : Unit
        kHz, MHz, GHz, etc.
    jurisdiction : str
        R1, R2, R3
    metadata : dict, optional
        Added to the Band entry (e.g., source page)
    """
    # Return none for empty or "None" cells
    if text is None or text == "":
        return None
    lines = text.split("\n")
    # Parse the frequency bounds.  Note that this already includes code to handle the
    # special case for the fisrt row ("Below 8.3")
    frequency_range, remainder = parse_bounds(lines[0], units=units, allow_extra=True)
    # Put the remainder into lines[0]
    lines[0] = remainder.strip()
    # If there is no remainder, skip it
    if lines[0] == "":
        lines = lines[1:]
    # Now work backwards and gather lines that start with "5.", i.e., are just
    # footnotes. Note that there is some risk associated with this approach. For
    # example, see the bottom row of page RR5-58 in the 2024 Edition of the RRs, where
    # this approach will apply 5.286B and 5.286C in Region 2 to the whole band, whereas
    # it looks like it's intended only for the MOBILE-SATTELITE allocation.  However, in
    # that particular case, I think the ITU have messed things up (judging by how it's
    # typeset in the other columns), so I feel OK for us to risk getting things wrong.
    footnote_only_lines = []
    for line in lines[::-1]:
        if line.startswith("5."):
            footnote_only_lines.append(line)
        else:
            break
    # Drop those from the main "lines" buffer
    lines = lines[: -len(footnote_only_lines)]
    # OK, now go through the lines and try to parse them into allocations.  There is a
    # complication here that if a line is non-parseable, it probably means that it
    # should be merged with its predecessor.
    prior_line = None
    allocations = list()
    for line in lines:
        try:
            this_allocation = parse_allocation(line)
        except NotAllocationError:
            # Perhaps we have to wait for a next line
            if prior_line is None:
                continue
            # OK, perhaps this line is actually a suffix to the prior line of text, glob
            # them together and parse again.
            line = prior_line + line
            # Save it again, just in case it turns out it's split over three lines (or
            # more), don't expect so, but keep safe.
            prior_line = line
            this_allocation = parse_allocation(line)
            # Delete the prior insertion of this allocation, don't think we can get here
            # with an empty list, so I'll just let python raise the error if somehow I'm
            # wrong.
            allocations = allocations[:-1]
        # Now add this allocation
        allocations.append(this_allocation)
    # Restrict this to the allocations that actually exist (the first and last "bands" in the table return None)
    allocations = [allocation for allocation in allocations if allocation is not None]
    # Now go through and organize the allocations
    primary_allocations = [
        allocation for allocation in allocations if allocation.primary
    ]
    secondary_allocations = [
        allocation for allocation in allocations if allocation.secondary
    ]
    # Bands constructed from the ITU tables cannot be footnote mentions, they have to be
    # incoroprated another way.
    footnote_mentions = []
    # Now do all the footnote-only lines, gather them into a list of footnotes
    footnotes = " ".join(footnote_only_lines).split(" ")
    # OK, create a Band with the result
    return Band(
        bounds=frequency_range,
        jurisdictions=[jurisdiction],
        primary_allocations=primary_allocations,
        secondary_allocations=secondary_allocations,
        footnote_mentions=footnote_mentions,
        footnotes=footnotes,
        metadata=metadata,
    )


def compute_sha1(file_path):
    sha1 = hashlib.sha1()
    # Read the file in binary mode and in chunks
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha1.update(chunk)
    return sha1.hexdigest()
