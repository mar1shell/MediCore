"""Integration tests for POST /upload-chart."""
import io
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from backend.ocr.models import ExtractedEntities, OCRResult, ChartPage
from backend.ocr.chart_processor import OCRProcessingError
from backend.ocr.entity_extractor import EntityExtractionError


def _make_ocr_result(text: str = "Patient: John\nAllergies: Penicillin") -> OCRResult:
    page = ChartPage(page_number=0, text=text)
    return OCRResult(
        filename="chart.pdf",
        full_text=text,
        pages=[page],
        model_used="mistral-ocr-latest",
        pages_processed=1,
    )


def _make_entities() -> ExtractedEntities:
    return ExtractedEntities(
        source="chart",
        allergies=["penicillin"],
        medications=[{"name": "metformin", "dose": "500mg"}],
        diagnosis="type 2 diabetes",
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _upload(client, *, content_type: str = "application/pdf", filename: str = "chart.pdf", data: bytes = b"%PDF stub"):
    return client.post(
        "/upload-chart",
        files={"file": (filename, io.BytesIO(data), content_type)},
    )


# ---------------------------------------------------------------------------
# Unsupported file type — no external calls needed
# ---------------------------------------------------------------------------

def test_upload_unsupported_content_type_returns_415(client):
    resp = _upload(client, content_type="text/plain", filename="notes.txt")
    assert resp.status_code == 415


def test_upload_unsupported_content_type_body(client):
    resp = _upload(client, content_type="text/csv", filename="data.csv")
    assert "unsupported" in resp.json()["detail"].lower()


# ---------------------------------------------------------------------------
# Successful upload — mock OCR + entity extraction
# ---------------------------------------------------------------------------

@patch("backend.api.routes.chart.EntityExtractor")
@patch("backend.api.routes.chart.ChartProcessor")
def test_upload_pdf_success(mock_processor_cls, mock_extractor_cls, client, fake_pdf_bytes):
    ocr_result = _make_ocr_result()
    entities = _make_entities()

    # ChartProcessor used as async context manager
    mock_processor = AsyncMock()
    mock_processor.process = AsyncMock(return_value=ocr_result)
    mock_processor_cls.return_value.__aenter__ = AsyncMock(return_value=mock_processor)
    mock_processor_cls.return_value.__aexit__ = AsyncMock(return_value=False)

    # EntityExtractor used as async context manager
    mock_extractor = AsyncMock()
    mock_extractor.extract = AsyncMock(return_value=entities)
    mock_extractor_cls.return_value.__aenter__ = AsyncMock(return_value=mock_extractor)
    mock_extractor_cls.return_value.__aexit__ = AsyncMock(return_value=False)

    resp = _upload(client, content_type="application/pdf", data=fake_pdf_bytes)
    assert resp.status_code == 200


@patch("backend.api.routes.chart.EntityExtractor")
@patch("backend.api.routes.chart.ChartProcessor")
def test_upload_returns_session_id(mock_processor_cls, mock_extractor_cls, client, fake_pdf_bytes):
    ocr_result = _make_ocr_result()
    entities = _make_entities()

    mock_processor = AsyncMock()
    mock_processor.process = AsyncMock(return_value=ocr_result)
    mock_processor_cls.return_value.__aenter__ = AsyncMock(return_value=mock_processor)
    mock_processor_cls.return_value.__aexit__ = AsyncMock(return_value=False)

    mock_extractor = AsyncMock()
    mock_extractor.extract = AsyncMock(return_value=entities)
    mock_extractor_cls.return_value.__aenter__ = AsyncMock(return_value=mock_extractor)
    mock_extractor_cls.return_value.__aexit__ = AsyncMock(return_value=False)

    data = _upload(client, content_type="application/pdf", data=fake_pdf_bytes).json()
    assert "session_id" in data
    assert len(data["session_id"]) == 36  # UUID


@patch("backend.api.routes.chart.EntityExtractor")
@patch("backend.api.routes.chart.ChartProcessor")
def test_upload_response_shape(mock_processor_cls, mock_extractor_cls, client, fake_pdf_bytes):
    ocr_result = _make_ocr_result("Some chart text")
    entities = _make_entities()

    mock_processor = AsyncMock()
    mock_processor.process = AsyncMock(return_value=ocr_result)
    mock_processor_cls.return_value.__aenter__ = AsyncMock(return_value=mock_processor)
    mock_processor_cls.return_value.__aexit__ = AsyncMock(return_value=False)

    mock_extractor = AsyncMock()
    mock_extractor.extract = AsyncMock(return_value=entities)
    mock_extractor_cls.return_value.__aenter__ = AsyncMock(return_value=mock_extractor)
    mock_extractor_cls.return_value.__aexit__ = AsyncMock(return_value=False)

    data = _upload(client, content_type="application/pdf", data=fake_pdf_bytes).json()

    assert data["filename"] == "chart.pdf"
    assert data["pages_processed"] == 1
    assert data["ocr_text"] == "Some chart text"
    assert data["entities"]["source"] == "chart"
    assert data["entities"]["allergies"] == ["penicillin"]
    assert data["entities"]["medications"][0]["name"] == "metformin"
    assert data["entities"]["diagnosis"] == "type 2 diabetes"


@patch("backend.api.routes.chart.EntityExtractor")
@patch("backend.api.routes.chart.ChartProcessor")
def test_upload_png_accepted(mock_processor_cls, mock_extractor_cls, client, fake_png_bytes):
    ocr_result = _make_ocr_result()
    entities = _make_entities()

    mock_processor = AsyncMock()
    mock_processor.process = AsyncMock(return_value=ocr_result)
    mock_processor_cls.return_value.__aenter__ = AsyncMock(return_value=mock_processor)
    mock_processor_cls.return_value.__aexit__ = AsyncMock(return_value=False)

    mock_extractor = AsyncMock()
    mock_extractor.extract = AsyncMock(return_value=entities)
    mock_extractor_cls.return_value.__aenter__ = AsyncMock(return_value=mock_extractor)
    mock_extractor_cls.return_value.__aexit__ = AsyncMock(return_value=False)

    resp = _upload(client, content_type="image/png", filename="chart.png", data=fake_png_bytes)
    assert resp.status_code == 200


# ---------------------------------------------------------------------------
# OCR failure → 422
# ---------------------------------------------------------------------------

@patch("backend.api.routes.chart.ChartProcessor")
def test_upload_ocr_failure_returns_422(mock_processor_cls, client, fake_pdf_bytes):
    mock_processor = AsyncMock()
    mock_processor.process = AsyncMock(side_effect=OCRProcessingError("Mistral OCR returned 500"))
    mock_processor_cls.return_value.__aenter__ = AsyncMock(return_value=mock_processor)
    mock_processor_cls.return_value.__aexit__ = AsyncMock(return_value=False)

    resp = _upload(client, content_type="application/pdf", data=fake_pdf_bytes)
    assert resp.status_code == 422
    assert "detail" in resp.json()


# ---------------------------------------------------------------------------
# Entity extraction failure → 422
# ---------------------------------------------------------------------------

@patch("backend.api.routes.chart.EntityExtractor")
@patch("backend.api.routes.chart.ChartProcessor")
def test_upload_extraction_failure_returns_422(mock_processor_cls, mock_extractor_cls, client, fake_pdf_bytes):
    mock_processor = AsyncMock()
    mock_processor.process = AsyncMock(return_value=_make_ocr_result())
    mock_processor_cls.return_value.__aenter__ = AsyncMock(return_value=mock_processor)
    mock_processor_cls.return_value.__aexit__ = AsyncMock(return_value=False)

    mock_extractor = AsyncMock()
    mock_extractor.extract = AsyncMock(side_effect=EntityExtractionError("LLM returned invalid JSON"))
    mock_extractor_cls.return_value.__aenter__ = AsyncMock(return_value=mock_extractor)
    mock_extractor_cls.return_value.__aexit__ = AsyncMock(return_value=False)

    resp = _upload(client, content_type="application/pdf", data=fake_pdf_bytes)
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Session is persisted after successful upload
# ---------------------------------------------------------------------------

@patch("backend.api.routes.chart.EntityExtractor")
@patch("backend.api.routes.chart.ChartProcessor")
def test_upload_session_persisted(mock_processor_cls, mock_extractor_cls, client, fake_pdf_bytes):
    from backend import session as store

    ocr_result = _make_ocr_result()
    entities = _make_entities()

    mock_processor = AsyncMock()
    mock_processor.process = AsyncMock(return_value=ocr_result)
    mock_processor_cls.return_value.__aenter__ = AsyncMock(return_value=mock_processor)
    mock_processor_cls.return_value.__aexit__ = AsyncMock(return_value=False)

    mock_extractor = AsyncMock()
    mock_extractor.extract = AsyncMock(return_value=entities)
    mock_extractor_cls.return_value.__aenter__ = AsyncMock(return_value=mock_extractor)
    mock_extractor_cls.return_value.__aexit__ = AsyncMock(return_value=False)

    data = _upload(client, content_type="application/pdf", data=fake_pdf_bytes).json()
    sid = data["session_id"]

    assert store.get_session(sid) is not None
    store.delete_session(sid)  # cleanup
