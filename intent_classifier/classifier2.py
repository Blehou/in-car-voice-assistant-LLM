from language_model.gpt4_driver_assistant import get_response

def create_prompt(user_query: str) -> str:
    """Create a prompt for the user query.

    Args:
        user_query (str): The user's query.

    Returns:
        str: The formatted prompt.
    """
    prompt = f"User request: \"{user_query}\"\n\n"
    prompt += "Act as an expert in artificial intelligence. Based on the user's query, Highlight the intention that is most evident in the question asked by the driver.\n"
    prompt += "The expected intention must be: stations, restaurants, hobbies.\n"
    prompt += "Only one output is expected, not two at the same time. If the user specifies the name of his point of interest in the query, return that name.\n"
    prompt += "And if other conditions are mentioned in the queries, return them also.\n"
    prompt += "Expected output: intention, name."
    prompt += "For example, if the user asks: \"Find me a place for biking near here.\", the expected output is: [\"hobbies\", \"biking\"]\n"
    prompt += "If the user asks: \"Suggest me a place where can I have fun?\", the expected output is: [\"hobbies\"]\n"
    prompt += "If the user asks: \"Find some bakeries with a minimum rating of 4.5 stars near me\", the expected output is: [\"restaurants\", \"bakeries\", \"4.5\"]\n"
    prompt += "If the user asks: \"Recommend me a seafood restaurant in 5km with a minimum rating of 4.4 stars.\", the expected output is: [\"restaurants\", \"seafood\", \"5km\", \"4.4\"]\n"
    prompt += "If you do not detect the intentions I mentioned before (stations, restaurants, hobbies) in the user's question, return None."
    return prompt


def get_intent(user_query: str) -> list:
    """Get the user's intent from the query.

    Args:
        user_query (str): The user's query.

    Returns:
        str: The user's intent.
    """
    prompt = create_prompt(user_query)
    response = get_response(prompt)
    response = parse_intent(response)
    return response

def parse_intent(intent: str) -> list:
    """Parse the intent string into a list of components.

    Args:
        intent (str): The intent string to parse.

    Returns:
        list: A list of components extracted from the intent string.
    """
    components = intent.strip("[]").split(", ")
    return [c.strip("\"").strip("'") for c in components]


# Example usage
if __name__ == "__main__":
    intent = "['restaurants', 'vegetarian', '4.5']"
    components = parse_intent(intent)
    print(components)
    min_rating = float(components[2])
    print(f"Minimum rating: {min_rating}")
