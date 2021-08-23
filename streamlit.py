import streamlit as st
import pandas as pd
import numpy as np
from analytics import Project
from utils import construct_feature_path

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
    layer = st.sidebar.selectbox(
        'Select Layer',
        sorted(project.custom_layers)
    )

    feature = st.sidebar.selectbox(
        'Select Feature',
        sorted(project.features(layer))
    )


    annotators = sorted(project.annotators)
    selected_annotators = st.sidebar.multiselect(
        "Annotators",
        options=annotators,
        default=list(annotators),
        key="annotator_select",
    )

    files = sorted(project.source_file_names)
    selected_files = st.sidebar.multiselect(
        "Files",
        options=files,
        default=list(files),
        key="files_select",
    )

    view = project.select(
        annotation=construct_feature_path(layer, feature), 
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

    body.write(view.iaa(measure='krippendorff'))
    body.write(view.iaa_pairwise())

    body.write(view.progress_chart())
    body.write(view.progress_chart(include_empty_files=False))
    
#   body.write(view.confusion_matrix_plots())