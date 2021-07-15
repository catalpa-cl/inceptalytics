import cassis
import os
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile


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
    uima_type = typesystem.get_type(layer_name).get_feature(feature_name).rangeTypeName
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

