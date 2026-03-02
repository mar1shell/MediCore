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
    """Append a safety check result to the session. Returns False if session not found.

    Deduplicates by drug_name (case-insensitive): if a check for the same drug
    already exists the previous result is replaced, so re-triggering the same
    drug (e.g. when the agent re-mentions it while giving advice) never creates
    a duplicate alert on the frontend.
    """
    record = _store.get(session_id)
    if record is None:
        return False
    drug_key = result.get("drug_name", "").lower().strip()
    for i, existing in enumerate(record.safety_checks):
        if existing.get("drug_name", "").lower().strip() == drug_key:
            record.safety_checks[i] = result
            return True
    record.safety_checks.append(result)
    return True


def was_recommended(session_id: str, drug_name: str) -> bool:
    """Return True if drug_name was previously recommended by the safety checker in this session.

    When our own LLM suggests a drug as a safe alternative, we must not re-check
    it if ElevenLabs re-triggers check_safety for that name (which happens when
    the agent reads its own recommendation aloud and the STT picks it up).
    """
    record = _store.get(session_id)
    if record is None:
        return False
    key = drug_name.lower().strip()
    for check in record.safety_checks:
        rec = (check.get("recommendation") or "").lower()
        if key and key in rec:
            return True
    return False


def delete_session(session_id: str) -> bool:
    """Remove a session by ID. Returns True if it existed, False otherwise."""
    if session_id in _store:
        del _store[session_id]
        return True
    return False


def list_sessions() -> list[str]:
    """Return all active session IDs."""
    return list(_store.keys())
