import pyttsx3
import time

engine = pyttsx3.init()

def set_zira_voice():
    # Use "Microsoft Zira" voice if available
    for voice in engine.getProperty('voices'):
        if "zira" in voice.name.lower():
            engine.setProperty('voice', voice.id)
            return
    print("Zira voice not found. Using default.")

set_zira_voice()

def speak(text):
    engine.say(text)
    engine.runAndWait()

# Example usage (for testing or manual call)
if __name__ == "__main__":
    texte = "Hello, this is a test of the text-to-speech system."

    start = time.time()
    speak(texte)
    end = time.time()
    
    print(f"[INFO] Speech synthesis completed in {end - start:.2f} seconds")