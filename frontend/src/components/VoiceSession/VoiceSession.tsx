import { useVoiceSession } from '../../hooks/useVoiceSession'

export default function VoiceSession() {
  const { start, stop, isActive } = useVoiceSession()

  return (
    <div>
      <h2>Voice Session</h2>
      {/* TODO: ElevenLabs WebSocket session UI */}
      <button onClick={isActive ? stop : start}>
        {isActive ? 'End Session' : 'Start Session'}
      </button>
    </div>
  )
}
