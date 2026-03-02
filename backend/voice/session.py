"""Voice — ElevenLabs Conversational AI WebSocket proxy.

Bridges the browser WebSocket (FastAPI) to the ElevenLabs agent WebSocket,
forwarding audio frames and control messages in both directions.
"""

from __future__ import annotations

import asyncio

import websockets
from fastapi import WebSocket

from backend.config import get_settings

ELEVENLABS_WS_URL = (
    "wss://api.elevenlabs.io/v1/convai/conversation?agent_id={agent_id}"
)


async def run_voice_session(client_ws: WebSocket) -> None:
    """Proxy audio between the browser and ElevenLabs in real time.

    Uses asyncio.wait(FIRST_COMPLETED) so that whichever side closes first
    (browser disconnect or ElevenLabs disconnect) immediately cancels the other
    direction and exits the `async with` block, which sends a proper WebSocket
    close frame to ElevenLabs and ends the agent session immediately.
    """
    settings = get_settings()
    url = ELEVENLABS_WS_URL.format(agent_id=settings.elevenlabs_agent_id)
    headers = {"xi-api-key": settings.elevenlabs_api_key}

    async with websockets.connect(url, additional_headers=headers) as el_ws:
        forward_task = asyncio.create_task(_forward(client_ws, el_ws))
        backward_task = asyncio.create_task(_backward(el_ws, client_ws))

        # Block until either side finishes (browser disconnects or ElevenLabs ends)
        _done, pending = await asyncio.wait(
            [forward_task, backward_task],
            return_when=asyncio.FIRST_COMPLETED,
        )

        # Cancel the still-running direction so we exit the context manager
        # immediately instead of waiting for ElevenLabs to time out.
        for task in pending:
            task.cancel()
        await asyncio.gather(*pending, return_exceptions=True)

    # `async with` exit → websockets sends a close frame to ElevenLabs ✓


async def _forward(client_ws: WebSocket, el_ws: websockets.WebSocketClientProtocol) -> None:
    """Browser → ElevenLabs.

    Handles both binary frames (raw PCM audio) and text frames (JSON control
    messages such as pong replies to ElevenLabs ping events).
    """
    while True:
        try:
            data = await client_ws.receive()
        except Exception:
            break

        msg_type = data.get("type")
        if msg_type == "websocket.disconnect":
            break

        raw_bytes: bytes | None = data.get("bytes")
        raw_text: str | None = data.get("text")

        if raw_bytes:
            await el_ws.send(raw_bytes)
        elif raw_text:
            await el_ws.send(raw_text)


async def _backward(el_ws: websockets.WebSocketClientProtocol, client_ws: WebSocket) -> None:
    """ElevenLabs → Browser."""
    async for message in el_ws:
        if isinstance(message, bytes):
            await client_ws.send_bytes(message)
        else:
            await client_ws.send_text(message)
