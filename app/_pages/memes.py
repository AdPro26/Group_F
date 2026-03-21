import random
from pathlib import Path

import streamlit as st

# --- Configuration ---
MEDIA_FOLDER = Path("memesMedia")  # Change this to your actual folder path

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm"}

MEDIA_WIDTH = 480  # Fixed width in pixels — adjust to your liking


def _get_all_media_files() -> list[Path]:
    """Scans the media folder and returns all image and video files."""
    if not MEDIA_FOLDER.exists():
        return []
    return [
        f for f in MEDIA_FOLDER.rglob("*")
        if f.suffix.lower() in IMAGE_EXTENSIONS | VIDEO_EXTENSIONS
    ]


def _render():
    """
    Builds the page layout with:
    - A 'Random Media Generator' button
    - A fixed-size placeholder that displays a random image or video
    """

    st.button(
        "🎲 Random Media Generator",
        key="random_media_btn",
        use_container_width=True,
        type="primary",
    )

    if st.session_state.get("random_media_btn"):
        media_files = _get_all_media_files()

        if not media_files:
            st.warning(
                f"No media files found in `{MEDIA_FOLDER.resolve()}`. "
                "Please check your folder path."
            )
            return

        picked: Path = random.choice(media_files)
        suffix = picked.suffix.lower()

        # Center the media using columns
        col_left, col_media, col_right = st.columns([1, 2, 1])

        with col_media:
            if suffix in IMAGE_EXTENSIONS:
                st.image(
                    str(picked),
                    caption=picked.name,
                    width=MEDIA_WIDTH,
                )
            elif suffix in VIDEO_EXTENSIONS:
                st.video(str(picked))
                # Clamp video width via CSS
                st.markdown(
                    f"""
                    <style>
                        video {{
                            max-width: {MEDIA_WIDTH}px !important;
                            height: auto !important;
                        }}
                    </style>
                    """,
                    unsafe_allow_html=True,
                )


# --- Entrypoint for testing this page standalone ---
if __name__ == "__main__":
    st.set_page_config(page_title="Random Media", layout="wide")
    st.title("Random Media Generator")
    _render()