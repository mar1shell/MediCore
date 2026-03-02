from fastapi import APIRouter, HTTPException, Response

from backend.session import get_session, delete_session
from backend.schemas.session import SessionDataResponse
from backend.schemas.chart import EntitiesSchema, MedicationSchema
from backend.schemas.common import ErrorResponse

router = APIRouter(prefix="/sessions", tags=["Sessions"])

_NOT_FOUND = {"model": ErrorResponse, "description": "No session found for the given ID."}


@router.get(
    "/{session_id}",
    response_model=SessionDataResponse,
    summary="Retrieve session data",
    description=(
        "Return the extracted clinical entities stored for a given session. "
        "Useful for the frontend to display the patient data associated with an active consultation "
        "without having to re-upload the chart."
    ),
    response_description="Session ID and its associated extracted entities.",
    responses={404: _NOT_FOUND},
)
async def get_session_data(session_id: str) -> SessionDataResponse:
    entities = get_session(session_id)
    if entities is None:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")

    return SessionDataResponse(
        session_id=session_id,
        entities=EntitiesSchema(
            source=entities.source,
            allergies=entities.allergies,
            medications=[
                MedicationSchema(name=m["name"], dose=m.get("dose"))
                for m in entities.medications
            ],
            diagnosis=entities.diagnosis,
            extraction_notes=entities.extraction_notes,
            diagrams=entities.diagrams,
        ),
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
