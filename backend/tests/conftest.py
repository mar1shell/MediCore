"""
Shared pytest fixtures for the MediCore test suite.

All external I/O (Mistral OCR, Mistral LLM, ElevenLabs) is mocked so the tests
run without any real API keys or network access.
"""
import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# Set env vars before any app code is imported so OCRConfig.from_env() succeeds
os.environ.setdefault("MISTRAL_API_KEY", "test-mistral-key")
os.environ.setdefault("ELEVENLABS_API_KEY", "test-elevenlabs-key")
os.environ.setdefault("ELEVENLABS_AGENT_ID", "test-agent-id")

from fastapi.testclient import TestClient

from backend.main import app
from backend.ocr.models import ExtractedEntities, OCRResult, ChartPage
from backend import session as session_store


# ---------------------------------------------------------------------------
# HTTP test client
# ---------------------------------------------------------------------------

@pytest.fixture
def client() -> TestClient:
    """Starlette synchronous test client — wraps async FastAPI app correctly."""
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c


# ---------------------------------------------------------------------------
# Domain object fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_entities() -> ExtractedEntities:
    return ExtractedEntities(
        source="chart",
        allergies=["penicillin"],
        medications=[{"name": "metformin", "dose": "500mg twice daily"}],
        diagnosis="type 2 diabetes mellitus",
        extraction_notes=None,
        diagrams=False,
    )


@pytest.fixture
def clean_entities() -> ExtractedEntities:
    """Entities with no allergies or medications."""
    return ExtractedEntities(
        source="chart",
        allergies=[],
        medications=[],
        diagnosis=None,
        extraction_notes=None,
        diagrams=False,
    )


@pytest.fixture
def sample_ocr_result() -> OCRResult:
    page = ChartPage(
        page_number=0,
        text="Patient: John Smith\nAllergies: Penicillin\nMedications: Metformin 500mg",
        width=595.0,
        height=842.0,
    )
    return OCRResult(
        filename="patient_chart.pdf",
        full_text=page.text,
        pages=[page],
        model_used="mistral-ocr-latest",
        pages_processed=1,
    )


# ---------------------------------------------------------------------------
# Pre-populated session fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def active_session(sample_entities) -> str:
    """Create a live session in the store and clean it up afterwards."""
    sid = session_store.create_session(sample_entities)
    yield sid
    session_store.delete_session(sid)


# ---------------------------------------------------------------------------
# Helpers: build a minimal valid in-memory PDF bytes (1 byte stub)
# ---------------------------------------------------------------------------

@pytest.fixture
def fake_pdf_bytes() -> bytes:
    """Minimal bytes that pass content-type checks (real OCR is mocked)."""
    return b"%PDF-1.4 stub"


@pytest.fixture
def fake_png_bytes() -> bytes:
    # 1×1 red PNG
    return (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00"
        b"\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
    )
