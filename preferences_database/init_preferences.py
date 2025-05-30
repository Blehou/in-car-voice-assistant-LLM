import json
from pathlib import Path

# Path to the preferences file
PREF_FILE = Path("preferences_database/user_preferences.json")

def init_user_preferences():
    """
    Prompt the user for their driving and charging preferences and save them to a JSON file.
    
    The preferences include:
        - Fuel type
        - Preferred providers (e.g. Tesla, Ionity)
        - Maximum detour distance (in km)
        - Types of stations or features to avoid
        - Minimum charging power (in kW)
        - Usage history (initialized as empty)
    
    """
    
    print("Initializing user preferences:\n")

    # Ask the user for each preference
    prefs = {
        "fuel_type": input("Fuel type (electric / diesel / gas): ").strip().lower(),
        "preferred_providers": input("Preferred providers (comma-separated): ").split(","),
        "max_detour_km": int(input("Maximum allowed detour (in km): ")),
        "avoid": input("Things to avoid (e.g. highway stations, comma-separated): ").split(","),
        "charging_power_min_kw": int(input("Minimum required charging power (in kW): ")), 
        "history": []  # Will store usage history later
    }

    # Clean up whitespaces from lists
    prefs["preferred_providers"] = [p.strip() for p in prefs["preferred_providers"]]
    prefs["avoid"] = [a.strip() for a in prefs["avoid"]]

    # Ensure directory exists, then write to JSON
    PREF_FILE.parent.mkdir(parents=True, exist_ok=True)
    with PREF_FILE.open("w") as f:
        json.dump(prefs, f, indent=4)
    
    print(f"\nPreferences saved to {PREF_FILE.resolve()}")

if __name__ == "__main__":
    init_user_preferences()
