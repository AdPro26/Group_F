import os
import pytest
import pandas as pd
from pathlib import Path
from LoadingDatasets import data_urls, metadata_urls, download_file, download_metadata

def test_download_folder():
    # Ensure downloads folder exists
    download_dir = Path("downloads")
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)
    assert os.path.exists(download_dir), "Downloads folder should exist."

def test_download_files():
    for data_url, metadata_url in zip(data_urls, metadata_urls):

        download_dir = Path("downloads")

        data_path = download_dir / data_url.split('?')[0].split('/')[-1]
        metadata_path = download_dir / metadata_url.split('?')[0].split('/')[-1]

        # Test downloading data file
        download_file(data_url, data_path)
        assert os.path.exists(data_path), f"{data_path} should exist after download."

        # Test downloading metadata file
        download_metadata(metadata_url, metadata_path)
        assert os.path.exists(metadata_path), f"{metadata_path} should exist after download."
        
        # Clean up downloaded files after test
        os.remove(data_path)
        os.remove(metadata_path)     
      