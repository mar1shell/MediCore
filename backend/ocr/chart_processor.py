import base64
import logging
from typing import Optional
import httpx
from backend.ocr.config import OCRConfig
from backend.ocr.models import OCRResult, ChartPage

logger = logging.getLogger(__name__)

# Supported MIME types and their data-URI prefixes
_PDF_TYPES = {"application/pdf"}
_IMAGE_TYPES = {"image/jpeg", "image/jpg", "image/png", "image/gif", "image/webp"}
SUPPORTED_MIME_TYPES = _PDF_TYPES | _IMAGE_TYPES

# Map file extensions to MIME types (fallback when content_type is unknown)
_EXT_TO_MIME = {
    ".pdf": "application/pdf",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".webp": "image/webp",
}


def _detect_mime(filename: str, content_type: Optional[str] = None) -> str:
    """Resolve MIME type from explicit content_type or filename extension."""
    if content_type and content_type in SUPPORTED_MIME_TYPES:
        return content_type
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    mime = _EXT_TO_MIME.get(f".{ext}")
    if mime:
        return mime
    raise OCRProcessingError(
        f"Unsupported file type for '{filename}' (content_type={content_type}). "
        f"Supported: PDF, JPEG, PNG, GIF, WEBP."
    )


class ChartProcessor:
    OCR_MODEL = "mistral-ocr-latest"  # mistral ocr 3
    API_ENDPOINT = "https://api.mistral.ai/v1/ocr"
    
    def __init__(self, config: OCRConfig):
        self.config = config
        self.client = httpx.AsyncClient(
                timeout=httpx.Timeout(
                    connect=30.0,
                    write=120.0,
                    read=self.config.request_timeout,
                    pool=30.0,
                ),
                headers={"Authorization": f"Bearer {self.config.api_key}"}
        )
    
    async def process(
        self,
        file_bytes: bytes,
        filename: str = "chart.pdf",
        content_type: Optional[str] = None,
    ) -> OCRResult:
        """Process a PDF or image file through Mistral OCR."""
        mime = _detect_mime(filename, content_type)
        logger.info("Starting OCR for '%s' (%d bytes, %s)", filename, len(file_bytes), mime)
        b64 = base64.standard_b64encode(file_bytes).decode("utf-8")
        payload = self._build_payload(b64, filename, mime)
        raw_response = await self._call_ocr_api(payload)
        result = self._parse_response(raw_response, filename)
        logger.info(
            "OCR completed for '%s': %d pages, %d chars",
            filename,
            len(result.pages) if result.pages else 0,
            len(result.full_text) if result.full_text else 0,
        )
        return result

    # Keep backward-compat alias
    async def process_pdf(self, pdf_bytes: bytes, filename: str = "chart.pdf") -> OCRResult:
        return await self.process(pdf_bytes, filename, content_type="application/pdf")

    def _build_payload(self, b64: str, filename: str, mime: str) -> dict:
        is_image = mime in _IMAGE_TYPES
        data_uri = f"data:{mime};base64,{b64}"

        if is_image:
            document = {
                "type": "image_url",
                "image_url": data_uri,
            }
        else:
            document = {
                "type": "document_url",
                "document_url": data_uri,
                "document_name": filename,
            }

        return {
            "model": self.OCR_MODEL,
            "document": document,
            "include_image_base64": False,
        }
    
    async def _call_ocr_api(self, payload: dict) -> dict:
        try:
            response = await self.client.post(self.API_ENDPOINT, json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise OCRProcessingError(
                f"Mistral OCR API returned {e.response.status_code}: {e.response.text}"
            ) from e
        except httpx.TimeoutException as e:
            raise OCRProcessingError(
                f"Mistral OCR API timeout after {self.config.request_timeout}s: {e}"
            ) from e
        except httpx.RequestError as e:
            raise OCRProcessingError(f"Network error calling Mistral OCR API: {e}") from e
    
    def _parse_response(self, response: dict, filename: str) -> OCRResult:
        pages_raw = response.get("pages", [])
        if not pages_raw:
            raise OCRProcessingError(
                f"Mistral OCR returned no pages for '{filename}'."
                "PDF may be empty, encrypted, or contain unsupported content."
            )
        pages = []
        full_text_parts = []
        for page_data in pages_raw:
            page_text = page_data.get("markdown","").strip()
            page = ChartPage(
                page_number=page_data.get("index", len(pages)),
                text=page_text,
                width=page_data.get("dimensions", {}).get("width"),
                height=page_data.get("dimensions", {}).get("height")
            )
            pages.append(page)
            full_text_parts.append(page_text)
        full_text = "\n\n".join(full_text_parts)
        return OCRResult(filename=filename, full_text=full_text,
                         pages=pages, model_used=response.get("model", self.OCR_MODEL),
                         pages_processed=response.get("usage_info", {}).get("pages_processed", len(pages)))
    
    async def close(self):
        await self.client.aclose()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, *args):
        await self.close()
    
class OCRProcessingError(Exception):
    pass

    