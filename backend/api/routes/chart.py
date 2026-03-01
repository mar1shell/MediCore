from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from llm.entity_extractor import extract_entities
from ocr.extractor import extract_structured_data_from_bytes

router = APIRouter()


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class ExtractEntitiesRequest(BaseModel):
    text: str


class ExtractEntitiesResponse(BaseModel):
    entities: dict


class UploadChartResponse(BaseModel):
    filename: str
    patient: dict
    diagnoses: list
    allergies: list
    medications: list
    symptoms: list
    doctor_notes: str | None


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@router.post("/upload-chart", response_model=UploadChartResponse)
async def upload_chart(file: UploadFile = File(...)):
    """Accept a PDF chart and return structured medical data extraction."""
    if file.content_type not in ("application/pdf",):
        raise HTTPException(status_code=415, detail="Only PDF files are supported.")

    try:
        contents = await file.read()
        structured_data = extract_structured_data_from_bytes(contents)
        return {
            "filename": file.filename,
            **structured_data,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"OCR extraction failed: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.post("/extract-entities", response_model=ExtractEntitiesResponse)
async def extract_entities_route(body: ExtractEntitiesRequest):
    """Run LLM entity extraction on the provided chart text."""
    entities = await extract_entities(body.text)
    return ExtractEntitiesResponse(entities=entities)
