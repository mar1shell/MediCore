from .abbreviations import expand
from .rules import generate_flags


def cross_reference(chart_data: dict, spoken_data: dict) -> list[dict]:
    """
    Orchestrate all 3 match steps:
      1. Exact match
      2. Abbreviation expansion
      3. LLM synonym check
    Returns a list of discrepancy flags matching shared/schemas/discrepancy_flag.json.
    """
    # TODO: implement matching logic
    raise NotImplementedError
