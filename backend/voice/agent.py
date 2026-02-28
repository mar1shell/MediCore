import os
from elevenlabs import ElevenLabs


def create_voice_session(chart_context: dict):
    """Initialize an ElevenLabs Conversational AI session grounded with chart context."""
    client = ElevenLabs(api_key=os.environ["ELEVENLABS_API_KEY"])
    agent_id = os.environ["ELEVENLABS_AGENT_ID"]
    # TODO: implement session setup
    raise NotImplementedError
