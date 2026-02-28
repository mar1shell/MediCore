import os
from mistralai import Mistral


def get_client() -> Mistral:
    return Mistral(api_key=os.environ["MISTRAL_API_KEY"])


def chat(messages: list[dict], model: str = "mistral-large-latest") -> str:
    """Send messages to Mistral and return the assistant reply."""
    client = get_client()
    response = client.chat.complete(model=model, messages=messages)
    return response.choices[0].message.content
