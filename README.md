# Inception Analytics

An easy-to-use API for analyzing [INCEpTION](https://inception-project.github.io) annotation projects.
* We parse an XMI export of an Inception annotation project and provide easy access to (most) of the underlying data including annotators, source files, etc.
* We provide *recipes* for computing project statistics, confusion matrices, inter-annotator-agreement, or plotting progress reports.

## Installation

```bash
git clone https://github.com/zesch/inception-analytics.git
./install.sh
```

## Basic Usage

```python
from analytics import Project

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

To run the dashbord
```bash
git clone https://github.com/zesch/inception-analytics.git
./install.sh
./run_streamlit.sh
```
The application should be available in your browser under `http://localhost:8501`. The URL is also printed on the shell.

![Screenshot of dashboard](img/dashboard.png?raw=true "Dashboard")
