# Inception Analytics

## Basic Usage

```python
from analytics import Project

# loading a project into memory
project = Project('path/to/export.zip')

# getting annotations
project.annotations_of_layer('cassis.Token')
>>> [
    (cassis_Token(...), 'file_0.txt', 'annotator_a'),
    (cassis_Token(...), 'file_0.txt', 'annotator_b'),
    ...,
    (cassis_Token(...), 'file_999.txt', 'annotator_f')
]

# omit source file and annotator information
project.annotations_of_layer('cassis.Token', return_info=False)
>>> [
    cassis_Token(...),
    cassis_Token(...),
    ...,
    cassis_Token(...)
]

# query for some custom layer
project.annotations_of_layer('webanno.custom.SomeLayerName', return_info=False)
>>> [
    webanno_custom_SomeLayerName(...),  
    ...
    webanno_custom_SomeLayerName(...)
]


# slightly shorter when using custom annotations
project.annotations_of_layer('SomeLayerName')
>>> ...

# selecting specific annotators and source files
project.annotations_of_layer('SomeLayerName', 
                             annotators=['annotator_a', 'annotator_b', 'annotator_d'], 
                             source_files=['file_1.txt', 'file_42.txt'])

# unzipping and storing annotations to disk
project.extract_project_files('out/path/')
```