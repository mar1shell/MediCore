# MediCore

A medical AI cross-validation tool that catches discrepancies between written patient charts and spoken patient history using OCR, LLM entity extraction, and real-time voice AI.

## Team

| Role | Person | Owns |
|------|--------|------|
| Backend Engineer | Person 1 | `backend/`, API routes, OCR, Voice |
| Frontend Engineer | Person 2 | `frontend/` |
| ML / Prompt Engineer | Person 3 | `ml/`, `backend/cross_reference/` |
| Demo Lead | Person 4 | `demo/`, integration testing |

## Architecture

See `docs/architecture/` for the system diagram.

## Quick Start

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # fill in your API keys
uvicorn main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Environment Variables

Copy `.env.example` to `.env` at the root and in `backend/` and fill in:

- `MISTRAL_API_KEY` — from https://console.mistral.ai
- `ELEVENLABS_API_KEY` — from https://elevenlabs.io
- `ELEVENLABS_AGENT_ID` — your configured Conversational AI agent ID

## Shared Contract

`shared/schemas/` is the source of truth for all data shapes. Backend validates against these JSON Schemas; frontend types are derived from them.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/upload-chart` | Upload PDF chart, returns extracted text |
| POST | `/extract-entities` | Run LLM entity extraction on chart text |
| WS | `/voice-session` | ElevenLabs real-time voice agent WebSocket |
| POST | `/cross-reference` | Compare chart entities vs spoken entities, return flags |
