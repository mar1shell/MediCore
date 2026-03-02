from fastapi import APIRouter, File, HTTPException, UploadFile

from backend.ocr.chart_processor import ChartProcessor, SUPPORTED_MIME_TYPES
from backend.ocr.entity_extractor import EntityExtractor
from backend.ocr.config import OCRConfig
from backend.session import create_session

router = APIRouter()


@router.post("/upload-chart")
async def upload_chart(file: UploadFile = File(...)):
    """Accept a PDF or image chart, extract OCR text, extract structured entities, and create a session."""
    if file.content_type not in SUPPORTED_MIME_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type '{file.content_type}'. Accepted: PDF, JPEG, PNG, GIF, WEBP.",
        )

    contents = await file.read()

    # Stage 1: OCR extraction
    config = OCRConfig.from_env()
    async with ChartProcessor(config) as processor:
        ocr_result = await processor.process(
            contents, filename=file.filename, content_type=file.content_type
        )

    # Stage 2: Entity extraction
    async with EntityExtractor(config) as extractor:
        entities = await extractor.extract(ocr_result.full_text)

    # Stage 3: Create session for ElevenLabs webhook use
    session_id = create_session(entities)

    return {
        "session_id": session_id,
        "filename": file.filename,
        "ocr_text": ocr_result.full_text,
        "pages_processed": ocr_result.pages_processed,
        "entities": entities.to_dict(),
    }
