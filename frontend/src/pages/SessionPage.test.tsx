import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { SessionProvider } from '../context/SessionContext'
import SessionPage from './SessionPage'
import { MOCK_SESSION_ID } from '../test/fixtures'

const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom')
  return { ...actual, useNavigate: () => mockNavigate }
})

// Stub WebSocket, getUserMedia, and AudioContext so tests don't open real connections
class FakeWS {
  static readonly OPEN = 1
  static readonly CLOSING = 2
  static readonly CLOSED = 3
  readyState = 1
  onopen: (() => void) | null = null
  onclose: (() => void) | null = null
  onerror: (() => void) | null = null
  onmessage: (() => void) | null = null
  binaryType = ''
  send = vi.fn()
  close() { this.onclose?.() }
}
vi.stubGlobal('WebSocket', FakeWS)

const fakeStream = { getTracks: () => [{ stop: vi.fn() }] } as unknown as MediaStream
Object.defineProperty(globalThis.navigator, 'mediaDevices', {
  writable: true,
  configurable: true,
  value: { getUserMedia: vi.fn().mockResolvedValue(fakeStream) },
})

class FakeAudioContext {
  currentTime = 0
  destination = {}
  createScriptProcessor() { return { connect: vi.fn(), disconnect: vi.fn(), onaudioprocess: null } }
  createMediaStreamSource() { return { connect: vi.fn() } }
  close = vi.fn().mockResolvedValue(undefined)
}
vi.stubGlobal('AudioContext', FakeAudioContext)

function renderSession() {
  return render(
    <MemoryRouter initialEntries={[`/session/${MOCK_SESSION_ID}`]}>
      <SessionProvider>
        <Routes>
          <Route path="/session/:sessionId" element={<SessionPage />} />
        </Routes>
      </SessionProvider>
    </MemoryRouter>,
  )
}

describe('SessionPage', () => {
  beforeEach(() => {
    mockNavigate.mockReset()
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('renders session ID fragment in the header', () => {
    renderSession()
    const shortId = MOCK_SESSION_ID.slice(0, 4).toUpperCase()
    expect(screen.getByText(`Session #${shortId}`)).toBeTruthy()
  })

  it('renders "Connecting…" initially (getUserMedia has not resolved yet)', () => {
    renderSession()
    expect(screen.getByText('Connecting…')).toBeTruthy()
  })

  it('renders the "End Session" button when no alert is present', () => {
    renderSession()
    expect(screen.getByText('End Session')).toBeTruthy()
  })

  it('clicking End Session navigates to /analyzing/:id', () => {
    renderSession()
    fireEvent.click(screen.getByText('End Session'))
    expect(mockNavigate).toHaveBeenCalledWith(`/analyzing/${MOCK_SESSION_ID}`)
  })

  it('renders "Medicore AI" brand label', () => {
    renderSession()
    expect(screen.getByText('Medicore AI')).toBeTruthy()
  })
})
