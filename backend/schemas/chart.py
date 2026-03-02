from pydantic import BaseModel, Field


class MedicationSchema(BaseModel):
    name: str = Field(..., description="Medication name, lowercased.")
    dose: str | None = Field(None, description="Dosage string as written on the chart, e.g. `500mg twice daily`.")

    model_config = {
        "json_schema_extra": {
            "examples": [{"name": "metformin", "dose": "500mg twice daily"}]
        }
    }


class EntitiesSchema(BaseModel):
    source: str = Field(
        ...,
        description="Origin of the extracted data. Either `chart` (from uploaded document) or `spoken` (from voice transcription).",
    )
    patient_name: str | None = Field(None, description="Full patient name as written on the chart, or null if not found.")
    allergies: list[str] = Field(
        default_factory=list,
        description="List of substance names the patient is allergic to, lowercased. Empty list means no known allergies (NKDA).",
    )
    medications: list[MedicationSchema] = Field(
        default_factory=list,
        description="Active medications listed in the chart.",
    )
    diagnosis: str | None = Field(None, description="Primary diagnosis as written, or null if not specified.")
    extraction_notes: str | None = Field(
        None,
        description="Optional note from the LLM if any field was ambiguous or inferred.",
    )
    diagrams: bool = Field(False, description="Whether the chart contained diagrams or non-textual content.")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "source": "chart",
                    "patient_name": "Jane Doe",
                    "allergies": ["penicillin"],
                    "medications": [{"name": "metformin", "dose": "500mg twice daily"}],
                    "diagnosis": "type 2 diabetes",
                    "extraction_notes": None,
                    "diagrams": False,
                }
            ]
        }
    }


class UploadChartResponse(BaseModel):
    session_id: str = Field(
        ...,
        description="UUID identifying this consultation session. Pass this to `/check-safety` and `/voice-session`.",
    )
    filename: str = Field(..., description="Original filename of the uploaded file.")
    ocr_text: str = Field(..., description="Full OCR-extracted text from the chart, all pages concatenated.")
    pages_processed: int = Field(..., description="Number of pages processed by Mistral OCR.")
    entities: EntitiesSchema = Field(..., description="Structured clinical entities extracted from the OCR text.")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "session_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                    "filename": "patient_chart.pdf",
                    "ocr_text": "Patient: John Smith\nAllergies: Penicillin\n...",
                    "pages_processed": 2,
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
