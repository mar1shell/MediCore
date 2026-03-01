import json
from pathlib import Path

_PROMPTS_DIR = Path(__file__).parent / "prompts"
_DATA_DIR = Path(__file__).parent / "data"

def _load_prompt(filename: str) -> str:
    path = _PROMPTS_DIR / filename
    return path.read_text(encoding="utf-8")

def _load_data(filename: str) -> dict:
    path = _DATA_DIR / filename
    if not path.exists():
        raise FileNotFoundError(
            f"Data file not found: {filename}"
            f"Make sure the data/ directory contains {filename}"
        )
    return json.loads(path.read_text(encoding="utf-8"))