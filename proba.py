import math

def lat_lon_to_tile(lat, lon, zoom):
    n = 2 ** zoom
    x = int((lon + 180) / 360 * n)
    y = int((1 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.pi) / 2 * n)
    return x, y

print(lat_lon_to_tile(48.8584, 2.2945, 15))  # Eiffel Tower


#Get the real `x, y` output, then plug into:

# https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/15/{y}/{x}
# https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/15/11272/16592