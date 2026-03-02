"""Unit tests for backend/schemas/ — Pydantic request/response models."""
import pytest
from pydantic import ValidationError

from backend.schemas.common import ErrorResponse, HealthResponse
from backend.schemas.chart import MedicationSchema, EntitiesSchema, UploadChartResponse
from backend.schemas.safety import SafetyCheckRequest, SafetyCheckResponse
from backend.schemas.session import SessionDataResponse


# ---------------------------------------------------------------------------
# ErrorResponse
# ---------------------------------------------------------------------------

class TestErrorResponse:
    def test_valid(self):
        r = ErrorResponse(detail="Something went wrong.")
        assert r.detail == "Something went wrong."

    def test_missing_detail_raises(self):
        with pytest.raises(ValidationError):
            ErrorResponse()

    def test_serialise(self):
        r = ErrorResponse(detail="oops")
        assert r.model_dump() == {"detail": "oops"}


# ---------------------------------------------------------------------------
# HealthResponse
# ---------------------------------------------------------------------------

class TestHealthResponse:
    def test_valid(self):
        r = HealthResponse(status="ok", service="MediCore API")
        assert r.status == "ok"
        assert r.service == "MediCore API"

    def test_missing_field_raises(self):
        with pytest.raises(ValidationError):
            HealthResponse(status="ok")


# ---------------------------------------------------------------------------
# MedicationSchema
# ---------------------------------------------------------------------------

class TestMedicationSchema:
    def test_with_dose(self):
        m = MedicationSchema(name="metformin", dose="500mg")
        assert m.name == "metformin"
        assert m.dose == "500mg"

    def test_dose_optional(self):
        m = MedicationSchema(name="aspirin", dose=None)
        assert m.dose is None

    def test_dose_defaults_none(self):
        m = MedicationSchema(name="aspirin")
        assert m.dose is None


# ---------------------------------------------------------------------------
# EntitiesSchema
# ---------------------------------------------------------------------------

class TestEntitiesSchema:
    def _valid(self) -> dict:
        return {
            "source": "chart",
            "allergies": ["penicillin"],
            "medications": [{"name": "metformin", "dose": "500mg"}],
            "diagnosis": "type 2 diabetes",
            "extraction_notes": None,
            "diagrams": False,
        }

    def test_valid(self):
        e = EntitiesSchema(**self._valid())
        assert e.source == "chart"
        assert e.allergies == ["penicillin"]
        assert len(e.medications) == 1
        assert e.medications[0].name == "metformin"

    def test_empty_allergies(self):
        data = self._valid()
        data["allergies"] = []
        e = EntitiesSchema(**data)
        assert e.allergies == []

    def test_missing_source_raises(self):
        data = self._valid()
        del data["source"]
        with pytest.raises(ValidationError):
            EntitiesSchema(**data)

    def test_serialise_round_trip(self):
        e = EntitiesSchema(**self._valid())
        d = e.model_dump()
        e2 = EntitiesSchema(**d)
        assert e == e2


# ---------------------------------------------------------------------------
# UploadChartResponse
# ---------------------------------------------------------------------------

class TestUploadChartResponse:
    def _valid(self) -> dict:
        return {
            "session_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
            "filename": "chart.pdf",
            "ocr_text": "Patient: John",
            "pages_processed": 1,
            "entities": {
                "source": "chart",
                "allergies": [],
                "medications": [],
                "diagnosis": None,
                "extraction_notes": None,
                "diagrams": False,
            },
        }

    def test_valid(self):
        r = UploadChartResponse(**self._valid())
        assert r.session_id == "3fa85f64-5717-4562-b3fc-2c963f66afa6"
        assert r.pages_processed == 1

    def test_entities_nested(self):
        r = UploadChartResponse(**self._valid())
        assert isinstance(r.entities, EntitiesSchema)

    def test_missing_session_id_raises(self):
        data = self._valid()
        del data["session_id"]
        with pytest.raises(ValidationError):
            UploadChartResponse(**data)


# ---------------------------------------------------------------------------
# SafetyCheckRequest
# ---------------------------------------------------------------------------

class TestSafetyCheckRequest:
    def test_valid(self):
        r = SafetyCheckRequest(
            drug_name="amoxicillin",
            session_id="3fa85f64-5717-4562-b3fc-2c963f66afa6",
        )
        assert r.drug_name == "amoxicillin"

    def test_missing_drug_name_raises(self):
        with pytest.raises(ValidationError):
            SafetyCheckRequest(session_id="abc")

    def test_missing_session_id_raises(self):
        with pytest.raises(ValidationError):
            SafetyCheckRequest(drug_name="aspirin")


# ---------------------------------------------------------------------------
# SafetyCheckResponse
# ---------------------------------------------------------------------------

class TestSafetyCheckResponse:
    def test_unsafe_response(self):
        r = SafetyCheckResponse(
            is_safe=False,
            issue="Penicillin allergy detected.",
            recommendation="Use azithromycin.",
        )
        assert r.is_safe is False
        assert r.issue == "Penicillin allergy detected."

    def test_safe_response(self):
        r = SafetyCheckResponse(is_safe=True, issue=None, recommendation=None)
        assert r.is_safe is True
        assert r.issue is None

    def test_issue_and_recommendation_optional(self):
        r = SafetyCheckResponse(is_safe=True)
        assert r.issue is None
        assert r.recommendation is None


# ---------------------------------------------------------------------------
# SessionDataResponse
# ---------------------------------------------------------------------------

class TestSessionDataResponse:
    def test_valid(self):
        r = SessionDataResponse(
            session_id="abc-123",
            entities=EntitiesSchema(
                source="chart",
                allergies=[],
                medications=[],
                diagnosis=None,
                extraction_notes=None,
                diagrams=False,
            ),
        )
        assert r.session_id == "abc-123"
        assert isinstance(r.entities, EntitiesSchema)
