from platform import processor

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import sys
import os
import pycountry 

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from notebooks.DataProcessor import ForestDataProcessor

import plotly.express as px


st.markdown("""
    <style>
        .block-container {
            padding-top: 1rem;
        }
    </style>
""", unsafe_allow_html=True)

st.title("Forest and Land Use Data Visualization")

# Configure page settings and layout
st.set_page_config(
    page_title="Forest and Land Use Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.sidebar.title("Are you interested in forest data?")
st.sidebar.markdown("Hijo de puta")

@st.cache_resource
def load_processor():
    return ForestDataProcessor()

processor = load_processor()

df = processor.merged_dataframe

#print(df.head()) 

@st.cache_resource
def load_choropleth_fig():
    fig = px.choropleth(df, geojson=df.geometry, locations=df.index, color_continuous_scale="Viridis", projection="natural earth")
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

st.plotly_chart(fig, use_container_width=True)

country_list = [country.name for country in pycountry.countries]



# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("Forest Data Explorer")
    st.markdown("Explore forest and land use trends around the world.")
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

# ── Histogram ─────────────────────────────────────────────────────────────────
def show_histogram(processor, column_name="annual-change-forest_area"):
    selected_country = st.session_state.get("selected_country", None)

    st.header(f"Showing histogram for column: {column_name}")


    country = st.selectbox(
        "Select a country",
        options=country_list,
        index=country_list.index("Brazil")  # sets Brazil as default
    )
    st.markdown(f"Showing data for: **{country}**")

    try:
        df = processor.merged_dataframe
        country_df = df[df["entity"] == country].dropna(subset=[column_name, "year"])

        if country_df.empty:
            st.warning(f"No data found for '{country}'.")
            return

        fig, ax = plt.subplots(figsize=(12, 5))
        colors = ["#d32f2f" if v < 0 else "#2e7d32" for v in country_df[column_name]]
        ax.bar(country_df["year"], country_df[column_name], color=colors, edgecolor="white", linewidth=0.5)
        ax.axhline(0, color="black", linewidth=0.8, linestyle="--")
        ax.set_title(
            f"{column_name.replace('-', ' ').title()} — {country}",
            fontsize=16,
            fontweight="bold",
        )
        ax.set_xlabel("Year", fontsize=13)
        ax.set_ylabel("Value", fontsize=13)
        ax.grid(axis="y", linestyle="--", alpha=0.4)
        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

    except (KeyError, ValueError) as e:
        st.error(f"Error: {e}")


# ── Page routing ──────────────────────────────────────────────────────────────
if page == "Main Page":
    st.write("Welcome! Click a country on the map, then use the sidebar to explore forest data.")
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