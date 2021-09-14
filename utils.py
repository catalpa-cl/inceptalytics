import cassis
import os
import re
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile
import pandas as pd
import plotly.graph_objects as go
from sklearn.metrics import confusion_matrix as conf_mat
import numpy as np
from typing import List, Union
from matplotlib.figure import Figure
from pygamma_agreement import Continuum, CombinedCategoricalDissimilarity
from pyannote.core import Segment

###
# UIMA / Cassis Utils
###

SENTENCE_TYPE_NAME = 'de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Sentence'

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


def construct_feature_path(layer, feature, sep='>'):
    return f'{layer}{sep}{feature}'

###
# IO Utils
###


def annotation_info_from_xmi_zip(project_zip: str):
    """
    Returns a list of tuples containing information about annotations. Tuples contain (CAS, Source File Name, Annotator name).

    Args:
        project_zip: String representing a path to an Inception XMI export.
    """
    annotations = []
    regex = re.compile('.*annotation/.*/(?!\._).*zip$')
    with ZipFile(project_zip) as project_zip:
        annotation_zips = (fp for fp in project_zip.namelist() if
                           regex.match(fp))
        for file_path in annotation_zips:
            source_file = Path(file_path).parent.name
            with ZipFile(BytesIO(project_zip.read(file_path))) as annotation_zip:
                typesystem = cassis.load_typesystem(BytesIO(annotation_zip.read('TypeSystem.xml')))
                cas_file = next(f for f in annotation_zip.namelist() if f.endswith('.xmi'))
                annotator = Path(cas_file).stem
                cas = cassis.load_cas_from_xmi(BytesIO(annotation_zip.read(cas_file)), typesystem)

                annotations.append((cas, source_file, annotator))
    
    if not annotations:
        raise RuntimeError('Could not parse project or empty project.')
    
    return annotations


def source_files_from_xmi_zip(project_zip: str):
    """
    Returns the list of all source file names of the project.

    Args:
        project_zip: String representing a path to an exported Inception XMI export.
    """
    with ZipFile(project_zip) as project_zip:
        return [fp.split('/', 1)[1] for fp in project_zip.namelist() if fp.startswith('source/')]


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

###
# Statistics
###


def confusion_matrix(da_matrix: pd.DataFrame,
                     annotators: Union[List[int], List[str]],
                     labels: List[any] = None) -> pd.DataFrame:
    if labels is None:
        labels = da_matrix.stack().unique()

    M = da_matrix[annotators].dropna()
    a, b = annotators

    if isinstance(a, int):
        annos_a = M.iloc[:, a]
        annos_b = M.iloc[:, b]
    else:
        annos_a = M.loc[:, a]
        annos_b = M.loc[:, b]

    return conf_mat(annos_a, annos_b, labels=labels)


def percentage_agreement(a, b):
    a = np.asarray(a)
    b = np.asarray(b)
    return sum(a == b) / a.shape[0]


def gamma_agreement(annotation_df: pd.DataFrame) -> float:
    def gamma_for_continuum(df, dissimilarity):
        continuum = Continuum()
        for _, _, annotator, begin, end, annotation in df.itertuples():
            continuum.add(annotator, Segment(begin, end), annotation)
        return continuum.compute_gamma(dissimilarity, fast=True).gamma

    continuum_dfs = annotation_df[['sentence', 'annotator', 'begin', 'end', 'annotation']].groupby('sentence')
    diss = CombinedCategoricalDissimilarity()
    gammas = []
    for sf, df in continuum_dfs:
        try:
            gammas.append(gamma_for_continuum(df, diss))
        except AssertionError:
            print(f'Could not calculate gamma for source file "{sf}". Skipping.')

    return np.mean(gammas)


###
# Plotting
###

def heatmap(table: pd.DataFrame) -> Figure:
    fig = go.Figure(data=go.Heatmap(
        z=table.values,
        x=table.columns,
        y=table.index,
        colorscale='Blues'))

    fig.update_layout(dict(
        xaxis_title=table.columns.name,
        yaxis_title=table.index.name
    ))

    return fig
