"""
retriever.py

Retrieves nearby charging stations based on either:
- user-provided address
- or (lat, lon) GPS coordinates

Uses OpenChargeMap API and returns the data preprocessed
in a format compatible with the recommendation engine.
"""

# --- IMPORTS ---
import requests
from geopy.geocoders import Nominatim
from typing import List, Tuple, Optional

# --- API KEYS ---
OPENCHARGEMAP_API_KEY = "49af854f-f8fb-4b73-9fb1-b5a04ab8e393"
TOMTOM_API_KEY = "V4Z58HqLLL2QnGFjC1RFsGnLn8alwNjK"

# --- URLs & Headers ---
OPENCHARGEMAP_URL = "https://api.openchargemap.io/v3/poi/"
OCM_HEADERS = {
    "Content-Type": "application/json",
    "X-API-Key": OPENCHARGEMAP_API_KEY
}


def geocode_address(address: str) -> Optional[Tuple[float, float]]:
    """Convert an address into GPS coordinates using geopy."""
    geolocator = Nominatim(user_agent="geoapi")
    location = geolocator.geocode(address)
    if location:
        return location.latitude, location.longitude
    return None


# --- ELECTRIC STATIONS (OpenChargeMap) ---

def get_electric_stations(lat: float, lon: float, radius_km: int = 10) -> List[dict]:
    params = {
        "output": "json",
        "latitude": lat,
        "longitude": lon,
        "distance": str(radius_km),
        "distanceunit": "KM",
        "maxresults": 20
    }

    try:
        response = requests.get(OPENCHARGEMAP_URL, headers=OCM_HEADERS, params=params)
        if response.status_code != 200:
            print(f"[ERROR] OpenChargeMap error: {response.status_code} - {response.text}")
            return []
        return preprocess_ocm(response.json())
    except requests.RequestException as e:
        print(f"[ERROR] OCM request failed: {e}")
        return []


def preprocess_ocm(raw_data: List[dict]) -> List[dict]:
    stations = []
    for entry in raw_data:
        try:
            name = entry.get("AddressInfo", {}).get("Title", "Unknown Station")
            provider = entry.get("OperatorInfo", {}).get("Title", "Unknown Provider")
            distance = entry.get("AddressInfo", {}).get("Distance", 0)
            power = 0

            connections = entry.get("Connections", [])
            if connections:
                power = max((c.get("PowerKW", 0) or 0) for c in connections)

            stations.append({
                "name": name,
                "provider": provider,
                "distance_km": round(distance, 2),
                "charging_power_kw": power
            })
        except Exception as e:
            print(f"[WARNING] Skipped entry due to error: {e}")
            continue
    return stations


# --- PETROL STATIONS (HERE API) ---

def get_petrol_stations_tomtom(lat: float, lon: float, radius_m: int = 10000, api_key: str = TOMTOM_API_KEY) -> list:
    """
    Get nearby petrol stations using TomTom Search API.

    Args:
        lat (float): latitude
        lon (float): longitude
        radius_m (int): radius in meters
        api_key (str): TomTom API key

    Returns:
        List[dict]: formatted list of stations
    """
    url = "https://api.tomtom.com/search/2/poiSearch/fuel.json"
    params = {
        "lat": lat,
        "lon": lon,
        "radius": radius_m,
        "limit": 20,
        "key": api_key
    }

    try:
        response = requests.get(url, params=params)
        if response.status_code != 200:
            print(f"[ERROR] TomTom API error: {response.status_code} - {response.text}")
            return []

        data = response.json()
        stations = []

        for result in data.get("results", []):
            poi = result.get("poi", {})
            stations.append({
                "name": poi.get("name", "Unknown Station"),
                "provider": poi.get("name", "Unknown Provider").split()[0],
                "distance_km": round(result.get("dist", 0) / 1000, 2),
                "charging_power_kw": 0
            })

        return stations

    except Exception as e:
        print(f"[ERROR] TomTom request failed: {e}")
        return []


# --- MAIN ENTRYPOINT ---

def retrieve_stations(user_preferences: dict, location_input: str = "", latlon: Optional[Tuple[float, float]] = None) -> List[dict]:
    """
    Main function to retrieve stations (electric or petrol) based on preferences and location.

    Args:
        user_preferences (dict): must contain 'fuel_type'
        location_input (str): user address (optional)
        latlon (Tuple[float, float]): GPS coordinates (optional)

    Returns:
        List[dict]: preprocessed list of stations
    """
    if latlon:
        lat, lon = latlon
    elif location_input:
        coords = geocode_address(location_input)
        if not coords:
            print("[ERROR] Could not geocode the address.")
            return []
        lat, lon = coords
    else:
        raise ValueError("Either latlon or location_input must be provided.")

    fuel_type = user_preferences.get("fuel_type", "electric")
    print(f"[INFO] Searching for '{fuel_type}' stations near lat={lat}, lon={lon}")

    if fuel_type == "electric":
        return get_electric_stations(lat, lon)
    elif fuel_type == "petrol":
        return get_petrol_stations_tomtom(lat, lon)
    else:
        print(f"[ERROR] Unsupported fuel type: {fuel_type}")
        return []


if __name__ == "__main__":
    # Example usage
    user_preferences = {"fuel_type": "electric"}
    address = "L344 Lanchester Road, Cranfield, MK43 0AL"
    stations = retrieve_stations(user_preferences, location_input=address)
    for station in stations:
        print(station)