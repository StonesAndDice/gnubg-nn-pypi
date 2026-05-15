# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
import re
from pathlib import Path
import pypandoc


DIR = Path(__file__).parent

project = 'gnubg-nn'
copyright = '2026, David Reay'
author = 'David Reay'
release = '1.1.0'

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
    "gnubg": "./doxygen/xml"
}
breathe_default_project = "gnubg"


# def prepare(app):
#     readme_md = DIR.parent / "README.md"
#     readme_rst = DIR / "readme.rst"
#
#     if readme_md.exists():
#         contents = pypandoc.convert_file(str(readme_md), 'rst')
#         with open(readme_rst, "w") as f:
#             f.write(contents)
#
#
# def setup(app):
#     # Copy the readme in
#     app.connect("builder-inited", prepare)
