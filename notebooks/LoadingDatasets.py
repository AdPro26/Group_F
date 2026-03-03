import pandas as pd
import requests
import json
from pathlib import Path
import zipfile
import geopandas as gpd

# --- Constants ---
DATA_URLS = [
    "https://ourworldindata.org/grapher/annual-change-forest-area.csv?v=1&csvType=full&useColumnShortNames=true",
    "https://ourworldindata.org/grapher/annual-deforestation.csv?v=1&csvType=full&useColumnShortNames=true",
    "https://ourworldindata.org/grapher/terrestrial-protected-areas.csv?v=1&csvType=full&useColumnShortNames=true",
    "https://ourworldindata.org/grapher/forest-area-as-share-of-land-area.csv?v=1&csvType=full&useColumnShortNames=true",
    "https://ourworldindata.org/grapher/red-list-index.csv?v=1&csvType=full&useColumnShortNames=true",
]

METADATA_URLS = [
    "https://ourworldindata.org/grapher/annual-change-forest-area.metadata.json?v=1&csvType=full&useColumnShortNames=true",
    "https://ourworldindata.org/grapher/annual-deforestation.metadata.json?v=1&csvType=full&useColumnShortNames=true",
    "https://ourworldindata.org/grapher/terrestrial-protected-areas.metadata.json?v=1&csvType=full&useColumnShortNames=true",
    "https://ourworldindata.org/grapher/forest-area-as-share-of-land-area.metadata.json?v=1&csvType=full&useColumnShortNames=true",
    "https://ourworldindata.org/grapher/red-list-index.metadata.json?v=1&csvType=full&useColumnShortNames=true",
]

SHAPEFILE_URL = "https://naturalearth.s3.amazonaws.com/110m_cultural/ne_110m_admin_0_countries.zip"


# --- Helper functions ---
def download_file(url: str, save_path: Path, timeout: int = 30) -> None:
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    save_path.write_bytes(response.content)
    print(f"  Downloaded: {save_path.name}")


def download_metadata(url: str, save_path: Path, timeout: int = 30) -> None:
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(response.json(), f, indent=2)
    print(f"  Downloaded metadata: {save_path.name}")


# --- Main Function ---
def load_all_data(download_dir: str | Path = "downloads") -> tuple:
    """
    Downloads (if needed) and loads all datasets and the world shapefile.

    Returns:
        dataframes_list : list of pd.DataFrames (one per dataset)
        metadata_list   : list of metadata dicts
        gdf             : GeoDataFrame of world countries
    """
    download_dir = Path(download_dir)
    download_dir.mkdir(exist_ok=True)

    dataframes_list = []
    metadata_list = []

    # --- CSVs + Metadata ---
    for data_url, metadata_url in zip(DATA_URLS, METADATA_URLS):
        data_path = download_dir / data_url.split("?")[0].split("/")[-1]
        metadata_path = download_dir / metadata_url.split("?")[0].split("/")[-1]

        if not data_path.exists():
            download_file(data_url, data_path)
        else:
            print(f"  Skipping (exists): {data_path.name}")

        if not metadata_path.exists():
            download_metadata(metadata_url, metadata_path)
        else:
            print(f"  Skipping (exists): {metadata_path.name}")

        dataframes_list.append(pd.read_csv(data_path))
        with open(metadata_path, "r", encoding="utf-8") as f:
            metadata_list.append(json.load(f))

    print("✅ All datasets loaded successfully.")

    # --- Shapefile ---
    shapefile_zip_path = download_dir / "ne_110m_admin_0_countries.zip"
    shapefile_dir = download_dir / "ne_110m_admin_0_countries"
    shapefile_path = shapefile_dir / "ne_110m_admin_0_countries.shp"

    if not shapefile_dir.exists():
        if not shapefile_zip_path.exists():
            download_file(SHAPEFILE_URL, shapefile_zip_path)
        with zipfile.ZipFile(shapefile_zip_path, "r") as zip_ref:
            zip_ref.extractall(shapefile_dir)
        print("  Shapefile extracted.")
    else:
        print("  Skipping (exists): shapefile directory")

    gdf = gpd.read_file(shapefile_path)
    print("✅ Shapefile loaded.") 

    return dataframes_list, metadata_list, gdf
