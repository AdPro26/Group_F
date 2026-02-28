# Merges the map with the datasets

import geopandas as gpd

def merge_map_with_datasets(
    geodataframe: gpd.GeoDataFrame,
    dataframes: list[pd.DataFrame],
    geo_key: str = "iso_a3",
    data_key: str = "Code",
    year: int | None = None,
) -> gpd.GeoDataFrame:
    """
    Merges a GeoDataFrame with a list of datasets (DataFrames).

    Parameters
    ----------
    geodataframe : gpd.GeoDataFrame
        The base GeoDataFrame (map). Must be the left dataframe.
    dataframes : list[pd.DataFrame]
        List of DataFrames to merge into the GeoDataFrame.
    geo_key : str
        Column name in the GeoDataFrame to merge on (default: 'iso_a3').
    data_key : str
        Column name in each DataFrame to merge on (default: 'Code').
    year : int or None
        If provided, filters each DataFrame to that year before merging.

    Returns
    -------
    gpd.GeoDataFrame
        The merged GeoDataFrame.
    """
    merged_gdf = geodataframe.copy()

    for df in dataframes:
        # Optional: filter by year
        if year is not None and "Year" in df.columns:
            df = df[df["Year"] == year].copy()

        # Drop duplicates on the key to avoid row explosion
        df = df.drop_duplicates(subset=[data_key])

        # Align key types (both to string, strip whitespace)
        merged_gdf[geo_key] = merged_gdf[geo_key].astype(str).str.strip()
        df[data_key] = df[data_key].astype(str).str.strip()

        # Drop non-numeric/non-essential columns that may conflict (except key)
        cols_to_keep = [data_key] + [
            c for c in df.columns
            if c not in merged_gdf.columns or c ==


world = gpd.read_file(shapefile_path)
