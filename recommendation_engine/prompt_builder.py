"""
prompt_builder.py

Generates a human-like LLM prompt from selected recommendations,
and saves it as a .txt file inside the prompts/ directory.
"""

from pathlib import Path
import os

PROMPT_DIR = Path("prompts")
PROMPT_DIR.mkdir(exist_ok=True)


def build_prompt(query: str, recommendations: list[dict]) -> str:
    """
    Builds a natural prompt summarizing the recommendations for the LLM.

    Args:
        query (str): what the user asked
        recommendations (list): list of dicts with name, distance_km, type or provider

    Returns:
        str: formatted prompt
    """
    prompt = f"User request: \"{query}\"\n\n"
    prompt += "Here are the filtered recommendations:\n"
    
    for rec in recommendations:
        name = rec.get("name", "Unknown")
        distance = rec.get("distance_km", "?")
        provider = rec.get("provider", "N/A")
        prompt += f"- {name} ({provider}), {distance} km away\n"
    
    prompt += "\nAct as an AI expert specialising in the field of in-car voice assistants for driving assistance.\n"
    prompt += "Based on the driver's request and the list of recommendations provided, intelligently and appropriately suggest\n"
    prompt += "recommendations to the driver so that he or she can make a choice.\n\n"
    
    return prompt

def save_prompt(prompt: str):
    """
    Save the generated prompt to a uniquely named .txt file in /prompts.

    Args:
        prompt (str): the final LLM prompt text
    """
    existing = list(PROMPT_DIR.glob("prompt_*.txt"))
    next_id = len(existing) + 1
    file_path = PROMPT_DIR / f"prompt_{next_id:03d}.txt"

    with file_path.open("w", encoding="utf-8") as f:
        f.write(prompt)

def update_prompt_history(file: str, response: str, who: str = "assistant"):
    """
    Append a line to the conversation history file, identifying the speaker.

    Args:
        file (str): filename to store the prompt history (e.g. 'dialogue.txt')
        response (str): message to log (either from user or assistant)
        who (str): speaker label, either 'user' or 'assistant' (default: 'assistant')
    """
    os.makedirs(PROMPT_DIR, exist_ok=True)  # ensure the directory exists
    path = os.path.join(PROMPT_DIR, file)

    label = "User" if who.lower() == "user" else "Assistant"
    
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"{label}: {response.strip()}\n")


def load_prompt(file: str) -> str:
    """
    Load the full dialogue history from a text file in the PROMPT_DIR.

    Args:
        file (str): filename of the prompt history (e.g. 'dialogue.txt')

    Returns:
        str: full content of the dialogue as a single string
    """
    path = os.path.join(PROMPT_DIR, file)

    if not os.path.exists(path):
        return ""  # No previous conversation

    with open(path, "r", encoding="utf-8") as f:
        return f.read()
    