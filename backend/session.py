import uuid
from backend.ocr.models import ExtractedEntities

_store: dict[str, ExtractedEntities] = {}


def create_session(entities: ExtractedEntities) -> str:
    sid = str(uuid.uuid4())
    _store[sid] = entities
    return sid


def get_session(session_id: str) -> ExtractedEntities | None:
    return _store.get(session_id)
