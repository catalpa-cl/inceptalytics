import cassis
import pandas as pd
from itertools import combinations
from sklearn.metrics import cohen_kappa_score
from krippendorff import alpha

from utils import extend_layer_name, annotation_info_from_xmi_zip


class Project:
    @classmethod
    def from_zipped_xmi(cls, project_zip):
        annotations = annotation_info_from_xmi_zip(project_zip)
        return cls(annotations)

    def __init__(self, annotations):
        self._annotation_info = pd.DataFrame(annotations, columns=['cas', 'source_file', 'annotator'])

    @property
    def typesystem(self):
        return self._annotation_info.loc[0, 'cas'].typesystem

    @property
    def source_file_names(self):
        return self._unique_entries('source_file')

    @property
    def annotators(self):
        return self._unique_entries('annotator')

    @property
    def cases(self):
        return self._unique_entries('cas')

    def _unique_entries(self, info_type):
        return self._annotation_info[info_type].unique().tolist()

    def _filter_annotation_info(self, annotators=None, source_files=None):
        df = self._annotation_info

        if annotators:
            df = df.query('annotator == @annotators')

        if source_files:
            df = df.query('source_file == @source_files')

        return df

    def annotations(self, layer_name, annotators=None, source_files=None):
        layer_name = extend_layer_name(layer_name)
        relevant_annotations = self._filter_annotation_info(annotators, source_files).itertuples(index=False, name=None)

        annotations = []
        for cas, source_file, annotator in relevant_annotations:
            try:
                for annotation in cas.select(layer_name):
                    entry = (annotation, source_file, annotation.begin, annotation.end, annotator)
                    annotations.append(entry)
            except cassis.typesystem.TypeNotFoundError:
                continue

        colnames = ['annotation', 'source_file', 'begin', 'end', 'annotator']

        return pd.DataFrame(annotations, columns=colnames)

    def annotation_matrix(self, layer_name, annotators=None, source_files=None):
        index = ['source_file', 'begin', 'end', 'annotator']
        annotations = self.annotations(layer_name, annotators, source_files).set_index(index)
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

                score = cohen_kappa_score(data[0], data[1])

                entries.append((annotator_a, annotator_b, n, score))

            return pd.DataFrame(entries, columns=['a', 'b', 'n', 'kappa']).set_index(['a', 'b'])

        if measure == 'krippendorff':
            categories = annotations.stack().unique()
            category_to_index = {category: i for i, category in enumerate(categories)}
            return alpha(annotations.replace(category_to_index).values.T, level_of_measurement=level)
