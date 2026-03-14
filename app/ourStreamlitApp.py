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
from notebooks.ImageDownloader import download_esri_image

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
    if st.button("🌍 New Page", width='stretch'):
        st.session_state.page = "New Page"
    if st.button("🛰️ AI Image Analysis", width='stretch'):
        st.session_state.page = "AI Image Analysis"
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
        # print("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")
        st.error(f"Error: {e}")


def draw_chloropleth_map(gdf, column_name):

    print(gdf[gdf['ISO_A3']=='MNG'][column_name].head())
    

    filtered_gdf = gdf[gdf[column_name].notna()]  # Filter out rows where the specified column is NaN

    # Get the latest year available
    year = filtered_gdf["year"].max()
    
    
    # Filter for that year - includes countries with NaN values in column_name
    filtered_gdf = filtered_gdf[filtered_gdf['year'] == year]



    st.write(f"This map shows the data for the indicator {column_name} for the year {year}. You can see the distribution of this indicator across different countries. Darker colors indicate higher values, while lighter colors indicate lower values. Countries with no data are shown in gray.")
    
    # print(f"Drawing map for column: {column_name} (Year: {year})")
    # print(filtered_gdf[column_name].head())
    
    fig = px.choropleth(
        filtered_gdf,
        geojson=filtered_gdf.geometry,
        locations=filtered_gdf.index,
        color=column_name,
        color_continuous_scale='Plasma',
        projection='natural earth'
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
    
    st.plotly_chart(fig, width='stretch', key=f"map_{column_name}")


# ── Page routing ──────────────────────────────────────────────────────────────
if page == "Main Page": 
    st.plotly_chart(fig, width='stretch')
    st.write("Welcome! This big map is showing the latest available data. When you click on a page on the left, the chloropleth map will update to show the data for that specific indicator for the last year available. Scroll down on each page to see more detailed visualizations for each indicator.")
elif page == "Anual Change in forest area":
    draw_chloropleth_map(processor.merged_dataframe, "annual-change-forest_area")
    show_histogram(processor, "annual-change-forest_area")
elif page == "Annual deforestation":  
    draw_chloropleth_map(processor.merged_dataframe, "annual-deforestation")
    show_histogram(processor, "annual-deforestation")
elif page == "Share of land that is protected":
    draw_chloropleth_map(processor.merged_dataframe, "forest-area-as-share-of-land-area")
    show_histogram(processor, "forest-area-as-share-of-land-area")
elif page == "Terrestrial protected areas":
    draw_chloropleth_map(processor.merged_dataframe, "terrestrial-protected-areas_1")
    show_histogram(processor, "terrestrial-protected-areas_1")
elif page == "Red List Index":
    draw_chloropleth_map(processor.merged_dataframe, "red-list-index")  
    show_linegraph(processor, "red-list-index")
elif page == "New Page":
    st.header("Welcome to the New Page!")
    st.write("Petra is the GOAT")


elif page == "AI Image Analysis":
    st.header("🛰️ AI Image Analysis")
    st.write("Select geographical coordinates and zoom level to download satellite imagery from ESRI World Imagery.")
    
    # Create three columns for latitude, longitude, zoom
    col1, col2, col3 = st.columns(3)
    
    with col1:
        latitude = st.slider("Latitude", min_value=-90.0, max_value=90.0, value=0.0, step=0.1)
    
    with col2:
        longitude = st.slider("Longitude", min_value=-180.0, max_value=180.0, value=0.0, step=0.1)
    
    with col3:
        zoom = st.slider("Zoom Level", min_value=1, max_value=18, value=10, step=1)
    
    # Display current coordinates
    st.info(f"📍 Current coordinates: Lat {latitude:.2f}, Lon {longitude:.2f}, Zoom {zoom}")
    
    # Download button
    if st.button("📥 Download Image", use_container_width=True):
        with st.spinner("Downloading image from ESRI..."):
            success, filepath, message = download_esri_image(latitude, longitude, zoom)
            
            if success:
                st.success(f"✅ {message}")
                # Display the downloaded image
                try:
                    from PIL import Image
                    img = Image.open(filepath)
                    st.image(img, caption=f"ESRI Satellite Image - Lat {latitude:.2f}, Lon {longitude:.2f}, Zoom {zoom}")
                except Exception as e:
                    st.error(f"Error displaying image: {str(e)}")
            else:
                st.error(f"❌ {message}")