import whisper
import sounddevice as sd
from scipy.io.wavfile import write
from pathlib import Path
from datetime import datetime

# Load Whisper-small model once
model = whisper.load_model("small")

# Define the output directory
AUDIO_DIR = Path("user/audio")
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

def record_audio(duration: int = 5, fs: int = 16000) -> str:
    """
    Record audio from the microphone and save it to user/audio/ as a .wav file.

    Args:
        duration (int): Duration in seconds (default 5s)
        fs (int): Sampling rate (default 16kHz)

    Returns:
        str: Path to the saved audio file
    """
    print(f"[INFO] Recording {duration}s of audio...")
    audio = sd.rec(int(duration * fs), samplerate=fs, channels=1)
    sd.wait()

    # Generate a filename based on timestamp
    filename = f"audio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
    file_path = AUDIO_DIR / filename

    write(file_path, fs, audio)
    print(f"[INFO] Audio saved to: {file_path}")
    return str(file_path)


def recognize_speech(audio_path: str) -> str:
    """
    Transcribe speech from an audio file using Whisper-small.

    Args:
        audio_path (str): Path to the audio file (.wav)

    Returns:
        str: Transcribed text
    """
    print("[INFO] Transcribing audio with Whisper-small...")
    result = model.transcribe(audio_path)
    return result["text"].strip()


if __name__ == "__main__":
    audio_file = record_audio(duration=5)
    transcription = recognize_speech(audio_file)
    print("\nTranscription:", transcription)
