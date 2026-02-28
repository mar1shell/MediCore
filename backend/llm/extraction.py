from .client import chat


def extract_entities(text: str) -> dict:
    """
    Extract allergies, medications, and diagnosis from chart/spoken text.
    Returns a dict matching shared/schemas/chart_data.json.
    """
    # TODO: load prompt from ml/prompts/extraction_prompt.txt
    raise NotImplementedError
