# Person 1 — Backend Engineer

## Owns
- `backend/` (all of it)
- `backend/ocr/` — Mistral OCR integration
- `backend/voice/` — ElevenLabs Conversational AI
- `backend/llm/` — Mistral Large entity extraction & synonym check
- `backend/api/` — FastAPI routes

## Responsibilities
1. Wire up Mistral OCR to accept PDF upload and return structured text
2. Set up ElevenLabs Conversational AI WebSocket proxy
3. Implement LLM entity extraction with JSON schema enforcement
4. Integrate `cross_reference/` engine into POST `/cross-reference` route
5. Keep `backend/.env.example` up to date

## Key Interfaces
- `POST /upload-chart` → calls `ocr.client.run_ocr` → returns `{ raw_text }`
- `POST /extract-entities` → calls `llm.extraction.extract_entities` → returns `EntityData`
- `WS /voice-session` → proxies to ElevenLabs agent
- `POST /cross-reference` → calls `cross_reference.engine.cross_reference` → returns `{ flags }`

## Coordinate With
- Person 2 (frontend): Agree on exact request/response shapes — use `shared/schemas/` as truth
- Person 3 (ML): They will implement `cross_reference/engine.py`; you wire it to the route
