from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    detail: str = Field(..., description="Human-readable error description.")

    model_config = {
        "json_schema_extra": {
            "examples": [{"detail": "Session not found."}]
        }
    }


class HealthResponse(BaseModel):
    status: str = Field(..., description="Service liveness status. Always `ok` when the server is up.")
    service: str = Field(..., description="Name of the running service.")

    model_config = {
        "json_schema_extra": {
            "examples": [{"status": "ok", "service": "MediCore API"}]
        }
    }
