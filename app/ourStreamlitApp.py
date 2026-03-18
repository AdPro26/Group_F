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
        
def _interpolate_plasma(stops, pos):
    """Return the hex color at `pos` by linearly interpolating between plasma stops."""
    pos = max(0.0, min(1.0, pos))
    for i in range(len(stops) - 1):
        p0, c0 = stops[i]
        p1, c1 = stops[i + 1]
        if p0 <= pos <= p1:
            t = (pos - p0) / (p1 - p0) if p1 != p0 else 0
            r = int(int(c0[1:3], 16) + t * (int(c1[1:3], 16) - int(c0[1:3], 16)))
            g = int(int(c0[3:5], 16) + t * (int(c1[3:5], 16) - int(c0[3:5], 16)))
            b = int(int(c0[5:7], 16) + t * (int(c1[5:7], 16) - int(c0[5:7], 16)))
            return f"#{r:02x}{g:02x}{b:02x}"
    return stops[-1][1]


def draw_chloropleth_map(df, column_name):
    filtered_df = df[df[column_name].notnull()].copy()

    real_min = filtered_df[column_name].min()
    real_max = filtered_df[column_name].max()

    EPSILON = 1e-6
    zero_pos = (0 - real_min) / (real_max - real_min)

    plasma_stops = [
        (0.000, "#0d0887"),
        (0.042, "#1b0990"),
        (0.083, "#280b98"),
        (0.125, "#3607a0"),
        (0.167, "#4302a7"),
        (0.208, "#5002ac"),
        (0.250, "#5c01a6"),
        (0.292, "#6a00a8"),
        (0.333, "#7201a8"),
        (0.375, "#8405a7"),
        (0.417, "#9512a1"),
        (0.458, "#a52c60"),
        (0.500, "#b5367a"),
        (0.542, "#c33d80"),
        (0.583, "#d1426a"),
        (0.625, "#de5046"),
        (0.667, "#ed7953"),
        (0.708, "#f48849"),
        (0.750, "#fb9f3a"),
        (0.792, "#fbb130"),
        (0.833, "#fac228"),
        (0.875, "#f7d324"),
        (0.917, "#f4e322"),
        (0.958, "#f2f022"),
        (1.000, "#f0f921"),
    ]

    # Build colorscale: plasma stops either side, grey injected at zero_pos
    custom_colorscale = []

    for pos, color in plasma_stops:
        if pos < zero_pos - EPSILON:
            custom_colorscale.append([pos, color])

    custom_colorscale += [
        [max(0.0, zero_pos - EPSILON), _interpolate_plasma(plasma_stops, zero_pos - EPSILON)],
        [zero_pos,                      "#aaaaaa"],
        [min(1.0, zero_pos + EPSILON),  _interpolate_plasma(plasma_stops, zero_pos + EPSILON)],
    ]

    for pos, color in plasma_stops:
        if pos > zero_pos + EPSILON:
            custom_colorscale.append([pos, color])

    custom_colorscale = sorted(custom_colorscale, key=lambda x: x[0])

    fig = px.choropleth(
        filtered_df,
        locations="ISO_A3",
        locationmode="ISO-3",
        color=column_name,
        color_continuous_scale=custom_colorscale,
        range_color=[real_min, real_max],
        projection="natural earth",
        hover_name="NAME",
        hover_data={"year": True, column_name: True, "ISO_A3": False},
    )

    tick_vals = [real_min + i * (real_max - real_min) / 4 for i in range(5)]
    fig.update_coloraxes(
        colorbar=dict(
            tickvals=tick_vals,
            ticktext=[f"{v:.1f}" for v in tick_vals],
            title=column_name,
        )
    )

    fig.update_geos(
        fitbounds="locations",
        visible=False,
        center={"lat": 20, "lon": 0}
    )
    fig.update_layout(
        height=450,
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
    )

    st.write(
        f"This map shows the most recent available data for **{column_name}**. "
        "Darker colors indicate higher values. "
        "Countries with a value of **0** are shown in **grey**. "
        "Countries with no data are shown in the default map background."
    )

    st.plotly_chart(fig, width='stretch', key=f"map_{column_name}")

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
    show_linegraph(processor, "red-list-index")

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