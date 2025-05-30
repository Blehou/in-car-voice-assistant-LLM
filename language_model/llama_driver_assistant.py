import os
from openai import OpenAI
from dotenv import load_dotenv

# Load API key from .env file
load_dotenv()
api_key = os.getenv("OPENROUTER_API_KEY")

if not api_key:
    raise ValueError("OPENROUTER_API_KEY not found in .env")

# Initialize OpenAI client with OpenRouter base URL
client = OpenAI(
    api_key=api_key,
    base_url="https://openrouter.ai/api/v1"
)

def get_llama_response(prompt: str, model: str = "meta-llama/llama-3-8b-instruct") -> str:
    """
    Get a response from a LLaMA model via OpenRouter.

    Args:
        prompt (str): the user's question or instruction
        model (str): LLaMA model to use (default: LLaMA 3 8B)

    Returns:
        str: the assistant's response
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
        print(f"[ERROR] LLaMA via OpenRouter call failed: {e}")
        return "Sorry, I couldn't generate a response right now."


if __name__ == "__main__":
    prompt = "Where can I find a charging station on the highway?"
    response = get_llama_response(prompt)
    print(f"LLaMA response: {response}")
