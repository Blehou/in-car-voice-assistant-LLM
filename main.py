from dialogue_manager.dialog_manager import DialogueManager
from dialogue_manager.state import State
from preferences_database.init_preferences import init_user_preferences
from preferences_database.preferences_loader import load_user_preferences, is_preferences_file_empty
from utils.tts import speak
import json


if is_preferences_file_empty():
    text1 = "Hello ! I'm delighted to welcome you on board. I'm your driving assistant, at your service to navigate according " \
    "to your points of interest. Before we start, please answer a few questions so that I can get to know your preferences better."

    speak(text1)

    # Initialize user preferences
    init_user_preferences()

else:
    text2 = "Hello ! I'm delighted to welcome you on board. I'm your driving assistant, at your service to navigate according " \
    "to your points of interest. Let's get started."

    speak(text2)

# Load user preferences from the JSON file
user_preferences = load_user_preferences()
# print("Loaded user preferences:")
# print(json.dumps(user_preferences, indent=4))

# Initialize the DialogueManager with user preferences
dm = DialogueManager(user_preferences)

while not dm.exit:
    reply = dm.handle_input()
    if reply:
        print("\n")
        print(f"Assistant: {reply}")
        speak(reply)
        print("\n")
    