# Judge Q&A — Anticipated Questions

## "How does it handle medical abbreviations?"

We load a curated abbreviation dictionary (`ml/abbreviations/medical_abbrev.json`) and expand terms before comparison. For example, "ASA" → "aspirin", "PCN" → "penicillin". This runs before any LLM call, keeping latency low.

## "What if the LLM hallucinates an entity?"

Entity extraction uses JSON schema enforcement via Mistral's structured output mode. The response is validated against `shared/schemas/chart_data.json` before it enters the pipeline. Invalid responses are rejected.

## "Is this HIPAA compliant?"

This is a hackathon prototype. For production we would use a BAA-covered API endpoint, encrypt data at rest and in transit, and avoid logging PHI. The architecture is designed with this in mind — all patient data stays server-side and is never stored.

## "Why ElevenLabs instead of a simpler STT solution?"

ElevenLabs Conversational AI handles the full dialogue loop — turn detection, interruption handling, and natural back-and-forth — out of the box. This lets us focus on the medical logic rather than voice infrastructure.

## "What's the accuracy of the cross-reference engine?"

Our test suite (`ml/test_cases/`) covers 5 scenarios including true negatives (case 05 — zero flags). We prioritize false positives over false negatives: it's safer to surface a flag that turns out to be fine than to miss a real discrepancy.

## "Could this work with an EHR system?"

Yes. The API contract (`shared/openapi.yaml`) is designed to be EHR-agnostic. Any system that can POST structured JSON can integrate with MedRound.

## "How did you split the work?"

- Person 1: Backend API, OCR, Voice integration
- Person 2: React frontend, real-time UI
- Person 3: ML prompts, cross-reference engine, test cases
- Person 4: Demo preparation, integration testing, synthetic charts
