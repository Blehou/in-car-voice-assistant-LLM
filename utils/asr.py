import whisper
import sounddevice as sd
from scipy.io.wavfile import write
from pathlib import Path
from datetime import datetime
import time
from faster_whisper import WhisperModel


# Load Whisper-small model once
model = whisper.load_model("small")
fast_model = WhisperModel("small", device="cpu", compute_type="int8")

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


def recognize_speech_fast(audio_path: str) -> str:
    """
    Transcribe speech from an audio file using faster-whisper.

    This function uses the optimized faster-whisper library to convert spoken
    audio into text. It loads a quantized version of the Whisper model for
    faster inference on CPU.

    Args:
        audio_path (str): Path to the audio file (.wav) to transcribe.

    Returns:
        str: The transcribed text from the audio file.
    """
    print("[INFO] Transcribing audio with faster-whisper...")
    segments, _ = fast_model.transcribe(audio_path)
    result = " ".join(segment.text for segment in segments)
    return result.strip()



if __name__ == "__main__":
    # Audio recording timing
    start_audio = time.time()
    audio_file = record_audio(duration=5)
    end_audio = time.time()
    print(f"[INFO] Audio recording took {end_audio - start_audio:.2f} seconds")
    print('\n')

    # # Whisper timing
    # start_whisper = time.time()
    # transcription1 = recognize_speech(audio_file)
    # end_whisper = time.time()
    # print(f"[INFO] Whisper-small transcription took {end_whisper - start_whisper:.2f} seconds")
    # print(transcription1)
    # print('\n')

    # Faster-whisper timing
    start_fast = time.time()
    transcription2 = recognize_speech_fast(audio_file)
    end_fast = time.time()
    print(f"[INFO] Faster-whisper transcription took {end_fast - start_fast:.2f} seconds")
    print(transcription2)
