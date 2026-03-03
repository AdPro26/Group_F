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

st.sidebar.title("Are you interested in forest and land data?")
st.sidebar.markdown("Dive into exploration with this tool!")

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

st.plotly_chart(fig, width='stretch')

country_list = [country.name for country in pycountry.countries]



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

if "page" not in st.session_state:
    st.session_state.page = "Main Page"

page = st.session_state.page

# ── Histogram ─────────────────────────────────────────────────────────────────
def show_histogram(processor, column_name="annual-change-forest_area"):
   # selected_country = st.session_state.get("selected_country", None)

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

def show_linegraph(processor, column_name="red-list-index"):
    st.header("Red List Index Trends")

    countries = st.multiselect("Select countries", options=country_list, default=["Chile", "Georgia","Italy","Serbia"])

    if not countries:
        st.warning("Please select at least one country.")
        return

    try:
        # Get the DataFrame from your fixed function
        df_plot = processor.get_red_list_index(countries)

        fig, ax = plt.subplots(figsize=(10, 5))


        # Loop through each country to create a separate line
        for country in countries:
            # Filter the data just for this specific country
            country_data = df_plot[df_plot["entity"] == country]
            
            if not country_data.empty:
                ax.plot(
                    country_data["year"], 
                    country_data[column_name], 
                    label=country
                )

        ax.set_title("Species Survival Trend (Red List Index)")
        ax.set_xlabel("Year")
        ax.set_ylabel("Index (1.0 = Not Threatened)")
        ax.legend() # This shows which color belongs to which country
        ax.grid(True, alpha=0.3)
        
        st.pyplot(fig)

    except Exception as e:
        print("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")
        st.error(f"Error: {e}")


def update_map(column_name, year=2025):
     
    filtered_df = df[df['year'] == year]
    
    fig.update_traces(
        selector=dict(type='choropleth'),
        locations=filtered_df.index,
        z=filtered_df[column_name],
        colorscale='Plasma'
    )
    fig.update_geos(fitbounds="locations", visible=False)
    
    # Remove margin from the figure itself
    fig.update_layout(margin=dict(l=0, r=0, t=0, b=0))
    
    st.plotly_chart(fig, width='content', key=f"map_{column_name}")

# ── Page routing ──────────────────────────────────────────────────────────────
if page == "Main Page":
    st.write("Welcome! This big map is showing the latest available data for the year 2025. When you click on a page on the left, the map will update to show the data for that specific indicator. Scroll down on each page to see more detailed visualizations for each indicator.")
elif page == "Anual Change in forest area":
    show_histogram(processor, "annual-change-forest_area")
elif page == "Annual deforestation":
    show_histogram(processor, "annual-deforestation")
elif page == "Share of land that is protected":
    show_histogram(processor, "forest-area-as-share-of-land-area")
elif page == "Terrestrial protected areas":
    show_histogram(processor, "terrestrial-protected-areas_1")
elif page == "Red List Index":
    show_linegraph(processor, "red-list-index")