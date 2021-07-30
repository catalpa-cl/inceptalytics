import cassis
import pandas as pd
from itertools import combinations
from sklearn.metrics import cohen_kappa_score
from krippendorff import alpha
from utils import extend_layer_name, annotation_info_from_xmi_zip, get_dtype
from typing import Union, Sequence, List


class Project:
    @classmethod
    def from_zipped_xmi(cls, project_path):
        """
        Loads an Inception project exported to XMI format, located at the given path.

        Args:
            project_path (str): A string representing the path to the exported project.
        """
        annotations = annotation_info_from_xmi_zip(project_path)
        return cls(annotations, project_path, 'xmi')

    def __init__(self, annotations, project_path, export_format):
        self._annotation_info = pd.DataFrame(annotations, columns=['cas', 'source_file', 'annotator'])
        self.path = project_path
        self.export_format = export_format
        self.layer_feature_separator = '>'

    @property
    def typesystem(self):
        """Returns the Typesystem used by the CAS Objects in the Project."""
        return self._annotation_info.loc[0, 'cas'].typesystem

    @property
    def layers(self) -> List[str]:
        """Returns a list of all layer names in the project."""
        return [t.name for t in self.typesystem.get_types()]

    @property
    def custom_layers(self) -> List[str]:
        """Returns a list of all custom layer names in the project."""
        return [l for l in self.layers if l.startswith('webanno.custom')]

    @property
    def source_file_names(self) -> List[str]:
        """Returns a list of all source file names that have at least a single annotation attached."""
        return self._unique_entries('source_file')

    @property
    def annotators(self) -> List[str]:
        """Returns a list of all annotator names with at least a single annotation in the project."""
        return self._unique_entries('annotator')

    @property
    def cas_objects(self) -> List[cassis.Cas]:
        """Returns a list with all CAS Objects in the project."""
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

    def features(self, layer_name: str, filter_empty=False) -> List[str]:
        """Returns a list of all feature names for the given layer name.

        Args:
              layer_name: The layer from which to pull feature names.
              filter_empty: If set to true, features without any annotations are filtered out. Note that
        """
        layer_name = extend_layer_name(layer_name)
        no_features = ['begin', 'end', 'sofa']
        feature_names = (f.name for f in self.typesystem.get_type(layer_name).all_features if f.name not in no_features)

        if filter_empty:
            feature_names = (name for name in feature_names if any(self.select(f'{layer_name}>{name}').annotations))

        return list(feature_names)

    def select(self,
               annotation: str,
               annotators: Union[str, List[str], None] = None,
               source_files: Union[str, List[str], None] = None):
        """
        Returns a View object, based on the specified selection parameters.

        Args:
            annotation: String specifying the annotation to select (combination of layer and feature name). Feature names must be separated from the layer names by the project's separator. If no feature is specified, the text covered by the annotation is used as the layer's feature.
            annotators: List of annotators to be included. A single annotator can be selected by passing a string. If None is provided, all annotators are included in the view.
            source_files: List of source files to be included. A single source file can be selected by passing a string. If None is provided, all annotators are included in the view.
        """
        layer_name, feature_name = self._layer_feature_split(annotation)
        layer_name = extend_layer_name(layer_name)
        info = self._filter_annotation_info(annotators, source_files)
        annotations = self._annotations(info, layer_name, feature_name)
        return View(annotations, self, layer_name, feature_name)

    def _layer_feature_split(self, layer_feature_string):
        split = layer_feature_string.rsplit(self.layer_feature_separator, 1)
        if len(split) == 2:
            return split
        else:
            return split[0], None

    def _annotations(self, annotation_info, layer_name, feature_name):
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

            # convert java boolean strings into booleans
            dtype = get_dtype(self.typesystem, layer_name, feature_name)
            if dtype == 'bool':
                annotations['annotation'] = annotations['annotation'].map(lambda x: x.startswith('t'), na_action='ignore')

        else:
            annotations['annotation'] = annotations['text']

        return annotations


class View:
    def __init__(self, annotations, project, layer_name, feature_name=None):
        self._annotation_dataframe = annotations
        self.project = project
        self.layer_name = layer_name
        self.feature_name = feature_name

    @property
    def level(self):
        """Returns whether the view represents a Layer or a specific Feature of a Layer"""
        return 'layer' if self.feature_name is None else 'feature'

    @property
    def annotations(self) -> pd.Series:
        """Returns a Series of all annotations in the view."""
        return self._annotation_dataframe['annotation']

    @property
    def data_frame(self) -> pd.DataFrame:
        return self._annotation_dataframe.reset_index()

    @property
    def document_annotator_matrix(self) -> pd.DataFrame:
        """Returns a Dataframe with document names as indices and annotator names als """
        # TODO: handle more elegantly, annotations are lost by dropping duplicates
        return self._annotation_dataframe.loc[~self._annotation_dataframe.index.duplicated(), 'annotation'].unstack()

    def counts(self, grouped_by: Union[str, Sequence[str]] = None) -> pd.Series:
        """
        Returns a Series containing value counts of the feature included in the view.

        Args:
            grouped_by: Name of the variable to group the counts by, either "annotator", "source_file" or a list containing both. If a list is given, the order of the variables determines the nesting order.
        """
        annotations = self._annotation_dataframe
        if grouped_by is not None:
            annotations = self._annotation_dataframe.groupby(grouped_by)
        return annotations['annotation'].value_counts()

    def iaa(self, measure='pairwise_kappa', level='nominal'):
        """
        Returns inter-annotator agreement statistics for features in the view.

        Args:
            measure: Name of the measure to use, either 'pairwise_kappa' (default), or 'krippendorff'. When 'pairwise_kappa' is selected, a Series with annotator names as indices is returned.
            level: Variable scale to use, when calculating Krippendorff's Alpha. Valid values are 'nominal' (default), 'ordinal' and 'interval'.

        Returns: Either a float with Krippendorff's Alpha or a Series with pairwise Cohen's Kappas between Annotators.
        """
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
