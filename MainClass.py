import pandas as pd
import requests
import os
import json
from pathlib import Path

data_urls = [
    "https://ourworldindata.org/grapher/annual-change-forest-area.csv?v=1&csvType=full&useColumnShortNames=true",
    "https://ourworldindata.org/grapher/annual-deforestation.csv?v=1&csvType=full&useColumnShortNames=true",
    "https://ourworldindata.org/grapher/terrestrial-protected-areas.csv?v=1&csvType=full&useColumnShortNames=true",
    "https://ourworldindata.org/grapher/forest-area-as-share-of-land-area.csv?v=1&csvType=full&useColumnShortNames=true",
]

metadata_urls = [
    "https://ourworldindata.org/grapher/annual-change-forest-area.metadata.json?v=1&csvType=full&useColumnShortNames=true",
    "https://ourworldindata.org/grapher/annual-deforestation.metadata.json?v=1&csvType=full&useColumnShortNames=true",
    "https://ourworldindata.org/grapher/terrestrial-protected-areas.metadata.json?v=1&csvType=full&useColumnShortNames=true",
    "https://ourworldindata.org/grapher/share-degraded-land.metadata.json?v=1&csvType=full&useColumnShortNames=true",
]


def download_file(url: str, save_path: Path):
    response = requests.get(url)
    response.raise_for_status()

    with open(save_path, "wb") as f:
        f.write(response.content)

    print(f"Downloaded: {save_path.name}")


def download_metadata(url: str, save_path: Path):
    response = requests.get(url)
    response.raise_for_status()

    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(response.json(), f, indent=2)

    print(f"Downloaded metadata: {save_path.name}")


# Ensure downloads folder exists
download_dir = Path("downloads")
download_dir.mkdir(exist_ok=True)

dataframes_list = []
metadata_list = []

for i, (data_url, metadata_url) in enumerate(zip(data_urls, metadata_urls)):

    data_path = download_dir / f"data_{i}.csv"
    metadata_path = download_dir / f"metadata_{i}.json"

    # Download only if files do not exist
    if not data_path.exists():
        download_file(data_url, data_path)
    else:
        print(f"{data_path.name} already exists. Skipping download.")

    if not metadata_path.exists():
        download_metadata(metadata_url, metadata_path)
    else:
        print(f"{metadata_path.name} already exists. Skipping download.")

    # Always load from local files
    df = pd.read_csv(data_path)
    with open(metadata_path, "r", encoding="utf8") as f:
        metadata = json.load(f)

    dataframes_list.append(df)
    metadata_list.append(metadata)

print("All datasets loaded successfully.")