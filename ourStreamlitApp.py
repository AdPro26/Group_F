import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

st.title("Forest and Land Use Data Visualization")


# Configure page settings and layout
st.set_page_config(
    page_title="Movie Data Processor",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.sidebar.title("Are you interested in forest data?")
st.sidebar.markdown("Hijo de puta")


st.balloons()

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
    if st.button("⭐ Our Special Dataset", use_container_width=True):
        st.session_state.page = "OUR SPECIAL DATASET"


# Initialize default page
if "page" not in st.session_state:
    st.session_state.page = "Main Page"

page = st.session_state.page

if page == "Main Page":
    st.write("Welcome!")
elif page == "Anual Change in forest area":
    st.write("Forest area content...")
elif page == "Annual deforestation":
    st.write("Deforestation content...")
elif page == "Share of land that is protected":
    st.write("Protected land content...")       
elif page == "Share of land that is degraded":
    st.write("Degraded land content...")
elif page == "OUR SPECIAL DATASET":
    st.write("Special dataset content...")

