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

                    annotations.append((source_file, annotator, cas))

        return pd.DataFrame(annotations, columns=['source_file', 'annotator', 'cas'])

    def _cas_objects(self, filter_by=None):
        df = self._annotation_info

        if filter_by:
            df = df.query(filter_by)

        return df['cas'].tolist()

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

    def annotations_of_layer(self, layer_name):
        if len(layer_name.split('.')) == 1:
            layer_name = f'webanno.custom.{layer_name}'

        annotations = []
        for cas in self._cas_objects():
            try:
                for annotation in cas.select(layer_name):
                    annotations.append(annotation)
            except cassis.typesystem.TypeNotFoundError:
                continue

        return annotations


if __name__ == '__main__':
    project = Project('data/Gruppenannotation_project_2021-07-13_0813.zip')
    print(project._annotation_info['source_file'].sort_values().unique()[:6])
    print(len(project.annotations_of_layer('Zielgruppenadressierung')))
