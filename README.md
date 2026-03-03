# MediCore AI

**Real-time patient safety assistant for clinical ward rounds — powered by Mistral AI and ElevenLabs.**

> Built for the [**Mistral AI Hackathon**](https://worldwide-hackathon.mistral.ai/)

> the backend is hosted on [railway](https://medicore.up.railway.app)

---

## The Problem

Ward rounds move fast. A doctor sees dozens of patients, juggles handwritten charts, verbal histories, and prescription decisions, all under time pressure. Medication errors (wrong drug, allergy conflict, dangerous interaction) are among the most preventable causes of patient harm, yet they continue to occur because safety checks are manual, slow, and easy to skip.

**MediCore AI turns every prescription moment into a guarded decision.**

---

## What It Does

1. **Upload the patient chart** — the doctor uploads a photo or PDF of the patient's written chart (handwritten or printed).
2. **AI reads and understands it** — Mistral OCR 3 extracts all text; Mistral Large parses it into structured clinical entities: patient name, allergies, active medications, and diagnosis.
3. **Speak naturally** — the doctor starts a live voice consultation with an AI agent (powered by ElevenLabs Conversational AI). The agent has full context of the patient's chart.
4. **Safety checks fire automatically** — the moment the doctor mentions a drug they intend to prescribe, the agent silently calls our `/check-safety` backend. Mistral Large cross-references the drug against the patient's allergies, current medications, and diagnosis in real time.
5. **Instant alert** — if a conflict is detected (allergy match, drug-drug interaction, contraindication), a visual Safety Alert overlays the screen and the agent verbally flags the issue with a concrete recommendation.
6. **Consultation summary** — when the session ends, a full summary is generated: extracted entities, safety check results, and a timestamped transcript of the conversation.

---

## Tech Stack

| Layer             | Technology                                         |
| ----------------- | -------------------------------------------------- |
| API Framework     | FastAPI                                            |
| OCR               | **Mistral OCR 3** (`mistral-ocr-latest`)           |
| Entity Extraction | **Mistral Large** (`mistral-large-latest`, temp=0) |
| Safety Evaluation | **Mistral Large** (`mistral-large-latest`, temp=0) |
| Voice AI          | ElevenLabs Conversational AI (WebSocket proxy)     |
| Deployment        | Railway (Backend)                                  |
| Frontend          | React (TypeScript + Vite)                          |

---

## How Mistral AI Powers MediCore

MediCore makes **three distinct calls to Mistral** in every consultation:

### 1. OCR — Chart Reading

```
model: mistral-ocr-latest
```

Converts uploaded patient charts (PDF, handwritten notes, photos) into machine-readable text. Mistral OCR handles messy handwriting, multi-page documents, and scanned images that traditional OCR tools struggle with.

### 2. Entity Extraction — Chart Understanding

```
model: mistral-large-latest
```

Given the raw OCR text, Mistral Large extracts a structured clinical record:

```json
{
  "patient_name": "Mary Johnson",
  "allergies": ["penicillin", "sulfonamides"],
  "medications": [{ "name": "metformin", "dose": "500mg twice daily" }],
  "diagnosis": "type 2 diabetes"
}
```

The prompt enforces strict rules: extract only what is explicitly stated, never infer, return empty lists for confirmed absence (NKDA), never fabricate.

### 3. Safety Evaluation — Real-Time Prescription Check

```
model: mistral-large-latest
```

Called mid-conversation as a webhook from ElevenLabs. Given the patient's chart data and the drug the doctor just mentioned:

```json
{
  "is_safe": false,
  "issue": "Amoxicillin is a penicillin-type antibiotic — patient has a documented penicillin allergy.",
  "recommendation": "Consider Azithromycin 500mg as an alternative."
}
```

The verdict is returned in milliseconds and read back to the doctor verbally by the AI agent.

---

## API Reference

Full API documentation: [`docs/API.md`](docs/API.md)

Interactive Swagger UI (when running): `http://localhost:8000/docs`

### Endpoints

| Method   | Path             | Description                                      |
| -------- | ---------------- | ------------------------------------------------ |
| `GET`    | `/`              | Health check                                     |
| `POST`   | `/upload-chart`  | Upload chart → OCR → entity extraction → session |
| `WS`     | `/voice-session` | ElevenLabs real-time voice proxy                 |
| `POST`   | `/check-safety`  | ElevenLabs webhook → Mistral safety check        |
| `GET`    | `/sessions/{id}` | Retrieve session data + safety check results     |
| `DELETE` | `/sessions/{id}` | End session and clear patient data               |

---

## Local Development

### Prerequisites

- Python 3.11+
- Node.js 18+
- A [Mistral AI](https://console.mistral.ai/) API key
- An [ElevenLabs](https://elevenlabs.io/) account with a configured Conversational AI agent
- The backend must be publicly accessible for ElevenLabs webhook calls (use Railway or a tool like ngrok for local testing)

### Backend

```bash
# Clone and enter the project
git clone https://github.com/mar1shell/MediCore.git
cd MediCore

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp backend/.env.example backend/.env
# Edit backend/.env with your API keys

# Run the backend
uvicorn backend.main:app --reload
```

The API will be available at `http://localhost:8000`.
Swagger docs at `http://localhost:8000/docs`.

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Configure the backend URL
echo "VITE_API_URL=http://localhost:8000" > .env.local

# Start the dev server
npm run dev
```

The app will be available at `http://localhost:5173`.

### Environment Variables

| Variable              | Required | Description                                                      |
| --------------------- | -------- | ---------------------------------------------------------------- |
| `MISTRAL_API_KEY`     | Yes      | Mistral AI API key — used for OCR, extraction, and safety checks |
| `ELEVENLABS_API_KEY`  | Yes      | ElevenLabs API key                                               |
| `ELEVENLABS_AGENT_ID` | Yes      | ID of your configured ElevenLabs Conversational AI agent         |
| `VITE_API_URL`        | YES      | Backend API URL (default: `http://localhost:8000`)               |

---

## Project Structure

```
MediCore/
├── requirements.txt              # Pinned Python dependencies
├── Procfile                      # Railway/Heroku start command
├── railway.toml                  # Railway deployment config
│
├── backend/
│   ├── main.py                   # FastAPI app (CORS, routers, error handlers)
│   ├── config.py                 # Pydantic settings (API keys, memoized)
│   ├── session.py                # In-memory session store
│   │
│   ├── api/routes/
│   │   ├── chart.py              # POST /upload-chart
│   │   ├── voice.py              # WS  /voice-session
│   │   ├── safety.py             # POST /check-safety
│   │   └── sessions.py           # GET/DELETE /sessions/{id}
│   │
│   ├── ocr/
│   │   ├── chart_processor.py    # Mistral OCR 3 client
│   │   ├── entity_extractor.py   # Mistral Large entity extraction
│   │   ├── models.py             # Domain dataclasses
│   │   └── prompts/              # System prompts (text files)
│   │
│   ├── schemas/                  # Pydantic request/response models
│   ├── voice/session.py          # Async WebSocket proxy to ElevenLabs
│   └── tests/                    # pytest test suite
│
├── frontend/
│   └── src/
│       ├── pages/                # HomePage, SessionPage, AnalyzingPage, SummaryPage
│       ├── components/ui/        # Orb, Badge, Avatar, Button, Card
│       ├── hooks/                # useUploadChart, useVoiceSession
│       ├── context/              # SessionContext (global session state)
│       ├── api/client.ts         # Typed fetch wrappers
│       └── types/index.ts        # TypeScript interfaces
│
└── docs/
    └── API.md                    # Full API reference
```

---

## Team

| Name                                                   |
| ------------------------------------------------------ |
| [_El-Hamdaoui Marouane_](https://github.com/mar1shell) |
| [_Hany EL Atlassi_](https://github.com/TheGitSlender)  |
| [_Salwa Khattami_](https://github.com/Salwa08)         |
| [_Malak Mekyassi_](https://github.com/mal0101)         |

---

## License

MIT
