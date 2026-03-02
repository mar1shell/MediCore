from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.voice.session import run_voice_session

router = APIRouter()


@router.websocket("/voice-session")
async def voice_session(websocket: WebSocket):
    """Proxy a real-time ElevenLabs Conversational AI voice session."""
    await websocket.accept()
    try:
        await run_voice_session(websocket)
    except WebSocketDisconnect:
        pass
