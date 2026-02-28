import pandas as pd 
import numpy as np
from MainClass import load_all_data
import DataProcessor



dataframes_list, metadata_list, gdf = load_all_data()
print(dataframes_list[0].columns)

ourProcessor = DataProcessor.ForestDataProcessor()

#dataframes_list = ourProcessor.get_all_dataframes()

result = ourProcessor.get_annual_change("Brazil")
print(result)

