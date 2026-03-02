import json
from typing import Literal
import logging

import httpx

from backend.ocr.config import OCRConfig
from backend.ocr.models import ExtractedEntities
from backend.ocr.prompt_loader import load_prompt

EXTRACTION_SYSTEM_PROMPT = load_prompt("extraction_system_prompt.txt")
EXTRACTION_USER_TEMPLATE = load_prompt("extraction_user_template.txt")
logger = logging.getLogger(__name__)
class EntityExtractor:
    LLM_MODEL = "mistral-large-latest"
    API_ENDPOINT = "https://api.mistral.ai/v1/chat/completions"
    
    def __init__(self, config: OCRConfig):
        self.config = config
        self.client = httpx.AsyncClient(timeout=config.request_timeout,
                                        headers= {
                                            "Authorization":f"Bearer {config.api_key}",
                                            "Content-Type": "application/json"
                                        })
    
    async def extract(self, text: str, source: Literal["chart", "spoken"] = "chart") -> ExtractedEntities:
        if not text or len(text.strip()) < 10:
            logger.warning("Input text is too short for extraction.")
            return ExtractedEntities(source)
        logger.info("Extracting entities from %s text (%d chars)", source, len(text))
        payload = self._build_payload(text, source)
        raw_response = await self._call_llm(payload)
        entities = self._parse_response(raw_response, source)
        logger.info(
            "Extraction done (%s): %d allergies, %d meds, diagrams=%s",
            source,
            len(entities.allergies),
            len(entities.medications),
            entities.diagrams
        )
        return entities
    
    def _build_payload(self, text:str, source:str) -> dict:
        source_label = "patient" if source == "chart" else "doctor's spoken assessment"
        return {
            "model": self.LLM_MODEL,
            "temperature": 0.0,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
                {"role": "user", "content": EXTRACTION_USER_TEMPLATE.format(source_type=source_label, text=text[:8000])}
            ]
        }
    
    async def _call_llm(self, payload: dict) -> dict:
        try:
            response = await self.client.post(self.API_ENDPOINT, json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise EntityExtractionError(
                f"Mistral LLM returned {e.response.status_code}: {e.response.text}"
            ) from e
        
        except httpx.RequestError as e:
            raise EntityExtractionError(f"Error calling Mistral LLM: {str(e)}") from e
        
    def _parse_response(self, raw: dict, source: str) -> ExtractedEntities:
        try:
            content = raw["choices"][0]["message"]["content"]
            data = json.loads(content)
        except (KeyError, json.JSONDecodeError) as e:
            raise EntityExtractionError(f"Invalid response format from LLM: {str(e)}") from e
        return ExtractedEntities(
            source=source,
            patient_name=data.get("patient_name") or None,
            allergies=[a.lower().strip() for a in data.get("allergies", [])],
            medications=[
                {
                    "name": m.get("name", "").lower().strip(),
                    "dose": m.get("dose"),
                }
                for m in data.get("medications", [])
                if m.get("name")
            ],
            diagnosis=data.get("diagnosis"),
            extraction_notes=data.get("extraction_notes"),
        )
        
    async def close(self):
        await self.client.aclose()
        
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, *args):
        await self.close()
        
class EntityExtractionError(Exception):
    pass