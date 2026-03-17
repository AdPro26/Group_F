import pandas as pd
import geopandas as gpd
from pathlib import Path


# --- Fase 1: Load all datasets and merge them into a single DataFrame ---

def do_the_merging(dataframes_list: list[pd.DataFrame], gdf: gpd.GeoDataFrame, download_dir: str | Path = "downloads") -> pd.DataFrame:


    DATASET_NAMES = [
        "annual-change-forest_area",
        "annual-deforestation",
        "forest-area-as-share-of-land-area",
        "terrestrial-protected-areas",
        "red-list-index",
    ]

    # --- Build a master code -> entity mapping from all dataframes ---
    code_to_entity = {}
    for df in dataframes_list:
        df_temp = df.copy()
        df_temp.columns = [c.lower().strip() for c in df_temp.columns]
        df_temp = df_temp[df_temp["code"].notna() & (df_temp["code"].str.strip() != "")]
        # Exclude codes containing underscores
        df_temp = df_temp[~df_temp["code"].str.contains("_", na=False)]
        mapping = df_temp.drop_duplicates("code").set_index("code")["entity"].to_dict()
        code_to_entity.update(mapping)

    # --- Clean, filter and rename columns for each dataframe ---
    dfs_cleaned = []
    for df, name in zip(dataframes_list, DATASET_NAMES):
        df = df.copy()

        df = df.fillna(0)  # Replace NaN with 0
        df.columns = [c.lower().strip() for c in df.columns]

        print(df.isna().sum())  # Debug: Check for remaining NaN values after fillna    

        # Remove rows where 'code' is missing or empty (e.g. continents, world aggregates)
        df = df[df["code"].notna() & (df["code"].str.strip() != "")]

        # Remove rows where 'code' contains underscores (e.g. OWID_XXX aggregates)
        df = df[~df["code"].str.contains("_", na=False)]

        # Identify value columns (everything except the key columns)
        key_cols = ["entity", "code", "year"]
        value_cols = [c for c in df.columns if c not in key_cols]

        # Rename value columns using only the dataset name as column name
        # If there's only one value column, use the dataset name directly
        # If there are multiple, append an index to keep them unique
        if len(value_cols) == 1:
            rename_map = {value_cols[0]: name}
        else:
            rename_map = {c: f"{name}_{i+1}" for i, c in enumerate(value_cols)}
        df = df.rename(columns=rename_map)

        # Drop entity from all dataframes — will be restored after merge
        df = df.drop(columns=["entity"])



        dfs_cleaned.append(df)



    # --- Progressive outer merge on 'code' + 'year' ---
    merged = dfs_cleaned[0]
    for df in dfs_cleaned[1:]:
        merged = pd.merge(merged, df, on=["code", "year"], how="left")

    # --- Restore entity column from the master mapping ---
    merged["entity"] = merged["code"].map(code_to_entity)

    # --- Reorder columns: entity, code, year first ---
    cols = ["entity", "code", "year"] + [c for c in merged.columns if c not in ["entity", "code", "year"]]
    merged = merged[cols]

    merged = merged.fillna(0)  # Final fillna to ensure no missing values remain after merge

    # --- Sort by country and year ---
    merged = merged.sort_values(["entity", "year"]).reset_index(drop=True)


    # To save the merged dataset before merging with the GeoDataFrame
    # merged.to_csv("merged_dataset.csv", index=False)

    #-----------------------------------------------------------------------------------------------

    # --- Fase 2: Merge with GeoDataFrame ---

    # gdf is already loaded from load_all_data() in Phase 1
    # Keep only essential shapefile columns to avoid noise
    gdf_clean = gdf[["NAME", "ISO_A3", "geometry"]].copy()

    # Fix known ISO_A3 encoding issues in Natural Earth shapefile (e.g. France = -99)
    gdf_clean["ISO_A3"] = gdf_clean["ISO_A3"].replace("-99", pd.NA)


    # Merge world geometries with our dataset using ISO A3 country code
    merged_geo = gdf_clean.merge(merged, left_on="ISO_A3", right_on="code", how="left")

    # Result is a GeoDataFrame with geometry + all our data columns
    #print(f"\n✅ Geo merge complete: {merged_geo.shape[0]} rows, {merged_geo.shape[1]} columns")
    #print(merged_geo.head())



    # --- Fase 3: Cleaning and check ---

    indicator_cols = [c for c in merged_geo.columns if c not in ["NAME", "ISO_A3", "geometry", "entity", "code", "year"]]

    # For each country, keep the most recent non-zero value per indicator column
    records = []
    for iso, group in merged_geo.groupby("ISO_A3"):
        row = {
            "ISO_A3": iso,
            "entity": group["entity"].iloc[0],
            "NAME": group["NAME"].iloc[0],
        }
        for col in indicator_cols:
            valid = group[group[col] != 0][["year", col]].dropna()
            if not valid.empty:
                latest = valid.loc[valid["year"].idxmax()]
                row[col] = latest[col]
                row[f"{col}_year"] = int(latest["year"])
            else:
                row[col] = 0
                row[f"{col}_year"] = None
        records.append(row)

    latest_df = pd.DataFrame(records)

    # Replace any remaining NaN in indicator columns with 0
    latest_df[indicator_cols] = latest_df[indicator_cols].fillna(0)

    # --- Quick check: find missing countries vs world shapefile ---
    all_world = gdf_clean[["ISO_A3", "NAME"]].dropna(subset=["ISO_A3"]).drop_duplicates("ISO_A3")
    missing_isos = set(all_world["ISO_A3"]) - set(latest_df["ISO_A3"])

    print(f"\n--- Fase 3 Check ---")
    print(f"Countries in dataset: {len(latest_df)}")
    print(f"Countries in world shapefile: {len(all_world)}")
    print(f"Missing countries: {len(missing_isos)}")
    if missing_isos:
        missing_names = all_world[all_world["ISO_A3"].isin(missing_isos)][["ISO_A3", "NAME"]].values.tolist()
        for iso, name in sorted(missing_names, key=lambda x: x[1]):
            print(f"  - {name} ({iso})")

    # Add missing countries as rows with 0 for all indicator columns
    missing_rows = []
    for _, world_row in all_world[all_world["ISO_A3"].isin(missing_isos)].iterrows():
        row = {"ISO_A3": world_row["ISO_A3"], "entity": None, "NAME": world_row["NAME"]}
        for col in indicator_cols:
            row[col] = 0
            row[f"{col}_year"] = "-"
        missing_rows.append(row)

    if missing_rows:
        latest_df = pd.concat([latest_df, pd.DataFrame(missing_rows)], ignore_index=True)



    

    # --- Save outputs ---
    download_dir = Path(download_dir)
    download_dir.mkdir(exist_ok=True)
    latest_df.to_excel(download_dir / "latest_by_country.xlsx", index=False)

    return merged_geo



