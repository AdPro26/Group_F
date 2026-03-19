import os
import pandas as pd
import geopandas as gpd
from pathlib import Path
from typing import Optional
from typing import Optional
from pydantic import BaseModel, field_validator
from pydantic.functional_validators import field_validator
import sys 

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from notebooks.Processing import load_all_data
from notebooks.Processing import do_the_merging2
from notebooks.Processing import clean_all_dataframes

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


DOWNLOAD_DIR = Path(__file__).parent.parent / "downloads"

class CountryInfo(BaseModel):
    """Pydantic model to validate country information."""

    entity: str
    code: Optional[str] = None

    @field_validator("entity")
    def validate_entity(cls, value):
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Entity must be a non-empty string.")
        return value.strip()

    @field_validator("code")
    def validate_code(cls, value):
        if value is not None:
            if not isinstance(value, str) or len(value) != 3:
                raise ValueError("Code must be a 3-letter ISO country code.")
            return value.upper()
        return value


class ForestDataProcessor:
    """Class to process all required datasets from Our World in Data."""

    def __init__(self) -> None:
        """
        Initializes the ForestDataProcessor.

        Runs Function 1 to download (if needed) and load all datasets into
        named DataFrame attributes. Optionally runs Function 2 to merge
        the datasets with a geospatial map.

        :param map_path: Optional path to a geospatial file (shapefile, GeoJSON, etc.)
                         If provided, all datasets are merged with the map geometry.
        """
        self.geo_dataframe: Optional[gpd.GeoDataFrame] = None
        self.merged_dataframe: Optional[dict] = None
        self.raw_dataframes: dict[str, pd.DataFrame] = {}
        self.metadata: list[dict] = []

        dataframes, self.metadata, gdf = load_all_data(DOWNLOAD_DIR)

        raw_dataframes = clean_all_dataframes(dataframes, DATASET_NAMES)
        self.raw_dataframes = raw_dataframes

        merged_dataframe = do_the_merging2(dataframes, gdf, DOWNLOAD_DIR)
        self.merged_dataframe = merged_dataframe

         

        # Named DataFrame attributes — one per dataset
        self.annual_change_df: Optional[pd.DataFrame] = None
        """
        Annual net change in forest area per country/region.
        Columns:
            - entity (str): Country or region name (e.g. 'Brazil', 'World').
            - code (str): ISO 3166-1 alpha-3 country code (e.g. 'BRA'). Empty for regions.
            - year (int): Year of the observation (1991–2025).
            - net_change_forest_area (float): Net change in forest area in hectares.
              Calculated as afforestation + natural expansion - deforestation.
              Negative values indicate net forest loss.
        """

        self.annual_deforestation_df: Optional[pd.DataFrame] = None
        """
        Annual deforestation rates per country/region.
        Columns:
            - entity (str): Country or region name (e.g. 'Africa', 'Brazil').
            - code (str): ISO 3166-1 alpha-3 country code. Empty for regions.
            - year (int): Year of the observation (1990–2020).
            - _1d_deforestation (int): Annual forest loss in hectares per year.
              Values are averages over 5- or 10-year periods reported by the FAO.
        """

        self.terrestrial_protected_df: Optional[pd.DataFrame] = None
        """
        Share of land area under terrestrial protection per country/region.
        Columns:
            - entity (str): Country or region name (e.g. 'India', 'World').
            - code (str): ISO 3166-1 alpha-3 country code. Empty for regions.
            - year (int): Year of the observation (2013–2024).
            - er_lnd_ptld_zs (float): Terrestrial protected areas as a percentage
              of total land area. Only includes areas of at least 1,000 hectares
              designated by national authorities.
        """

        self.forest_share_df: Optional[pd.DataFrame] = None
        """
        Forest area as a share of total land area per country/region.
        Columns:
            - entity (str): Country or region name (e.g. 'Russia', 'World').
            - code (str): ISO 3166-1 alpha-3 country code. Empty for regions.
            - year (int): Year of the observation (1990–2022).
            - forest_share (float): Forest area as a percentage of total land area.
            - forest_share__annotations (str): Optional notes on specific data points.
              Empty for most rows.
        """

        self.annual_change_df = self.merged_dataframe["annual-change-forest_area"]
        self.annual_deforestation_df = self.merged_dataframe["annual-deforestation"]
        self.terrestrial_protected_df = self.merged_dataframe["terrestrial-protected-areas"]
        self.forest_share_df = self.merged_dataframe["forest-area-as-share-of-land-area"]
        self.red_list_index = self.merged_dataframe["red-list-index"]

    

        # Function 2 — merge with map if a path was provided
      # if map_path is not None:
       # self.geo_dataframe = gpd.read_file(map_path)

    def get_annual_change(self, entity: str) -> pd.DataFrame:
        """
        Returns the annual net change in forest area for a given country or region.

        :param entity: str, the country or region name (e.g. 'Brazil', 'World').
        :return: pandas DataFrame with columns ['entity', 'code', 'year', 'net_change_forest_area'].
        :raises RuntimeError: If annual_change_df was not loaded correctly by Function 1.
        :raises KeyError: If the column 'entity' is not found in the dataset.
        :raises ValueError: If the given entity is not found in the dataset.
        """
        if self.annual_change_df is None:
            raise RuntimeError(
                "annual_change_df is not loaded. Check that Function 1 ran correctly."
            )

        if "entity" not in self.annual_change_df.columns:
            raise KeyError(
                "Column 'entity' not found in annual_change_df. Check dataset format."
            )

        result = self.annual_change_df[self.annual_change_df["entity"] == entity]

        if result.empty:
            raise ValueError(
                f"Entity '{entity}' not found in annual_change_df. "
                "Check the spelling or use a region name like 'World'."
            )

        return result.reset_index(drop=True)

    def get_deforestation(self, entity: str) -> pd.DataFrame:
        """
        Returns annual deforestation rates for a given country or region.

        :param entity: str, the country or region name (e.g. 'Brazil', 'Africa').
        :return: pandas DataFrame with columns ['entity', 'code', 'year', '_1d_deforestation'].
        :raises RuntimeError: If annual_deforestation_df was not loaded correctly by Function 1.
        :raises KeyError: If the column 'entity' is not found in the dataset.
        :raises ValueError: If the given entity is not found in the dataset.
        """
        if self.annual_deforestation_df is None:
            raise RuntimeError(
                "annual_deforestation_df is not loaded. Check that Function 1 ran correctly."
            )

        if "entity" not in self.annual_deforestation_df.columns:
            raise KeyError(
                "Column 'entity' not found in annual_deforestation_df. Check dataset format."
            )

        result = self.annual_deforestation_df[
            self.annual_deforestation_df["entity"] == entity
        ]

        if result.empty:
            raise ValueError(
                f"Entity '{entity}' not found in annual_deforestation_df. "
                "Check the spelling or use a region name like 'Africa'."
            )

        return result.reset_index(drop=True)

    def get_protected_areas(self, entity: str) -> pd.DataFrame:
        """
        Returns the share of land under terrestrial protection for a given country or region.

        :param entity: str, the country or region name (e.g. 'India', 'World').
        :return: pandas DataFrame with columns ['entity', 'code', 'year', 'er_lnd_ptld_zs'].
        :raises RuntimeError: If terrestrial_protected_df was not loaded correctly by Function 1.
        :raises KeyError: If the column 'entity' is not found in the dataset.
        :raises ValueError: If the given entity is not found in the dataset.
        """
        if self.terrestrial_protected_df is None:
            raise RuntimeError(
                "terrestrial_protected_df is not loaded. Check that Function 1 ran correctly."
            )

        if "entity" not in self.terrestrial_protected_df.columns:
            raise KeyError(
                "Column 'entity' not found in terrestrial_protected_df. Check dataset format."
            )

        result = self.terrestrial_protected_df[
            self.terrestrial_protected_df["entity"] == entity
        ]

        if result.empty:
            raise ValueError(
                f"Entity '{entity}' not found in terrestrial_protected_df. "
                "Check the spelling or use a region name like 'World'."
            )

        return result.reset_index(drop=True)

    def get_forest_share(self, entity: str) -> pd.DataFrame:
        """
        Returns forest area as a percentage of total land area for a given country or region.

        :param entity: str, the country or region name (e.g. 'Russia', 'World').
        :return: pandas DataFrame with columns ['entity', 'code', 'year', 'forest_share',
                 'forest_share__annotations'].
        :raises RuntimeError: If forest_share_df was not loaded correctly by Function 1.
        :raises KeyError: If the column 'entity' is not found in the dataset.
        :raises ValueError: If the given entity is not found in the dataset.
        """
        if self.forest_share_df is None:
            raise RuntimeError(
                "forest_share_df is not loaded. Check that Function 1 ran correctly."
            )

        if "entity" not in self.forest_share_df.columns:
            raise KeyError(
                "Column 'entity' not found in forest_share_df. Check dataset format."
            )

        result = self.forest_share_df[self.forest_share_df["entity"] == entity]

        if result.empty:
            raise ValueError(
                f"Entity '{entity}' not found in forest_share_df. "
                "Check the spelling or use a region name like 'World'."
            )

        return result.reset_index(drop=True)

            
    def get_red_list_index(self, entities: list[str]) -> pd.DataFrame:
        if self.red_list_index is None:
            print("red_list_index is None")
            raise RuntimeError("red_list_index is not loaded.")
        else:
            print(self.red_list_index.head())

        # Filter for the countries
        mask = self.red_list_index["entity"].isin(entities)
        
        # IMPORTANT: Select a LIST of columns to keep it as a DataFrame
        # We need 'entity' to group the lines and 'year' for the x-axis
        result_df = self.red_list_index[mask][['entity', 'year', 'red-list-index']].copy()

        if result_df.empty:
            raise ValueError(f"None of the entities {entities} were found.")

        # Now .sort_values(by=...) will work because 'entity' and 'year' exist!
        return result_df.sort_values(by=["entity", "year"])
    
