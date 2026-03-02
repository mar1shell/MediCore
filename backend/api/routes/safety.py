from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import httpx
import json

from backend.ocr.config import OCRConfig
from backend.ocr.prompt_loader import _load_prompt
from backend.session import get_session

router = APIRouter()
SAFETY_SYSTEM_PROMPT = _load_prompt("safety_check_system_prompt.txt")


class SafetyCheckRequest(BaseModel):
    drug_name: str
    session_id: str


@router.post("/check-safety")
async def check_safety(body: SafetyCheckRequest):
    entities = get_session(body.session_id)
    if entities is None:
        raise HTTPException(status_code=404, detail="Session not found.")

    config = OCRConfig.from_env()
    user_msg = (
        f"Patient allergies: {', '.join(entities.allergies) or 'none'}\n"
        f"Current medications: {', '.join(entities.medication_names) or 'none'}\n"
        f"Diagnosis: {entities.diagnosis or 'not specified'}\n\n"
        f"Doctor wants to prescribe: {body.drug_name}\n"
        f"Is this safe?"
    )
    payload = {
        "model": "mistral-large-latest",
        "temperature": 0.0,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": SAFETY_SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
    }
    async with httpx.AsyncClient(
        timeout=30.0,
        headers={
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json",
        },
    ) as client:
        resp = await client.post(
            "https://api.mistral.ai/v1/chat/completions", json=payload
        )
        resp.raise_for_status()

    data = json.loads(resp.json()["choices"][0]["message"]["content"])
    return {
        "is_safe": data.get("is_safe", True),
        "issue": data.get("issue"),
        "recommendation": data.get("recommendation"),
    }
