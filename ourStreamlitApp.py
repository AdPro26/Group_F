from platform import processor

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from DataProcessor import ForestDataProcessor

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


with st.sidebar:
    st.title("Navigation")
    
    if st.button("🏠 Main Page", use_container_width=True):
        st.session_state.page = "Main Page"
    if st.button("🌲 Annual Change in Forest Area", use_container_width=True):
        st.session_state.page = "Anual Change in forest area"
    if st.button("🪓 Annual Deforestation", use_container_width=True):
        st.session_state.page = "Annual deforestation"
    if st.button("🛡️ Share of Land Protected", use_container_width=True):
        st.session_state.page = "Share of land that is protected"
    if st.button("⚠️ Share of Land Degraded", use_container_width=True):
        st.session_state.page = "Share of land that is degraded"
    if st.button("⭐ Red List Index", use_container_width=True):
        st.session_state.page = "Red List Index"


# Initialize default page
if "page" not in st.session_state:
    st.session_state.page = "Main Page"

page = st.session_state.page

def show_annual_forest_change(processor):
    st.header("🌲 Annual Change in Forest Area")

    country = st.text_input("Enter a country name", value="Brazil")

    if st.button("Generate Histogram"):
        try:
            df = processor.merged_dataframe

            print(df.columns)

            fig, ax = plt.subplots(figsize=(12, 5))

            colors = ["#d32f2f" if v < 0 else "#2e7d32" for v in df["annual-change-forest_area"]]
            ax.bar(df["year"], df["annual-change-forest_area"], color=colors, edgecolor="white", linewidth=0.5)

            ax.axhline(0, color="black", linewidth=0.8, linestyle="--")
            ax.set_title(f"Annual Forest Area Change — {country}", fontsize=16, fontweight="bold")
            ax.set_xlabel("year", fontsize=13)
            ax.set_ylabel("Net Forest Conversion (ha)", fontsize=13)
            ax.grid(axis="y", linestyle="--", alpha=0.4)

            st.pyplot(fig)

            st.subheader("Summary Statistics")
            st.dataframe(df.describe().rename(columns={"Forest_Change": "Forest Change (ha)"}))

        except (KeyError, ValueError) as e:
            st.error(f"Error: {e}")
            

if page == "Main Page":
    st.write("Write the description of the project here, and maybe some instructions on how to use the dashboard. You can also include some key insights or highlights from the data to engage users right away.")
elif page == "Anual Change in forest area":
    show_annual_forest_change(processor)
elif page == "Annual deforestation":
    st.write("Deforestation content...")
elif page == "Share of land that is protected":
    st.write("Protected land content...")       
elif page == "Share of land that is degraded":
    st.write("Degraded land content...")
elif page == "OUR SPECIAL DATASET":
    st.write("Special dataset content...")

