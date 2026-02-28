import pandas as pd
import geopandas as gpd
from MainClass import load_all_data

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
    mapping = df_temp.drop_duplicates("code").set_index("code")["entity"].to_dict()
    code_to_entity.update(mapping)

# --- Clean, filter and rename columns for each dataframe ---
dfs_cleaned = []
for df, name in zip(dataframes_list, DATASET_NAMES):
    df = df.copy()
    df.columns = [c.lower().strip() for c in df.columns]

    # Remove rows where 'code' is missing or empty (e.g. continents, world aggregates)
    df = df[df["code"].notna() & (df["code"].str.strip() != "")]

    # Identify value columns (everything except the key columns)
    key_cols = ["entity", "code", "year"]
    value_cols = [c for c in df.columns if c not in key_cols]

    # Prefix value columns with dataset name to avoid conflicts after merge
    rename_map = {c: f"{name}__{c}" for c in value_cols}
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

merged.to_csv("merged_dataset.csv", index=False)