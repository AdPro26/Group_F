import pandas as pd
import geopandas as gpd
from pathlib import Path

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

DATASET_NAMES = [
        "annual-change-forest_area",
        "annual-deforestation",
        "forest-area-as-share-of-land-area",
        "terrestrial-protected-areas",
        "red-list-index",
    ]


# --- Helper functions ---
def download_file(url: str, save_path: Path, timeout: int = 30) -> None:
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    save_path.write_bytes(response.content)


def download_metadata(url: str, save_path: Path, timeout: int = 30) -> None:
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(response.json(), f, indent=2)



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

        try:
            dataframes_list.append(pd.read_csv(data_path))
        except FileNotFoundError:
            download_file(data_url, data_path)
            dataframes_list.append(pd.read_csv(data_path))

        try:
            with open(metadata_path, "r", encoding="utf-8") as f:
                metadata_list.append(json.load(f))
        except FileNotFoundError:
            download_metadata(metadata_url, metadata_path)
            with open(metadata_path, "r", encoding="utf-8") as f:
                metadata_list.append(json.load(f))

    # --- Shapefile ---
    shapefile_zip_path = download_dir / "countries.zip"
    shapefile_dir = download_dir / "countries"
    shapefile_path = shapefile_dir / "ne_110m_admin_0_countries.shp"

    def _ensure_shapefile_zip(shapefile_zip_path):
        try:
            zipfile.ZipFile(shapefile_zip_path)
        except (FileNotFoundError, zipfile.BadZipFile):
            download_file(SHAPEFILE_URL, shapefile_zip_path)

    try:
        gdf = gpd.read_file(shapefile_path)
    except Exception:
        _ensure_shapefile_zip(shapefile_zip_path)
        with zipfile.ZipFile(shapefile_zip_path, "r") as zip_ref:
            zip_ref.extractall(shapefile_dir)
        gdf = gpd.read_file(shapefile_path)


    return dataframes_list, metadata_list, gdf


def do_the_merging2(dataframes_list: list[pd.DataFrame], gdf: gpd.GeoDataFrame, download_dir: str | Path = "downloads") -> dict[str, pd.DataFrame]:


    # --- Prepare GeoDataFrame ---
    gdf_clean = gdf[["NAME", "ISO_A3", "geometry"]].copy()
    gdf_clean["ISO_A3"] = gdf_clean["ISO_A3"].replace("-99", pd.NA)
    all_world = gdf_clean[["ISO_A3", "NAME"]].dropna(subset=["ISO_A3"]).drop_duplicates("ISO_A3")

    # Save to Excel (drop geometry since it's not needed)
    all_world[["ISO_A3", "NAME"]].to_excel(download_dir / "all_world_countries.xlsx", index=False)

    download_dir = Path(download_dir)
    download_dir.mkdir(exist_ok=True)

    results = {}

    for df, name in zip(dataframes_list, DATASET_NAMES):
        df = df.copy()

        df = df.fillna(0)
        df.columns = [c.lower().strip() for c in df.columns]

        #print(f"\n--- Processing: {name} ---")
        #print(df.isna().sum())

        # Remove rows where 'code' is missing or empty (e.g. continents, world aggregates)
        df = df[df["code"].notna() & (df["code"].str.strip() != "")]
        # Remove rows where 'code' contains underscores (e.g. OWID_XXX aggregates)
        df = df[~df["code"].str.contains("_", na=False)]

        # Identify value columns (everything except the key columns)
        key_cols = ["entity", "code", "year"]
        value_cols = [c for c in df.columns if c not in key_cols]

        # Rename value columns using the dataset name
        if len(value_cols) == 1:
            rename_map = {value_cols[0]: name}
        else:
            rename_map = {c: f"{name}_{i+1}" for i, c in enumerate(value_cols)}
        df = df.rename(columns=rename_map)

        # --- Merge with GeoDataFrame ---
        merged_geo = gdf_clean.merge(df, left_on="ISO_A3", right_on="code", how="left")
        merged_geo = merged_geo.fillna(0)


        indicator_cols = [c for c in merged_geo.columns if c not in ["NAME", "ISO_A3", "geometry", "entity", "code", "year"]]

        # --- Keep most recent year per country ---
        records = []
        for iso, group in merged_geo.groupby("ISO_A3"):
            # Only consider rows with a valid year (not 0 from fillna)
            valid_years = group[group["year"] != 0]
            if not valid_years.empty:
                latest_row = valid_years.loc[valid_years["year"].idxmax()]
                row = {
                    "ISO_A3": iso,
                    "NAME": group["NAME"].iloc[0],
                    "entity": latest_row.get("entity", None),
                    "year": int(latest_row["year"]),
                }
                for col in indicator_cols:
                    row[col] = latest_row[col]
            else:
                row = {
                    "ISO_A3": iso,
                    "NAME": group["NAME"].iloc[0],
                    "entity": group["entity"].iloc[0] if "entity" in group.columns else None,
                    "year": "-",
                }
                for col in indicator_cols:
                    row[col] = 0
            records.append(row)

        latest_df = pd.DataFrame(records)
        latest_df[indicator_cols] = latest_df[indicator_cols].fillna(0)

        # --- Check for missing countries vs world shapefile ---
        missing_isos = set(all_world["ISO_A3"]) - set(latest_df["ISO_A3"])

        #print(f"Countries in dataset: {len(latest_df)}")
        #print(f"Countries in world shapefile: {len(all_world)}")
        #print(f"Missing countries: {len(missing_isos)}")
        if missing_isos:
            missing_names = all_world[all_world["ISO_A3"].isin(missing_isos)][["ISO_A3", "NAME"]].values.tolist()
            for iso, wname in sorted(missing_names, key=lambda x: x[1]):
                #print(f"  - {wname} ({iso})")
                pass

        # Add missing countries as rows with "-" year and 0 for all indicator columns
        missing_rows = []
        for _, world_row in all_world[all_world["ISO_A3"].isin(missing_isos)].iterrows():
            row = {"ISO_A3": world_row["ISO_A3"], "NAME": world_row["NAME"], "entity": None, "year": "-"}
            for col in indicator_cols:
                row[col] = 0
            missing_rows.append(row)

        if missing_rows:
            latest_df = pd.concat([latest_df, pd.DataFrame(missing_rows)], ignore_index=True)

        # --- Save output ---
        output_path = download_dir / f"{name}_merged.xlsx"
        latest_df.to_excel(output_path, index=False)
        #print(f"Saved: {output_path}")

        results[name] = latest_df

    return results


def clean_all_dataframes(dataframes_list: list[pd.DataFrame], DATASET_NAMES: list[str]) -> dict[str, pd.DataFrame]:

    raw_dataframes = {}

    # Build raw time-series DataFrames (cleaned, full history, one row per country/year)
    for raw_df, name in zip(dataframes_list, DATASET_NAMES):
        df_clean = raw_df.copy()
        df_clean.columns = [c.lower().strip() for c in df_clean.columns]
        df_clean = df_clean[df_clean["code"].notna() & (df_clean["code"].str.strip() != "")]
        df_clean = df_clean[~df_clean["code"].str.contains("_", na=False)]
        key_cols = ["entity", "code", "year"]
        value_cols = [c for c in df_clean.columns if c not in key_cols]
        if len(value_cols) == 1:
            rename_map = {value_cols[0]: name}
        else:
            rename_map = {c: f"{name}_{i+1}" for i, c in enumerate(value_cols)}
        df_clean = df_clean.rename(columns=rename_map)
        raw_dataframes[name] = df_clean


    return raw_dataframes