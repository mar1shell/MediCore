import { describe, it, expect, vi, beforeEach } from 'vitest'
import { screen, fireEvent, waitFor } from '@testing-library/react'
import { renderWithProviders } from '../test/utils'
import HomePage from './HomePage'
import { MOCK_SESSION_ID } from '../test/fixtures'

// Capture navigation calls
const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom')
  return { ...actual, useNavigate: () => mockNavigate }
})

describe('HomePage', () => {
  beforeEach(() => mockNavigate.mockReset())

  it('renders the page heading', () => {
    renderWithProviders(<HomePage />)
    expect(screen.getByText('New Consultation')).toBeTruthy()
  })

  it('renders the Medicore AI brand label', () => {
    renderWithProviders(<HomePage />)
    expect(screen.getByText('Medicore AI')).toBeTruthy()
  })

  it('renders the Scan Chart and Upload File action cards', () => {
    renderWithProviders(<HomePage />)
    expect(screen.getByText('Scan Chart')).toBeTruthy()
    expect(screen.getByText('Upload File')).toBeTruthy()
  })

  it('renders recent patients list', () => {
    renderWithProviders(<HomePage />)
    expect(screen.getByText('Recent Patients')).toBeTruthy()
    expect(screen.getByText('John Smith')).toBeTruthy()
    expect(screen.getByText('Maria Rodriguez')).toBeTruthy()
    expect(screen.getByText('Alan Liu')).toBeTruthy()
  })

  it('shows uploading spinner while a file upload is in progress', async () => {
    // Block the upload request so the loading state persists long enough to assert
    let resolveUpload!: () => void
    const { http, HttpResponse } = await import('msw')
    const { server } = await import('../test/server')

    server.use(
      http.post('http://localhost:8000/upload-chart', () =>
        new Promise<Response>(resolve => {
          resolveUpload = () => resolve(HttpResponse.json({}) as unknown as Response)
        }),
      ),
    )

    renderWithProviders(<HomePage />)

    const file = new File(['pdf'], 'test.pdf', { type: 'application/pdf' })
    const input = document.querySelector<HTMLInputElement>('input[type="file"]:not([capture])')!

    fireEvent.change(input, { target: { files: [file] } })

    await waitFor(() => {
      expect(screen.getByText('Uploading…')).toBeTruthy()
    })

    resolveUpload()
  })

  it('shows error banner when upload fails', async () => {
    const { http, HttpResponse } = await import('msw')
    const { server } = await import('../test/server')

    server.use(
      http.post('http://localhost:8000/upload-chart', () =>
        HttpResponse.json({ detail: 'Upload failed' }, { status: 500 }),
      ),
    )

    renderWithProviders(<HomePage />)

    const file = new File(['pdf'], 'test.pdf', { type: 'application/pdf' })
    const input = document.querySelector<HTMLInputElement>('input[type="file"]:not([capture])')!

    fireEvent.change(input, { target: { files: [file] } })

    await waitFor(() => {
      expect(screen.getByText('Upload failed')).toBeTruthy()
    })
  })

  it('navigates to /session/:id after successful upload', async () => {
    renderWithProviders(<HomePage />)

    const file = new File(['pdf'], 'test.pdf', { type: 'application/pdf' })
    const input = document.querySelector<HTMLInputElement>('input[type="file"]:not([capture])')!

    fireEvent.change(input, { target: { files: [file] } })

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith(`/session/${MOCK_SESSION_ID}`)
    })
  })
})
