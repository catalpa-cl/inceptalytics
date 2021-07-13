import os
import cassis
from pathlib import Path
from zipfile import ZipFile
from io import BytesIO
import pandas as pd
from functools import cached_property


def load_typesystem(path):
    with open(path, 'rb') as f:
        return cassis.load_typesystem(f)


def load_cas(path, typesystem):
    with open(path, 'rb') as f:
        return cassis.load_cas_from_xmi(f, typesystem)


class Project:
    def __init__(self, project_zip):
        self.project_zip = project_zip
        self._project_path = Path(project_zip)

    @cached_property
    def _annotation_info(self):
        annotations = []
        with ZipFile(self.project_zip) as project_zip:
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

        return pd.DataFrame(annotations, columns=['cas', 'source_file', 'annotator'])

    def _cas_df(self, annotators=None, source_files=None):
        df = self._annotation_info

        if annotators:
            df = df.query('annotator == @annotators')

        if source_files:
            df = df.query('source_file == @source_files')

        return df

    def get_annotated_file_names(self) -> tuple:
        complete_names = []
        annotation_files = []
        source_files = []

        with ZipFile(self.project_zip) as zip_file:
            for file in zip_file.namelist():
                if file.startswith('annotation/'):
                    complete_names.append(file)
                    annotation_files.append(file.split('/')[-1])
                    source_files.append(file.split('/')[1])
        return complete_names, source_files, annotation_files

    def extract_project_files(self, target_path: str, folder_name='annotation/'):
        """Extracts zip files in the given project folder to the target path."""
        with ZipFile(self.project_zip) as zip_file:
            for file in zip_file.namelist():
                if file.startswith(folder_name):
                    zip_file.extract(file, target_path)

                    if file.split('.')[-1] == 'zip':
                        with ZipFile(target_path + file) as sub_zip_file:
                            sub_zip_file.extractall(target_path + file.split('.')[0])
                        os.remove(target_path + file)

    def annotations_of_layer(self, layer_name, annotators=None, source_files=None, return_info=True):
        if len(layer_name.split('.')) == 1:
            layer_name = f'webanno.custom.{layer_name}'

        annotations = []
        for cas, source_file, annotator in self._cas_df(annotators, source_files).itertuples(index=False, name=None):
            try:
                for annotation in cas.select(layer_name):
                    if return_info:
                        entry = (annotation, source_file, annotator)
                    else:
                        entry = annotation
                    annotations.append(entry)
            except cassis.typesystem.TypeNotFoundError:
                continue

        return annotations
