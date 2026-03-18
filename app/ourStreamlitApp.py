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
from notebooks.Locations import download_area, analyse_image, analyse_text, already_in_csv, save_to_csv, config

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
def show_histogram(df_raw, column_name="annual-change-forest_area"):
    st.header(f"Showing histogram for column: {column_name}")

    country = st.selectbox(
        "Select a country",
        options=country_list,
        index=country_list.index("Brazil")  # sets Brazil as default
    )
    st.markdown(f"Showing data for: **{country}**")

    try:
        country_df = df_raw[df_raw["entity"] == country].dropna(subset=[column_name, "year"])

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


def draw_chloropleth_map(df, column_name):
    # Each row is already the most recent year per country — no further filtering needed
    filtered_df = df[df[column_name] != 0].copy()

    st.write(
        f"This map shows the most recent available data for **{column_name}**. "
        "Darker colors indicate higher values, while lighter colors indicate lower values. "
        "Countries with no data are shown in gray."
    )

    fig = px.choropleth(
        filtered_df,
        locations="ISO_A3",
        locationmode="ISO-3",
        color=column_name,
        color_continuous_scale="Plasma",
        projection="natural earth",
        hover_name="NAME",
        hover_data={"year": True, column_name: True, "ISO_A3": False},
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
    draw_chloropleth_map(processor.merged_dataframe["annual-change-forest_area"], "annual-change-forest_area")
    show_histogram(processor.raw_dataframes["annual-change-forest_area"], "annual-change-forest_area")
elif page == "Annual deforestation":
    draw_chloropleth_map(processor.merged_dataframe["annual-deforestation"], "annual-deforestation")
    show_histogram(processor.raw_dataframes["annual-deforestation"], "annual-deforestation")
elif page == "Share of land that is protected":
    draw_chloropleth_map(processor.merged_dataframe["forest-area-as-share-of-land-area"], "forest-area-as-share-of-land-area")
    show_histogram(processor.raw_dataframes["forest-area-as-share-of-land-area"], "forest-area-as-share-of-land-area")
elif page == "Terrestrial protected areas":
    draw_chloropleth_map(processor.merged_dataframe["terrestrial-protected-areas"], "terrestrial-protected-areas_1")
    show_histogram(processor.raw_dataframes["terrestrial-protected-areas"], "terrestrial-protected-areas_1")
elif page == "Red List Index":
    draw_chloropleth_map(processor.merged_dataframe["red-list-index"], "red-list-index")
    show_linegraph(processor, "red-list-index")
elif page == "New Page":
    st.header("Welcome to the New Page!")
    st.write("Petra is the GOAT")


elif page == "AI Image Analysis":
    st.header("🛰️ AI Image Analysis")
    st.write("Select geographical coordinates and zoom level to download and analyse satellite imagery.")

    col1, col2, col3 = st.columns(3)
    with col1:
        latitude = st.slider("Latitude", min_value=-90.0, max_value=90.0, value=0.0, step=0.1)
    with col2:
        longitude = st.slider("Longitude", min_value=-180.0, max_value=180.0, value=0.0, step=0.1)
    with col3:
        zoom = st.slider("Zoom Level", min_value=1, max_value=18, value=10, step=1)

    st.info(f"📍 Current coordinates: Lat {latitude:.2f}, Lon {longitude:.2f}, Zoom {zoom}")

    if st.button("🔍 Download & Analyse", use_container_width=True):
        from datetime import datetime
        from PIL import Image as PILImage

        tiles_around  = config["image_settings"]["tiles_around"]
        image_model   = config["image_analysis"]["model"]
        image_prompt  = config["image_analysis"]["prompt"]
        text_model    = config["text_analysis"]["model"]
        text_prompt   = config["text_analysis"]["prompt"]

        BASE_DIR  = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        save_path = os.path.join(BASE_DIR, "images", f"tile_{latitude:.4f}_{longitude:.4f}_{zoom}.png")

        # ── Check cache ────────────────────────────────────────────────────────
        cached = already_in_csv(latitude, longitude, zoom)

        if cached:
            st.info("📦 Loaded from cache — skipping AI pipeline.")
            col_img, col_desc = st.columns(2)
            with col_img:
                st.subheader("🖼️ Satellite Image")
                if os.path.exists(save_path):
                    st.image(PILImage.open(save_path), use_container_width=True)
                else:
                    st.warning("Cached image file not found on disk.")
            with col_desc:
                st.subheader("📝 Image Description")
                st.write(cached["image_description"])

            st.divider()
            st.subheader("🌍 Environmental Risk Assessment")
            if cached.get("danger", "N") == "Y":
                st.error("## ⚠️ ENVIRONMENTAL RISK DETECTED")
            else:
                st.success("## ✅ No significant environmental risk detected")
            with st.expander("See full assessment"):
                st.write(cached["text_description"])

        else:
            # ── Step 1: Download image ─────────────────────────────────────────
            with st.spinner("Downloading satellite image from ESRI..."):
                try:
                    download_area(latitude, longitude, zoom, tiles_around, save_path)
                    download_ok = True
                except Exception as e:
                    st.error(f"❌ Failed to download image: {e}")
                    download_ok = False

            if download_ok:
                # ── Step 2: Image + description side by side ───────────────────
                col_img, col_desc = st.columns(2)
                with col_img:
                    st.subheader("🖼️ Satellite Image")
                    st.image(PILImage.open(save_path),
                             caption=f"Lat {latitude:.2f}, Lon {longitude:.2f}, Zoom {zoom}",
                             use_container_width=True)

                description = None
                with col_desc:
                    st.subheader("📝 Image Description")
                    with st.spinner(f"Describing image with {image_model}..."):
                        try:
                            description = analyse_image(save_path, image_model, image_prompt)
                            st.write(description)
                        except Exception as e:
                            st.error(f"Image description failed: {e}")

                # ── Step 3: Risk assessment below both ────────────────────────
                if description:
                    st.divider()
                    st.subheader("🌍 Environmental Risk Assessment")
                    with st.spinner(f"Assessing environmental risk with {text_model}..."):
                        try:
                            risk_text = analyse_text(description, text_model, text_prompt)
                            is_danger = "Y" in risk_text[:5]

                            if is_danger:
                                st.error("## ⚠️ ENVIRONMENTAL RISK DETECTED")
                            else:
                                st.success("## ✅ No significant environmental risk detected")

                            with st.expander("See full assessment"):
                                st.write(risk_text)

                            save_to_csv({
                                "timestamp":         datetime.now().isoformat(),
                                "latitude":          latitude,
                                "longitude":         longitude,
                                "zoom":              zoom,
                                "image_description": description,
                                "image_prompt":      image_prompt,
                                "image_model":       image_model,
                                "text_description":  risk_text,
                                "text_prompt":       text_prompt,
                                "text_model":        text_model,
                                "danger":            "Y" if is_danger else "N",
                            })
                        except Exception as e:
                            st.error(f"Risk assessment failed: {e}")