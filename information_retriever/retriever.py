############################################################
## retriever.py

## Retrieves nearby points of interest based on either:
### - user-provided address
### - or (lat, lon) GPS coordinates

## Uses OpenChargeMap, TomTom, and Google Places APIs and returns
## the data preprocessed in a format compatible with the
## recommendation engine.
############################################################

# --- IMPORTS ---
import requests
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
from typing import List, Tuple, Optional
import unicodedata



# --- API KEYS ---
OPENCHARGEMAP_API_KEY = "49af854f-f8fb-4b73-9fb1-b5a04ab8e393"
TOMTOM_API_KEY = "V4Z58HqLLL2QnGFjC1RFsGnLn8alwNjK"
GOOGLE_PLACES_API_KEY = "AIzaSyD2QaQRB0pErm1jI_sV8MJAIdA4hXBBsrs"

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

def get_electric_stations(user_preferences: dict, lat: float, lon: float, radius_km: int = 10) -> List[dict]:
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
        return preprocess_ocm(user_preferences, response.json())
    except requests.RequestException as e:
        print(f"[ERROR] OCM request failed: {e}")
        return []


def preprocess_ocm(user_preferences: dict, raw_data: List[dict]) -> List[dict]:
    stations = []
    prefs = user_preferences.get("stations", {})
    preferred_providers = prefs.get("preferred_providers", [])
    max_detour_km = prefs.get("max_detour_km", 0)
    charging_power_min_kw = prefs.get("charging_power_min_kw", 0)
    for entry in raw_data:
        try:
            name = entry.get("AddressInfo", {}).get("Title", "Unknown Station")
            provider = entry.get("OperatorInfo", {}).get("Title", "Unknown Provider")
            distance = entry.get("AddressInfo", {}).get("Distance", 0)
            power = 0

            connections = entry.get("Connections", [])
            if connections:
                power = max((c.get("PowerKW", 0) or 0) for c in connections)

            if distance > max_detour_km:
                continue
            
            if power < charging_power_min_kw:
                continue

            if provider not in preferred_providers:
                continue

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

def get_petrol_stations_tomtom(user_preferences: dict, lat: float, lon: float, radius_m: int = 10000, api_key: str = TOMTOM_API_KEY) -> list:
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
        prefs = user_preferences.get("stations", {})
        preferred_providers = prefs.get("preferred_providers", [])
        max_detour_km = prefs.get("max_detour_km", 0)

        for result in data.get("results", []):
            poi = result.get("poi", {})
            name = poi.get("name", "Unknown Station")
            provider = poi.get("name", "Unknown Provider").split()[0]
            distance = round(result.get("dist", 0) / 1000, 2)

            if distance > max_detour_km:
                continue

            if provider not in preferred_providers:
                continue

            stations.append({
                "name": name,
                "provider": provider,
                "distance_km": distance,
                "charging_power_kw": 0
            })

        return stations

    except Exception as e:
        print(f"[ERROR] TomTom request failed: {e}")
        return []


# --- MAIN ENTRYPOINT ---

###### Case 1: Retrieve Stations #######

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

    prefs = user_preferences.get("stations", {})
    fuel_type = prefs.get("fuel_type", "electric")
    print(f"[INFO] Searching for '{fuel_type}' stations near lat={lat}, lon={lon}")

    if fuel_type == "electric":
        return get_electric_stations(user_preferences, lat, lon)
    elif fuel_type == "petrol":
        return get_petrol_stations_tomtom(user_preferences, lat, lon)
    else:
        print(f"[ERROR] Unsupported fuel type: {fuel_type}")
        return []


####### Case 2: Retrieve Restaurants #######

def compute_distance_km(user_coords: Tuple[float, float], place_coords: Tuple[float, float]) -> float:
    """
    Compute the geodesic distance in kilometers between two (lat, lon) points.

    Args:
        user_coords (Tuple[float, float]): (latitude, longitude) of the user
        place_coords (Tuple[float, float]): (latitude, longitude) of the place

    Returns:
        float: Distance in kilometers, rounded to 2 decimals
    """
    return round(geodesic(user_coords, place_coords).km, 2)

def fetch_place_details(place_id: str, api_key: str = GOOGLE_PLACES_API_KEY) -> dict:
    """
    Fetch additional details about a place using its Google Place ID.

    Args:
        place_id (str): Unique ID of the place.
        api_key (str): Your Google Places API key.

    Returns:
        dict: Dictionary containing 'website' and 'maps_url' if available.
    """
    url = "https://maps.googleapis.com/maps/api/place/details/json"
    params = {
        "place_id": place_id,
        "fields": "website,url",
        "key": api_key
    }

    try:
        response = requests.get(url, params=params)
        if response.status_code != 200:
            print(f"[ERROR] Place Details API error: {response.status_code}")
            return {}

        result = response.json().get("result", {})
        return {
            "website": result.get("website", None),
            "maps_url": result.get("url", None)
        }

    except Exception as e:
        print(f"[ERROR] Failed to fetch details for place_id {place_id}: {e}")
        return {}



def retrieve_restaurants(user_preferences: dict, keywords: Optional[List[str]] = None, location_input: str = "", latlon: Optional[Tuple[float, float]] = None, radius_m: int = 10000,
    api_key: str = GOOGLE_PLACES_API_KEY) -> List[dict]:
    """
    Retrieve a list of nearby restaurants using Google Places API based on user preferences and location.

    Args:
        user_preferences (dict): Dictionary containing restaurant preferences.
        keywords (Optional[List[str]]): Optional list of explicit keywords to filter restaurants.
        location_input (str): Optional address string.
        latlon (Tuple[float, float]): Optional (latitude, longitude) tuple.
        radius_m (int): radius in meters
        api_key (str): Google Places API key.

    Returns:
        List[dict]: A list of recommended restaurants matching preferences.
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

    try:
        prefs = user_preferences["restaurants"]

        preferred_cuisines = prefs["preferred_cuisine_types"]
        special_needs = prefs["special_needs"]
        ambiance = prefs["desired_ambiance"]  # No default
        budget = prefs["average_budget"]  # e.g., 'cheap', 'moderate', 'expensive'
        min_rating = prefs["min_rating"]
        blacklist = prefs["blacklisted_restaurants"]
        requires_reservation = prefs["reservation_preference"]  # 'yes' or 'no'

    except KeyError as e:
        print(f"[ERROR] Missing preference field: {e}")
        return []
    
    distance_keyword = None

    if keywords is None:
        search_keywords = preferred_cuisines
    else:
        if len(keywords) == 2:
            search_keywords = [keywords[1]]
        elif len(keywords) == 3:
            search_keywords = [keywords[1]]
            if "km" in keywords[2]:
                distance_keyword = float(keywords[2].replace("km", "").strip())
            else:
                min_rating = float(keywords[2])
        elif len(keywords) == 4:
            search_keywords = [keywords[1]]
            if "km" in keywords[2]:
                distance_keyword = float(keywords[2].replace("km", "").strip())
            else:
                min_rating = float(keywords[2])
            if "km" in keywords[3]:
                distance_keyword = float(keywords[3].replace("km", "").strip())
            else:
                min_rating1 = float(keywords[3])
        else:
            search_keywords = preferred_cuisines

    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    price_map = {'inexpensive': 0, 'cheap': 1, 'moderate': 2, 'expensive': 3, 'very_expensive': 4}
    max_price = price_map.get(budget.lower(), 2)  # Default to 'moderate'

    seen_place_ids = set()
    results = []
    
    for cuisine in search_keywords:
        params = {
            "key": api_key,
            "location": f"{lat},{lon}",
            "radius": radius_m,
            "type": "restaurant",
            "keyword": f"{cuisine} {' '.join(special_needs)} {ambiance}",
            "maxprice": max_price
        }

        try:
            response = requests.get(url, params=params)
            if response.status_code != 200:
                print(f"[ERROR] Google Places API error: {response.status_code} - {response.text}")
                continue

            for place in response.json().get("results", []):
                place_id = place["place_id"]

                if place_id in seen_place_ids:
                    continue  # Skip duplicate

                name = place["name"]
                rating = place.get("rating", 0)

                if rating < min_rating:
                    continue

                if any(bad_name.lower() in name.lower() for bad_name in blacklist):
                    continue

                place_lat = place["geometry"]["location"]["lat"]
                place_lon = place["geometry"]["location"]["lng"]
                distance_km = compute_distance_km((lat, lon), (place_lat, place_lon))

                if distance_keyword and distance_km > distance_keyword:
                    continue

                details = fetch_place_details(place_id, api_key)

                website = details.get("website", None)
                maps_url = details.get("maps_url", None)

                results.append({
                    "name": name,
                    "address": place.get("vicinity", ""),
                    "rating": rating,
                    "price_level": place.get("price_level", "Unknown"),
                    "open_now": place.get("opening_hours", {}).get("open_now", "Unknown"),
                    "distance_km": distance_km,
                    "types": place.get("types", []),
                    "place_id": place_id,
                    "website": website,
                    "maps_url": maps_url
                })

                seen_place_ids.add(place_id)

        except Exception as e:
            print(f"[ERROR] Failed to fetch restaurants for cuisine '{cuisine}': {e}")
            continue

    return results


#### Case 3: Retrieve hobbies #####

def activity_to_place_type(activity: str) -> Tuple[str, str]:
    """
    Retourne (place_type, keyword_supplementaire) pour Google Places.
    'keyword_supplementaire' peut être vide. Gère FR/EN + sports.
    """
    if not activity:
        return "point_of_interest", ""

    norm = unicodedata.normalize("NFKD", activity).encode("ascii", "ignore").decode("ascii")
    norm = norm.lower().strip()

    SYNS = {
        ("cinema", "cine", "film", "movies", "movie", "cinemas", "Cinema"): ("movie_theater", ""),
        ("musee", "museum"): ("museum", ""),
        ("galerie", "galerie d art", "art gallery"): ("art_gallery", ""),
        ("aquarium",): ("aquarium", ""),
        ("zoo",): ("zoo", ""),
        ("bibliotheque", "library", "mediatheque"): ("library", ""),
        ("amusement park", "parc d attractions", "parc d attraction", "luna park"): ("amusement_park", ""),
        ("bowling",): ("bowling_alley", ""),
        ("gym", "fitness", "salle de sport"): ("gym", ""),
        ("spa", "hammam"): ("spa", ""),
        ("stade", "stadium"): ("stadium", ""),
        ("camping", "campground"): ("campground", ""),
        ("parc", "park", "jardin", "jardins"): ("park", ""),
        ("librairie", "bookstore", "book shop", "bookshop"): ("book_store", ""),
        ("nightclub", "discotheque", "disco", "boite de nuit", "boite"): ("night_club", ""),
        ("piscine", "swimming", "swimming pool", "piscine municipale"): ("swimming_pool", ""),
    }
    for syns, out in SYNS.items():
        if norm in syns:
            return out

    # Sports
    if norm in {"basket", "basketball"}:
        return "gym", "basketball"              # indoor (marche bien)
    if norm in {"football", "foot", "soccer", "futsal", "five"}:
        return "stadium", "football"            # stades/terrains

    # Heuristiques simples
    if "escalade" in norm or "climb" in norm:
        return "gym", "climbing"
    if "patinoire" in norm or "ice skating" in norm:
        return "point_of_interest", "patinoire"
    if ("theatre" in norm or "theater" in norm) and "movie" not in norm:
        return "point_of_interest", "theatre"
    if "escape" in norm:
        return "point_of_interest", "escape game"
    if "concert" in norm or "salle de concert" in norm or "music" in norm:
        return "point_of_interest", "concert"

    return "point_of_interest", ""


def retrieve_hobby_activity(user_preferences: dict, keywords: Optional[List[str]] = None, location_input: str = "", latlon: Optional[Tuple[float, float]] = None, radius_m: int = 10000, 
                            api_key: str = GOOGLE_PLACES_API_KEY) -> List[dict]:
    """
    Retrieve hobby-related places (e.g. cinema, museum) based on preferences and optional activity keyword.

    Args:
        user_preferences (dict): Dictionary with 'hobbies' preferences.
        keywords (List[str]): Optional explicit activity keywords (e.g. 'bowling'). Overrides preferences.
        location_input (str): Optional user-provided address.
        latlon (Tuple[float, float]): Optional lat/lon GPS coordinates.
        radius_m (int): Search radius (in meters).
        api_key (str): Google Places API key.

    Returns:
        List[dict]: List of matching hobby activities nearby.
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

    try:
        prefs = user_preferences["hobbies"]
        preferred_activities = prefs.get("preferred_activity_types", [])
        indoor_or_outdoor = prefs.get("indoor_or_outdoor", "both")
        max_budget = prefs.get("max_budget_per_activity", 'moderate')
        easy_parking = prefs.get("easy_access_or_parking", "no") == "yes"
        min_rating = prefs.get("min_rating", 4.0)
        require_availability = prefs.get("availability", "yes") == "yes"
    except KeyError as e:
        print(f"[ERROR] Missing hobby preference field: {e}")
        return []

    
    distance_keyword = None

    if keywords is None:
        search_keywords = preferred_activities
    else:
        if len(keywords) == 2:
            search_keywords = [keywords[1]]
        elif len(keywords) == 3:
            search_keywords = [keywords[1]]
            if "km" in keywords[2]:
                distance_keyword = float(keywords[2].replace("km", "").strip())
            else:
                min_rating = float(keywords[2])
        elif len(keywords) == 4:
            search_keywords = [keywords[1]]
            if "km" in keywords[2]:
                distance_keyword = float(keywords[2].replace("km", "").strip())
            else:
                min_rating = float(keywords[2])
            if "km" in keywords[3]:
                distance_keyword = float(keywords[3].replace("km", "").strip())
            else:
                min_rating1 = float(keywords[3])
        else:
            search_keywords = preferred_activities


    if distance_keyword:
        try:
            radius_m = min(radius_m, int(float(distance_keyword) * 1000))
        except Exception:
            pass

    user_coords = (lat, lon)
    results = []
    seen_place_ids = set()  # ← Ajout pour filtrer les doublons

    price_map = {'inexpensive': 0, 'cheap': 1, 'moderate': 2, 'expensive': 3, 'very_expensive': 4}
    max_budget_ = price_map.get(max_budget.lower(), 2)

    for activity in search_keywords:
        # ✅ on déduit le type spécialisé + éventuel mot-clé complémentaire
        place_type, kw_extra = activity_to_place_type(activity)
        full_keyword = f"{activity} parking" if easy_parking else activity
        if kw_extra and kw_extra.lower() not in full_keyword.lower():
            full_keyword = f"{full_keyword} {kw_extra}"

        params = {
            "key": api_key,
            "location": f"{lat},{lon}",
            "radius": radius_m,
            "type": place_type,              # ✅ auparavant: "point_of_interest"
            "keyword": full_keyword,
            "language": "fr",  # or "en" based on user preference
        }

        if require_availability:
            params["opennow"] = "true"

        if max_budget is not None:
            params["maxprice"] = max_budget_
        
        try:
            resp = requests.get("https://maps.googleapis.com/maps/api/place/nearbysearch/json", params=params)
            if resp.status_code != 200:
                print(f"[ERROR] Google Places API error: {resp.status_code}")
                continue

            for place in resp.json().get("results", []):
                place_id = place["place_id"]

                if place_id in seen_place_ids:
                    continue

                rating = float(place.get("rating", 0) or 0)   # ✅ cast sûr

                if rating < float(min_rating):
                    continue

                seen_place_ids.add(place_id)

                place_lat = place["geometry"]["location"]["lat"]
                place_lon = place["geometry"]["location"]["lng"]

                details = fetch_place_details(place_id, api_key)

                website = details.get("website", None)
                maps_url = details.get("maps_url", None)
                distance_km = compute_distance_km(user_coords, (place_lat, place_lon))

                # ✅ compare float à float
                if distance_keyword and distance_km > float(distance_keyword):
                    continue

                results.append({
                    "name": place.get("name"),
                    "address": place.get("vicinity", ""),
                    "rating": place.get("rating", 0),
                    "types": place.get("types", []),
                    "place_id": place_id,
                    "open_now": place.get("opening_hours", {}).get("open_now", "Unknown"),
                    "distance_km": distance_km,
                    "website": website,
                    "maps_url": maps_url
                })

        except Exception as e:
            print(f"[ERROR] Failed to retrieve activity '{activity}': {e}")
            continue

    return results

# Example usage
if __name__ == "__main__":
    user_preferences = {
        "stations": {
            "fuel_type": "electric",
            "preferred_providers": ["BP Pulse (UK)", "Ionity", "TotalEnergies"],
            "max_detour_km": 7,
            "avoid": ["highway stations"],
            "charging_power_min_kw": 25,
            "history": []
        },
        "restaurants": {
            "preferred_cuisine_types": [ "African", "Italian", "European", "Asian"],
            "special_needs": ["vegan", "halal"],
            "desired_ambiance": "romantic",
            "average_budget": "moderate",
            "min_rating": 4.2,
            "blacklisted_restaurants": ["McDonald's", "Buffalo Grill"],
            "reservation_preference": True
        },
        "hobbies": {
            "preferred_activity_types": ["museum", "cinema", "bowling"],
            "indoor_or_outdoor": "both",
            "max_budget_per_activity": "moderate",
            "easy_access_or_parking": "no",
            "min_rating": 4.0,
            "availability": "no",
            "history": []
        }
    }
    address = "L344 Lanchester Road, Cranfield, MK43 0AL"
    keywords = ['hobbies', 'bowling', '10km', '4.0']

    # Case 1: Retrieve Stations
    # stations = retrieve_stations(user_preferences, location_input=address)
    stations = retrieve_stations(user_preferences, latlon=(48.9167, 2.2833)) 
    for station in stations:
        print(station)

    # Case 2: Retrieve Restaurants
    restaurants = retrieve_restaurants(user_preferences=user_preferences, latlon=(48.8566, 2.3522))
    # restaurants = retrieve_restaurants(user_preferences=user_preferences, keywords=keywords, location_input=address))
    # for r in restaurants:
    #     print(r)
    
    # Case 3: Retrieve Hobbies
    # hobbies = retrieve_hobby_activity(user_preferences=user_preferences, keywords=keywords, latlon=(48.60201740769193, 2.4705785538972003))
    hobbies = retrieve_hobby_activity(user_preferences=user_preferences, keywords=keywords, location_input=address)
    for hobby in hobbies:
        print(hobby)