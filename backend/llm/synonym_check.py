from .client import chat


def resolve_synonyms(term_a: str, term_b: str) -> bool:
    """Use LLM to determine if two medical terms refer to the same entity."""
    # TODO: load prompt from ml/prompts/synonym_prompt.txt
    raise NotImplementedError
