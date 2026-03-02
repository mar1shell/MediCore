from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.voice.session import run_voice_session

router = APIRouter()


@router.websocket("/voice-session")
async def voice_session(websocket: WebSocket) -> None:
    """
    **Real-time ElevenLabs Conversational AI voice proxy.**

    Upgrades the connection to a bidirectional WebSocket that transparently proxies
    audio frames and control messages between the browser and ElevenLabs.

    The client should pass `session_id` as a dynamic variable when initialising the
    ElevenLabs conversation so the agent can include it in `check-safety` webhook calls.

    **Protocol:**
    - Send raw PCM/opus audio bytes → forwarded to ElevenLabs.
    - Receive bytes (audio) or text (JSON control messages) from ElevenLabs.
    - Close the connection to end the session.
    """
    await websocket.accept()
    try:
        await run_voice_session(websocket)
    except WebSocketDisconnect:
        pass
