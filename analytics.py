import os
import cassis
from pathlib import Path
from zipfile import ZipFile


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

    @property
    def cas_objects(self):
        annotation_dir = self._project_path/'annotation'

        cases = []
        for source_dir in annotation_dir.iterdir():
            for annotator_dir in source_dir.iterdir():
                ts_file = (annotator_dir/'TypeSystem.xml').resolve()
                cas_file = next(annotator_dir.glob('*.xmi')).resolve()
                cas = load_cas(cas_file, load_typesystem(ts_file))

                cases.append(cas)

        return cases

    def annotations_of_layer(self, layer_name):
        if len(layer_name.split('.')) == 1:
            layer_name = f'webanno.custom.{layer_name}'

        annotations = []
        for cas in self.cas_objects:
            try:
                for annotation in cas.select(layer_name):
                    annotations.append(annotation)
            except cassis.typesystem.TypeNotFoundError:
                continue

        return annotations


if __name__ == '__main__':
    project = Project('project.zip')
    project.extract_project_files(target_path='extracted/', folder_name='annotation/')
