import pandas as pd
import streamlit as st
import sys
sys.path.append("..") 
from analytics import Project

@st.cache
def load_project(file):
    return Project.from_zipped_xmi(file)

st.set_page_config("Inception Analytics", None, "wide", "auto")

"""
# Inception Analytics

More than you ever wanted to know about your annotation project
"""

uploaded_file = st.file_uploader("Upload inception export file (zipped XMI format)")

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
    selected_annotators = st.sidebar.beta_expander("Select annotators").multiselect(
        "Annotators",
        options=annotators,
        default=list(annotators),
        key="annotator_select",
    )

    files = sorted(project.source_file_names)
    selected_files = st.sidebar.beta_expander("Select source files").multiselect(
        "Files",
        options=files,
        default=list(files),
        key="files_select",
    )

    annotation_select = layer + '>' + feature
    view = project.select(annotation=annotation_select, annotators=selected_annotators, source_files=selected_files)
    st.write(view.counts())
