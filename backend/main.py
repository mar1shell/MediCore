from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import chart, voice, cross_reference

app = FastAPI(
    title="MediCore API",
    description=(
        "Medical AI cross-validation tool — OCR chart extraction, "
        "LLM entity extraction, real-time voice AI, and chart/speech reconciliation."
    ),
    version="0.1.0",
)

# ---------------------------------------------------------------------------
# CORS — tighten origins in production
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(chart.router, tags=["Chart"])
app.include_router(voice.router, tags=["Voice"])
app.include_router(cross_reference.router, tags=["Cross-Reference"])


@app.get("/", tags=["Health"])
async def health_check():
    return {"status": "ok", "service": "MediCore API"}
