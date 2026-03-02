"""Unit tests for backend/ocr/prompt_loader.py."""
import pytest
from pathlib import Path

from backend.ocr.prompt_loader import load_prompt, _load_prompt


EXPECTED_PROMPTS = [
    "extraction_system_prompt.txt",
    "extraction_user_template.txt",
    "safety_check_system_prompt.txt",
]


class TestLoadPrompt:
    @pytest.mark.parametrize("filename", EXPECTED_PROMPTS)
    def test_loads_known_prompt(self, filename: str):
        text = load_prompt(filename)
        assert isinstance(text, str)
        assert len(text) > 10, f"{filename} should not be empty"

    def test_extraction_system_prompt_contains_key_instruction(self):
        text = load_prompt("extraction_system_prompt.txt")
        assert "allergies" in text.lower()
        assert "medications" in text.lower()

    def test_extraction_user_template_has_placeholders(self):
        text = load_prompt("extraction_user_template.txt")
        assert "{source_type}" in text
        assert "{text}" in text

    def test_safety_prompt_contains_key_concept(self):
        text = load_prompt("safety_check_system_prompt.txt")
        # The safety prompt should mention safety or allergy concepts
        lower = text.lower()
        assert any(word in lower for word in ["allerg", "safe", "drug", "medication"])

    def test_missing_file_raises(self):
        with pytest.raises(FileNotFoundError):
            load_prompt("nonexistent_prompt.txt")

    def test_backward_compat_alias(self):
        """_load_prompt alias still works for any code not yet updated."""
        text = _load_prompt("extraction_system_prompt.txt")
        assert isinstance(text, str)
        assert len(text) > 0

    def test_alias_returns_same_as_public(self):
        assert load_prompt("extraction_system_prompt.txt") == _load_prompt("extraction_system_prompt.txt")
