import uuid
from backend.ocr.models import ExtractedEntities

_store: dict[str, ExtractedEntities] = {}


def create_session(entities: ExtractedEntities) -> str:
    sid = str(uuid.uuid4())
    _store[sid] = entities
    return sid


def get_session(session_id: str) -> ExtractedEntities | None:
    return _store.get(session_id)


def delete_session(session_id: str) -> bool:
    """Remove a session by ID. Returns True if it existed, False otherwise."""
    if session_id in _store:
        del _store[session_id]
        return True
    return False


def list_sessions() -> list[str]:
    """Return all active session IDs."""
    return list(_store.keys())
