from platform import processor

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from DataProcessor import ForestDataProcessor
import plotly.express as px
from streamlit_plotly_events import plotly_events

# MUST be first
st.set_page_config(
    page_title="Forest and Land Use Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
    <style>
        .block-container { padding-top: 1rem; }
    </style>
""", unsafe_allow_html=True)

st.title("Forest and Land Use Data Visualization")

@st.cache_resource
def load_processor():
    return ForestDataProcessor()

processor = load_processor()
df = processor.merged_dataframe

@st.cache_data
def load_choropleth_fig():
    _df = processor.merged_dataframe
    fig = px.choropleth(
        _df,
        geojson=_df.geometry,
        color=_df["entity"],
        locations=_df.index,
        color_continuous_scale="Viridis",
        projection="natural earth"
    )
    fig.update_geos(
        visible=False,
        showframe=False,
        projection_type="natural earth",
        fitbounds="locations", 
        center={"lat": 20, "lon": 0},
        lataxis_range=[-60, 85],
        lonaxis_range=[-180, 180],
    )
    fig.update_layout(
        height=450,
        margin={"r":0,"t":0,"l":0,"b":0},
        showlegend=False,
        coloraxis_showscale=False,
    )
    return fig

fig = load_choropleth_fig()

clicked = plotly_events(fig, click_event=True, hover_event=False, override_width="100%", override_height=450)

if clicked:
    country_index = clicked[0]["pointIndex"]
    selected_country = df.index[country_index]
    st.session_state.selected_country = selected_country

selected_country = st.session_state.get("selected_country", None)
if selected_country:
    st.info(f"🌍 Selected: **{selected_country}**")

with st.sidebar:
    st.title("Are you interested in forest data?")
    st.markdown("Hijo de puta")
    st.title("Navigation")
    if st.button("🏠 Main Page", use_container_width=True):
        st.session_state.page = "Main Page"
    if st.button("🌲 Annual Change in Forest Area", use_container_width=True):
        st.session_state.page = "Anual Change in forest area"
    if st.button("🪓 Annual Deforestation", use_container_width=True):
        st.session_state.page = "Annual deforestation"
    if st.button("🛡️ Share of Land Protected", use_container_width=True):
        st.session_state.page = "Share of land that is protected"
    if st.button("⚠️ Terrestrial protected areas", use_container_width=True):
        st.session_state.page = "Terrestrial protected areas"
    if st.button("⭐ Red List Index", use_container_width=True):
        st.session_state.page = "Red List Index"

if "page" not in st.session_state:
    st.session_state.page = "Main Page"

page = st.session_state.page

def show_histogram(processor, column_name="annual-change-forest_area"):
    st.header(f"Showing histogram for column: {column_name}")

    selected_country = st.session_state.get("selected_country", None)

    if not selected_country:
        st.info("🗺️ Click on a country on the map to show its histogram")
        return

    st.markdown(f"Showing data for: **{selected_country}**")

    if not selected_country:
        return

    try:
        df = processor.merged_dataframe
        country_df = df[df["entity"] == selected_country]

        if country_df.empty:
            st.warning(f"No data found for {selected_country}")
            return

        fig, ax = plt.subplots(figsize=(12, 5))
        colors = ["#d32f2f" if v < 0 else "#2e7d32" for v in country_df[column_name]]
        ax.bar(country_df["year"], country_df[column_name], color=colors, edgecolor="white", linewidth=0.5)
        ax.axhline(0, color="black", linewidth=0.8, linestyle="--")
        ax.set_title(f"{column_name} — {selected_country}", fontsize=16, fontweight="bold")
        ax.set_xlabel("Year", fontsize=13)
        ax.set_ylabel("Value", fontsize=13)
        ax.grid(axis="y", linestyle="--", alpha=0.4)
        st.pyplot(fig)

    except (KeyError, ValueError) as e:
        st.error(f"Error: {e}")

if page == "Main Page":
    st.write("Write the description of the project here...")
elif page == "Anual Change in forest area":
    show_histogram(processor, "annual-change-forest_area")
elif page == "Annual deforestation":
    show_histogram(processor, "annual-deforestation")
elif page == "Share of land that is protected":
    show_histogram(processor, "forest-area-as-share-of-land-area")
elif page == "Terrestrial protected areas":
    show_histogram(processor, "terrestrial-protected-areas_1")
elif page == "Red List Index":
    show_histogram(processor, "red-list-index")