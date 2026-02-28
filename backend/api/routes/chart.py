from fastapi import APIRouter, UploadFile, File

from api.models import ChartUploadResponse

router = APIRouter()


@router.post("/upload-chart", response_model=ChartUploadResponse)
async def upload_chart(file: UploadFile = File(...)):
    """Accept a PDF chart and return OCR-extracted text."""
    # TODO: call ocr.client.run_ocr
    raise NotImplementedError
