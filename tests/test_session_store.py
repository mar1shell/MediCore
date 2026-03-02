"""Unit tests for backend/session.py — the in-memory session store."""
import pytest

from backend import session as store
from backend.ocr.models import ExtractedEntities


@pytest.fixture(autouse=True)
def _clean_store():
    """Wipe the store before and after every test so tests are isolated."""
    for sid in store.list_sessions():
        store.delete_session(sid)
    yield
    for sid in store.list_sessions():
        store.delete_session(sid)


def _make_entities(source: str = "chart") -> ExtractedEntities:
    return ExtractedEntities(
        source=source,
        allergies=["penicillin"],
        medications=[{"name": "metformin", "dose": "500mg"}],
        diagnosis="type 2 diabetes",
    )


# ---------------------------------------------------------------------------
# create_session
# ---------------------------------------------------------------------------

def test_create_session_returns_uuid_string():
    entities = _make_entities()
    sid = store.create_session(entities)
    assert isinstance(sid, str)
    assert len(sid) == 36  # UUID4 canonical form: 8-4-4-4-12


def test_create_session_each_call_unique():
    e = _make_entities()
    s1 = store.create_session(e)
    s2 = store.create_session(e)
    assert s1 != s2


def test_create_session_stores_entities():
    entities = _make_entities()
    sid = store.create_session(entities)
    retrieved = store.get_session(sid)
    assert retrieved is entities


# ---------------------------------------------------------------------------
# get_session
# ---------------------------------------------------------------------------

def test_get_session_missing_returns_none():
    result = store.get_session("00000000-0000-0000-0000-000000000000")
    assert result is None


def test_get_session_existing():
    entities = _make_entities()
    sid = store.create_session(entities)
    assert store.get_session(sid) is entities


# ---------------------------------------------------------------------------
# delete_session
# ---------------------------------------------------------------------------

def test_delete_session_existing_returns_true():
    sid = store.create_session(_make_entities())
    assert store.delete_session(sid) is True


def test_delete_session_removes_entry():
    sid = store.create_session(_make_entities())
    store.delete_session(sid)
    assert store.get_session(sid) is None


def test_delete_session_missing_returns_false():
    assert store.delete_session("nonexistent-id") is False


def test_delete_session_idempotent():
    sid = store.create_session(_make_entities())
    store.delete_session(sid)
    assert store.delete_session(sid) is False


# ---------------------------------------------------------------------------
# list_sessions
# ---------------------------------------------------------------------------

def test_list_sessions_empty():
    assert store.list_sessions() == []


def test_list_sessions_contains_created():
    s1 = store.create_session(_make_entities())
    s2 = store.create_session(_make_entities())
    ids = store.list_sessions()
    assert s1 in ids
    assert s2 in ids


def test_list_sessions_does_not_contain_deleted():
    sid = store.create_session(_make_entities())
    store.delete_session(sid)
    assert sid not in store.list_sessions()
