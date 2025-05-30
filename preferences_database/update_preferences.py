import json
from pathlib import Path
from datetime import datetime

# Path to the preferences file
PREF_FILE = Path("preferences_database/user_preferences.json")

def add_history_entry(location: str, station: str, used: bool = True):
    """
    Add a new usage record to the history field in the user preferences file.

    Each entry includes:
        - location: city or region
        - station: name of the charging provider
        - used: whether it was used or just recommended
        - timestamp: ISO 8601 formatted datetime (UTC)

    Args:
        location (str): Name of the city or area.
        station (str): Charging provider name.
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
            "station": station,
            "used": used,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

        # Append entry to history
        prefs["history"].append(entry)

        # Save updated preferences
        f.seek(0)
        json.dump(prefs, f, indent=4)
        f.truncate()

# Example usage (for testing or manual call)
if __name__ == "__main__":
    add_history_entry("Lyon", "Ionity", used=True)
