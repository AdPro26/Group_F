import sys
from pathlib import Path

# Works for both: pytest and direct python execution
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from Function2 import merge_map_with_datasets


# --- Fixtures ---

@pytest.fixture
def sample_gdf():
    """Minimal GeoDataFrame mimicking the Natural Earth shapefile."""
    return gpd.GeoDataFrame(
        {
            "NAME":     ["Portugal", "France", "Norway", "Fakeland"],
            "ISO_A3":  ["PRT",      "-99",    "-99",    "FAK"],
            "geometry": [Point(0, 0), Point(1, 1), Point(2, 2), Point(3, 3)],
        },
        crs="EPSG:4326",
    )


@pytest.fixture
def sample_dataframes():
    """Two minimal OWID-style DataFrames with different data columns."""
    df1 = pd.DataFrame({
        "entity":      ["Portugal", "France", "Norway", "World"],
        "code":        ["PRT",      "FRA",    "NOR",    None],
        "year":        [2020,        2020,     2020,     2020],
        "forest_area": [10.0,        20.0,     30.0,     999.0],
    })
    df2 = pd.DataFrame({
        "entity":         ["Portugal", "France", "Norway", "Africa"],
        "code":           ["PRT",      "FRA",    "NOR",    None],
        "year":           [2020,        2020,     2020,     2020],
        "red_list_index": [0.8,         0.7,      0.9,      None],
    })
    return [df1, df2]


# --- Tests ---

def test_merge_returns_geodataframe(sample_gdf, sample_dataframes):
    result = merge_map_with_datasets(sample_gdf, sample_dataframes, year=2020)
    assert isinstance(result, gpd.GeoDataFrame)


def test_merge_preserves_all_countries(sample_gdf, sample_dataframes):
    result = merge_map_with_datasets(sample_gdf, sample_dataframes, year=2020)
    assert len(result) == len(sample_gdf)


def test_merge_data_columns_present(sample_gdf, sample_dataframes):
    result = merge_map_with_datasets(sample_gdf, sample_dataframes, year=2020)
    assert "forest_area" in result.columns
    assert "red_list_index" in result.columns


def test_merge_correct_values(sample_gdf, sample_dataframes):
    result = merge_map_with_datasets(sample_gdf, sample_dataframes, year=2020)
    portugal = result[result["ISO_A3"] == "PRT"]
    assert portugal["forest_area"].values[0] == 10.0
    assert portugal["red_list_index"].values[0] == 0.8


def test_merge_iso_fix_applied(sample_gdf, sample_dataframes):
    result = merge_map_with_datasets(sample_gdf, sample_dataframes, year=2020)
    france = result[result["NAME"] == "France"]
    norway = result[result["NAME"] == "Norway"]
    assert france["forest_area"].values[0] == 20.0
    assert norway["forest_area"].values[0] == 30.0


def test_merge_unmatched_country_is_nan(sample_gdf, sample_dataframes):
    result = merge_map_with_datasets(sample_gdf, sample_dataframes, year=2020)
    fakeland = result[result["NAME"] == "Fakeland"]
    assert pd.isna(fakeland["forest_area"].values[0])


def test_merge_aggregates_dropped(sample_gdf, sample_dataframes):
    result = merge_map_with_datasets(sample_gdf, sample_dataframes, year=2020)
    assert len(result) == len(sample_gdf)


def test_merge_no_code_column_in_result(sample_gdf, sample_dataframes):
    result = merge_map_with_datasets(sample_gdf, sample_dataframes, year=2020)
    assert "code" not in result.columns


def test_merge_geometry_preserved(sample_gdf, sample_dataframes):
    result = merge_map_with_datasets(sample_gdf, sample_dataframes, year=2020)
    assert "geometry" in result.columns
    assert result.geometry.notnull().all()


# --- Allows running with: python test_merge_data.py ---
if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))