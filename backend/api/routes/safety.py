import json

import httpx
from fastapi import APIRouter, HTTPException

from backend.ocr.config import OCRConfig
from backend.ocr.prompt_loader import load_prompt
from backend.session import get_session, add_safety_check, was_recommended
from backend.schemas.safety import SafetyCheckRequest, SafetyCheckResponse
from backend.schemas.common import ErrorResponse

router = APIRouter()
_config = OCRConfig.from_env()
_SAFETY_SYSTEM_PROMPT = load_prompt("safety_check_system_prompt.txt")


@router.post(
    "/check-safety",
    response_model=SafetyCheckResponse,
    summary="Check drug safety against patient chart",
    description=(
        "**ElevenLabs webhook endpoint.**\n\n"
        "Called automatically by the ElevenLabs voice agent mid-conversation when the doctor "
        "mentions a drug they intend to prescribe. The backend looks up the patient's chart data "
        "from the session store and asks Mistral Large to evaluate safety against:\n\n"
        "- Direct allergies and cross-reactive allergies\n"
        "- Drug-drug interactions with current medications\n"
        "- Contraindications given the patient's diagnosis\n\n"
        "The verdict is returned as structured JSON and read back to the doctor by the voice agent in real time."
    ),
    response_description="Safety verdict with an optional issue description and recommendation.",
    responses={
        404: {
            "model": ErrorResponse,
            "description": "No session found for the provided `session_id`.",
        },
        502: {
            "model": ErrorResponse,
            "description": "Upstream Mistral API error.",
        },
    },
    tags=["Safety"],
)
async def check_safety(body: SafetyCheckRequest) -> SafetyCheckResponse:
    entities = get_session(body.session_id)
    if entities is None:
        raise HTTPException(status_code=404, detail="Session not found.")

    # Short-circuit: if this drug was previously recommended by our own safety
    # checker, trust it and skip the LLM call. This prevents the cascade where
    # ElevenLabs hears the agent say "consider <drug>" and immediately triggers
    # another check_safety for that same drug, causing a chain of rejections.
    if was_recommended(body.session_id, body.drug_name):
        safe_result = SafetyCheckResponse(is_safe=True, issue=None, recommendation=None)
        add_safety_check(body.session_id, {
            "drug_name": body.drug_name,
            "is_safe": True,
            "issue": None,
            "recommendation": None,
        })
        return safe_result

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
            {"role": "system", "content": _SAFETY_SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
    }

    try:
        async with httpx.AsyncClient(
            timeout=30.0,
            headers={
                "Authorization": f"Bearer {_config.api_key}",
                "Content-Type": "application/json",
            },
        ) as client:
            resp = await client.post("https://api.mistral.ai/v1/chat/completions", json=payload)
            resp.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Mistral API error {exc.response.status_code}: {exc.response.text}",
        ) from exc
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail=f"Failed to reach Mistral API: {exc}") from exc

    data = json.loads(resp.json()["choices"][0]["message"]["content"])
    result = SafetyCheckResponse(
        is_safe=data.get("is_safe", True),
        issue=data.get("issue"),
        recommendation=data.get("recommendation"),
    )
    add_safety_check(body.session_id, {
        "drug_name": body.drug_name,
        "is_safe": result.is_safe,
        "issue": result.issue,
        "recommendation": result.recommendation,
    })
    return result
