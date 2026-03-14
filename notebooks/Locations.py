import os
import math
import requests
import yaml
import csv
import ollama
import base64
import subprocess
import time
from datetime import datetime
from PIL import Image
from io import BytesIO
from pathlib import Path

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(BASE_DIR, "models.yaml"), "r") as f:
    config = yaml.safe_load(f)

ESRI_URL = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
HEADERS = {"User-Agent": "Mozilla/5.0"}
CSV_PATH = os.path.join(BASE_DIR, "database", "images.csv")

def ensure_ollama_running():
    try:
        ollama.list()
    except Exception:
        print("Starting Ollama...")
        subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(4)

def lat_lon_to_tile(lat, lon, zoom):
    n = 2 ** zoom
    x = int((lon + 180) / 360 * n)
    lat_rad = math.radians(lat)
    y = int((1 - math.log(math.tan(lat_rad) + 1 / math.cos(lat_rad)) / math.pi) / 2 * n)
    return x, y

def download_tile(z, x, y):
    url = ESRI_URL.format(z=z, x=x, y=y)
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return Image.open(BytesIO(response.content))

def download_area(lat, lon, zoom, tiles_around, save_path):
    cx, cy = lat_lon_to_tile(lat, lon, zoom)
    tile_size = 256
    grid = range(-tiles_around, tiles_around + 1)
    stitched = Image.new("RGB", (tile_size * len(grid), tile_size * len(grid)))
    for row, dy in enumerate(grid):
        for col, dx in enumerate(grid):
            tile = download_tile(zoom, cx + dx, cy + dy)
            stitched.paste(tile, (col * tile_size, row * tile_size))
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    stitched.save(save_path)
    print(f"  → Saved: {save_path}")

def analyse_image(image_path, model, prompt):
    ensure_ollama_running()
    available_models = [m.model for m in ollama.list().models]
    if not any(model in m for m in available_models):
        print(f"Pulling {model}...")
        ollama.pull(model)
    image_data = base64.b64encode(Path(image_path).read_bytes()).decode("utf-8")
    response = ollama.chat(
        model=model,
        messages=[{"role": "user", "content": prompt, "images": [image_data]}],
        options={"num_predict": 150, "temperature": 0.3}
    )

    return response.message.content.strip()

def analyse_text(text, model, prompt):
    ensure_ollama_running()
    available_models = [m.model for m in ollama.list().models]
    if not any(model in m for m in available_models):
        print(f"Pulling {model}...")
        ollama.pull(model)
    response = ollama.chat(
        model=model,
        messages=[{"role": "user", "content": f"{prompt}\n\n{text}"}]
    )
    return response.message.content.strip()

def already_in_csv(lat, lon, zoom):
    if not os.path.exists(CSV_PATH):
        return None
    with open(CSV_PATH, newline="") as f:
        for row in csv.DictReader(f):
            if float(row["latitude"]) == lat and float(row["longitude"]) == lon and int(row["zoom"]) == zoom:
                print(f"  → Already in database, skipping pipeline.")
                return row
    return None

def save_to_csv(row):
    file_exists = os.path.exists(CSV_PATH)
    with open(CSV_PATH, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=row.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)

# ── Config ────────────────────────────────────────────────────────────────────
zoom = config["image_settings"]["zoom"]
tiles_around = config["image_settings"]["tiles_around"]
image_model = config["image_analysis"]["model"]
image_prompt = config["image_analysis"]["prompt"]
text_model = config["text_analysis"]["model"]
text_prompt = config["text_analysis"]["prompt"]

# ── Monuments ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
 monuments = [
    {"name": "roman_colosseum",  "lat": 41.8902,  "lon": 12.4922},
    {"name": "machu_picchu",     "lat": -13.1631, "lon": -72.5450},
    {"name": "great_wall_china", "lat": 40.4319,  "lon": 116.5704},
    {"name": "pyramids_of_giza", "lat": 29.9792,  "lon": 31.1342},
    {"name": "angkor_wat",       "lat": 13.4125,  "lon": 103.8670},
 ]

 for m in monuments:
     existing = already_in_csv(m["lat"], m["lon"], zoom)
     if existing:
         continue

     save_path = os.path.join(BASE_DIR, "images", f"{m['name']}.png")
     download_area(m["lat"], m["lon"], zoom, tiles_around, save_path)

     image_desc = analyse_image(save_path, image_model, image_prompt)
     text_desc = analyse_text(image_desc, text_model, text_prompt)

     row = {
         "timestamp": datetime.now().isoformat(),
         "latitude": m["lat"],
         "longitude": m["lon"],
         "zoom": zoom,
         "image_description": image_desc,
         "image_prompt": image_prompt,
         "image_model": image_model,
         "text_description": text_desc,
         "text_prompt": text_prompt,
         "text_model": text_model,
         "danger": "Y" if "Y" in text_desc[:5] else "N"
     }
     save_to_csv(row)