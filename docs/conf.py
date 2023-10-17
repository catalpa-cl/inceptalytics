import sys
from pathlib import Path
sys.path.insert(0, str((Path(__file__).parent.parent.parent / 'inceptalytics').absolute()))
import inceptalytics

project = 'INCEpTALYTICS'
copyright = '2023, Marius Hamacher, Torsten Zesch'
author = 'Marius Hamacher, Torsten Zesch'
release = f'Version {inceptalytics.__version__}'

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'm2r2',
]

autodoc_member_order = 'groupwise'
napoleon_google_docstring = True

templates_path = ['_templates']
exclude_patterns = []

html_theme = 'furo'
html_static_path = ['_static']
