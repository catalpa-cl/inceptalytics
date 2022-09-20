# INCEpTALYTICS

[![DOI](https://zenodo.org/badge/379546031.svg)](https://zenodo.org/badge/latestdoi/379546031)

An easy-to-use API for analyzing [INCEpTION](https://inception-project.github.io) annotation projects.
* We parse an XMI export of an Inception annotation project and provide easy access to (most) of the underlying data including annotators, source files, etc.
* We provide *recipes* for computing project statistics, confusion matrices, inter-annotator-agreement, or plotting progress reports.

## Installation

INCEpTALYTICS is on [PyPi](https://pypi.org/). To install it run:

```bash
pip install inceptalytics
```

## Basic Usage

```python
from inceptalytics import Project

file = "data/Example_Project_POS.zip"

# load project
project = Project.from_zipped_xmi(file)

# print all annotator names
for annotator in project.annotators:
    print(annotator)

# create a view 
pos_type = "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.POS"

view = project.select(
        annotation=project.feature_path(pos_type, "coarseValue"), 
        annotators=project.annotators, 
        source_files=project.source_file_names
)

print('# pos annotations in view:', len(view.annotations))

print('IAA Krippendorff: ', view.iaa())
```

## Dashboard
We also provide a basic [Streamlit](http://streamlit.io) web application as a starting point for a dashboard that fits your needs.

To run the dashboard, you will have to install some additional dependencies.

```bash
pip install -r examples/streamlit_requirements.txt
```

Afterwards, you can run the dashboard.

```bash
streamlit run examples/dashboard.py
```

The application should be available in your browser under `http://localhost:8501`. The URL is also printed on the shell.

![Screenshot of dashboard](https://raw.githubusercontent.com/ltl-ude/inception-analytics/main/img/dashboard.png "Dashboard")

## Changelog

### Version 0.1.0

* Project is now on [PyPi](https://pypi.org/project/inceptalytics/).
* Projects can now be loaded using the [INCEpTION's Remote API](https://inception-project.github.io//releases/0.11.2/docs/admin-guide.html#sect_remote_api) using `Project.from_remote`.
* Removed plotting functionality from INCEpTALYTICS and moved it to the dashboard under example. 

### Version 0.1.1

* Added sanity checks and input normalisation to `Project.from_remote`.
* Updated `Project.from_remote` to be compatible with the latest version of [pycaprio](https://pypi.org/project/pycaprio/).
