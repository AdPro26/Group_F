import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point


# --- Fixtures ---

@pytest.fixture
def sample_dataframes():
    """Three minimal OWID-style DataFrames mimicking the real datasets."""
    df1 = pd.DataFrame({
        "Entity": ["Portugal", "France", "Norway", "World"],
        "Code":   ["PRT",      "FRA",    "NOR",    None],
        "Year":   [2020,        2020,     2020,     2020],
        "annual_change": [-1.0, -2.0,    -0.5,     999.0],
    })
    df2 = pd.DataFrame({
        "Entity": ["Portugal", "France", "Norway", "Africa"],
        "Code":   ["PRT",      "FRA",    "NOR",    None],
        "Year":   [2020,        2020,     2020,     2020],
        "deforestation": [5.0,  10.0,     2.0,      None],
    })
    df3 = pd.DataFrame({
        "Entity": ["Portugal", "France", "Norway"],
        "Code":   ["PRT",      "FRA",    "NOR"],
        "Year":   [2020,        2020,     2020],
        "red_list": [0.8,       0.7,      0.9],
    })
    return [df1, df2, df3]


@pytest.fixture
def sample_gdf():
    """Minimal GeoDataFrame mimicking the Natural Earth shapefile."""
    return gpd.GeoDataFrame(
        {
            "NAME":     ["Portugal", "France",  "Norway", "Fakeland"],
            "ISO_A3":  ["PRT",      "-99",      "-99",    "FAK"],
            "geometry": [Point(0, 0), Point(1, 1), Point(2, 2), Point(3, 3)],
        },
        crs="EPSG:4326",
    )


@pytest.fixture
def dataset_names():
    return ["annual_change", "deforestation", "red_list"]


# --- Helper: runs Phase 1 logic (dataset merge) ---

def run_phase1(dataframes_list, dataset_names):
    """Replicates Phase 1 logic from the merging file."""
    code_to_entity = {}
    for df in dataframes_list:
        df_temp = df.copy()
        df_temp.columns = [c.lower().strip() for c in df_temp.columns]
        df_temp = df_temp[df_temp["code"].notna() & (df_temp["code"].str.strip() != "")]
        df_temp = df_temp[~df_temp["code"].str.contains("_", na=False)]
        mapping = df_temp.drop_duplicates("code").set_index("code")["entity"].to_dict()
        code_to_entity.update(mapping)

    dfs_cleaned = []
    for df, name in zip(dataframes_list, dataset_names):
        df = df.copy()
        df.columns = [c.lower().strip() for c in df.columns]
        df = df[df["code"].notna() & (df["code"].str.strip() != "")]
        df = df[~df["code"].str.contains("_", na=False)]
        key_cols = ["entity", "code", "year"]
        value_cols = [c for c in df.columns if c not in key_cols]
        rename_map = {value_cols[0]: name} if len(value_cols) == 1 else {c: f"{name}_{i+1}" for i, c in enumerate(value_cols)}
        df = df.rename(columns=rename_map)
        df = df.drop(columns=["entity"])
        dfs_cleaned.append(df)

    merged = dfs_cleaned[0]
    for df in dfs_cleaned[1:]:
        merged = pd.merge(merged, df, on=["code", "year"], how="outer")

    merged["entity"] = merged["code"].map(code_to_entity)
    cols = ["entity", "code", "year"] + [c for c in merged.columns if c not in ["entity", "code", "year"]]
    merged = merged[cols].sort_values(["entity", "year"]).reset_index(drop=True)
    return merged


# --- Phase 1 Tests ---

def test_phase1_aggregates_removed(sample_dataframes, dataset_names):
    """Rows with no ISO code (World, Africa) must be dropped."""
    merged = run_phase1(sample_dataframes, dataset_names)
    assert "World" not in merged["entity"].values
    assert "Africa" not in merged["entity"].values


def test_phase1_all_countries_present(sample_dataframes, dataset_names):
    """All real countries should appear in the merged result."""
    merged = run_phase1(sample_dataframes, dataset_names)
    assert "Portugal" in merged["entity"].values
    assert "France" in merged["entity"].values
    assert "Norway" in merged["entity"].values


def test_phase1_columns_renamed(sample_dataframes, dataset_names):
    """Value columns should be renamed to dataset names."""
    merged = run_phase1(sample_dataframes, dataset_names)
    assert "annual_change" in merged.columns
    assert "deforestation" in merged.columns
    assert "red_list" in merged.columns


def test_phase1_correct_values(sample_dataframes, dataset_names):
    """Values should be correctly merged for a known country/year."""
    merged = run_phase1(sample_dataframes, dataset_names)
    row = merged[(merged["code"] == "PRT") & (merged["year"] == 2020)]
    assert row["annual_change"].values[0] == -1.0
    assert row["deforestation"].values[0] == 5.0
    assert row["red_list"].values[0] == 0.8


def test_phase1_entity_restored(sample_dataframes, dataset_names):
    """Entity column must be restored from the code->entity mapping."""
    merged = run_phase1(sample_dataframes, dataset_names)
    assert "entity" in merged.columns
    assert merged["entity"].notna().all()


def test_phase1_key_columns_order(sample_dataframes, dataset_names):
    """entity, code, year must be the first three columns."""
    merged = run_phase1(sample_dataframes, dataset_names)
    assert list(merged.columns[:3]) == ["entity", "code", "year"]


def test_phase1_owid_aggregates_with_underscore_removed(dataset_names):
    """Codes like OWID_WRL should be filtered out."""
    df_with_owid = pd.DataFrame({
        "Entity": ["Portugal", "OWID World"],
        "Code":   ["PRT",      "OWID_WRL"],
        "Year":   [2020,        2020],
        "annual_change": [-1.0, 999.0],
    })
    merged = run_phase1([df_with_owid], ["annual_change"])
    assert "OWID_WRL" not in merged["code"].values


# --- Phase 2 Tests ---

def test_phase2_returns_geodataframe(sample_dataframes, dataset_names, sample_gdf):
    """Output of geo merge must be a GeoDataFrame."""
    merged = run_phase1(sample_dataframes, dataset_names)
    gdf_clean = sample_gdf[["NAME", "ISO_A3", "geometry"]].copy()
    iso_fixes = {"France": "FRA", "Norway": "NOR"}
    for name, iso in iso_fixes.items():
        gdf_clean.loc[gdf_clean["NAME"] == name, "ISO_A3"] = iso
    gdf_clean["ISO_A3"] = gdf_clean["ISO_A3"].replace("-99", pd.NA)
    merged_geo = gdf_clean.merge(merged, left_on="ISO_A3", right_on="code", how="left")
    assert isinstance(merged_geo, gpd.GeoDataFrame)


def test_phase2_all_map_countries_preserved(sample_dataframes, dataset_names, sample_gdf):
    """Left join must keep all countries from the shapefile."""
    merged = run_phase1(sample_dataframes, dataset_names)
    gdf_clean = sample_gdf[["NAME", "ISO_A3", "geometry"]].copy()
    merged_geo = gdf_clean.merge(merged, left_on="ISO_A3", right_on="code", how="left")
    assert len(merged_geo) == len(sample_gdf)


def test_phase2_iso_fix_allows_match(sample_dataframes, dataset_names, sample_gdf):
    """France and Norway (-99) must match after ISO fix is applied."""
    merged = run_phase1(sample_dataframes, dataset_names)
    gdf_clean = sample_gdf[["NAME", "ISO_A3", "geometry"]].copy()
    iso_fixes = {"France": "FRA", "Norway": "NOR"}
    for name, iso in iso_fixes.items():
        gdf_clean.loc[gdf_clean["NAME"] == name, "ISO_A3"] = iso
    merged_geo = gdf_clean.merge(merged, left_on="ISO_A3", right_on="code", how="left")
    france = merged_geo[merged_geo["NAME"] == "France"]
    norway = merged_geo[merged_geo["NAME"] == "Norway"]
    assert france["annual_change"].values[0] == -2.0
    assert norway["annual_change"].values[0] == -0.5


def test_phase2_unmatched_country_is_nan(sample_dataframes, dataset_names, sample_gdf):
    """Fakeland has no OWID data — all data columns should be NaN."""
    merged = run_phase1(sample_dataframes, dataset_names)
    gdf_clean = sample_gdf[["NAME", "ISO_A3", "geometry"]].copy()
    merged_geo = gdf_clean.merge(merged, left_on="ISO_A3", right_on="code", how="left")
    fakeland = merged_geo[merged_geo["NAME"] == "Fakeland"]
    assert pd.isna(fakeland["annual_change"].values[0])


def test_phase2_geometry_preserved(sample_dataframes, dataset_names, sample_gdf):
    """Geometry must survive the geo merge intact."""
    merged = run_phase1(sample_dataframes, dataset_names)
    gdf_clean = sample_gdf[["NAME", "ISO_A3", "geometry"]].copy()
    merged_geo = gdf_clean.merge(merged, left_on="ISO_A3", right_on="code", how="left")
    assert "geometry" in merged_geo.columns
    assert merged_geo["geometry"].notnull().all()


# --- Allows running with: python test_merging.py ---
if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))