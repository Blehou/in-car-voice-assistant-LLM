import os
from openai import OpenAI
from dotenv import load_dotenv

# Load API key from .env
load_dotenv()
api_key = os.getenv("OPENROUTER_API_KEY")

if not api_key:
    raise ValueError("OPENROUTER_API_KEY not found in .env")

# Initialize OpenAI client with OpenRouter base URL
client = OpenAI(
    api_key=api_key,
    base_url="https://openrouter.ai/api/v1"
)

def get_response(prompt: str, model: str = "openai/gpt-4-1106-preview") -> str:
    """
    Get a response from OpenRouter-compatible model using OpenAI SDK v1+.
    This function sends a prompt to the OpenRouter API and returns the model's response.
    It uses the OpenAI Python SDK to interact with the OpenRouter API.
    The function is designed to be used in a car assistant context, where the model is expected
    to provide concise and helpful responses.

    Args:
        prompt (str): The input prompt for the model.
        model (str): The model to use. Defaults to "openai/gpt-4-1106-preview".
    Returns:
        str: The model's response.
    """
    try:
        chat_completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are an in-car voice assistant. Be concise, natural, and helpful."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.6,
            max_tokens=150
        )
        return chat_completion.choices[0].message.content.strip()
    except Exception as e:
        print(f"[ERROR] OpenRouter call failed: {e}")
        return "Sorry, I couldn't generate a response right now."


if __name__ == "__main__":
    prompt = "Where can I find the nearest gas station?"
    response = get_response(prompt)
    print(f"Response: {response}")
