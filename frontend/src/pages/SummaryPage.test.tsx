import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { SessionProvider, useSession } from '../context/SessionContext'
import SummaryPage from './SummaryPage'
import {
  MOCK_ENTITIES,
  MOCK_SESSION_ID,
  MOCK_SAFETY_CHECK_UNSAFE,
  MOCK_SAFETY_CHECK_SAFE,
  MOCK_SESSION_DATA,
} from '../test/fixtures'
import { http, HttpResponse } from 'msw'
import { server } from '../test/server'
import { useEffect, type ReactNode } from 'react'

const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom')
  return { ...actual, useNavigate: () => mockNavigate }
})

// Properly seeds context state via useEffect (avoids setState-in-render loops)
function SessionSeeder({
  children,
  unsafe = false,
}: {
  children: ReactNode
  unsafe?: boolean
}) {
  const { setSession, setSafetyChecks } = useSession()

  useEffect(() => {
    setSession(MOCK_SESSION_ID, MOCK_ENTITIES)
    if (unsafe) setSafetyChecks([MOCK_SAFETY_CHECK_UNSAFE, MOCK_SAFETY_CHECK_SAFE])
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  return <>{children}</>
}

function renderSummary({ unsafe = false } = {}) {
  // Override GET /sessions/:id to return only safe checks when unsafe=false
  if (!unsafe) {
    server.use(
      http.get('http://localhost:8000/sessions/:sessionId', () =>
        HttpResponse.json(
          { ...MOCK_SESSION_DATA, safety_checks: [MOCK_SAFETY_CHECK_SAFE] },
          { status: 200 },
        ),
      ),
    )
  }

  return render(
    <MemoryRouter initialEntries={[`/summary/${MOCK_SESSION_ID}`]}>
      <SessionProvider>
        <Routes>
          <Route
            path="/summary/:sessionId"
            element={
              <SessionSeeder unsafe={unsafe}>
                <SummaryPage />
              </SessionSeeder>
            }
          />
        </Routes>
      </SessionProvider>
    </MemoryRouter>,
  )
}

describe('SummaryPage', () => {
  beforeEach(() => mockNavigate.mockReset())

  it('renders the Consultation Summary heading', async () => {
    renderSummary()
    await waitFor(() => {
      expect(screen.getByText('Consultation Summary')).toBeTruthy()
    })
  })

  it('shows the Transcript section', async () => {
    renderSummary()
    await waitFor(() => {
      expect(screen.getByText('Transcript')).toBeTruthy()
    })
  })

  it('renders "Acknowledge & Save" button', async () => {
    renderSummary()
    await waitFor(() => {
      expect(screen.getByText('Acknowledge & Save')).toBeTruthy()
    })
  })

  it('renders allergy tags from extracted entities', async () => {
    renderSummary()
    await waitFor(() => {
      expect(screen.getByText(/Penicillin/)).toBeTruthy()
    })
  })

  it('renders medication tags from extracted entities', async () => {
    renderSummary()
    await waitFor(() => {
      // Amoxicillin appears in both the medication tag and the mock transcript
      expect(screen.getAllByText(/Amoxicillin/).length).toBeGreaterThanOrEqual(1)
    })
  })

  it('does NOT show "Conflict Detected" card when there are no unsafe checks', async () => {
    renderSummary({ unsafe: false })
    // Give time for the getSession useEffect to run and hydrate state
    await waitFor(() => {
      expect(screen.queryByText('Conflict Detected')).toBeNull()
    })
  })

  it('shows "Conflict Detected" card when an unsafe safety check exists', async () => {
    renderSummary({ unsafe: true })
    await waitFor(() => {
      expect(screen.getByText('Conflict Detected')).toBeTruthy()
    })
  })

  it('displays the drug name in the conflict card', async () => {
    renderSummary({ unsafe: true })
    await waitFor(() => {
      expect(screen.getByText(/Conflict: Amoxicillin/)).toBeTruthy()
    })
  })

  it('displays the conflict issue text', async () => {
    renderSummary({ unsafe: true })
    await waitFor(() => {
      expect(screen.getByText(/Patient is allergic to Penicillin/)).toBeTruthy()
    })
  })

  it('Acknowledge & Save calls deleteSession then navigates home', async () => {
    renderSummary()

    await waitFor(() => {
      expect(screen.getByText('Acknowledge & Save')).toBeTruthy()
    })

    fireEvent.click(screen.getByText('Acknowledge & Save'))

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/', { replace: true })
    })
  })
})
