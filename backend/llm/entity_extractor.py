"""LLM — entity extraction via Mistral.

Sends a structured prompt to Mistral and parses the JSON response into a
flat dict of medical entities (medications, diagnoses, allergies, vitals, …).
"""

from __future__ import annotations

import json

from mistralai import Mistral

from config import get_settings

SYSTEM_PROMPT = """You are a medical information extraction assistant.
Given a snippet of a patient chart, extract ALL clinically relevant entities.
Return ONLY a valid JSON object (no markdown fences) with these keys:
  - medications:   list of medication names + doses if present
  - diagnoses:     list of diagnoses / conditions
  - allergies:     list of allergies
  - vitals:        dict of vital signs (e.g. {"bp": "120/80", "hr": "72"})
  - procedures:    list of procedures or tests
  - other:         any other clinically relevant facts

If a category has no data, use an empty list or empty dict."""


async def extract_entities(chart_text: str) -> dict:
    """Call Mistral to extract structured medical entities from *chart_text*."""
    settings = get_settings()
    client = Mistral(api_key=settings.mistral_api_key)

    response = await client.chat.complete_async(
        model="mistral-small-latest",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": chart_text},
        ],
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content
    return json.loads(raw)
