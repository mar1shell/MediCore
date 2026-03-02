from pydantic import BaseModel, Field

from backend.schemas.chart import EntitiesSchema


class SafetyCheckRecord(BaseModel):
    drug_name: str = Field(..., description="The drug that was checked.")
    is_safe: bool = Field(..., description="`true` if safe to prescribe.")
    issue: str | None = Field(None, description="Clinical issue description if unsafe.")
    recommendation: str | None = Field(None, description="Suggested alternative if unsafe.")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "drug_name": "amoxicillin",
                    "is_safe": False,
                    "issue": "Amoxicillin is a penicillin-class antibiotic. Patient has documented penicillin allergy.",
                    "recommendation": "Consider azithromycin as an alternative.",
                }
            ]
        }
    }


class SessionDataResponse(BaseModel):
    session_id: str = Field(..., description="UUID of this consultation session.")
    entities: EntitiesSchema = Field(..., description="Structured clinical entities stored for this session.")
    safety_checks: list[SafetyCheckRecord] = Field(
        default_factory=list,
        description="All drug safety checks performed during this session, in order.",
    )

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
                    "safety_checks": [
                        {
                            "drug_name": "amoxicillin",
                            "is_safe": False,
                            "issue": "Patient has penicillin allergy.",
                            "recommendation": "Use azithromycin instead.",
                        }
                    ],
                }
            ]
        }
    }
