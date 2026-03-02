from pydantic import BaseModel, Field


class SafetyCheckRequest(BaseModel):
    drug_name: str = Field(
        ...,
        description="Name of the drug the doctor intends to prescribe.",
        examples=["amoxicillin"],
    )
    session_id: str = Field(
        ...,
        description="Session UUID returned by `POST /upload-chart`.",
        examples=["3fa85f64-5717-4562-b3fc-2c963f66afa6"],
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "drug_name": "amoxicillin",
                    "session_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                }
            ]
        }
    }


class SafetyCheckResponse(BaseModel):
    is_safe: bool = Field(
        ...,
        description="`true` if the drug is safe to prescribe given the patient's chart data.",
    )
    issue: str | None = Field(
        None,
        description="Clinical reason why the drug is not safe, or `null` if safe.",
    )
    recommendation: str | None = Field(
        None,
        description="Suggested alternative or action if unsafe, or `null` if safe.",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "is_safe": False,
                    "issue": "Amoxicillin is a penicillin-class antibiotic. Patient has a documented penicillin allergy.",
                    "recommendation": "Consider azithromycin or doxycycline as an alternative.",
                },
                {
                    "is_safe": True,
                    "issue": None,
                    "recommendation": None,
                },
            ]
        }
    }
