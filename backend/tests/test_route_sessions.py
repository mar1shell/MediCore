"""Integration tests for GET /sessions/{id} and DELETE /sessions/{id}."""
import pytest

from backend import session as store
from backend.ocr.models import ExtractedEntities


def _make_entities() -> ExtractedEntities:
    return ExtractedEntities(
        source="chart",
        allergies=["penicillin"],
        medications=[{"name": "metformin", "dose": "500mg"}],
        diagnosis="type 2 diabetes",
    )


# ---------------------------------------------------------------------------
# GET /sessions/{session_id}
# ---------------------------------------------------------------------------

class TestGetSession:
    def test_existing_session_returns_200(self, client):
        sid = store.create_session(_make_entities())
        resp = client.get(f"/sessions/{sid}")
        assert resp.status_code == 200
        store.delete_session(sid)

    def test_existing_session_body_shape(self, client):
        sid = store.create_session(_make_entities())
        data = client.get(f"/sessions/{sid}").json()
        assert data["session_id"] == sid
        assert "entities" in data
        assert data["entities"]["source"] == "chart"
        assert data["entities"]["allergies"] == ["penicillin"]
        assert data["entities"]["medications"][0]["name"] == "metformin"
        assert data["entities"]["diagnosis"] == "type 2 diabetes"
        store.delete_session(sid)

    def test_missing_session_returns_404(self, client):
        resp = client.get("/sessions/00000000-0000-0000-0000-000000000000")
        assert resp.status_code == 404

    def test_missing_session_error_body(self, client):
        resp = client.get("/sessions/nonexistent-id")
        assert "detail" in resp.json()

    def test_session_with_empty_allergies(self, client):
        e = ExtractedEntities(source="chart", allergies=[], medications=[], diagnosis=None)
        sid = store.create_session(e)
        data = client.get(f"/sessions/{sid}").json()
        assert data["entities"]["allergies"] == []
        store.delete_session(sid)

    def test_session_with_multiple_medications(self, client):
        e = ExtractedEntities(
            source="chart",
            allergies=[],
            medications=[
                {"name": "metformin", "dose": "500mg"},
                {"name": "lisinopril", "dose": "10mg"},
            ],
            diagnosis="hypertension",
        )
        sid = store.create_session(e)
        data = client.get(f"/sessions/{sid}").json()
        assert len(data["entities"]["medications"]) == 2
        store.delete_session(sid)


# ---------------------------------------------------------------------------
# DELETE /sessions/{session_id}
# ---------------------------------------------------------------------------

class TestDeleteSession:
    def test_existing_session_returns_204(self, client):
        sid = store.create_session(_make_entities())
        resp = client.delete(f"/sessions/{sid}")
        assert resp.status_code == 204

    def test_delete_removes_session(self, client):
        sid = store.create_session(_make_entities())
        client.delete(f"/sessions/{sid}")
        assert store.get_session(sid) is None

    def test_delete_no_content_body(self, client):
        sid = store.create_session(_make_entities())
        resp = client.delete(f"/sessions/{sid}")
        assert resp.content == b""

    def test_missing_session_returns_404(self, client):
        resp = client.delete("/sessions/00000000-0000-0000-0000-000000000000")
        assert resp.status_code == 404

    def test_double_delete_returns_404(self, client):
        sid = store.create_session(_make_entities())
        client.delete(f"/sessions/{sid}")
        resp = client.delete(f"/sessions/{sid}")
        assert resp.status_code == 404

    def test_after_delete_get_returns_404(self, client):
        sid = store.create_session(_make_entities())
        client.delete(f"/sessions/{sid}")
        resp = client.get(f"/sessions/{sid}")
        assert resp.status_code == 404
