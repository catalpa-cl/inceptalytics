import random

import pandas as pd
import streamlit as st
import re
from zipfile import ZipFile

st.set_page_config("Inception Analytics", None, "wide", "auto")

"""
# Inception Analytics

More than you ever wanted to know about your annotation project
"""

option = st.sidebar.selectbox(
    'Select Mode',
     ["simple", "advanced"])


uploaded_file = st.file_uploader("Upload inception export (XMI format)")

if uploaded_file:
    with ZipFile(uploaded_file) as archive:
        xmi_selector = re.compile("[^/]+\.xmi")
        xmi_filenames = [f for f in archive.namelist() if xmi_selector.fullmatch(f)]


        st.dataframe(pd.DataFrame(archive.namelist()))
#        st.dataframe(pd.DataFrame(xmi_filenames))