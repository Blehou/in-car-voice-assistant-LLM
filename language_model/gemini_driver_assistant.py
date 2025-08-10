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

def get_gemini_response(prompt: str, model: str = "google/gemini-2.0-flash-001") -> str:
    """
    Get a response from Gemini Pro model via OpenRouter.

    Args:
        prompt (str): the user's request
        model (str): model ID on OpenRouter

    Returns:
        str: response from the assistant
    """
    try:
        chat_completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are an in-car voice assistant. Be concise, natural, and helpful."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.6,
            # Controls the length of the response (≈ 1-2 short sentences max)
            max_tokens=150
        )
        return chat_completion.choices[0].message.content.strip()
    except Exception as e:
        print(f"[ERROR] Gemini via OpenRouter failed: {e}")
        return "Sorry, I couldn't generate a response right now."

if __name__ == "__main__":
    prompt = "Where can I find the nearest charging station?"
    response = get_gemini_response(prompt)
    print(f"Gemini response: {response}")
