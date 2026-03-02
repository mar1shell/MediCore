import uuid
from dataclasses import dataclass, field
from backend.ocr.models import ExtractedEntities


@dataclass
class SessionRecord:
    entities: ExtractedEntities
    safety_checks: list[dict] = field(default_factory=list)


_store: dict[str, SessionRecord] = {}


def create_session(entities: ExtractedEntities) -> str:
    sid = str(uuid.uuid4())
    _store[sid] = SessionRecord(entities=entities)
    return sid


def get_session(session_id: str) -> ExtractedEntities | None:
    record = _store.get(session_id)
    return record.entities if record else None


def get_session_record(session_id: str) -> SessionRecord | None:
    return _store.get(session_id)


def add_safety_check(session_id: str, result: dict) -> bool:
    """Append a safety check result to the session. Returns False if session not found."""
    record = _store.get(session_id)
    if record is None:
        return False
    record.safety_checks.append(result)
    return True


def delete_session(session_id: str) -> bool:
    """Remove a session by ID. Returns True if it existed, False otherwise."""
    if session_id in _store:
        del _store[session_id]
        return True
    return False


def list_sessions() -> list[str]:
    """Return all active session IDs."""
    return list(_store.keys())
