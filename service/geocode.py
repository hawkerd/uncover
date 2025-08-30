# geocode.py
import requests
from typing import Dict, Any, Optional

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

def geocode_place(place: str) -> Optional[Dict[str, Any]]:
    """
    Geocode a place name into a bounding box using OpenStreetMap Nominatim.
    
    Returns a dictionary with:
    {
        "lat": str,
        "lon": str,
        "boundingbox": [south, north, west, east]
    }
    
    Returns None if no result is found.
    """
    params = {
        "q": place,
        "format": "json",
        "limit": 1
    }
    headers = {
        "User-Agent": "Dan-MCP-Server/1.0"  # required by Nominatim usage policy
    }
    
    response = requests.get(NOMINATIM_URL, params=params, headers=headers)
    if response.status_code != 200:
        return None

    results = response.json()
    if not results:
        return None

    result = results[0]

    return {
        "lat": result["lat"],
        "lon": result["lon"],
        "southwest": [float(result["boundingbox"][0]), float(result["boundingbox"][2])],
        "northeast": [float(result["boundingbox"][1]), float(result["boundingbox"][3])]
    }

if __name__ == "__main__":
    place = "mall of america"
    result = geocode_place(place)
    if result:
        print(f"Geocoding result for '{place}': {result}")
    else:
        print(f"No results found for '{place}'")