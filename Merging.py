import pandas as pd
import geopandas as gpd
from MainClass import load_all_data

# --- Fase 1: Load all datasets and merge them into a single DataFrame ---

# --- Load data ---
dataframes_list, metadata_list, gdf = load_all_data()

# --- Dataset names (used to rename value columns) ---
DATASET_NAMES = [
    "annual_change_forest_area",
    "annual_deforestation",
    "terrestrial_protected_areas",
    "forest_area_share_land",
    "red_list_index",
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
    df.columns = [c.lower().strip() for c in df.columns]

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

    print(f"  [{name}] {len(df)} rows after filtering")
    dfs_cleaned.append(df)

# --- Progressive outer merge on 'code' + 'year' ---
merged = dfs_cleaned[0]
for df in dfs_cleaned[1:]:
    merged = pd.merge(merged, df, on=["code", "year"], how="outer")

# --- Restore entity column from the master mapping ---
merged["entity"] = merged["code"].map(code_to_entity)

# --- Reorder columns: entity, code, year first ---
cols = ["entity", "code", "year"] + [c for c in merged.columns if c not in ["entity", "code", "year"]]
merged = merged[cols]

# --- Sort by country and year ---
merged = merged.sort_values(["entity", "year"]).reset_index(drop=True)

print(f"\n✅ Merge complete: {merged.shape[0]} rows, {merged.shape[1]} columns")
print(merged.head(10))

# --- Check if forest_area_share_land_2 is empty ---
'''
print(merged["forest_area_share_land_2"].isna().sum(), "NaN values")
print(merged["forest_area_share_land_2"].notna().sum(), "non-NaN values")
print(merged["forest_area_share_land_2"].dropna().head(10))
'''

'''Since forest_area_share_land_2 is completely empty, we can safely drop it before merging with the GeoDataFrame.'''
merged = merged.drop(columns=["forest_area_share_land_2"])

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
print(f"\n✅ Geo merge complete: {merged_geo.shape[0]} rows, {merged_geo.shape[1]} columns")
print(merged_geo.head())

# --- Save outputs ---
merged_geo.to_file("merged_output.geojson", driver="GeoJSON")
merged_geo.to_csv("merged_dataset.csv", index=False)