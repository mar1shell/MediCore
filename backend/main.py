import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env when running locally; on Railway env vars are injected directly.
load_dotenv(Path(__file__).parent / ".env", override=False)

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.api.routes import chart, voice, safety, sessions
from backend.ocr.chart_processor import OCRProcessingError
from backend.ocr.entity_extractor import EntityExtractionError
from backend.schemas.common import HealthResponse

# ---------------------------------------------------------------------------
# OpenAPI tag metadata — drives the Swagger UI sidebar grouping & descriptions
# ---------------------------------------------------------------------------
_TAGS = [
    {
        "name": "Health",
        "description": "Liveness check. Confirm the API server is running.",
    },
    {
        "name": "Chart",
        "description": (
            "**Chart upload and processing.** "
            "Upload a patient chart (PDF or image), run Mistral OCR, extract clinical entities "
            "(allergies, medications, diagnosis), and create a consultation session."
        ),
    },
    {
        "name": "Safety",
        "description": (
            "**Real-time drug safety checking.** "
            "Called as an ElevenLabs webhook during a live voice session. "
            "Cross-references a proposed drug against the patient's chart entities using Mistral Large."
        ),
    },
    {
        "name": "Voice",
        "description": (
            "**Live voice session proxy.** "
            "WebSocket endpoint that bridges the browser to ElevenLabs Conversational AI, "
            "forwarding audio frames and control messages bidirectionally."
        ),
    },
    {
        "name": "Sessions",
        "description": (
            "**Session management.** "
            "Inspect or clean up in-memory consultation sessions. "
            "Each session holds the extracted patient entities for one consultation."
        ),
    },
]

app = FastAPI(
    title="MediCore API",
    description=(
        "## MediCore — Real-Time Medical AI Cross-Validation\n\n"
        "MediCore catches medication safety issues during clinical ward rounds. "
        "A clinician uploads a patient chart; the system runs OCR and entity extraction, "
        "then proxies a live ElevenLabs voice session. When the doctor mentions a drug, "
        "the system automatically cross-checks it against the patient's allergies, "
        "current medications, and diagnosis, returning a structured safety verdict in real time.\n\n"
        "### Workflow\n"
        "1. `POST /upload-chart` — Upload chart → OCR → entity extraction → `session_id`\n"
        "2. `WS  /voice-session` — Open voice session proxy (pass `session_id` to ElevenLabs)\n"
        "3. `POST /check-safety` — ElevenLabs webhook → safety verdict (auto-called mid-conversation)\n\n"
        "### Authentication\n"
        "All API keys (Mistral, ElevenLabs) are server-side only. "
        "No client authentication is required for these endpoints."
    ),
    version="0.1.0",
    openapi_tags=_TAGS,
    swagger_ui_parameters={
        "defaultModelsExpandDepth": -1,   # collapse schemas panel by default
        "docExpansion": "list",            # collapse all operations by default
        "tryItOutEnabled": True,
    },
    license_info={"name": "Private — All rights reserved"},
)

# ---------------------------------------------------------------------------
# CORS — tighten origins in production
# ---------------------------------------------------------------------------
# FRONTEND_URL can be set on Railway to lock CORS to the hosted frontend.
# Leave unset (or "*") during development / demo.
_frontend_url = os.getenv("FRONTEND_URL", "*")
_origins = [_frontend_url] if _frontend_url != "*" else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Global exception handlers — convert domain errors to structured HTTP errors
# ---------------------------------------------------------------------------

@app.exception_handler(OCRProcessingError)
async def ocr_error_handler(request: Request, exc: OCRProcessingError) -> JSONResponse:
    return JSONResponse(status_code=422, content={"detail": str(exc)})


@app.exception_handler(EntityExtractionError)
async def extraction_error_handler(request: Request, exc: EntityExtractionError) -> JSONResponse:
    return JSONResponse(status_code=422, content={"detail": str(exc)})


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(chart.router, tags=["Chart"])
app.include_router(voice.router, tags=["Voice"])
app.include_router(safety.router, tags=["Safety"])
app.include_router(sessions.router)  # prefix and tags defined on the router itself


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.get(
    "/",
    response_model=HealthResponse,
    summary="Health check",
    description="Returns `{status: ok}` when the server is running. Use for liveness probes.",
    tags=["Health"],
)
async def health_check() -> HealthResponse:
    return HealthResponse(status="ok", service="MediCore API")
