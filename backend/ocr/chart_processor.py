import base64
import logging
from typing import Optional
import httpx
from backend.ocr.config import OCRConfig
from backend.ocr.models import OCRResult, ChartPage

logger = logging.getLogger(__name__)

class ChartProcessor:
    OCR_MODEL = "mistral-ocr-latest" # mistral ocr 3
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
    
    async def process_pdf(self, pdf_bytes: bytes, filename:str = "chart.pdf") -> OCRResult:
        logger.info("Starting OCR for '%s' (%d bytes)", filename, len(pdf_bytes))
        b64_pdf = base64.standard_b64encode(pdf_bytes).decode("utf-8")
        payload = self._build_payload(b64_pdf, filename)
        raw_response = await self._call_ocr_api(payload)
        result = self._parse_response(raw_response, filename)
        logger.info("OCR completed for '%s'", filename,
                    len(result.pages) if result.pages else 0,
                    len(result.full_text) if result.full_text else 0)
        return result
    
    def _build_payload(self, b64_pdf: str, filename: str) -> dict:
        return {
            "model": self.OCR_MODEL,
            "document":{
                "type":"document_url",
                "document_url" : f"data:application/pdf;base64,{b64_pdf}",
                "document_name": filename,
            },
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

    