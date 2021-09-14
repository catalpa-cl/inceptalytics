import streamlit as st
import numpy as np
from analytics import Project

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
    stats.write('Nr custom layers: ' + str(len(project.custom_layers)))
    stats.write('Nr annotators: ' + str(len(project.annotators)))
    stats.write(f"Nr files (annotated / all): {nr_of_annotated_files}/{nr_of_all_files}")

    stats.write("## Current View")
    stats.write('Selected annotators: ' + str(len(selected_annotators)))
    stats.write('Selected files: ' + str(len(selected_files)))

    body.write(view.count(['annotator', 'source_file']))

    iaa = view.iaa(measure=iaa_type)
    body.metric(label=iaa_type, value=str(np.round(iaa, 4)))
    body.write(view.pairwise_kappa())

    body.write(view.progress_chart(normalize=True))
    body.write(view.progress_chart(include_empty_files=False))

    body.write('## Confusion Matrices')
    for plot in view.confusion_matrix_plots():
        body.write(plot)