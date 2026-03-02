from fastapi import APIRouter, HTTPException, Response

from backend.session import get_session_record, delete_session
from backend.schemas.session import SessionDataResponse, SafetyCheckRecord
from backend.schemas.chart import EntitiesSchema, MedicationSchema
from backend.schemas.common import ErrorResponse

router = APIRouter(prefix="/sessions", tags=["Sessions"])

_NOT_FOUND = {"model": ErrorResponse, "description": "No session found for the given ID."}


@router.get(
    "/{session_id}",
    response_model=SessionDataResponse,
    summary="Retrieve session data",
    description=(
        "Return the extracted clinical entities and all safety check results for a given session. "
        "Poll this endpoint during a live voice session to detect safety alerts in real time."
    ),
    response_description="Session ID, extracted entities, and accumulated safety check records.",
    responses={404: _NOT_FOUND},
)
async def get_session_data(session_id: str) -> SessionDataResponse:
    record = get_session_record(session_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")

    entities = record.entities
    return SessionDataResponse(
        session_id=session_id,
        entities=EntitiesSchema(
            source=entities.source,
            patient_name=entities.patient_name,
            allergies=entities.allergies,
            medications=[
                MedicationSchema(name=m["name"], dose=m.get("dose"))
                for m in entities.medications
            ],
            diagnosis=entities.diagnosis,
            extraction_notes=entities.extraction_notes,
            diagrams=entities.diagrams,
        ),
        safety_checks=[
            SafetyCheckRecord(
                drug_name=sc["drug_name"],
                is_safe=sc["is_safe"],
                issue=sc.get("issue"),
                recommendation=sc.get("recommendation"),
            )
            for sc in record.safety_checks
        ],
    )


@router.delete(
    "/{session_id}",
    status_code=204,
    summary="Delete a session",
    description=(
        "Remove a session and its associated patient data from the in-memory store. "
        "Call this after a consultation is complete to free memory and protect patient data."
    ),
    responses={
        204: {"description": "Session deleted successfully. No content returned."},
        404: _NOT_FOUND,
    },
)
async def delete_session_data(session_id: str) -> Response:
    existed = delete_session(session_id)
    if not existed:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")
    return Response(status_code=204)
