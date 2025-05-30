from pathlib import Path

LOG_FILE = Path("user/logs/user_queries.txt")
LOG_FILE.parent.mkdir(exist_ok=True)

def log_user_query(raw_query: str):
    """
    Append the user's raw query to a plain .txt file.

    Args:
        raw_query (str): the transcribed voice input from the user
    """
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(raw_query.strip() + "\n")

# Example usage (for testing or manual call)
if __name__ == "__main__":
    texte = "Where can I quickly charge my car?"
    log_user_query(texte)