import pandas as pd
import geopandas as gpd
from pathlib import Path

# this is Madda's function from Merging_02.py, moved here to avoid circular imports between DataProcessor and Processing

def do_the_merging2(dataframes_list: list[pd.DataFrame], gdf: gpd.GeoDataFrame, download_dir: str | Path = "downloads") -> dict[str, pd.DataFrame]:

    DATASET_NAMES = [
        "annual-change-forest_area",
        "annual-deforestation",
        "forest-area-as-share-of-land-area",
        "terrestrial-protected-areas",
        "red-list-index",
    ]

    # --- Prepare GeoDataFrame ---
    gdf_clean = gdf[["NAME", "ISO_A3", "geometry"]].copy()
    gdf_clean["ISO_A3"] = gdf_clean["ISO_A3"].replace("-99", pd.NA)
    all_world = gdf_clean[["ISO_A3", "NAME"]].dropna(subset=["ISO_A3"]).drop_duplicates("ISO_A3")

    download_dir = Path(download_dir)
    download_dir.mkdir(exist_ok=True)

    results = {}

    for df, name in zip(dataframes_list, DATASET_NAMES):
        df = df.copy()

        df = df.fillna(0)
        df.columns = [c.lower().strip() for c in df.columns]

        print(f"\n--- Processing: {name} ---")
        print(df.isna().sum())

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

        print(f"Countries in dataset: {len(latest_df)}")
        print(f"Countries in world shapefile: {len(all_world)}")
        print(f"Missing countries: {len(missing_isos)}")
        if missing_isos:
            missing_names = all_world[all_world["ISO_A3"].isin(missing_isos)][["ISO_A3", "NAME"]].values.tolist()
            for iso, wname in sorted(missing_names, key=lambda x: x[1]):
                print(f"  - {wname} ({iso})")

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
        print(f"Saved: {output_path}")

        results[name] = latest_df

    return results
