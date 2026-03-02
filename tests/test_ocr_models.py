"""Unit tests for backend/ocr/models.py — domain dataclasses."""
import pytest

from backend.ocr.models import ChartPage, OCRResult, ExtractedEntities, DiscrepancyFlag, CrossReferenceResult


# ---------------------------------------------------------------------------
# ChartPage
# ---------------------------------------------------------------------------

class TestChartPage:
    def test_is_empty_blank(self):
        page = ChartPage(page_number=0, text="   ")
        assert page.is_empty is True

    def test_is_empty_with_content(self):
        page = ChartPage(page_number=0, text="Patient: John Smith")
        assert page.is_empty is False

    def test_optional_dimensions_default_none(self):
        page = ChartPage(page_number=1, text="text")
        assert page.width is None
        assert page.height is None

    def test_dimensions_stored(self):
        page = ChartPage(page_number=0, text="x", width=595.0, height=842.0)
        assert page.width == 595.0
        assert page.height == 842.0


# ---------------------------------------------------------------------------
# OCRResult
# ---------------------------------------------------------------------------

class TestOCRResult:
    def _result(self, text: str = "Patient: John\nAllergies: Penicillin") -> OCRResult:
        page = ChartPage(page_number=0, text=text)
        return OCRResult(
            filename="chart.pdf",
            full_text=text,
            pages=[page],
            model_used="mistral-ocr-latest",
            pages_processed=1,
        )

    def test_char_count(self):
        r = self._result("abc")
        assert r.char_count == 3

    def test_is_usable_long_text(self):
        r = self._result("x" * 100)
        assert r.is_usable is True

    def test_is_usable_short_text(self):
        r = self._result("short")
        assert r.is_usable is False

    def test_get_page_found(self):
        r = self._result()
        assert r.get_page(0) is r.pages[0]

    def test_get_page_not_found(self):
        r = self._result()
        assert r.get_page(99) is None


# ---------------------------------------------------------------------------
# ExtractedEntities
# ---------------------------------------------------------------------------

class TestExtractedEntities:
    def _entities(self) -> ExtractedEntities:
        return ExtractedEntities(
            source="chart",
            allergies=["penicillin", "sulfa"],
            medications=[
                {"name": "metformin", "dose": "500mg"},
                {"name": "lisinopril", "dose": "10mg"},
            ],
            diagnosis="type 2 diabetes",
        )

    def test_allergy_names(self):
        e = self._entities()
        assert e.allergy_names == ["penicillin", "sulfa"]

    def test_medication_names(self):
        e = self._entities()
        assert e.medication_names == ["metformin", "lisinopril"]

    def test_to_dict_keys(self):
        e = self._entities()
        d = e.to_dict()
        assert set(d.keys()) == {"source", "allergies", "medications", "diagnosis", "extraction_notes", "diagrams"}

    def test_to_dict_values(self):
        e = self._entities()
        d = e.to_dict()
        assert d["source"] == "chart"
        assert d["allergies"] == ["penicillin", "sulfa"]
        assert d["diagnosis"] == "type 2 diabetes"
        assert d["diagrams"] is False

    def test_empty_factory(self):
        e = ExtractedEntities.empty("spoken")
        assert e.source == "spoken"
        assert e.allergies == []
        assert e.medications == []
        assert e.diagnosis is None

    def test_default_diagrams_false(self):
        e = ExtractedEntities(source="chart")
        assert e.diagrams is False


# ---------------------------------------------------------------------------
# DiscrepancyFlag
# ---------------------------------------------------------------------------

class TestDiscrepancyFlag:
    def test_defaults(self):
        flag = DiscrepancyFlag(
            severity="HIGH",
            category="allergy missing",
            chart_value="penicillin",
            spoken_value="amoxicillin",
            message="Cross-reactive allergy detected.",
        )
        assert flag.dismissed is False
        assert flag.added_to_notes is False

    def test_fields_stored(self):
        flag = DiscrepancyFlag(
            severity="MEDIUM",
            category="diagnosis missing",
            chart_value="diabetes",
            spoken_value="hypertension",
            message="Diagnosis mismatch.",
        )
        assert flag.severity == "MEDIUM"
        assert flag.chart_value == "diabetes"


# ---------------------------------------------------------------------------
# CrossReferenceResult
# ---------------------------------------------------------------------------

class TestCrossReferenceResult:
    def _high_flag(self) -> DiscrepancyFlag:
        return DiscrepancyFlag(
            severity="HIGH",
            category="allergy",
            chart_value="penicillin",
            spoken_value="amoxicillin",
            message="allergy conflict",
        )

    def _medium_flag(self) -> DiscrepancyFlag:
        return DiscrepancyFlag(
            severity="MEDIUM",
            category="interaction",
            chart_value="warfarin",
            spoken_value="aspirin",
            message="interaction risk",
        )

    def test_critical_flags_filters_high_only(self):
        result = CrossReferenceResult(flags=[self._high_flag(), self._medium_flag()])
        assert len(result.critical_flags) == 1
        assert result.critical_flags[0].severity == "HIGH"

    def test_has_critical_flags_true(self):
        result = CrossReferenceResult(flags=[self._high_flag()])
        assert result.has_critical_flags is True

    def test_has_critical_flags_false(self):
        result = CrossReferenceResult(flags=[self._medium_flag()])
        assert result.has_critical_flags is False

    def test_empty_flags_by_default(self):
        result = CrossReferenceResult()
        assert result.flags == []
        assert result.has_critical_flags is False
