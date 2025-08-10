import json
from pathlib import Path

# Path to the preferences file
PREF_FILE = Path("preferences_database/user_preferences.json")

def init_user_preferences():
    """
    Prompt the user for initial driving, restaurant, and activity (hobby) preferences,
    then store the result in a structured JSON file at 'preferences_database/user_preferences.json'.

    The stored preferences follow a structured schema with three main categories:

    1. stations:
        - fuel_type (str): Type of fuel used by the vehicle (e.g., "electric", "diesel", "gas").
        - preferred_providers (list[str]): List of preferred fuel or charging providers (e.g., Tesla, Ionity).
        - max_detour_km (int): Maximum distance allowed for detours, in kilometers.
        - avoid (list[str]): List of station features to avoid (e.g., "highway", "expensive").
        - charging_power_min_kw (int or None): Minimum required charging power in kW (only if electric).
        - history (list): List of visited or suggested stations with metadata.

    2. restaurants:
        - preferred_cuisine_types (list[str]): List of preferred types of cuisine (e.g., "Italian", "Asian").
        - average_budget (str): Average budget or price range per meal (e.g., "cheap", "moderate", "expensive").
        - max_distance_from_route_km (int): Maximum detour distance from the route to the restaurant.
        - special_needs (list[str]): Dietary restrictions or needs (e.g., "vegan", "gluten-free").
        - desired_ambiance (str): Desired restaurant ambiance (e.g., "calm", "family").
        - blacklisted_restaurants (list[str]): Chains or specific places to avoid.
        - reservation_preference (str): Whether reservations are preferred ("yes" or "no").
        - min_rating (float): Minimum acceptable review rating (e.g., 4.0).
        - history (list): List of visited or recommended restaurants with metadata.

    3. hobbies:
        - preferred_activity_types (list[str]): Preferred leisure activities (e.g., "museum", "cinema").
        - indoor_or_outdoor (str): Preference for activity type ("indoor", "outdoor", or "both").
        - max_budget_per_activity (int): Maximum acceptable price per activity.
        - easy_access_or_parking (str): Whether easy access or parking is desired ("yes" or "no").
        - availability (str): Whether only freely accessible or non-reservation activities are preferred.
        - max_distance_from_route_km (int): Maximum detour distance from the route to the activity.
        - min_rating (float): Minimum acceptable rating for activities (e.g., 4.0).
        - history (list): List of hobbies done or recommended, stored with optional metadata.

    Returns:
        None
    """

    print("Initializing user preferences:\n")

    # === STATIONS ===
    print("Preferences - Stations")
    fuel_type = input("Fuel type (electric / diesel / gas): ").strip().lower()
    stations = {
        "fuel_type": fuel_type,
        "preferred_providers": input("Preferred providers (comma-separated): ").split(","),
        "max_detour_km": int(input("Maximum allowed detour (in km): ")),
        "avoid": input("Things to avoid (e.g. highway stations, comma-separated): ").split(","),
        "charging_power_min_kw": int(input("Minimum required charging power (in kW): ")) if fuel_type == "electric" else None,
        "history": []
    }

    stations["preferred_providers"] = [p.strip() for p in stations["preferred_providers"]]
    stations["avoid"] = [e.strip() for e in stations["avoid"]]

    # === RESTAURANTS ===
    print("\nPreferences - Restaurants")
    restaurants = {
        "preferred_cuisine_types": input("Preferred cuisine types (comma-separated): ").split(","),
        "average_budget": input("Average budget ('cheap', 'moderate', 'expensive'): ").strip().lower(),
        "max_distance_from_route_km": int(input("Maximum distance from route (in km): ")),
        "special_needs": input("Special needs (vegan, halal, gluten-free, allergies - comma-separated): ").split(","),
        "desired_ambiance": input("Preferred ambiance (calm, romantic, family, etc.): ").strip(),
        "blacklisted_restaurants": input("Chains/restaurants to avoid (comma-separated): ").split(","),
        "reservation_preference": input("Prefer restaurants with reservation? (yes/no): ").strip().lower(),
        "min_rating": float(input("Minimum acceptable rating (e.g. 4.0): ")),
        "history": []
    }

    restaurants["preferred_cuisine_types"] = [c.strip() for c in restaurants["preferred_cuisine_types"]]
    restaurants["special_needs"] = [b.strip() for b in restaurants["special_needs"]]
    restaurants["blacklisted_restaurants"] = [r.strip() for r in restaurants["blacklisted_restaurants"]]

    # === HOBBIES ===
    print("\nPreferences - Hobbies")
    hobbies = {
        "preferred_activity_types": input("Preferred activity types (museums, hiking, etc. - comma-separated): ").split(","),
        "indoor_or_outdoor": input("Indoor or outdoor preference (indoor / outdoor / both): ").strip().lower(),
        "max_distance_from_route_km": int(input("Maximum distance from route (in km): ")),
        "max_budget_per_activity": input("Maximum budget per activity ('cheap', 'moderate', 'expensive'): ").strip(),
        "easy_access_or_parking": input("Require easy access or parking? (yes/no): ").strip().lower(),
        "availability": input("Only recommend activities without reservation? (yes/no): ").strip().lower(),
        "min_rating": float(input("Minimum acceptable rating (e.g. 4.0): ")),
        "history": []
    }

    hobbies["preferred_activity_types"] = [a.strip() for a in hobbies["preferred_activity_types"]]

    # Final structure
    preferences = {
        "stations": stations,
        "restaurants": restaurants,
        "hobbies": hobbies
    }

    # Save to JSON
    PREF_FILE.parent.mkdir(parents=True, exist_ok=True)
    with PREF_FILE.open("w") as f:
        json.dump(preferences, f, indent=4)

    print(f"\nPreferences saved to {PREF_FILE.resolve()}")

if __name__ == "__main__":
    init_user_preferences()
