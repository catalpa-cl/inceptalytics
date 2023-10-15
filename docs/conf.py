# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information


import sys
from pathlib import Path
sys.path.insert(0, str((Path(__file__).parent.parent.parent / 'inceptalytics').absolute()))

project = 'INCEpTALYTICS'
copyright = '2023, Marius Hamacher, Torsten Zesch'
author = 'Marius Hamacher, Torsten Zesch'
release = f'Version 0.1.1'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'm2r2',
]

# this needs proper fixing
autodoc_mock_imports = ['cassis', 'numpy', 'pycaprio', 'krippendorff', 'sklearn', 'pandas']
napoleon_google_docstring = True


templates_path = ['_templates']
exclude_patterns = []



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'furo'
html_static_path = ['_static']
