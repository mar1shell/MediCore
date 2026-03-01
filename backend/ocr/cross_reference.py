import json
import logging
from typing import Optional
import httpx
from backend.ocr.config import OCRConfig
from backend.ocr.models import ExtractedEntities, DiscrepancyFlag, CrossReferenceResult
from backend.ocr.prompt_loader import _load_data, _load_prompt

logger = logging.getLogger(__name__)

ABBREVIATION_MAP: dict = _load_data("abbreviation_map.json")
CROSS_REACTIVITY: dict = _load_data("cross_reactivity.json")

class CrossReferenceEngine:
    SYNONYM_MODEL = "mistral-small-latest"
    API_ENDPOINT = "https://api.mistral.ai/v1/chat/completions"
    
    def __init__(self, config: OCRConfig):
        self.config = config
        self.client = httpx.AsyncClient(
            timeout=config.request_timeout,
            headers = {
                "Authorization": f"Bearer {config.api_key}",
                "Content-Type": "application/json"
            }
        )
        
    async def comapre(self, chart: ExtractedEntities, spoken: ExtractedEntities) -> CrossReferenceResult:
        flags = []
        allergy_flags = await self._check_allergy_omissions(chart, spoken)
        flags.extend(allergy_flags)
        contraindication_flags = await self._check_contraindications(chart, spoken)
        flags.extend(contraindication_flags)
        diagnosis_flags = await self._check_diagnosis_omissions(chart, spoken)
        flags.extend(diagnosis_flags)
        logger.info(f"Cross reference completed with {len(flags)} flags ({sum(1 for f in flags if f.severity=='HIGH')} HIGH)")
        return CrossReferenceResult(flags=flags, chart_entities=chart, spoken_entities=spoken)
    
    async def _check_allergy_omissions(self, chart: ExtractedEntities, spoken: ExtractedEntities) -> list[DiscrepancyFlag]:
        flags = []
        for chart_allergy in chart.allergy_names:
            mentioned = await self._entity_mentioned(chart_allergy, spoken.allergy_names)
            if not mentioned:
                flags.append(DiscrepancyFlag(
                    severity="HIGH",
                    category="Allergy Omission",
                    chart_value=chart_allergy,
                    spoken_value=None,
                    message = (
                        f"Chart documents allergy to {chart_allergy}, but it was not mentioned in the spoken summary. This could lead to serious patient harm if the allergy is not communicated to the care team."
                        f"Please confirm before prescribing"
                    )
                ))
        return flags
    
    async def _check_contraindications(self, chart: ExtractedEntities, spoken: ExtractedEntities) -> list[DiscrepancyFlag]:
        flags = []
        for chart_allergy in chart.allergy_names:
            canonical = self._canonicalize(chart_allergy)
            contraindicated = CROSS_REACTIVITY.get(canonical, [])
            for spoken_med in spoken.medication_names:
                spoken_canonical = self._canonicalize(spoken_med)
                if spoken_canonical in contraindicated:
                    flags.append(DiscrepancyFlag(
                        severity="HIGH",
                        category="Contraindication",
                        chart_value=chart_allergy,
                        spoken_value=spoken_med,
                        message = (
                            f"Patient has allergy to {chart_allergy} which is known to have cross-reactivity with {spoken_med}. Prescribing {spoken_med} could lead to a severe allergic reaction. Please review the patient's allergies and consider alternative medications."
                        )
                    ))
        return flags
    
    async def _check_diagnosis_mismatch(self, chart:ExtractedEntities, spoken: ExtractedEntities) -> list[DiscrepancyFlag]:
        if not chart.diagnosis_names or not spoken.diagnosis_names:
            return []
        same = await self._entities_are_same(chart.diagnosis, spoken.diagnosis)
        if not same:
            return [DiscrepancyFlag(
                severity="MEDIUM",
                category="Diagnosis Mismatch",
                chart_value=", ".join(chart.diagnosis_names),
                spoken_value=", ".join(spoken.diagnosis_names),
                message = (
                    f"The diagnoses mentioned in the chart ({', '.join(chart.diagnosis_names)}) do not match those mentioned in the spoken summary ({', '.join(spoken.diagnosis_names)}). "
                    f"Please review the patient's diagnoses to ensure they are accurately communicated."
                )
            )]
        return []
    
    async def _entity_mentioned_in_list(self, entity: str, entity_list: list[str]) -> bool:
        for candidate in entity_list:
            if await self._entities_are_same(entity, candidate):
                return True
        return False
    
    async def _entities_are_same(self, a: str, b: str) -> bool:
        a,b = a.lower().strip(), b.lower().strip()
        if a == b:
            return True
        if self._abbreviation_match(a,b):
            return True
        return await self._llm_synonym_check(a,b)
    
    def _canonicalize(self, name:str) -> str:
        name_lower = name.strip().lower()
        for canonical, aliases in ABBREVIATION_MAP.items():
            if name_lower == canonical or name_lower in aliases:
                return canonical
        return name_lower
    
    def _abbreviation_match(self, a:str, b:str) -> bool:
        a_canonical = self._canonicalize(a)
        b_canonical = self._canonicalize(b)
        return a_canonical == b_canonical
    
    async def _llm_synonym_check(self, a:str, b:str) -> bool:
        logger.debug(f"Checking LLM synonymy for '{a}' vs '{b}'")
        payload = {
            "model": self.SYNONYM_MODEL,
            "temperature": 0.0,
            "max_tokens": 10,
            "messages": [
                {
                    "role": "user",
                    "content": (
                        f"In a clinical context, do '{a}' and '{b}' refer to the "
                        f"exact same drug, allergy, or diagnosis? "
                        f"Reply with SAME or DIFFERENT only."
                    )
                }
            ]
        }
        try:
            response = await self.client.post(self.API_ENDPOINT, json=payload)
            response.raise_for_status()
            data = response.json()
            answer = data["choices"][0]["message"]["content"].strip().upper()
            return answer == "SAME"
        except Exception as e:
            logger.error(f"Error during LLM synonym check: {str(e)}")
            return False
    
    async def close(self):
        await self.client.aclose()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, *args):
        await self.close()
            