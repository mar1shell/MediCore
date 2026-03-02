# MediCore — System Overview

## What it is

MediCore (internally called MedRound) is a real-time ward-round patient safety assistant built for clinicians. Its core purpose is to catch medication safety issues on the spot: a doctor uploads a patient's written chart, then has a live spoken conversation with an AI agent. When the doctor mentions a drug they intend to prescribe, the system automatically cross-checks it against the patient's chart data — allergies, current medications, diagnosis — and immediately returns a structured safety verdict.

---

## Full Workflow

### Step 1 — Chart Upload (`POST /upload-chart`)

The doctor (or a staff member) uploads the patient's chart as a PDF or image (JPEG, PNG, GIF, WEBP) through the frontend.

The backend runs two sequential stages:

**Stage 1 — OCR (Mistral OCR 3)**
The file is base64-encoded and sent to `https://api.mistral.ai/v1/ocr`. Mistral OCR 3 returns a page-by-page markdown transcription. All pages are concatenated into a single `full_text` string.

**Stage 2 — Entity Extraction (Mistral Large)**
The OCR text is sent to Mistral Large (`mistral-large-latest`, temperature 0) with a strict clinical extraction prompt. The model returns structured JSON containing:
- `allergies` — list of substance strings the patient is allergic to
- `medications` — list of `{name, dose}` objects for active/current medications
- `diagnosis` — primary diagnosis string or null
- `extraction_notes` — optional note if anything was ambiguous

The extraction prompt enforces strict rules: extract only what is explicitly stated, never infer, never fabricate, return empty lists rather than null for confirmed absence of allergies (NKDA).

**Stage 3 — Session Creation**
The extracted `ExtractedEntities` object is stored in a module-level in-memory dictionary keyed by a UUID (`session_id`). This ID ties the chart data to the subsequent voice session and safety check.

**Response:**
```json
{
  "session_id": "<uuid>",
  "filename": "patient_chart.pdf",
  "ocr_text": "...",
  "pages_processed": 3,
  "entities": {
    "allergies": ["penicillin"],
    "medications": [{"name": "metformin", "dose": "500mg"}],
    "diagnosis": "type 2 diabetes",
    "extraction_notes": null
  }
}
```

---

### Step 2 — Voice Session (`WS /voice-session`)

The frontend opens a WebSocket connection to `/voice-session`, passing the `session_id` to ElevenLabs as a dynamic variable when initialising the conversation.

The backend acts as a transparent bidirectional proxy:
- Browser audio frames → forwarded to ElevenLabs via `wss://api.elevenlabs.io/v1/convai/conversation?agent_id=<id>`
- ElevenLabs responses (audio + control messages) → forwarded back to the browser

The ElevenLabs agent is a pre-configured conversational AI that listens to the doctor speaking. It is configured with a `check_safety` tool. When the doctor mentions a drug name they want to prescribe, the agent invokes that tool as a webhook.

---

### Step 3 — Safety Check (`POST /check-safety`)

ElevenLabs calls this endpoint as a webhook mid-conversation:

```json
{ "drug_name": "aspirin", "session_id": "<uuid>" }
```

The backend:
1. Looks up the session store for the `session_id` — returns 404 if not found.
2. Builds a user message from the patient's chart data:
   ```
   Patient allergies: penicillin
   Current medications: metformin
   Diagnosis: type 2 diabetes

   Doctor wants to prescribe: aspirin
   Is this safe?
   ```
3. Sends the message to Mistral Large with a clinical pharmacology safety checker system prompt. The model checks for direct allergies, cross-reactive allergies, drug-drug interactions, and contraindications. Temperature is 0 and `response_format` is forced to `json_object`.
4. Returns the verdict:

```json
{
  "is_safe": false,
  "issue": "Aspirin is contraindicated in patients with salicylate sensitivity or active peptic ulcer disease.",
  "recommendation": "Consider paracetamol as an alternative analgesic."
}
```

ElevenLabs reads this response and relays the safety verdict to the doctor verbally in real time.

---

## API Surface

| Endpoint | Method | Purpose |
|---|---|---|
| `/upload-chart` | POST (multipart) | File → OCR → entity extraction → session |
| `/voice-session` | WebSocket | ElevenLabs real-time voice proxy |
| `/check-safety` | POST (JSON) | ElevenLabs webhook → Mistral safety check → verdict |
| `/` | GET | Health check |

---

## Codebase Structure

```
backend/
├── main.py                        # FastAPI app, CORS, router registration
├── config.py                      # Pydantic settings (MISTRAL_API_KEY, ELEVENLABS_*)
├── session.py                     # In-memory session store (session_id → ExtractedEntities)
│
├── ocr/
│   ├── chart_processor.py         # Mistral OCR 3 client (PDF + image, base64 encoding)
│   ├── entity_extractor.py        # Mistral Large entity extraction client
│   ├── config.py                  # OCRConfig dataclass (api_key, request_timeout)
│   ├── models.py                  # Dataclasses: ChartPage, OCRResult, ExtractedEntities
│   ├── prompt_loader.py           # Reads prompt .txt files from ocr/prompts/
│   └── prompts/
│       ├── extraction_system_prompt.txt   # Strict clinical extraction rules for Mistral
│       ├── extraction_user_template.txt   # User message template for extraction
│       └── safety_check_system_prompt.txt # Clinical pharmacology safety checker prompt
│
├── api/
│   ├── __init__.py
│   └── routes/
│       ├── chart.py               # POST /upload-chart
│       ├── voice.py               # WS /voice-session
│       └── safety.py              # POST /check-safety
│
└── voice/
    └── session.py                 # Async WebSocket proxy to ElevenLabs

frontend/                          # React + Vite + TypeScript UI
shared/                            # JSON schemas + OpenAPI contract
ml/                                # Prompts, abbreviations, test cases
demo/                              # Synthetic charts, demo script
docs/                              # Architecture diagrams, per-person plans
```

---

## Data Models

### `ExtractedEntities`
Produced by entity extraction, stored in session, consumed by safety check.

| Field | Type | Description |
|---|---|---|
| `source` | str | `"chart"` or `"spoken"` |
| `allergies` | list[str] | Substance names, lowercased |
| `medications` | list[{name, dose}] | Active medications only |
| `diagnosis` | str \| None | Primary diagnosis |
| `extraction_notes` | str \| None | Ambiguity notes from the LLM |

### `OCRResult`

| Field | Type | Description |
|---|---|---|
| `filename` | str | Original file name |
| `full_text` | str | All pages concatenated |
| `pages` | list[ChartPage] | Per-page text + dimensions |
| `model_used` | str | Mistral OCR model identifier |
| `pages_processed` | int | Number of pages billed |

---

## Environment Variables

| Variable | Used by |
|---|---|
| `MISTRAL_API_KEY` | OCR, entity extraction, safety check |
| `ELEVENLABS_API_KEY` | Voice proxy |
| `ELEVENLABS_AGENT_ID` | Voice proxy |
| `OCR_REQUEST_TIMEOUT` | ChartProcessor HTTP timeout (default 300s) |

---

## Technology Stack

| Layer | Technology |
|---|---|
| API framework | FastAPI (Python, async) |
| OCR | Mistral OCR 3 (`mistral-ocr-latest`) |
| LLM | Mistral Large (`mistral-large-latest`, temp=0) |
| Voice AI | ElevenLabs Conversational AI (WebSocket) |
| HTTP client | `httpx` (async) |
| Settings | `pydantic-settings` |
| Frontend | React + Vite + TypeScript |
