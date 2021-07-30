import cassis
import os
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile
import pandas as pd
import seaborn as sns
from sklearn.metrics import confusion_matrix
import numpy as np

###
# UIMA / Cassis Utils
###

UIMA_TO_PANDAS_TYPE_MAP = {
    'uima.cas.Boolean': 'bool',
    'uima.cas.Integer': 'int',
    'uima.cas.Float': 'float',
    'uima.cas.String': 'str'
}


def get_dtype(typesystem, layer_name, feature_name):
    try:
        uima_type = typesystem.get_type(layer_name).get_feature(feature_name).rangeTypeName
    except AttributeError:
        return None
    return UIMA_TO_PANDAS_TYPE_MAP.get(uima_type, 'object')


def extend_layer_name(layer_name, prefix='webanno.custom'):
    return f'{prefix}.{layer_name}' if len(layer_name.split('.')) == 1 else layer_name


###
# IO Utils
###

def annotation_info_from_xmi_zip(project_zip):
    annotations = []
    with ZipFile(project_zip) as project_zip:
        annotation_zips = (fp for fp in project_zip.namelist() if
                           fp.startswith('annotation/') and fp.endswith('.zip'))
        for file_path in annotation_zips:
            source_file = Path(file_path).parent.name
            with ZipFile(BytesIO(project_zip.read(file_path))) as annotation_zip:
                typesystem = cassis.load_typesystem(BytesIO(annotation_zip.read('TypeSystem.xml')))

                cas_file = next(f for f in annotation_zip.namelist() if f.endswith('.xmi'))
                annotator = Path(cas_file).stem
                cas = cassis.load_cas_from_xmi(BytesIO(annotation_zip.read(cas_file)), typesystem)

                annotations.append((cas, source_file, annotator))
    return annotations


def get_annotated_file_names(project_zip) -> tuple:
    complete_names = []
    annotation_files = []
    source_files = []

    with ZipFile(project_zip) as zip_file:
        for file in zip_file.namelist():
            if file.startswith('annotation/'):
                complete_names.append(file)
                annotation_files.append(file.split('/')[-1])
                source_files.append(file.split('/')[1])
    return complete_names, source_files, annotation_files


def extract_project_files(project_zip, target_path: str, folder_name='annotation/'):
    """Extracts zip files in the given project folder to the target path."""
    with ZipFile(project_zip) as zip_file:
        for file in zip_file.namelist():
            if file.startswith(folder_name):
                zip_file.extract(file, target_path)

                if file.split('.')[-1] == 'zip':
                    with ZipFile(target_path + file) as sub_zip_file:
                        sub_zip_file.extractall(target_path + file.split('.')[0])
                    os.remove(target_path + file)


def heatmap(annotations_a: pd.Series,
            annotations_b: pd.Series,
            labels=[],
            catch_all_labels=[],
            annotator_names=[],
            na_value='NA'):
    annotations = annotations_a.append(annotations_b)

    if not labels:
        labels = annotations.unique()
        labels.sort()

    # move catch-all categories to end of list
    if catch_all_labels:
        labels = [val for val in labels if val not in catch_all_labels] + catch_all_labels

    # limit to cases that both annotators annotated
    annotations = annotations[~annotations.index.duplicated()].unstack().fillna(na_value)

    if annotator_names:
        annotator_a, annotator_b = annotator_names[:2]
    else:
        annotator_a, annotator_b = annotations


    # generate confusion matrix
    cm = confusion_matrix(annotations[annotator_a],
                          annotations[annotator_b],
                          labels=labels)
    cm_df = pd.DataFrame(cm, columns=labels, index=labels)

    # generate heatmap figure
    diagonal = np.eye(cm.shape[0], dtype=bool)
    max_no_diag = cm[~diagonal].max()
    fig = sns.heatmap(cm_df, cmap='seismic', center=0, square=True, annot=True,
                      vmax=max_no_diag, cbar=False, fmt='d')

    # add labels
    fig.set_ylabel(annotator_a, fontsize=14)
    fig.set_xlabel(annotator_b, fontsize=14)
    fig.set_xticklabels(labels, rotation=45, ha='right')

    # add dashed separator line for catch-all categories
    if catch_all_labels:
        n_none_labels = len(catch_all_labels)
        w = fig.get_xticks()
        h = fig.get_yticks()
        xmax = (w[-n_none_labels] + w[-n_none_labels - 1]) / 2
        ymax = (h[-n_none_labels] + h[-n_none_labels - 1]) / 2
        fig.hlines(y=ymax, xmin=0, xmax=xmax, linestyles='dashed', colors='black', linewidth=0.66)
        fig.vlines(x=xmax, ymin=0, ymax=ymax, linestyles='dashed', colors='black', linewidth=0.66)

    # size figure
    fig.get_figure().set_size_inches(5.5, 5.5)
    fig.get_figure().tight_layout()

    return fig.get_figure(), cm, labels