import streamlit as st
import numpy as np
from analytics import Project
from streamlit_utils import st_indexed_triangle, st_grid
from math import ceil
import pandas as pd

@st.cache
def load_project(file):
    return Project.from_zipped_xmi(file)

st.set_page_config("Inception Analytics", None, "wide", "auto")

body, stats = st.columns([4, 1])

body.write(
"""
# Inception Analytics

More than you ever wanted to know about your annotation project
"""
)

uploaded_file = st.sidebar.file_uploader("Upload inception export file (zipped XMI format)")

project = None

if uploaded_file:
    project = load_project(uploaded_file)

if project:
    ## if you already know which layers you are interested in, you may want to hard-code them here.
    ## especially if you are using just some elements of the build-in layers 
    layers = []
    if project.custom_layers:
        layers = sorted(project.custom_layers)
    else:
        layers = sorted(project.layers)

    layer = st.sidebar.selectbox(
        'Select Layer',
       layers,
       format_func=lambda x: x.split('.')[-1]
    )
    
    feature = st.sidebar.selectbox(
        'Select Feature',
        sorted(project.features(layer))
    )

    iaa_type = st.sidebar.selectbox(
        'Select IAA type',
        ['krippendorff','gamma']
    )

    annotators = sorted(project.annotators)
    if len(annotators) > 0:
        selected_annotators = st.sidebar.expander('Select Annotators').multiselect(
            "Annotators",
            options=annotators,
            default=list(annotators),
            key="annotator_select",
        )
    else:
        st.warning('No annotators found in the project.')
        st.stop()

    files = sorted(project.source_file_names)
    if len(files) > 0:
        selected_files = st.sidebar.expander('Select Source Files').multiselect(
            "Files",
            options=files,
            default=list(files),
            key="files_select",
        )
    else:
        st.warning('No source files found in the project.')
        st.stop()

    view = project.select(
        annotation=project.feature_path(layer, feature),
        annotators=selected_annotators, 
        source_files=selected_files
    )

    nr_of_annotated_files = len(project.source_file_names)
    nr_of_all_files = nr_of_annotated_files + len(project.empty_source_file_names)

    stats.write("## Project Stats")
    stats.write('Custom layers: ' + str(len(project.custom_layers)))
    stats.write('Annotators: ' + str(len(project.annotators)))
    stats.write(f"Files (annotated / all): {nr_of_annotated_files}/{nr_of_all_files}")

    stats.write("## Current View")
    stats.write(f'Selected Annotation: **{feature}**')
    stats.write('Selected annotators: ' + str(len(selected_annotators)))
    stats.write('Selected files: ' + str(len(selected_files)))

    counts = view.count(['annotator', 'source_file'])

    stats.write(f'Annotations in Selection: {sum(counts)}')
    stats.write('### Breakdown by Annotator')
    stats.write(view.count('annotator'))
    stats.write('### Breakdown by Labels')
    stats.write(view.value_counts())

    body.write('## Annotation Overview')
    body.write('Select details to include in the overview')

    split_by_files = body.checkbox('Files')
    split_by_labels = body.checkbox('Labels')

    count_fn = view.value_counts if split_by_labels else view.count
    levels = ['annotator']

    if split_by_files:
        levels.append('source_file')

    count_overview = count_fn(grouped_by=levels)

    if count_overview.index.nlevels > 1:
        count_overview = count_overview.unstack(level=0)

    body.write(count_overview)

    body.write('## Progress')
    show_percentages_per_file = body.checkbox('Show completion status of files.')
    body.write(view.progress_chart(normalize=show_percentages_per_file))

    body.write('## Agreement Statistics')
    iaa = view.iaa(measure=iaa_type)
    body.metric(label=iaa_type, value=str(np.round(iaa, 4)))
    body.write(view.pairwise_kappa())

    body.write('### IAA by Label')

    individual_iaa_labels = body.multiselect(
        'Labels to calculate IAA',
        options=view.labels,
        default=view.labels,
        key='individual_iaa_labels'
    )

    if individual_iaa_labels:
        if iaa_type == 'gamma':
            iaa_label_scores = [view.filter_labels(label).iaa(measure=iaa_type) for label in individual_iaa_labels]
            body.write(pd.Series(iaa_label_scores, index=individual_iaa_labels, name=iaa_type))
        else:
            body.warning('Unitising IAA per Label is currently only supported for the _gamma_ IAA measure. '
                         'Please select the appropriate IAA statistic on the left. '
                         'Keep in mind that calculating the _gamma_ measure per label may take a while.')

    body.write('## Confusion Matrices')
    # TODO: wrap in util function
    conf_plots = view.confusion_matrix_plots
    max_cols = 5

    if len(project.annotators) < max_cols:  # organise matrices in triangle
        grid = st_indexed_triangle(project.annotators, offset=1)
        for idx, plot in conf_plots.iteritems():
            a, b = idx
            grid[a][b].write(plot)
    else:  # organise plots in grid, square if possible
        n_annotators = len(annotators)
        n_cols = min(ceil(n_annotators ** 0.5), max_cols)
        n_rows = ceil(n_annotators / n_cols)
        grid = st_grid(n_rows, n_cols)

        i = j = 0
        for plot in conf_plots:
            grid[i][j].write(plot)
            j = (j + 1) % n_cols
            if j == 0:
                i = (i + 1) % n_rows
