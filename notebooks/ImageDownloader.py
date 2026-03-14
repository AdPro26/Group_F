import os
import math
import requests
from datetime import datetime
from pathlib import Path
from typing import Tuple, Optional

def lat_lon_to_tile(lat: float, lon: float, zoom: int) -> Tuple[int, int]:
    """Convert latitude, longitude, zoom to ESRI tile coordinates (x, y)."""
    n = 2 ** zoom
    x = int((lon + 180) / 360 * n)
    y = int((1 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.pi) / 2 * n)
    return x, y


def get_esri_tile_url(lat: float, lon: float, zoom: int) -> str:
    """Generate ESRI World Imagery tile URL for given coordinates."""
    x, y = lat_lon_to_tile(lat, lon, zoom)
    url = f"https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{zoom}/{y}/{x}"
    return url


def generate_filename(lat: float, lon: float, zoom: int) -> str:
    """Generate unique filename for image based on coordinates and zoom."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"esri_lat{lat:.2f}_lon{lon:.2f}_zoom{zoom}_{timestamp}.png"
    return filename


def ensure_images_directory(base_path: str = ".") -> str:
    """Create images directory if it doesn't exist. Returns path to images directory."""
    images_dir = Path(base_path) / "images"
    images_dir.mkdir(parents=True, exist_ok=True)
    return str(images_dir)


def download_esri_image(lat: float, lon: float, zoom: int, output_dir: Optional[str] = None) -> Tuple[bool, str, str]:
    """
    Download ESRI World Imagery tile and save to images directory.
    
    Args:
        lat: Latitude (-90 to 90)
        lon: Longitude (-180 to 180)
        zoom: Zoom level (1-18)
        output_dir: Output directory (if None, uses ./images)
    
    Returns:
        Tuple: (success: bool, filepath: str, message: str)
    """
    try:
        # Validate coordinates
        if not -90 <= lat <= 90:
            return False, "", "Latitude must be between -90 and 90"
        if not -180 <= lon <= 180:
            return False, "", "Longitude must be between -180 and 180"
        if not 1 <= zoom <= 18:
            return False, "", "Zoom must be between 1 and 18"
        
        # Ensure output directory exists
        if output_dir is None:
            output_dir = ensure_images_directory()
        else:
            Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Get ESRI URL and download
        url = get_esri_tile_url(lat, lon, zoom)
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        # Save image
        filename = generate_filename(lat, lon, zoom)
        filepath = Path(output_dir) / filename
        filepath.write_bytes(response.content)
        
        return True, str(filepath), f"Image saved successfully to {filepath}"
    
    except requests.exceptions.RequestException as e:
        return False, "", f"Error downloading image: {str(e)}"
    except Exception as e:
        return False, "", f"Unexpected error: {str(e)}"