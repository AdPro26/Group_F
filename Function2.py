import geopandas as gpd
import pandas as pd
from pathlib import Path

from MainClass import load_all_data


# --- Load data from MainClass ---
dataframes_list, metadata_list, gdf = load_all_data()


def merge_map_with_datasets(
    gdf: gpd.GeoDataFrame,
    dataframes_list: list[pd.DataFrame],
    year: int = 2020,
) -> gpd.GeoDataFrame:
    """
    Merges the world GeoDataFrame (left) with all OWID datasets.
    Filters each dataset to a single year before merging to avoid memory explosion.
    """

    iso_fixes = {
        "France":           "FRA",
        "Norway":           "NOR",
        "Kosovo":           "XKX",
        "Northern Cyprus":  "CYN",
        "Somaliland":       "SOL",
    }
    for name, iso in iso_fixes.items():
        gdf.loc[gdf["NAME"] == name, "ISO_A3"] = iso

    def normalize_owid_df(df: pd.DataFrame) -> pd.DataFrame:
        rename_map = {}
        for col in df.columns:
            if col.lower() == "entity":
                rename_map[col] = "entity"
            elif col.lower() == "code":
                rename_map[col] = "code"
            elif col.lower() == "year":
                rename_map[col] = "year"
        return df.rename(columns=rename_map)

    merged_gdf = gdf.copy()

    for i, df in enumerate(dataframes_list):
        df = normalize_owid_df(df)
        df = df.dropna(subset=["code"])

        # ✅ Filter to a single year to prevent cartesian explosion
        if "year" in df.columns:
            df = df[df["year"] == year].copy()
            print(f"  Dataset {i + 1}: filtered to year={year}, {len(df)} rows")

        df = df.drop(columns=[c for c in ["entity", "year"] if c in df.columns])

        merged_gdf = merged_gdf.merge(
            df,
            how="left",
            left_on="ISO_A3",
            right_on="code",
            suffixes=("", f"_df{i + 1}"),
        )

        if "code" in merged_gdf.columns:
            merged_gdf = merged_gdf.drop(columns=["code"])

    print(f"✅ Merged {len(dataframes_list)} datasets for year={year}. Final shape: {merged_gdf.shape}")
    return merged_gdf




if __name__ == "__main__":
    merged_gdf = merge_map_with_datasets(gdf, dataframes_list, year=2020)
    
    # Quick inspection
    print("\n--- Shape ---")
    print(merged_gdf.shape)

    print("\n--- Columns ---")
    print(merged_gdf.columns.tolist())

    print("\n--- First 5 rows (key columns only) ---")
    key_cols = ["NAME", "ISO_A3"] + [col for col in merged_gdf.columns if col not in gdf.columns and col != "geometry"]
    print(merged_gdf[key_cols].head(10).to_string())

    print("\n--- Null check (how many countries got no data per column) ---")
    data_cols = [col for col in merged_gdf.columns if col not in gdf.columns and col != "geometry"]
    print(merged_gdf[data_cols].isnull().sum().to_string())