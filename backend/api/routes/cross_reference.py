from fastapi import APIRouter
from pydantic import BaseModel

from backend.cross_reference.comparator import compare_entities

router = APIRouter()


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class CrossReferenceRequest(BaseModel):
    chart_entities: dict
    spoken_entities: dict


class CrossReferenceResponse(BaseModel):
    flags: list[dict]
    match_score: float


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@router.post("/cross-reference", response_model=CrossReferenceResponse)
async def cross_reference_route(body: CrossReferenceRequest):
    """Compare chart-extracted entities against voice-captured entities and return discrepancy flags."""
    result = compare_entities(body.chart_entities, body.spoken_entities)
    return CrossReferenceResponse(**result)
