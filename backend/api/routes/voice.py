from fastapi import APIRouter, WebSocket

router = APIRouter()


@router.websocket("/voice-session")
async def voice_session(websocket: WebSocket):
    """Proxy WebSocket connection to ElevenLabs Conversational AI agent."""
    await websocket.accept()
    # TODO: call voice.agent.create_voice_session and proxy messages
    await websocket.close()
