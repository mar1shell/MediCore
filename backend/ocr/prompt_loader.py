from pathlib import Path

_PROMPTS_DIR = Path(__file__).parent / "prompts"

def _load_prompt(filename: str) -> str:
    path = _PROMPTS_DIR / filename
    return path.read_text(encoding="utf-8")