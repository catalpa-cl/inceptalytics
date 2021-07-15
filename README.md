# Inception Analytics

## Basic Usage

```python
from analytics import Project

# loading a project into memory
project = Project('path/to/export.zip')

# getting annotations
project.annotations('cassis.Token')
>>> [
    (cassis_Token(...), 'file_0.txt', 'annotator_a'),
    (cassis_Token(...), 'file_0.txt', 'annotator_b'),
    ...,
    (cassis_Token(...), 'file_999.txt', 'annotator_f')
]

# omit source file and annotator information
project.annotations('cassis.Token', return_info=False)
>>> [
    cassis_Token(...),
    cassis_Token(...),
    ...,
    cassis_Token(...)
]

# query for some custom layer
project.annotations('webanno.custom.SomeLayerName', return_info=False)
>>> [
    webanno_custom_SomeLayerName(...),  
    ...
    webanno_custom_SomeLayerName(...)
]


# slightly shorter when using custom annotations
project.annotations('SomeLayerName')
>>> ...

# selecting specific annotators and source files
project.annotations('SomeLayerName', 
                             annotators=['annotator_a', 'annotator_b', 'annotator_d'], 
                             source_files=['file_1.txt', 'file_42.txt'])

# unzipping and storing annotations to disk
project.extract_project_files('out/path/')
```