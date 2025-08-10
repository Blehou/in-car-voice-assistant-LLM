import json
from pathlib import Path
from datetime import datetime

# Path to the preferences file
PREF_FILE = Path("preferences_database/user_preferences.json")

def add_history_entry(location: str, POIs: str, POI_category: str, used: bool = True):
    """
    Add a new usage record to the history field in the user preferences file.

    Each entry includes:
        - location: city or region
        - POIs: name of the points of interest
        - used: whether it was used or just recommended
        - timestamp: ISO 8601 formatted datetime (UTC)

    Args:
        location (str): Name of the city or area.
        POIs (str): Points of interest.
        POI_category (str): Category of the points of interest (stations, restaurants, hobbies).
        used (bool): Whether the station was actually used.

    Raises:
        FileNotFoundError: If the preferences file doesn't exist.
    """
    if not PREF_FILE.exists():
        raise FileNotFoundError("Preferences file not found. Run init_preferences.py first.")

    with PREF_FILE.open("r+") as f:
        prefs = json.load(f)

        # Create the new history entry
        entry = {
            "location": location,
            "name": POIs,
            "used": used,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

        # Append entry to history
        prefs[POI_category]["history"].append(entry)

        # Save updated preferences
        f.seek(0)
        json.dump(prefs, f, indent=4)
        f.truncate()

# Example usage (for testing or manual call)
if __name__ == "__main__":
    add_history_entry("Paris", "Museum of Illusions", "hobbies", used=True)
