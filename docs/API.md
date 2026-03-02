# MediCore API Reference

**Version:** 0.1.0  
**Base URL:** `http://localhost:8000` (development)  
**Interactive docs:** `http://localhost:8000/docs` (Swagger UI) · `http://localhost:8000/redoc` (ReDoc)

---

## Overview

MediCore is a real-time medical AI cross-validation tool. During a clinical ward round, a clinician uploads a patient chart; the system runs OCR and entity extraction, then facilitates a live ElevenLabs voice session. When the doctor mentions a drug they intend to prescribe, the system automatically cross-checks it against the patient's allergies, current medications, and diagnosis.

### Full Workflow

```
1. POST /upload-chart        → OCR + entity extraction → session_id
2. WS   /voice-session       → Live voice proxy (ElevenLabs ↔ browser)
3. POST /check-safety        → Drug safety verdict (called by ElevenLabs mid-conversation)
```

### Authentication

All AI API keys (Mistral, ElevenLabs) are managed server-side via environment variables. No client-side authentication token is required for any endpoint.

### Content Types

| Endpoint | Request format | Response format |
|---|---|---|
| `POST /upload-chart` | `multipart/form-data` | `application/json` |
| `POST /check-safety` | `application/json` | `application/json` |
| `WS /voice-session` | WebSocket (binary + text frames) | WebSocket (binary + text frames) |
| `GET /sessions/{id}` | — | `application/json` |
| `DELETE /sessions/{id}` | — | No content |
| `GET /` | — | `application/json` |

---

## Data Models

### `MedicationSchema`

| Field | Type | Description |
|---|---|---|
| `name` | `string` | Medication name, lowercased |
| `dose` | `string \| null` | Dosage as written on the chart, e.g. `"500mg twice daily"` |

### `EntitiesSchema`

| Field | Type | Description |
|---|---|---|
| `source` | `string` | Origin: `"chart"` or `"spoken"` |
| `allergies` | `string[]` | Substance names, lowercased. Empty list = NKDA (no known drug allergies) |
| `medications` | `MedicationSchema[]` | Active medications listed on the chart |
| `diagnosis` | `string \| null` | Primary diagnosis, or `null` if not specified |
| `extraction_notes` | `string \| null` | LLM note if any field was ambiguous |
| `diagrams` | `boolean` | Whether the chart contained diagrams or non-textual content |

### `UploadChartResponse`

| Field | Type | Description |
|---|---|---|
| `session_id` | `string (UUID)` | Unique ID for this consultation session |
| `filename` | `string` | Original filename of the uploaded file |
| `ocr_text` | `string` | Full OCR-extracted text, all pages concatenated |
| `pages_processed` | `integer` | Number of pages billed by Mistral OCR |
| `entities` | `EntitiesSchema` | Structured clinical entities extracted by the LLM |

### `SafetyCheckRequest`

| Field | Type | Description |
|---|---|---|
| `drug_name` | `string` | Name of the drug the doctor intends to prescribe |
| `session_id` | `string (UUID)` | Session ID from `POST /upload-chart` |

### `SafetyCheckResponse`

| Field | Type | Description |
|---|---|---|
| `is_safe` | `boolean` | `true` if safe to prescribe |
| `issue` | `string \| null` | Clinical reason why unsafe, or `null` if safe |
| `recommendation` | `string \| null` | Suggested alternative or action, or `null` if safe |

### `SessionDataResponse`

| Field | Type | Description |
|---|---|---|
| `session_id` | `string (UUID)` | UUID of this session |
| `entities` | `EntitiesSchema` | Clinical entities stored in the session |

### `ErrorResponse`

| Field | Type | Description |
|---|---|---|
| `detail` | `string` | Human-readable error description |

---

## Endpoints

---

### `GET /`

**Health check.** Confirms the API server is running.

**Response `200 OK`**

```json
{
  "status": "ok",
  "service": "MediCore API"
}
```

**cURL**

```bash
curl http://localhost:8000/
```

---

### `POST /upload-chart`

**Upload a patient chart for OCR and entity extraction.**

The backend runs two sequential AI stages:

1. **OCR** — Mistral OCR 3 (`mistral-ocr-latest`) reads every page and returns markdown-formatted text.
2. **Entity extraction** — Mistral Large (`mistral-large-latest`, temperature 0) identifies allergies, active medications, and diagnosis from the OCR text.

The extracted entities are stored in the in-memory session store. The returned `session_id` must be passed to the voice session and safety check endpoints.

**Request**

`Content-Type: multipart/form-data`

| Field | Type | Required | Description |
|---|---|---|---|
| `file` | file | Yes | Patient chart. Accepted: `application/pdf`, `image/jpeg`, `image/png`, `image/gif`, `image/webp` |

**Response `200 OK`** → `UploadChartResponse`

```json
{
  "session_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "filename": "patient_chart.pdf",
  "ocr_text": "Patient: John Smith\nDate of Birth: 1960-03-14\nAllergies: Penicillin (anaphylaxis)\n...",
  "pages_processed": 2,
  "entities": {
    "source": "chart",
    "allergies": ["penicillin"],
    "medications": [
      { "name": "metformin", "dose": "500mg twice daily" },
      { "name": "lisinopril", "dose": "10mg once daily" }
    ],
    "diagnosis": "type 2 diabetes mellitus",
    "extraction_notes": null,
    "diagrams": false
  }
}
```

**Error Responses**

| Status | Condition |
|---|---|
| `415 Unsupported Media Type` | File type not in the accepted list |
| `422 Unprocessable Entity` | OCR failed (e.g. encrypted/blank PDF) or entity extraction failed |

```json
{ "detail": "Unsupported file type 'text/plain'. Accepted: application/pdf, image/jpeg, image/png, image/gif, image/webp." }
```

**cURL**

```bash
curl -X POST http://localhost:8000/upload-chart \
  -F "file=@/path/to/patient_chart.pdf"
```

---

### `WS /voice-session`

**Real-time ElevenLabs Conversational AI voice proxy.**

Upgrades the HTTP connection to a WebSocket that bidirectionally proxies audio frames and control messages between the browser and ElevenLabs. The backend opens a corresponding `wss://api.elevenlabs.io/v1/convai/conversation?agent_id=<id>` connection and bridges them transparently.

#### Client Protocol

**Connecting**

```
ws://localhost:8000/voice-session
```

Pass the `session_id` as a dynamic variable when initialising the ElevenLabs conversation (in the `conversation_initiation_client_data` message) so the agent can include it in `check-safety` webhook calls.

**Sending audio (browser → server → ElevenLabs)**

Send raw PCM audio as binary WebSocket frames. ElevenLabs expects 16 kHz, 16-bit PCM audio encoded as base64 within a JSON `user_audio_chunk` message — this encoding is handled by the ElevenLabs JS SDK on the client side.

**Receiving messages (ElevenLabs → server → browser)**

| Frame type | Content |
|---|---|
| Binary | Audio response bytes from the ElevenLabs agent |
| Text | JSON control message (see ElevenLabs Conversational AI docs) |

**Common ElevenLabs JSON control messages**

```jsonc
// Agent starts speaking
{ "type": "audio", "audio_event": { "audio_base_64": "<base64>" } }

// Conversation turn metadata
{ "type": "agent_response", "agent_response_event": { "agent_response": "..." } }

// Safety tool call result relayed back as speech
{ "type": "interruption", ... }
```

**Closing the session**

Close the WebSocket connection from the client to end the voice session.

#### Notes

- The proxy is fully transparent — no message transformation is applied.
- ElevenLabs `check_safety` tool calls are handled server-side via `POST /check-safety` (see below). The client does not need to handle these.
- The `session_id` flow: chart upload → `session_id` → pass to ElevenLabs init → ElevenLabs includes in webhook → `/check-safety` looks up patient data.

---

### `POST /check-safety`

**Check drug safety against the patient's chart data.**

> **This endpoint is called automatically by ElevenLabs** as a webhook mid-conversation when the doctor mentions a drug. You do not call it directly from the frontend unless testing.

The backend:

1. Retrieves `ExtractedEntities` from the in-memory session store using `session_id`.
2. Builds a clinical user message with the patient's allergies, current medications, and diagnosis.
3. Calls Mistral Large (temperature 0, JSON mode) with a clinical pharmacology safety system prompt.
4. The LLM checks for:
   - Direct allergies (e.g. patient allergic to penicillin, doctor prescribes amoxicillin)
   - Cross-reactive allergies (e.g. penicillin → cephalosporins)
   - Drug-drug interactions with current medications
   - Contraindications given the diagnosis
5. Returns the structured verdict.

**Request** `application/json` → `SafetyCheckRequest`

```json
{
  "drug_name": "amoxicillin",
  "session_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6"
}
```

**Response `200 OK`** → `SafetyCheckResponse`

*Unsafe example:*

```json
{
  "is_safe": false,
  "issue": "Amoxicillin is a penicillin-class antibiotic. The patient has a documented penicillin allergy.",
  "recommendation": "Consider azithromycin or doxycycline as an alternative antibiotic."
}
```

*Safe example:*

```json
{
  "is_safe": true,
  "issue": null,
  "recommendation": null
}
```

**Error Responses**

| Status | Condition |
|---|---|
| `404 Not Found` | `session_id` does not exist in the session store |
| `502 Bad Gateway` | Mistral API returned an error or was unreachable |

**cURL**

```bash
curl -X POST http://localhost:8000/check-safety \
  -H "Content-Type: application/json" \
  -d '{"drug_name": "amoxicillin", "session_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6"}'
```

#### ElevenLabs Webhook Configuration

When configuring the ElevenLabs agent tool, set:

| Setting | Value |
|---|---|
| Tool name | `check_safety` |
| Webhook URL | `https://<your-domain>/check-safety` |
| Method | `POST` |
| Parameters | `drug_name` (string), `session_id` (string) |

---

### `GET /sessions/{session_id}`

**Retrieve stored session data.**

Returns the clinical entities associated with a session. Useful for the frontend to display patient data for an active consultation without re-uploading the chart.

**Path Parameters**

| Parameter | Type | Description |
|---|---|---|
| `session_id` | `string (UUID)` | Session ID returned by `POST /upload-chart` |

**Response `200 OK`** → `SessionDataResponse`

```json
{
  "session_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "entities": {
    "source": "chart",
    "allergies": ["penicillin"],
    "medications": [
      { "name": "metformin", "dose": "500mg twice daily" }
    ],
    "diagnosis": "type 2 diabetes mellitus",
    "extraction_notes": null,
    "diagrams": false
  }
}
```

**Error Responses**

| Status | Condition |
|---|---|
| `404 Not Found` | Session does not exist |

**cURL**

```bash
curl http://localhost:8000/sessions/3fa85f64-5717-4562-b3fc-2c963f66afa6
```

---

### `DELETE /sessions/{session_id}`

**Delete a session.**

Removes the session and its associated patient data from the in-memory store. Call this after a consultation is complete to free memory and protect patient data.

**Path Parameters**

| Parameter | Type | Description |
|---|---|---|
| `session_id` | `string (UUID)` | Session ID to delete |

**Response `204 No Content`** — No body returned.

**Error Responses**

| Status | Condition |
|---|---|
| `404 Not Found` | Session does not exist |

**cURL**

```bash
curl -X DELETE http://localhost:8000/sessions/3fa85f64-5717-4562-b3fc-2c963f66afa6
```

---

## Error Handling

All error responses follow the same `ErrorResponse` shape:

```json
{ "detail": "Human-readable description of what went wrong." }
```

| HTTP Status | When it occurs |
|---|---|
| `404 Not Found` | Session ID not in store |
| `415 Unsupported Media Type` | File type not accepted by `/upload-chart` |
| `422 Unprocessable Entity` | OCR or entity extraction pipeline failure |
| `502 Bad Gateway` | Upstream Mistral or ElevenLabs API error |

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `MISTRAL_API_KEY` | Yes | Mistral AI API key — used for OCR, entity extraction, and safety checks |
| `ELEVENLABS_API_KEY` | Yes | ElevenLabs API key — used by the voice session proxy |
| `ELEVENLABS_AGENT_ID` | Yes | ID of the pre-configured ElevenLabs Conversational AI agent |
| `OCR_REQUEST_TIMEOUT` | No | HTTP read timeout for Mistral OCR (seconds, default: `300`) |

---

## Running the Backend

```bash
cd backend
cp .env.example .env       # fill in API keys
pip install -r requirements.txt
uvicorn backend.main:app --reload --port 8000
```

Swagger UI will be available at `http://localhost:8000/docs`.

---

## Session Store Limitations

The current session store is an **in-memory Python dictionary**. This means:

- Sessions are lost on server restart.
- The store is not shared between multiple server instances (not horizontally scalable).
- No session expiry — sessions accumulate until the process is restarted or explicitly deleted.

For production, replace `backend/session.py` with a Redis-backed or database-backed store.

---

## Planned Endpoints (Frontend Phase)

The following endpoints are not yet implemented but will be required by the frontend UI:

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/patients` | Retrieve recent patients list (Home screen) |
| `GET` | `/consultations/{id}/summary` | Consultation Summary with transcript, vitals, and conflict flags |
| `POST` | `/consultations/{id}/acknowledge` | Acknowledge and save a completed consultation |
