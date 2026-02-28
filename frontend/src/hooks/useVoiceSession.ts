import { useState, useRef } from 'react'

export function useVoiceSession() {
  const [isActive, setIsActive] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)

  function start() {
    wsRef.current = new WebSocket(`ws://localhost:8000/voice-session`)
    wsRef.current.onopen = () => setIsActive(true)
    wsRef.current.onclose = () => setIsActive(false)
    // TODO: wire up audio input/output
  }

  function stop() {
    wsRef.current?.close()
  }

  return { start, stop, isActive }
}
