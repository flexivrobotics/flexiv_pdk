"""Sphinx configuration for the Flexiv PDK manual.

Look and layout follow the Flexiv RDK manual
(https://www.flexiv.com/software/rdk/manual/).
"""

import pathlib
import re

# The SDK checkout this manual documents and pulls examples from.
_ROOT = pathlib.Path(__file__).resolve().parents[2]


def _read_version():
    """Reads __version__ without importing flexiv.pdk, which needs generated stubs."""
    init = (_ROOT / "python" / "flexiv" / "pdk" / "__init__.py").read_text()
    match = re.search(r'^__version__\s*=\s*"([^"]+)"', init, re.MULTILINE)
    return match.group(1) if match else "unknown"


project = "Motion Planning software Development Kit (PDK)"
author = "Flexiv Ltd."
# The theme appends the final period.
copyright = "2016–2026 Flexiv Ltd. All Rights Reserved"
release = _read_version()
version = ".".join(release.split(".")[:2])

extensions = [
    "sphinx.ext.autosectionlabel",
    "sphinx_rtd_theme",
]

# Prefix section labels with the document name so headings like "Overview"
# can repeat across pages.
autosectionlabel_prefix_document = True
autosectionlabel_maxdepth = 2

exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

highlight_language = "python"

html_theme = "sphinx_rtd_theme"
# "<page> — <project> documentation", without the version, as in the RDK manual.
html_title = f"{project} documentation"
html_logo = "_static/flexiv_logo.svg"
html_favicon = "_static/flexiv_logo.ico"
html_static_path = ["_static"]
html_css_files = ["style_override.css"]

rst_prolog = f"""
.. |version_full| replace:: {release}
"""
