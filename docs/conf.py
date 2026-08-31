# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
import re
from pathlib import Path


DIR = Path(__file__).parent

# Same lightweight approach src/_build_utils/_version.py already uses (not
# tomllib: that's Python 3.11+, this project supports 3.10+, and this is
# the only place in this file a TOML parser would be needed).
_pyproject = (DIR.parent / "pyproject.toml").read_text()
release = re.search(r'^version = "([^"]+)"', _pyproject, re.MULTILINE).group(1)

project = 'gnubg-nn'
copyright = '2026, Stones And Dice'
author = 'David Reay'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ["myst_parser","breathe"]
source_suffix = {".rst": "restructuredtext", ".md": "markdown"}
templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_rtd_theme"
html_static_path = ['_static']


# -- Options for breathe
breathe_projects = {
    "gnubg-nn": "./doxygen/xml"
}
breathe_default_project = "gnubg-nn"
