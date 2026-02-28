from fastapi import FastAPI
from dotenv import load_dotenv

from api.routes import chart, entities, voice, cross_reference

load_dotenv()

app = FastAPI(title="MedRound API", version="0.1.0")

app.include_router(chart.router)
app.include_router(entities.router)
app.include_router(voice.router)
app.include_router(cross_reference.router)


@app.get("/health")
def health():
    return {"status": "ok"}
