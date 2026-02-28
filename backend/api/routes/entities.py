from fastapi import APIRouter

from api.models import ExtractEntitiesRequest, EntityData

router = APIRouter()


@router.post("/extract-entities", response_model=EntityData)
async def extract_entities(body: ExtractEntitiesRequest):
    """Run LLM entity extraction on chart or spoken text."""
    # TODO: call llm.extraction.extract_entities
    raise NotImplementedError
