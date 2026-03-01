from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from backend.ocr.chart_processor import ChartProcessor
from backend.ocr.entity_extractor import EntityExtractor
from backend.ocr.config import OCRConfig

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
    """Accept a PDF chart, extract OCR text, then extract structured entities."""
    if file.content_type not in ("application/pdf",):
        raise HTTPException(status_code=415, detail="Only PDF files are supported.")

    contents = await file.read()
    
    # Stage 1: OCR extraction
    config = OCRConfig.from_env()
    async with ChartProcessor(config) as processor:
        ocr_result = await processor.process_pdf(contents, filename=file.filename)
    
    # Stage 2: Entity extraction
    async with EntityExtractor(config) as extractor:
        entities = await extractor.extract(ocr_result.full_text)
    
    return {
        "filename": file.filename,
        "ocr_text": ocr_result.full_text,
        "pages_processed": ocr_result.pages_processed,
        "entities": entities.to_dict()
    }


@router.post("/extract-entities", response_model=ExtractEntitiesResponse)
async def extract_entities_route(body: ExtractEntitiesRequest):
    """Run LLM entity extraction on provided chart text."""
    config = OCRConfig.from_env()
    async with EntityExtractor(config) as extractor:
        entities = await extractor.extract(body.text)
    return ExtractEntitiesResponse(entities=entities.to_dict())
