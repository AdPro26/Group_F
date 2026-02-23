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

    df = pd.read_csv(data_url,storage_options = {'User-Agent': 'Our World In Data data fetch/1.0'})
    metadata = requests.get(metadata_url).json()
    print("successfully downloaded data from url: ", data_url)
    return df, metadata

dataframes_list = []
metadata_list = []  

for i in range(len(data_url)):
    df, metadata = download_data(data_url[i], metadata_url[i])
    print(f"DataFrame: {df}")
    dataframes_list.append(df)  
    metadata_list.append(metadata)  
    print(f"Metadata: {metadata}")

for i in range(len(dataframes_list)):
    print(f"DataFrame {i}:")
    print(dataframes_list[i])
    print(f"Metadata {i}:")
    print(metadata_list[i])



