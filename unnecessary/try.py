
import os
import sys


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from notebooks.DataProcessor import ForestDataProcessor

'''

def load_processor():
    return ForestDataProcessor()

processor = load_processor()


print(processor.annual_deforestation_df[processor.annual_deforestation_df['ISO_A3'] == 'USA'])
'''

import geopandas as gpd


gdf = gpd.read_file("downloads/countries/ne_110m_admin_0_countries.shp")
gdf[["NAME", "ISO_A3"]].to_excel("countriescheck.xlsx", index=False)
