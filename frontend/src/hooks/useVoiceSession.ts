import { useRef, useState, useCallback, useEffect } from 'react'
import { getVoiceWsUrl, getSession } from '../api/client'
import { useSession } from '../context/SessionContext'

export interface UseVoiceSession {
  connected: boolean
  /** Non-null when the browser denied microphone access */
  micError: string | null
  connect: () => void
  disconnect: () => void
}

const POLL_INTERVAL_MS = 3000
/** ElevenLabs Conversational AI expects PCM at 16 kHz */
const SAMPLE_RATE = 16_000
/** ScriptProcessorNode buffer — ~256 ms @ 16 kHz */
const BUFFER_SIZE = 4096

// ── helpers ───────────────────────────────────────────────────────────────────

function safeClose(ws: WebSocket | null): void {
  if (!ws) return
  ws.onopen = null
  ws.onclose = null
  ws.onerror = null
  ws.onmessage = null
  if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CLOSING) {
    ws.close()
  }
}

function float32ToPcm16Base64(float32: Float32Array): string {
  const pcm = new Int16Array(float32.length)
  for (let i = 0; i < float32.length; i++) {
    pcm[i] = Math.max(-32768, Math.min(32767, Math.round(float32[i] * 32768)))
  }
  // Convert raw bytes to base64 — ElevenLabs expects JSON {"user_audio_chunk":"<b64>"}
  const bytes = new Uint8Array(pcm.buffer)
  let binary = ''
  for (let i = 0; i < bytes.byteLength; i++) binary += String.fromCharCode(bytes[i])
  return btoa(binary)
}

function base64ToPcm16Float32(b64: string): Float32Array {
  const binary = atob(b64)
  const bytes = new Uint8Array(binary.length)
  for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i)
  const int16 = new Int16Array(bytes.buffer)
  const float32 = new Float32Array(int16.length)
  for (let i = 0; i < int16.length; i++) float32[i] = int16[i] / 32768
  return float32
}

// ── hook ──────────────────────────────────────────────────────────────────────

export function useVoiceSession(): UseVoiceSession {
  const wsRef = useRef<WebSocket | null>(null)
  const audioCtxRef = useRef<AudioContext | null>(null)
  const streamRef = useRef<MediaStream | null>(null)
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const processorRef = useRef<any>(null) // ScriptProcessorNode (deprecated but universal)
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)
  /** Used to schedule back-to-back TTS audio chunks without gaps */
  const nextPlayAtRef = useRef(0)
  /** Cancellation flag — set by cleanup so an in-flight getUserMedia resolves cleanly */
  const cancelledRef = useRef(false)

  const [connected, setConnected] = useState(false)
  const [micError, setMicError] = useState<string | null>(null)

  const { sessionId, setSafetyChecks } = useSession()

  // ── polling ─────────────────────────────────────────────────────────────────

  const stopPolling = useCallback(() => {
    if (pollRef.current) {
      clearInterval(pollRef.current)
      pollRef.current = null
    }
  }, [])

  const startPolling = useCallback(() => {
    if (!sessionId) return
    pollRef.current = setInterval(async () => {
      try {
        const data = await getSession(sessionId)
        setSafetyChecks(data.safety_checks)
      } catch {
        // silently ignore transient errors
      }
    }, POLL_INTERVAL_MS)
  }, [sessionId, setSafetyChecks])

  // ── audio teardown ──────────────────────────────────────────────────────────

  const stopAudio = useCallback(() => {
    if (processorRef.current) {
      processorRef.current.disconnect()
      processorRef.current = null
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(t => t.stop())
      streamRef.current = null
    }
    if (audioCtxRef.current) {
      audioCtxRef.current.close().catch(() => {})
      audioCtxRef.current = null
    }
  }, [])

  // ── playback helper ─────────────────────────────────────────────────────────

  /**
   * Schedule a base64-encoded PCM 16 kHz audio chunk for sequential playback.
   * Uses AudioContext.currentTime scheduling so back-to-back chunks play
   * smoothly without gaps or overlaps.
   */
  const playAudioChunk = useCallback((base64: string) => {
    const ctx = audioCtxRef.current
    if (!ctx) return

    const float32 = base64ToPcm16Float32(base64)
    const buffer = ctx.createBuffer(1, float32.length, SAMPLE_RATE)
    buffer.getChannelData(0).set(float32)

    const src = ctx.createBufferSource()
    src.buffer = buffer
    src.connect(ctx.destination)

    const startAt = Math.max(ctx.currentTime, nextPlayAtRef.current)
    src.start(startAt)
    nextPlayAtRef.current = startAt + buffer.duration
  }, [])

  // ── connect ─────────────────────────────────────────────────────────────────

  const connect = useCallback(async () => {
    if (wsRef.current) return
    cancelledRef.current = false
    setMicError(null)

    // 1. Request microphone permission (triggers the browser permission dialog).
    //    echoCancellation prevents the mic from picking up ElevenLabs' speaker
    //    output and sending it back, which would cause the AI voice to repeat.
    let stream: MediaStream
    try {
      stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
        video: false,
      })
    } catch (err) {
      if (!cancelledRef.current) {
        setMicError(
          err instanceof Error
            ? err.message
            : 'Microphone access denied. Please allow mic access and try again.',
        )
      }
      return
    }

    // Component may have unmounted while we awaited getUserMedia
    if (cancelledRef.current) {
      stream.getTracks().forEach(t => t.stop())
      return
    }

    streamRef.current = stream

    // 2. AudioContext (capture at ElevenLabs' required sample rate so we avoid
    //    manual resampling)
    const ctx = new AudioContext({ sampleRate: SAMPLE_RATE })
    audioCtxRef.current = ctx
    nextPlayAtRef.current = 0

    // 3. Open WebSocket proxy
    const ws = new WebSocket(getVoiceWsUrl())
    ws.binaryType = 'arraybuffer'
    wsRef.current = ws

    // 4. Wire up WebSocket handlers
    ws.onopen = () => {
      // Send session_id as a dynamic variable FIRST, before any audio.
      // ElevenLabs requires this so its tools (e.g. check-safety webhook) can
      // reference the session. Without it the conversation fails immediately
      // with "Missing required dynamic variables in tools: {session_id}".
      if (sessionId) {
        ws.send(JSON.stringify({
          type: 'conversation_initiation_client_data',
          dynamic_variables: { session_id: sessionId },
        }))
      }

      setConnected(true)
      startPolling()

      // 5. Start mic capture: float32 → PCM-16 base64 JSON frame
      const source = ctx.createMediaStreamSource(stream)
      // ScriptProcessorNode is deprecated but has universal browser support;
      // upgrade to AudioWorklet when browser support is more uniform.
      const processor = ctx.createScriptProcessor(BUFFER_SIZE, 1, 1)
      processorRef.current = processor

      processor.onaudioprocess = (e: AudioProcessingEvent) => {
        if (ws.readyState !== WebSocket.OPEN) return
        // ElevenLabs Conversational AI requires JSON text frames, not binary:
        // {"user_audio_chunk": "<base64_pcm_16kHz_16bit_mono>"}
        const b64 = float32ToPcm16Base64(e.inputBuffer.getChannelData(0))
        ws.send(JSON.stringify({ user_audio_chunk: b64 }))
      }

      source.connect(processor)
      // ScriptProcessorNode must be connected downstream to fire, but we must
      // NOT route mic audio to the speakers — that would feed ElevenLabs' own
      // voice back into the session and cause it to repeat itself.
      // Route through a muted gain node so the processor fires silently.
      const silentSink = ctx.createGain()
      silentSink.gain.value = 0
      processor.connect(silentSink)
      silentSink.connect(ctx.destination)
    }

    ws.onmessage = (event: MessageEvent) => {
      // Binary frames are raw audio from ElevenLabs in some legacy paths — skip
      if (event.data instanceof ArrayBuffer) return

      try {
        // All ElevenLabs Conversational AI v1 messages are JSON text frames
        const msg = JSON.parse(event.data as string) as {
          type: string
          audio_event?: { audio_base_64: string }
          ping_event?: { event_id: number }
        }

        switch (msg.type) {
          case 'audio':
            if (msg.audio_event?.audio_base_64) {
              playAudioChunk(msg.audio_event.audio_base_64)
            }
            break

          case 'ping':
            // ElevenLabs requires a pong to keep the session alive
            ws.send(JSON.stringify({ type: 'pong', event_id: msg.ping_event?.event_id }))
            break

          // conversation_initiation_metadata, agent_response, user_transcript,
          // interruption — logged for future use (transcript display, etc.)
          default:
            break
        }
      } catch {
        // ignore unparseable frames
      }
    }

    ws.onclose = () => {
      setConnected(false)
      stopPolling()
      stopAudio()
      wsRef.current = null
    }

    ws.onerror = () => {
      setConnected(false)
      stopPolling()
    }
  }, [startPolling, stopPolling, stopAudio, playAudioChunk])

  // ── disconnect ──────────────────────────────────────────────────────────────

  const disconnect = useCallback(() => {
    cancelledRef.current = true
    safeClose(wsRef.current)
    wsRef.current = null
    stopPolling()
    stopAudio()
    setConnected(false)
  }, [stopPolling, stopAudio])

  // ── cleanup on unmount ──────────────────────────────────────────────────────

  useEffect(() => {
    cancelledRef.current = false
    return () => {
      cancelledRef.current = true
      safeClose(wsRef.current)
      wsRef.current = null
      stopPolling()
      stopAudio()
    }
  }, [stopPolling, stopAudio])

  return { connected, micError, connect, disconnect }
}
