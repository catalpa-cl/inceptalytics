"""
# INCEpTALYTICS Quick Start Guide
The _INCEpTALYTICS_ package allows you to export and analyse annotation projects using the [_INCEpTION_](https://inception-project.github.io/) annotation tool. 
This guide gives an overview over its functionalities. It assumes that you are familiar with the INCEpTION annotation tool.

## Loading a Project
Projects can be loaded in two ways: 

* Importing a [zipped XMI](https://inception-project.github.io/releases/22.4/docs/user-guide.html#sect_formats_uimaxmi) export
* INCEpTION's [remote API](https://inception-project.github.io/releases/22.5/docs/admin-guide.html#sect_remote_api).

***NOTE***: XMI exports must be in XMI v1.0 format, as INCEpTALYTICS is built on top of [_dkpro cassis_](https://github.com/dkpro/dkpro-cassis).
"""

from inceptalytics import Project

project = Project.from_zipped_xmi('../data/Example_Project_POS.zip')

# project = Project.from_remote(project='my_project_name',
#                              remote_url='https://my.inception.instance',
#                              auth=('user', 'password'))

"""Once a project is loaded, you can access different properties such as annotators and annotated files. 
Per default, those include only annotators who annotated at least a single document and documents that contain at least a single annotation.
"""

print('Annotators:', project.annotators)
print('Files:', project.source_file_names)
print('Layers:', project.layers)

"""You can also access the typesystem and CAS objects directly. There is a single CAS object per source file.

See the [dkpro cassis documentation](https://cassis.readthedocs.io/en/latest/) for more details on their usage.
"""

typesystem = project.typesystem
cas_objects = project.cas_objects

# do something useful with those here

"""## Analysing a specific annotation

Annotations are organised in _layers_ and _features_. To analyse a specific annotation, you need to select a feature-layer combination. The returned _View_ offers the main analysis functionalities of INCEpTALYTICS.
"""

pos_layer = 'de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.POS'
print(f'Features: {project.features(pos_layer)}')
feature = 'coarseValue'

feature_path = f'{pos_layer}>{feature}'
pos_annos = project.select(annotation=feature_path)

"""You can also create a view that contains a specific subset of files and annotators."""

reduced_pos_annos = project.select(annotation=feature_path,
                                   annotators=['ia-test1', 'ia-test2'],
                                   source_files=['test1.txt', 'test2.txt'])

"""Once we have selected a specific annotation, we can look at some numbers, e.g. the total number of annotations."""

print('# pos annotations in view:', pos_annos.count())

"""Many methods of the View API accept the `grouped_by` parameter. We can use it to refine a query and organise returned values."""

print('# annotations per file per annotator', pos_annos.count(grouped_by=['source_file', 'annotator']))
print('label distribution', pos_annos.count(grouped_by='annotation'))

"""Most methods of the View API return [pandas](https://pandas.pydata.org/) objects. In case you want to implement an analysis not covered by the API, you can directly work with a `DataFrame` as well."""

df = pos_annos.data_frame
df.head()

"""If you want to use your annotated data for ML training, INCEpTALYTICS can do a simple majority vote.
The `levels` parameter controls across which unit levels annotations are aggregated. `['sentence', 'begin', 'end']` aggregates over individual spans contained in a sentence.
"""

dataset = pos_annos.consolidated_annotations(levels=['sentence', 'begin', 'end'])
dataset.head()

"""The resulting DataFrame can be stored in many common formats."""

dataset.to_csv('../data/pos.csv')

"""### Inspecting Data in Detail

To get an overview over the annotation, you can look at the document-annotator matrix.
"""

pos_annos.document_annotator_matrix

"""It may be useful to have a look at the text that was annotated to adjudicate disagreements."""

document_annotator_matrix = pos_annos.document_annotator_matrix
covered_texts = pos_annos.texts
document_annotator_matrix.join(covered_texts).head()

"""If you are looking for annotation quality, we also provide confusion matrices and agreement measures. Confusion matrices produced pairwise and are indexed by annotators."""

cms = pos_annos.confusion_matrices()
cms[('ia-test3', 'ia-test2')]

"""If you are not interested in individual annotators, but overall disagreements over certain classes, you can aggregate the pairwise matrices into a single matrix."""

# sum over all pairwise matrices
print(pos_annos.confusion_matrices(aggregate='total'))

"""If you want to quantify disagreements, INCEpTALYTICS offers different agreement measures which can be calculated pairwise or in aggregate."""

print('Krippendorff\'s alpha: ', pos_annos.iaa())
print('Pairwise Cohen\'s Kappa: ', pos_annos.iaa_pairwise(measure='kappa'))