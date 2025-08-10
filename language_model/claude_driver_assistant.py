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

def get_claude_response(prompt: str, model: str = "anthropic/claude-sonnet-4") -> str:
    """
    Get a response from Claude 3 Opus via OpenRouter.

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
        print(f"[ERROR] Claude via OpenRouter failed: {e}")
        return "Sorry, I couldn't generate a response right now."

if __name__ == "__main__":
    prompt = "Where can I stop for gas near the highway?"
    response = get_claude_response(prompt)
    print(f"Claude response: {response}")
