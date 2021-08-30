# Inception Analytics

An easy-to-use API for analyzing [Inception](https://inception-project.github.io) annotation projects.
* We parse an XMI export of an Inception annotation project and provide easy access to (most) of the underlying data including annotators, source files, etc.
* We provide *recipes* for computing project statistics, confusion matrices, inter-annotator-agreement, or plotting progress reports.

## Basic Usage

```python
from analytics import Project
from utils import construct_feature_path

file = "data/Example_Project_POS.zip"

# load project
project = Project.from_zipped_xmi(file)

# print all annotator names
for annotator in project.annotators:
    print(annotator)

# create a view 
pos_type = "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.POS"

view = project.select(
        annotation=construct_feature_path(pos_type, "coarseValue"), 
        annotators=project.annotators, 
        source_files=project.source_file_names
)

print('# pos annotations in view:', len(view.annotations))

print('IAA Krippendorff: ', view.iaa())
```

## GUI
We also provide a basic [Streamlit](http://streamlit.io) web application as a starting point for a dashboard that fits your needs.
