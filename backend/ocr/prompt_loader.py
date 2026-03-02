from pathlib import Path

_PROMPTS_DIR = Path(__file__).parent / "prompts"


def load_prompt(filename: str) -> str:
    """Load a prompt text file from the prompts/ directory."""
    return (_PROMPTS_DIR / filename).read_text(encoding="utf-8")
