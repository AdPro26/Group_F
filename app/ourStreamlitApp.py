from platform import processor

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import sys
import os
import pycountry 

from datetime import datetime
from PIL import Image as PILImage

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from notebooks.DataProcessor import ForestDataProcessor
from utils.charts import draw_chloropleth_map, show_histogram, show_histogram_red_list_index
from _pages.aiAnalysis import render as render_ai


import plotly.express as px


st.markdown("""
    <style>
        .block-container {
            padding-top: 1rem;
        }
    </style>
    <script>
        window.addEventListener('beforeunload', function (e) {
            e.preventDefault();
            e.returnValue = 'Are you sure you want to close this beautiful page?';
        });
    </script>
""", unsafe_allow_html=True)

st.title("Forest and Land Use Data Visualization")

# Configure page settings and layout
st.set_page_config(
    page_title="Forest and Land Use Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.sidebar.title("Are you interested in forest and land data?")
st.sidebar.markdown("Dive into exploration with this tool!")

@st.cache_resource
def load_processor():
    return ForestDataProcessor()

processor = load_processor()

@st.cache_resource
def load_choropleth_fig():
    df_main = processor.merged_dataframe["forest-area-as-share-of-land-area"]
    df_filtered = df_main[df_main["forest-area-as-share-of-land-area"] != 0]
    fig = px.choropleth(
        df_filtered,
        locations="ISO_A3",
        locationmode="ISO-3",
        color="forest-area-as-share-of-land-area",
        color_continuous_scale="Viridis",
        projection="natural earth",
        hover_name="NAME",
    )
    fig.update_geos(
        fitbounds="locations",
        visible=False,
        center={"lat": 20, "lon": 0}
    )
    fig.update_layout(
        height=450,
        margin={"r":0,"t":0,"l":0,"b":0},
    )
    return fig

fig = load_choropleth_fig()

#tiles_around  = config["image_settings"]["tiles_around"]
#image_model   = config["image_analysis"]["model"]
#image_prompt  = config["image_analysis"]["prompt"]
#text_model    = config["text_analysis"]["model"]
#text_prompt   = config["text_analysis"]["prompt"]


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("Forest Data Explorer")
    st.markdown("Explore forest and land use trends around the world.")
    st.title("Navigation")
    if st.button("🏠 Main Page", width='stretch'):
        st.session_state.page = "Main Page"
    if st.button("🌲 Annual Change in Forest Area", width='stretch'):
        st.session_state.page = "Anual Change in forest area"
    if st.button("🪓 Annual Deforestation", width='stretch'):
        st.session_state.page = "Annual deforestation"
    if st.button("🛡️ Share of Land Protected", width='stretch'):
        st.session_state.page = "Share of land that is protected"
    if st.button("⚠️ Terrestrial protected areas", width='stretch'):
        st.session_state.page = "Terrestrial protected areas"
    if st.button("⭐ Red List Index", width='stretch'):
        st.session_state.page = "Red List Index"
    if st.button("🛰️ AI Image Analysis", width='stretch'):
        st.session_state.page = "AI Image Analysis"
if "page" not in st.session_state:
    st.session_state.page = "Main Page"

page = st.session_state.page


# ── Page routing ──────────────────────────────────────────────────────────────
if page == "Main Page": 
    st.plotly_chart(fig, width='stretch')
    st.write("Welcome! This big map is showing the latest available data. When you click on a page on the left, the chloropleth map will update to show the data for that specific indicator for the last year available. Scroll down on each page to see more detailed visualizations for each indicator.")

elif page == "Anual Change in forest area":
    draw_chloropleth_map(processor.annual_change_df, "annual-change-forest_area")
    show_histogram(processor.raw_dataframes["annual-change-forest_area"], "annual-change-forest_area")

elif page == "Annual deforestation":
    draw_chloropleth_map(processor.annual_deforestation_df, "annual-deforestation")
    show_histogram(processor.raw_dataframes["annual-deforestation"], "annual-deforestation")

elif page == "Share of land that is protected":
    draw_chloropleth_map(processor.forest_share_df, "forest-area-as-share-of-land-area")
    show_histogram(processor.raw_dataframes["forest-area-as-share-of-land-area"], "forest-area-as-share-of-land-area")

elif page == "Terrestrial protected areas":
    draw_chloropleth_map(processor.terrestrial_protected_df, "terrestrial-protected-areas_1")
    show_histogram(processor.raw_dataframes["terrestrial-protected-areas"], "terrestrial-protected-areas_1")

elif page == "Red List Index":
    draw_chloropleth_map(processor.red_list_index, "red-list-index")
    show_histogram_red_list_index(processor, "red-list-index")

elif page == "AI Image Analysis":
    render_ai()
    