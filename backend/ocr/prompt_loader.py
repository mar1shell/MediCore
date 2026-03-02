import json
from pathlib import Path

_PROMPTS_DIR = Path(__file__).parent / "prompts"
_DATA_DIR = Path(__file__).parent / "data"


def load_prompt(filename: str) -> str:
    """Load a prompt text file from the prompts/ directory."""
    path = _PROMPTS_DIR / filename
    return path.read_text(encoding="utf-8")


def load_data(filename: str) -> dict:
    """Load a JSON data file from the data/ directory."""
    path = _DATA_DIR / filename
    if not path.exists():
        raise FileNotFoundError(
            f"Data file not found: {filename}. "
            f"Make sure the data/ directory contains {filename}"
        )
    return json.loads(path.read_text(encoding="utf-8"))


# Backward-compatible aliases
_load_prompt = load_prompt
_load_data = load_data
