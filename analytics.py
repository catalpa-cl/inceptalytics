import cassis
import pandas as pd
from itertools import combinations
from functools import lru_cache
from sklearn.metrics import cohen_kappa_score
from krippendorff import alpha
from utils import extend_layer_name, annotation_info_from_xmi_zip

class Project:
    @classmethod
    def from_zipped_xmi(cls, project_zip):
        annotations = annotation_info_from_xmi_zip(project_zip)
        return cls(annotations, project_zip, 'xmi')

    def __init__(self, annotations, project_path, export_format):
        self._annotation_info = pd.DataFrame(annotations, columns=['cas', 'source_file', 'annotator'])
        self.path = project_path
        self.export_format = export_format

    @property
    def typesystem(self):
        return self._annotation_info.loc[0, 'cas'].typesystem

    @property
    def layers(self):
        return [t.name for t in self.typesystem.get_types()]

    @property
    def custom_layers(self):
        return [l for l in self.layers if l.startswith('webanno.custom')]

    @property
    def source_file_names(self):
        return self._unique_entries('source_file')

    @property
    def annotators(self):
        return self._unique_entries('annotator')

    @property
    def cas_objects(self):
        return self._annotation_info['cas'].tolist()

    def _unique_entries(self, info_type):
        return self._annotation_info[info_type].unique().tolist()

    def _filter_annotation_info(self, annotators=None, source_files=None):
        df = self._annotation_info

        if annotators:
            df = df.query('annotator == @annotators')

        if source_files:
            df = df.query('source_file == @source_files')

        return df

    def features(self, layer_name):
        return [f.name for f in self.typesystem.get_type(extend_layer_name(layer_name)).all_features]

    def select(self, layer_name, feature_name=None, annotators=None, source_files=None):
        layer_name = extend_layer_name(layer_name)
        level = 'layer' if feature_name is None else 'feature'

        info = self._filter_annotation_info(annotators, source_files)
        annotations = self._annotations(info, layer_name, feature_name)

        return View(annotations, self, level)

    @staticmethod
    def _annotations(annotation_info, layer_name, feature_name):
        entries = []
        for cas, source_file, annotator in annotation_info.itertuples(index=False, name=None):
            try:
                for annotation in cas.select(layer_name):
                    entry = (annotation, annotation.get_covered_text(), source_file, annotation.begin, annotation.end, annotator)
                    entries.append(entry)
            except cassis.typesystem.TypeNotFoundError:
                continue

        columns = ['_annotation', 'text', 'source_file', 'begin', 'end', 'annotator']
        index = ['source_file', 'begin', 'end', 'annotator']
        annotations = pd.DataFrame(entries, columns=columns).set_index(index)

        if feature_name is not None:
            annotations['annotation'] = annotations['_annotation'].map(lambda x: x.get(feature_name), na_action='ignore')
        else:
            annotations['annotation'] = annotations['text']

        return annotations


class View:
    def __init__(self, annotations, project, layer_name, feature_name=None):
        self.annotations = annotations
        self.project = project
        self.layer_name = layer_name
        self.feature_name = feature_name

    @property
    def level(self):
        return 'layer' if self.feature_name is None else 'feature'

    @property
    def document_annotator_matrix(self):
        # TODO: handle more elegantly, annotations are lost by dropping duplicates
        return self.annotations.loc[~self.annotations.index.duplicated(), 'annotation'].unstack()

    def counts(self, grouped_by=None):
        annotations = self.annotations
        if grouped_by is not None:
            annotations = self.annotations.groupby(grouped_by)
        return annotations['annotation'].value_counts()

    def iaa(self, measure='pairwise_kappa', level='nominal'):
        matrix = self.document_annotator_matrix

        if measure == 'pairwise_kappa':
            annotators = matrix.columns
            entries = []
            for pair in combinations(annotators, 2):
                annotator_a, annotator_b = pair
                data = matrix[list(pair)].dropna().values.T
                n = data.shape[1]
                score = cohen_kappa_score(data[0], data[1])
                entries.append((annotator_a, annotator_b, n, score))
            return pd.DataFrame(entries, columns=['a', 'b', 'n', 'kappa']).set_index(['a', 'b'])

        if measure == 'krippendorff':
            categories = matrix.stack().unique()
            category_to_index = {category: i for i, category in enumerate(categories)}
            return alpha(matrix.replace(category_to_index).values.T, level_of_measurement=level)
