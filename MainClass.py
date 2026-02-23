import pandas as pd
import requests 

import os
import tarfile
import ast
import matplotlib.pyplot as plt
from pathlib import Path
import ollama
from openai import OpenAI  
import random
from typing import Optional
from pydantic import BaseModel, field_validator
from pydantic.functional_validators import field_validator


data_url = ['https://ourworldindata.org/grapher/annual-change-forest-area.csv?v=1&csvType=full&useColumnShortNames=true',
                'https://ourworldindata.org/grapher/annual-deforestation.csv?v=1&csvType=full&useColumnShortNames=true',
                'https://ourworldindata.org/grapher/terrestrial-protected-areas.csv?v=1&csvType=full&useColumnShortNames=true',
                'https://ourworldindata.org/grapher/forest-area-as-share-of-land-area.csv?v=1&csvType=full&useColumnShortNames=true',
    ]

metadata_url = ['https://ourworldindata.org/grapher/annual-change-forest-area.metadata.json?v=1&csvType=full&useColumnShortNames=true',
                    'https://ourworldindata.org/grapher/annual-deforestation.metadata.json?v=1&csvType=full&useColumnShortNames=true',
                    'https://ourworldindata.org/grapher/terrestrial-protected-areas.metadata.json?v=1&csvType=full&useColumnShortNames=true',
                    'https://ourworldindata.org/grapher/share-degraded-land.metadata.json?v=1&csvType=full&useColumnShortNames=true']


def download_data(data_url, metadata_url):

    download_dir = Path("downloads/")
    print(download_dir)

    df = pd.read_csv(data_url,storage_options = {'User-Agent': 'Our World In Data data fetch/1.0'})
    metadata = requests.get(metadata_url).json()
    print("successfully downloaded data from url: ", data_url)
    return df, metadata

dataframes_list = []
metadata_list = []  


# This section checks if the data and metadata files already exist in the "downloads/" directory before attempting to download them again. If the files exist, it skips the download and prints a message. If not, it proceeds to download the data and metadata, saves them to the specified directory, and appends them to the respective lists.
path = "downloads/"
dir_list = os.listdir(path)
print("Files in 'downloads/' directory:", dir_list)


for i in range(len(data_url)):

    # Check if the data and metadata files already exist in the "downloads/" directory
    if os.path.exists(f"{path}data_{i}.csv") and os.path.exists(f"{path}metadata_{i}.json"):
        print(f"Data and metadata for index {i} already exist. Skipping download.")
        dataframes_list.append(pd.read_csv(f"{path}data_{i}.csv"))  # Load existing data into the list
        metadata_list.append(ast.literal_eval(open(f"{path}metadata_{i}.json").read()))  # Load existing metadata into the list
    else:
        # If the files do not exist, download the data and metadata
        df, metadata = download_data(data_url[i], metadata_url[i])

        # Save the downloaded data and metadata to the "downloads/" directory
        with open(f"{path}data_{i}.csv","wb") as f:
            df.to_csv(f, index=False)
            print(f"DataFrame saved to {path}data_{i}.csv")
        with open(f"{path}metadata_{i}.json", "w") as f:
            f.write(str(metadata))
            print(f"Metadata saved to {path}metadata_{i}.json")

        # Append the downloaded data and metadata to the respective lists
        dataframes_list.append(df)  
        metadata_list.append(metadata)  

'''
for i in range(len(dataframes_list)):
    print(f"DataFrame {i}:")
    print(dataframes_list[i])
    print(f"Metadata {i}:")
    print(metadata_list[i])
'''

# I am not sure if we will need to merge all the dataframes into one, but I will keep this code here just in case we do. It merges all the dataframes in the dataframes_list into a single dataframe called merge_all, ignoring the index to create a continuous index for the merged dataframe. Finally, it prints the first few rows of the merged dataframe using the head() method.
'''
merge_all = pd.concat(dataframes_list, ignore_index=True)
print(merge_all.head())
'''




