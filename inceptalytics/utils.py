import cassis
import re
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile
import pandas as pd
from sklearn.metrics import confusion_matrix as conf_mat
import numpy as np
from typing import List, Union
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


def annotation_info_from_xmi_zip(project_fp: str):
    """
    Returns a list of tuples containing information about annotations. Tuples contain (CAS, Source File Name, Annotator name).

    Args:
        project_fp: String representing a path to an Inception XMI export.
    """
    annotations = []
    with ZipFile(project_fp) as project_zip:
        regex = re.compile('.*annotation/.*/(?!\._).*zip$')
        annotation_fps = (fp for fp in project_zip.namelist() if regex.match(fp))

        typesystem = None
        for file_path in annotation_fps:
            with ZipFile(BytesIO(project_zip.read(file_path))) as annotation_zip:
                if typesystem is None:
                    typesystem = cassis.load_typesystem(BytesIO(annotation_zip.read('TypeSystem.xml')))

                cas_file = next(f for f in annotation_zip.namelist() if f.endswith('.xmi'))
                cas = cassis.load_cas_from_xmi(BytesIO(annotation_zip.read(cas_file)), typesystem)
                source_file = Path(file_path).parent.name
                annotator = Path(cas_file).stem

                annotations.append((cas, source_file, annotator))
    
    if not annotations:
        raise RuntimeError('Could not parse project or empty project.')
    
    return annotations


def source_files_from_xmi_zip(project_fp: str):
    """
    Returns the list of all source file names of the project.

    Args:
        project_fp: String representing a path to an exported Inception XMI export.
    """
    with ZipFile(project_fp) as project_zip:
        return [fp.split('/', 1)[1] for fp in project_zip.namelist() if fp.startswith('source/')]


###
# Statistics
###


def confusion_matrix(da_matrix: pd.DataFrame,
                     annotators: Union[List[int], List[str]],
                     labels: List[any] = None) -> pd.DataFrame:

    M = da_matrix[annotators].dropna()
    a, b = annotators

    if isinstance(a, int):
        annos_a = M.iloc[:, a]
        annos_b = M.iloc[:, b]
    else:
        annos_a = M.loc[:, a]
        annos_b = M.loc[:, b]

    return conf_mat(annos_a, annos_b, labels=labels)


def zero_diag_cm_df(cm_df):
    cm_df = cm_df.copy()
    labels = cm_df.columns
    for i in labels:
        cm_df.loc[i, i] = 0
    return cm_df


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
