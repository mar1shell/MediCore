from fastapi import APIRouter

from api.models import CrossReferenceRequest, CrossReferenceResponse

router = APIRouter()


@router.post("/cross-reference", response_model=CrossReferenceResponse)
async def cross_reference(body: CrossReferenceRequest):
    """Compare chart entities vs spoken entities and return discrepancy flags."""
    # TODO: call cross_reference.engine.cross_reference
    raise NotImplementedError
