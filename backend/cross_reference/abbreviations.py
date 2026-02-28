import json
import os

_ABBREV_PATH = os.path.join(
    os.path.dirname(__file__), "../../../ml/abbreviations/medical_abbrev.json"
)

with open(_ABBREV_PATH) as f:
    ABBREVIATIONS: dict[str, str] = json.load(f)


def expand(term: str) -> str:
    """Expand a medical abbreviation to its full form, or return term unchanged."""
    return ABBREVIATIONS.get(term.lower(), term)
