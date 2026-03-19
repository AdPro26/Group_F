import os
import sys
import streamlit as st
from datetime import datetime
from PIL import Image as PILImage

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from notebooks.Locations import download_area, analyse_image, analyse_text, already_in_csv, save_to_csv, config


def _get_parameters():
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

    return latitude, longitude, zoom


def _build_layout():
    """Pre-build the full page skeleton with empty placeholders."""
    st.write("When you click the button below, the app will download the satellite image, analyse it with AI, and provide an environmental risk assessment.")

    clicked = st.button("🔍 Download & Analyse", use_container_width=True)

    col_img, col_desc = st.columns(2)
    with col_img:
        st.subheader("🖼️ Satellite Image")
        img_placeholder = st.empty()

    with col_desc:
        st.subheader("📝 Image Description")
        desc_placeholder = st.empty()

    st.divider()
    st.subheader("🌍 Environmental Risk Assessment")
    risk_status_placeholder = st.empty()
    risk_detail_placeholder = st.empty()

    return clicked, img_placeholder, desc_placeholder, risk_status_placeholder, risk_detail_placeholder


def _fill_from_cache(cached, save_path, img_placeholder, desc_placeholder, risk_status_placeholder, risk_detail_placeholder):
    st.info("📦 Loaded from cache — skipping AI pipeline.")

    if os.path.exists(save_path):
        img_placeholder.image(PILImage.open(save_path), use_container_width=True)
    else:
        img_placeholder.warning("Cached image file not found on disk.")

    desc_placeholder.write(cached["image_description"])

    if cached.get("danger", "N") == "Y":
        risk_status_placeholder.error("## ⚠️ ENVIRONMENTAL RISK DETECTED")
    else:
        risk_status_placeholder.success("## ✅ No significant environmental risk detected")

    with risk_detail_placeholder.expander("See full assessment"):
        st.write(cached["text_description"])


def _run_pipeline(latitude, longitude, zoom, save_path, img_placeholder, desc_placeholder, risk_status_placeholder, risk_detail_placeholder):
    tiles_around = config["image_settings"]["tiles_around"]
    image_model  = config["image_analysis"]["model"]
    image_prompt = config["image_analysis"]["prompt"]
    text_model   = config["text_analysis"]["model"]
    text_prompt  = config["text_analysis"]["prompt"]

    # ── Step 1: Download ──────────────────────────────────────────────────────
    img_placeholder.info("⏳ Downloading satellite image...")
    desc_placeholder.info("⏳ Waiting for image download...")
    risk_status_placeholder.info("⏳ Waiting for image description...")

    with st.spinner("Downloading satellite image from ESRI..."):
        try:
            download_area(latitude, longitude, zoom, tiles_around, save_path)
            img_placeholder.image(
                PILImage.open(save_path),
                caption=f"Lat {latitude:.2f}, Lon {longitude:.2f}, Zoom {zoom}",
                use_container_width=True,
            )
        except Exception as e:
            img_placeholder.error(f"❌ Failed to download image: {e}")
            desc_placeholder.warning("Skipped — no image to describe.")
            risk_status_placeholder.warning("Skipped — no image to analyse.")
            return

    # ── Step 2: Describe image ────────────────────────────────────────────────
    desc_placeholder.info("⏳ Analysing image...")
    with st.spinner(f"Describing image with {image_model}..."):
        try:
            description = analyse_image(save_path, image_model, image_prompt)
            desc_placeholder.write(description)
        except Exception as e:
            desc_placeholder.error(f"Image description failed: {e}")
            risk_status_placeholder.warning("Skipped — description unavailable.")
            return

    # ── Step 3: Risk assessment ───────────────────────────────────────────────
    risk_status_placeholder.info("⏳ Assessing environmental risk...")
    with st.spinner(f"Assessing environmental risk with {text_model}..."):
        try:
            risk_text = analyse_text(description, text_model, text_prompt)
            is_danger = "Y" in risk_text[:5]

            if is_danger:
                risk_status_placeholder.error("## ⚠️ ENVIRONMENTAL RISK DETECTED")
            else:
                risk_status_placeholder.success("## ✅ No significant environmental risk detected")

            with risk_detail_placeholder.expander("See full assessment"):
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
            risk_status_placeholder.error(f"Risk assessment failed: {e}")


def render():
    latitude, longitude, zoom = _get_parameters()

    BASE_DIR  = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    save_path = os.path.join(BASE_DIR, "images", f"tile_{latitude:.4f}_{longitude:.4f}_{zoom}.png")

    clicked, img_ph, desc_ph, risk_status_ph, risk_detail_ph = _build_layout()

    if not clicked:
        return

    cached = already_in_csv(latitude, longitude, zoom)
    if cached:
        _fill_from_cache(cached, save_path, img_ph, desc_ph, risk_status_ph, risk_detail_ph)
    else:
        _run_pipeline(latitude, longitude, zoom, save_path, img_ph, desc_ph, risk_status_ph, risk_detail_ph)