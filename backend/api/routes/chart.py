from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from llm.entity_extractor import extract_entities
from ocr.extractor import extract_text_from_pdf

router = APIRouter()


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class ExtractEntitiesRequest(BaseModel):
    text: str


class ExtractEntitiesResponse(BaseModel):
    entities: dict


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@router.post("/upload-chart")
async def upload_chart(file: UploadFile = File(...)):
    """Accept a PDF chart and return the extracted plain text."""
    if file.content_type not in ("application/pdf",):
        raise HTTPException(status_code=415, detail="Only PDF files are supported.")

    contents = await file.read()
    text = extract_text_from_pdf(contents)
    return {"filename": file.filename, "text": text}


@router.post("/extract-entities", response_model=ExtractEntitiesResponse)
async def extract_entities_route(body: ExtractEntitiesRequest):
    """Run LLM entity extraction on the provided chart text."""
    entities = await extract_entities(body.text)
    return ExtractEntitiesResponse(entities=entities)
