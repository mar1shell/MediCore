import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useVoiceSession } from './useVoiceSession'
import { SessionProvider } from '../context/SessionContext'
import type { ReactNode } from 'react'

// ── MediaDevices stub ─────────────────────────────────────────────────────────

function makeFakeStream(): MediaStream {
  const track = { stop: vi.fn(), kind: 'audio' } as unknown as MediaStreamTrack
  return {
    getTracks: () => [track],
    getAudioTracks: () => [track],
  } as unknown as MediaStream
}

function stubGetUserMedia(stream: MediaStream | Error) {
  Object.defineProperty(globalThis.navigator, 'mediaDevices', {
    writable: true,
    configurable: true,
    value: {
      getUserMedia: vi.fn().mockImplementation(() =>
        stream instanceof Error ? Promise.reject(stream) : Promise.resolve(stream),
      ),
    },
  })
}

// ── AudioContext stub ─────────────────────────────────────────────────────────

class MockScriptProcessor {
  onaudioprocess: ((e: AudioProcessingEvent) => void) | null = null
  disconnect = vi.fn()
  connect = vi.fn()
}

class MockMediaStreamSource {
  connect = vi.fn()
}

class MockAudioContext {
  currentTime = 0
  destination = {}

  createScriptProcessor() { return new MockScriptProcessor() }
  createMediaStreamSource() { return new MockMediaStreamSource() }
  createBuffer(_channels: number, length: number, sampleRate: number) {
    return { getChannelData: () => new Float32Array(length), duration: length / sampleRate }
  }
  createBufferSource() {
    return { connect: vi.fn(), start: vi.fn(), buffer: null, onended: null }
  }
  close = vi.fn().mockResolvedValue(undefined)
}

// ── WebSocket stub ────────────────────────────────────────────────────────────

class MockWebSocket {
  static readonly OPEN = 1
  static readonly CLOSING = 2
  static readonly CLOSED = 3

  readyState = 1
  binaryType = ''

  onopen: (() => void) | null = null
  onclose: (() => void) | null = null
  onerror: (() => void) | null = null
  onmessage: ((e: MessageEvent) => void) | null = null

  url: string
  send = vi.fn()
  close = vi.fn().mockImplementation(() => { this.onclose?.() })

  constructor(url: string) {
    this.url = url
    MockWebSocket.instances.push(this)
  }

  open() { this.onopen?.() }

  static instances: MockWebSocket[] = []
  static reset() { MockWebSocket.instances = [] }
}

function wrapper({ children }: { children: ReactNode }) {
  return <SessionProvider>{children}</SessionProvider>
}

describe('useVoiceSession', () => {
  beforeEach(() => {
    MockWebSocket.reset()
    vi.stubGlobal('WebSocket', MockWebSocket)
    vi.stubGlobal('AudioContext', MockAudioContext)
    vi.useFakeTimers()
    stubGetUserMedia(makeFakeStream())
  })

  afterEach(() => {
    vi.restoreAllMocks()
    vi.useRealTimers()
  })

  it('starts disconnected with no mic error', () => {
    const { result } = renderHook(() => useVoiceSession(), { wrapper })
    expect(result.current.connected).toBe(false)
    expect(result.current.micError).toBeNull()
  })

  it('becomes connected after mic permission is granted and WebSocket opens', async () => {
    const { result } = renderHook(() => useVoiceSession(), { wrapper })

    await act(async () => {
      result.current.connect()
      await Promise.resolve()
      await Promise.resolve()
    })

    act(() => { MockWebSocket.instances[0]?.open() })
    expect(result.current.connected).toBe(true)
  })

  it('sets micError when mic permission is denied', async () => {
    stubGetUserMedia(new Error('Permission denied'))

    const { result } = renderHook(() => useVoiceSession(), { wrapper })

    await act(async () => {
      result.current.connect()
      await Promise.resolve()
      await Promise.resolve()
    })

    expect(result.current.micError).toMatch(/Permission denied/i)
    expect(result.current.connected).toBe(false)
    expect(MockWebSocket.instances).toHaveLength(0)
  })

  it('does not create a second WS if already connected', async () => {
    const { result } = renderHook(() => useVoiceSession(), { wrapper })

    await act(async () => {
      result.current.connect()
      await Promise.resolve()
      await Promise.resolve()
    })

    await act(async () => {
      result.current.connect()
      await Promise.resolve()
    })

    expect(MockWebSocket.instances).toHaveLength(1)
  })

  it('disconnect() closes the socket and sets connected=false', async () => {
    const { result } = renderHook(() => useVoiceSession(), { wrapper })

    await act(async () => {
      result.current.connect()
      await Promise.resolve()
      await Promise.resolve()
    })

    act(() => { MockWebSocket.instances[0]?.open() })
    expect(result.current.connected).toBe(true)

    act(() => { result.current.disconnect() })
    expect(result.current.connected).toBe(false)
  })

  it('becomes disconnected when WebSocket closes', async () => {
    const { result } = renderHook(() => useVoiceSession(), { wrapper })

    await act(async () => {
      result.current.connect()
      await Promise.resolve()
      await Promise.resolve()
    })

    act(() => { MockWebSocket.instances[0]?.open() })
    act(() => { MockWebSocket.instances[0]?.close() })
    expect(result.current.connected).toBe(false)
  })

  it('becomes disconnected on WebSocket error', async () => {
    const { result } = renderHook(() => useVoiceSession(), { wrapper })

    await act(async () => {
      result.current.connect()
      await Promise.resolve()
      await Promise.resolve()
    })

    act(() => { MockWebSocket.instances[0]?.onerror?.() })
    expect(result.current.connected).toBe(false)
  })
})
