import os
import cassis
from pathlib import Path
from zipfile import ZipFile
from io import BytesIO
import pandas as pd
from functools import cached_property
from itertools import combinations
from sklearn.metrics import cohen_kappa_score
from krippendorff import alpha

UIMA_TO_PANDAS_TYPE_MAP = {
    'uima.cas.Boolean': 'bool',
    'uima.cas.Integer': 'int',
    'uima.cas.Float': 'float',
    'uima.cas.String': 'str'
}

class Project:
    # TODO: refactor into static constructor fromZippedXMI
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

    @property
    def typesystem(self):
        return self._annotation_info.loc[0, 'cas'].typesystem

    @property
    def source_file_names(self):
        return self._annotation_info['source_file'].unique().tolist()

    @property
    def annotators(self):
        return self._annotation_info['annotator'].unique().tolist()

    def _filter_cases(self, annotators=None, source_files=None):
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

    def get_dtype(self, layer_name, feature_name):
        layer_name = self._extend_layer_name(layer_name)
        uima_type = self.typesystem.get_type(layer_name).get_feature(feature_name).rangeTypeName
        return UIMA_TO_PANDAS_TYPE_MAP.get(uima_type, 'object')

    def _extend_layer_name(self, layer_name):
        return f'webanno.custom.{layer_name}' if len(layer_name.split('.')) == 1 else layer_name

    def annotations_of_layer(self, layer_name, annotators=None, source_files=None, return_info=True, as_dataframe=False):
        layer_name = self._extend_layer_name(layer_name)

        annotations = []
        for cas, source_file, annotator in self._filter_cases(annotators, source_files).itertuples(index=False, name=None):
            try:
                for annotation in cas.select(layer_name):
                    if return_info:
                        entry = (annotation, source_file, annotator)
                    else:
                        entry = annotation
                    annotations.append(entry)
            except cassis.typesystem.TypeNotFoundError:
                continue

        if as_dataframe and return_info:
            colnames = ['annotation', 'source_file', 'annotator']
            annotations = pd.DataFrame(annotations, columns=colnames)

        return annotations

    def annotation_matrix(self, layer_name, annotators=None, source_files=None):
        annotations = self.annotations_of_layer(layer_name, annotators, source_files, as_dataframe=True)

        transformations = {'begin': lambda a: a.begin, 'end': lambda a: a.end}
        index = ['source_file', 'begin', 'end', 'annotator']
        annotations = annotations.join(annotations['annotation'].transform(transformations)).set_index(index)

        # FIXME: deal with duplicate annotations in a safer way
        return annotations.loc[~annotations.index.duplicated(), 'annotation'].unstack()

    def feature_matrix(self, layer_name, feature_name, annotators=None, source_files=None):
        annotations = self.annotation_matrix(layer_name, annotators, source_files)
        return annotations.applymap(lambda x: x.get(feature_name), na_action='ignore')

    def feature_counts(self, layer_name, feature_name, grouped_by=None, annotators=None, source_files=None):
        annotations = self.feature_matrix(layer_name, feature_name, annotators, source_files).stack()

        if grouped_by is not None:
            annotations = annotations.groupby(grouped_by)

        return annotations.value_counts()

    def iaa(self, layer_name, feature_name, measure='pairwise_kappa', level='nominal', annotators=None, source_files=None):
        annotations = self.feature_matrix(layer_name, feature_name, annotators, source_files)

        if measure == 'pairwise_kappa':
            annotators = annotations.columns

            entries = []
            for pair in combinations(annotators, 2):
                annotator_a, annotator_b = pair
                data = annotations[list(pair)].dropna().values.T
                n = data.shape[1]

                try:
                    score = cohen_kappa_score(data[0], data[1])
                except Exception:
                    score = 0.0

                entries.append((annotator_a, annotator_b, n, score))

            return pd.DataFrame(entries, columns=['a', 'b', 'n', 'kappa']).set_index(['a', 'b'])

        if measure == 'krippendorff':
            categories = annotations.stack().unique()
            category_to_index = {category: i for i, category in enumerate(categories)}
            return alpha(annotations.replace(category_to_index).values.T, level_of_measurement=level)
