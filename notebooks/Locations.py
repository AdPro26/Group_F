
import os
import math
import requests
from PIL import Image
from io import BytesIO
import yaml

with open("../models.yaml", "r") as f:
    config = yaml.safe_load(f)

ESRI_URL = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

def lat_lon_to_tile(lat, lon, zoom):
    """Convert lat/lon to XYZ tile coordinates."""
    n = 2 ** zoom
    x = int((lon + 180) / 360 * n)
    lat_rad = math.radians(lat)
    y = int((1 - math.log(math.tan(lat_rad) + 1 / math.cos(lat_rad)) / math.pi) / 2 * n)
    return x, y

def download_tile(z, x, y):
    """Download a single tile from ESRI World Imagery."""
    url = ESRI_URL.format(z=z, x=x, y=y)
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return Image.open(BytesIO(response.content))

def download_area(lat, lon, zoom=15, tiles_around=1, save_path="images/output.png"):
    """
    Download and stitch tiles around a given lat/lon.
    tiles_around=1 → 3x3 grid of tiles
    tiles_around=2 → 5x5 grid of tiles
    """
    cx, cy = lat_lon_to_tile(lat, lon, zoom)

    tile_size = 256
    grid = range(-tiles_around, tiles_around + 1)
    grid_size = len(grid)

    stitched = Image.new("RGB", (tile_size * grid_size, tile_size * grid_size))

    for row, dy in enumerate(grid):
        for col, dx in enumerate(grid):
            tile = download_tile(zoom, cx + dx, cy + dy)
            stitched.paste(tile, (col * tile_size, row * tile_size))
            print(f"  ✓ Tile ({cx+dx}, {cy+dy})")

    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    stitched.save(save_path)
    print(f"  → Saved: {save_path}\n")

# ── Monuments ─────────────────────────────────────────────────────────────────
monuments = [
    {"name": "roman_colosseum",   "lat": 41.8902,  "lon": 12.4922},
    {"name": "machu_picchu",      "lat": -13.1631, "lon": -72.5450},
    {"name": "great_wall_china",  "lat": 40.4319,  "lon": 116.5704},
    {"name": "pyramids_of_giza",  "lat": 29.9792,  "lon": 31.1342},
    {"name": "angkor_wat",        "lat": 13.4125,  "lon": 103.8670},
]

for m in monuments:
    print(f"Downloading: {m['name']}...")
    download_area(
        lat=m["lat"],
        lon=m["lon"],
        zoom=config["image_settings"]["zoom"],
        tiles_around=config["image_settings"]["tiles_around"],
        save_path=f"images/{m['name']}.png"
    )

print("Done! All images saved to /images")