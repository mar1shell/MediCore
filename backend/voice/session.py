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
    """Proxy audio between the browser and ElevenLabs in real time."""
    settings = get_settings()
    url = ELEVENLABS_WS_URL.format(agent_id=settings.elevenlabs_agent_id)

    headers = {"xi-api-key": settings.elevenlabs_api_key}

    async with websockets.connect(url, additional_headers=headers) as el_ws:
        await asyncio.gather(
            _forward(client_ws, el_ws),
            _backward(el_ws, client_ws),
        )


async def _forward(client_ws: WebSocket, el_ws: websockets.WebSocketClientProtocol) -> None:
    """Browser → ElevenLabs."""
    async for message in client_ws.iter_bytes():
        await el_ws.send(message)


async def _backward(el_ws: websockets.WebSocketClientProtocol, client_ws: WebSocket) -> None:
    """ElevenLabs → Browser."""
    async for message in el_ws:
        if isinstance(message, bytes):
            await client_ws.send_bytes(message)
        else:
            await client_ws.send_text(message)
