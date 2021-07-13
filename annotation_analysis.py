import cassis
from pathlib import Path
from functools import cached_property

def load_typesystem(path):
    with open(path, 'rb') as f:
        return cassis.load_typesystem(f)


def load_cas(path, typesystem):
    with open(path, 'rb') as f:
        return cassis.load_cas_from_xmi(f, typesystem)


class Project:
    def __init__(self, project_dir):
        self.project_dir = project_dir
        self._project_path = Path(project_dir)

    @property
    def cas_objects(self):
        annotation_dir = self._project_path/'annotation'
        for source_dir in annotation_dir.iterdir():
            for annotator_dir in source_dir.iterdir():
                ts_file = (annotator_dir/'TypeSystem.xml').resolve()
                cas_file = next(annotator_dir.glob('*.xmi')).resolve()
                cas = load_cas(cas_file, load_typesystem(ts_file))

                yield cas

    def annotations_of_layer(self, layer_name):
        if len(layer_name.split('.')) == 1:
            layer_name = f'webanno.custom.{layer_name}'

        for cas in self.cas_objects:
            try:
                for annotation in cas.select(layer_name):
                    yield annotation
            except cassis.typesystem.TypeNotFoundError:
                continue


project = Project('data/Gruppenannotation_project_2021-06-09_0758')
list(project.annotations_of_layer('Zielgruppenadressierung'))