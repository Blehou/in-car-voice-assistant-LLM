import json
from pathlib import Path

# Path to the preferences file
PREF_FILE = Path("preferences_database/user_preferences.json")

def load_user_preferences():
    """
    Load user preferences from the JSON file.
    
    Returns:
        dict: Loaded preferences.
    
    Raises:
        FileNotFoundError: If the preferences file does not exist.
        json.JSONDecodeError: If the file is not a valid JSON.
    """
    if not PREF_FILE.exists():
        raise FileNotFoundError(f"Preferences file not found at: {PREF_FILE.resolve()}")
    
    with PREF_FILE.open("r") as f:
        prefs = json.load(f)
    
    return prefs

def is_preferences_file_empty() -> bool:
    """
    Check if the user preferences file is empty or non-existent.
    
    Returns:
        bool: True if the file is empty or doesn't exist, False otherwise.
    """
    return not PREF_FILE.exists() or PREF_FILE.stat().st_size == 0

if __name__ == "__main__":
    try:
        preferences = load_user_preferences()
        print("Loaded user preferences:")
        print(json.dumps(preferences, indent=4))
    except Exception as e:
        print(f"Error loading preferences: {e}")
