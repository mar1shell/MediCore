from fastapi import APIRouter, File, HTTPException, UploadFile

from backend.ocr.chart_processor import ChartProcessor, SUPPORTED_MIME_TYPES, OCRProcessingError
from backend.ocr.entity_extractor import EntityExtractor, EntityExtractionError
from backend.ocr.config import OCRConfig
from backend.session import create_session
from backend.schemas.chart import UploadChartResponse, EntitiesSchema, MedicationSchema
from backend.schemas.common import ErrorResponse

router = APIRouter()


@router.post(
    "/upload-chart",
    response_model=UploadChartResponse,
    summary="Upload a patient chart",
    description=(
        "Accept a patient chart as a **PDF or image** (JPEG, PNG, GIF, WEBP). "
        "Runs two sequential AI stages:\n\n"
        "1. **OCR** — Mistral OCR 3 extracts text from every page.\n"
        "2. **Entity extraction** — Mistral Large identifies allergies, active medications, and diagnosis.\n\n"
        "Returns a `session_id` that ties the chart data to the subsequent voice session and safety checks."
    ),
    response_description="OCR text, extracted clinical entities, and a session UUID.",
    responses={
        415: {
            "model": ErrorResponse,
            "description": "Unsupported file type. Only PDF, JPEG, PNG, GIF, and WEBP are accepted.",
        },
        422: {
            "model": ErrorResponse,
            "description": "OCR or entity extraction failed (e.g. encrypted PDF, blank page, API error).",
        },
    },
    tags=["Chart"],
)
async def upload_chart(file: UploadFile = File(...)) -> UploadChartResponse:
    if file.content_type not in SUPPORTED_MIME_TYPES:
        raise HTTPException(
            status_code=415,
            detail=(
                f"Unsupported file type '{file.content_type}'. "
                "Accepted: application/pdf, image/jpeg, image/png, image/gif, image/webp."
            ),
        )

    contents = await file.read()
    config = OCRConfig.from_env()

    # Stage 1: OCR extraction
    try:
        async with ChartProcessor(config) as processor:
            ocr_result = await processor.process(
                contents, filename=file.filename or "chart", content_type=file.content_type
            )
    except OCRProcessingError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    # Stage 2: Entity extraction
    try:
        async with EntityExtractor(config) as extractor:
            entities = await extractor.extract(ocr_result.full_text)
    except EntityExtractionError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    # Stage 3: Create session
    session_id = create_session(entities)

    return UploadChartResponse(
        session_id=session_id,
        filename=file.filename or "chart",
        ocr_text=ocr_result.full_text,
        pages_processed=ocr_result.pages_processed,
        entities=EntitiesSchema(
            source=entities.source,
            allergies=entities.allergies,
            medications=[
                MedicationSchema(name=m["name"], dose=m.get("dose"))
                for m in entities.medications
            ],
            diagnosis=entities.diagnosis,
            extraction_notes=entities.extraction_notes,
            diagrams=entities.diagrams,
        ),
    )
