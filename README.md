<!-- Header block for project -->
<hr>

<div align="center">

<!-- [INSERT YOUR LOGO IMAGE HERE (IF APPLICABLE)] -->
<!-- ☝️ Replace with your logo (if applicable) via ![](https://uri-to-your-logo-image) ☝️ -->
<!-- ☝️ If you see logo rendering errors, make sure you're not using indentation, or try an HTML IMG tag -->

<h1 align="center">PyITURR5etc</h1>
<!-- ☝️ Replace with your repo name ☝️ -->

</div>

<pre align="center">Python library for ingesting querying and reporting on frequency allocation tables.</pre>
<!-- ☝️ Replace with a single sentence describing the purpose of your repo / proj ☝️ -->

<!-- Header block for project -->

<!-- [INSERT YOUR BADGES HERE (SEE: https://shields.io)]  -->
[![SLIM](https://img.shields.io/badge/Best%20Practices%20from-SLIM-blue)](https://nasa-ammos.github.io/slim/)
<!-- ☝️ Add badges via: https://shields.io e.g. ![](https://img.shields.io/github/your_chosen_action/your_org/your_repo) ☝️ -->

<!-- [INSERT SCREENSHOT OF YOUR SOFTWARE, IF APPLICABLE] -->

<!-- ☝️ Screenshot of your software (if applicable) via ![](https://uri-to-your-screenshot) ☝️ -->

The package is a Python library for dealing with frequency allocations within the radio spectrum, and for gathering and interpreting related information.  Specifically, it reads the frequency allocation tables from Article 5 of the ITU-R Radio Regulations.  It can also read comparable information (including US allocations) from the FCC tables.  It can also read an interpret information from the OSCAR database of Earth-observing spacecraft.

Included are the routines that made plots for the (US) National Academies of Science, Engineering, and Medicine report ["Views of the U.S. National Academies of Sciences, Engineering, and Medicine on Agenda Items at Issue at the World Radiocommunication Conference 2027"](https://doi.org/10.17226/28596) (2025).  It is hoped that this package will be of broad use for people involved in the realm of radio spectrum management.


<!-- example links>
[Website](INSERT WEBSITE LINK HERE) | [Docs/Wiki](INSERT DOCS/WIKI SITE LINK HERE) | [Discussion Board](INSERT DISCUSSION BOARD LINK HERE) | [Issue Tracker](INSERT ISSUE TRACKER LINK HERE)
-->

## Features

* Reads and ingests the ITU-R frequency allocation tables into a custom database
* Rigidly ensures that the correct version of tables is read based on the sha1-hash of the pdf file
* Can also read the FCC tables (currently from an outdated Word file), though the ITU-R document should be considered the definitive source for the international allocations, and the FCC document is not kept up to date in that regard.
* Reads information extracted from the WMO OSCAR database of frequencies used by Earth-observing satellites

## Contents

* [Quick Start](#quick-start)
* [Changelog](#changelog)
* [FAQ](#frequently-asked-questions-faq)
* [Contributing Guide](#contributing)
* [License](#license)
* [Support](#support)

## Quick Start

This guide provides a quick way to get started with our project.  Fuller documentation is pending.
<!-- Please see our [docs]([INSERT LINK TO DOCS SITE / WIKI HERE]) for a more comprehensive overview. -->

### Requirements

* Requires Python 3 (not sure which version)
* Makes heavy use of the `IntervalTree` package as the storage mechanism for all the bands in question (a tree-based storage mechanism that allows storage and manipulation of different frequency ranges)
* Uses `numpy`, `Pint`, `astropy` (perhaps not needed any more)
* Uses `pdfplumber` and `python-docx` for reading and parsing PDF and Word files
* Some other standardish libraries (`Pandas` etc.)
  
<!-- ☝️ Replace with a numbered list of your requirements, including hardware if applicable ☝️ -->

### Setup Instructions

1. Currently only supports installation via GitHub etc., followed by

```pip install -e .```
   
<!-- ☝️ Replace with a numbered list of how to set up your software prior to running ☝️ -->

### Run Instructions

1. More detailed instructions pending

<!-- ☝️ Replace with a numbered list of your run instructions, including expected results ☝️ -->

### Usage Examples

* Examples pending

<!-- ☝️ Replace with a list of your usage examples, including screenshots if possible, and link to external documentation for details ☝️ -->

<!-- ### Build Instructions (if applicable)

1. [INSERT STEP-BY-STEP BUILD INSTRUCTIONS HERE, WITH OPTIONAL SCREENSHOTS] -->

<!-- ☝️ Replace with a numbered list of your build instructions, including expected results / outputs with optional screenshots ☝️ -->

<!-- ### Test Instructions (if applicable)

1. [INSERT STEP-BY-STEP TEST INSTRUCTIONS HERE, WITH OPTIONAL SCREENSHOTS] -->

<!-- ☝️ Replace with a numbered list of your test instructions, including expected results / outputs with optional screenshots ☝️ -->

## Changelog

See our [CHANGELOG.md](CHANGELOG.md) for a history of our changes.

<!-- See our [releases page]([INSERT LINK TO YOUR RELEASES PAGE]) for our key versioned releases. -->

<!-- ☝️ Replace with links to your changelog and releases page ☝️ -->

<!-- ## Frequently Asked Questions (FAQ)

[INSERT LINK TO FAQ PAGE OR PROVIDE FAQ INLINE HERE] -->

<!-- example link to FAQ PAGE>
Questions about our project? Please see our: [FAQ]([INSERT LINK TO FAQ / DISCUSSION BOARD])
-->

<!-- example FAQ inline format>
1. Question 1
   - Answer to question 1
2. Question 2
   - Answer to question 2
-->

<!-- example FAQ inline with no questions yet>
No questions yet. Propose a question to be added here by reaching out to our contributors! See support section below.
-->

<!-- ☝️ Replace with a list of frequently asked questions from your project, or post a link to your FAQ on a discussion board ☝️ -->

## Contributing


Interested in contributing to our project? Please see our: [CONTRIBUTING.md](CONTRIBUTING.md)

<!-- example inline contributing guide>
1. Create an GitHub issue ticket describing what changes you need (e.g. issue-1)
2. [Fork](INSERT LINK TO YOUR REPO FORK PAGE HERE, e.g. https://github.com/my_org/my_repo/fork) this repo
3. Make your modifications in your own fork
4. Make a pull-request in this repo with the code in your fork and tag the repo owner / largest contributor as a reviewer

**Working on your first pull request?** See guide: [How to Contribute to an Open Source Project on GitHub](https://kcd.im/pull-request)
-->


For guidance on how to interact with our team, please see our code of conduct located at: [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)

For guidance on our governance approach, including decision-making process and our various roles, please see our governance model at: [GOVERNANCE.md](GOVERNANCE.md)

## License

See our: [LICENSE](LICENSE)
<!-- ☝️ Replace with the text of your copyright and license, or directly link to your license file ☝️ -->

## Support

Key points of contact are: [Nathaniel Livesey](mailto:Nathaniel.J.Livesey@jpl.nasa.gov)