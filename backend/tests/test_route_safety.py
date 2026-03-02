"""Integration tests for POST /check-safety."""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from backend import session as store
from backend.ocr.models import ExtractedEntities


def _make_entities(allergies: list[str] | None = None) -> ExtractedEntities:
    return ExtractedEntities(
        source="chart",
        allergies=allergies or ["penicillin"],
        medications=[{"name": "metformin", "dose": "500mg"}],
        diagnosis="type 2 diabetes",
    )


def _mistral_response(is_safe: bool, issue: str | None = None, recommendation: str | None = None) -> MagicMock:
    """Build a fake httpx response that looks like a Mistral chat completions reply."""
    content = json.dumps({"is_safe": is_safe, "issue": issue, "recommendation": recommendation})
    payload = {"choices": [{"message": {"content": content}}]}
    mock_resp = MagicMock()
    mock_resp.json.return_value = payload
    mock_resp.raise_for_status = MagicMock()
    return mock_resp


# ---------------------------------------------------------------------------
# Session not found
# ---------------------------------------------------------------------------

def test_safety_check_missing_session_returns_404(client):
    resp = client.post(
        "/check-safety",
        json={"drug_name": "amoxicillin", "session_id": "00000000-0000-0000-0000-000000000000"},
    )
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()


# ---------------------------------------------------------------------------
# Successful safe verdict
# ---------------------------------------------------------------------------

@patch("backend.api.routes.safety.httpx.AsyncClient")
def test_safety_check_safe_response(mock_client_cls, client):
    sid = store.create_session(_make_entities(allergies=[]))

    mock_http = AsyncMock()
    mock_http.post = AsyncMock(return_value=_mistral_response(is_safe=True))
    mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_http)
    mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

    resp = client.post("/check-safety", json={"drug_name": "aspirin", "session_id": sid})
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_safe"] is True
    assert data["issue"] is None

    store.delete_session(sid)


# ---------------------------------------------------------------------------
# Successful unsafe verdict
# ---------------------------------------------------------------------------

@patch("backend.api.routes.safety.httpx.AsyncClient")
def test_safety_check_unsafe_response(mock_client_cls, client):
    sid = store.create_session(_make_entities(allergies=["penicillin"]))

    mock_http = AsyncMock()
    mock_http.post = AsyncMock(return_value=_mistral_response(
        is_safe=False,
        issue="Amoxicillin is a penicillin-class antibiotic. Patient has penicillin allergy.",
        recommendation="Use azithromycin instead.",
    ))
    mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_http)
    mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

    resp = client.post("/check-safety", json={"drug_name": "amoxicillin", "session_id": sid})
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_safe"] is False
    assert data["issue"] is not None
    assert data["recommendation"] is not None

    store.delete_session(sid)


# ---------------------------------------------------------------------------
# Response shape
# ---------------------------------------------------------------------------

@patch("backend.api.routes.safety.httpx.AsyncClient")
def test_safety_check_response_keys(mock_client_cls, client):
    sid = store.create_session(_make_entities())

    mock_http = AsyncMock()
    mock_http.post = AsyncMock(return_value=_mistral_response(is_safe=True))
    mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_http)
    mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

    data = client.post("/check-safety", json={"drug_name": "paracetamol", "session_id": sid}).json()
    assert set(data.keys()) == {"is_safe", "issue", "recommendation"}

    store.delete_session(sid)


# ---------------------------------------------------------------------------
# Mistral API returns HTTP error → 502
# ---------------------------------------------------------------------------

@patch("backend.api.routes.safety.httpx.AsyncClient")
def test_safety_check_mistral_http_error_returns_502(mock_client_cls, client):
    import httpx

    sid = store.create_session(_make_entities())

    mock_resp = MagicMock()
    mock_resp.status_code = 500
    mock_resp.text = "Internal Server Error"

    http_error = httpx.HTTPStatusError("500", request=MagicMock(), response=mock_resp)
    mock_http = AsyncMock()
    mock_http.post = AsyncMock(return_value=mock_resp)
    mock_resp.raise_for_status = MagicMock(side_effect=http_error)
    mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_http)
    mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

    resp = client.post("/check-safety", json={"drug_name": "amoxicillin", "session_id": sid})
    assert resp.status_code == 502

    store.delete_session(sid)


# ---------------------------------------------------------------------------
# Mistral unreachable → 502
# ---------------------------------------------------------------------------

@patch("backend.api.routes.safety.httpx.AsyncClient")
def test_safety_check_mistral_network_error_returns_502(mock_client_cls, client):
    import httpx

    sid = store.create_session(_make_entities())

    mock_http = AsyncMock()
    mock_http.post = AsyncMock(side_effect=httpx.ConnectError("Connection refused"))
    mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_http)
    mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

    resp = client.post("/check-safety", json={"drug_name": "amoxicillin", "session_id": sid})
    assert resp.status_code == 502

    store.delete_session(sid)


# ---------------------------------------------------------------------------
# Request validation — missing required fields
# ---------------------------------------------------------------------------

def test_safety_check_missing_drug_name_returns_422(client):
    resp = client.post("/check-safety", json={"session_id": "abc"})
    assert resp.status_code == 422


def test_safety_check_missing_session_id_returns_422(client):
    resp = client.post("/check-safety", json={"drug_name": "aspirin"})
    assert resp.status_code == 422
