from pydantic import BaseModel, Field

from backend.schemas.chart import EntitiesSchema


class SessionDataResponse(BaseModel):
    session_id: str = Field(..., description="UUID of this consultation session.")
    entities: EntitiesSchema = Field(..., description="Structured clinical entities stored for this session.")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "session_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                    "entities": {
                        "source": "chart",
                        "allergies": ["penicillin"],
                        "medications": [{"name": "metformin", "dose": "500mg twice daily"}],
                        "diagnosis": "type 2 diabetes",
                        "extraction_notes": None,
                        "diagrams": False,
                    },
                }
            ]
        }
    }
