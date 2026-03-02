import { describe, it, expect } from 'vitest'
import { http, HttpResponse } from 'msw'
import { server } from '../test/server'
import { uploadChart, getSession, deleteSession, getVoiceWsUrl } from './client'
import {
  MOCK_SESSION_ID,
} from '../test/fixtures'

const BASE = 'http://localhost:8000'

// client.ts reads VITE_API_URL from import.meta.env — in tests that env var is
// undefined so it falls back to http://localhost:8000, which matches our MSW handlers.

describe('uploadChart', () => {
  it('posts form data and returns UploadChartResponse', async () => {
    const file = new File(['pdf-content'], 'chart.pdf', { type: 'application/pdf' })
    const result = await uploadChart(file)

    expect(result.session_id).toBe(MOCK_SESSION_ID)
    expect(result.filename).toBe('test-chart.pdf')
    expect(result.pages_processed).toBe(1)
    expect(result.entities.allergies).toContain('Penicillin')
  })

  it('throws an error when the server responds with 415', async () => {
    server.use(
      http.post(`${BASE}/upload-chart`, () =>
        HttpResponse.json({ detail: 'Unsupported file type' }, { status: 415 }),
      ),
    )

    const file = new File(['content'], 'chart.docx', { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' })
    await expect(uploadChart(file)).rejects.toThrow('Unsupported file type')
  })

  it('throws an error when the server responds with 500', async () => {
    server.use(
      http.post(`${BASE}/upload-chart`, () =>
        HttpResponse.json({ detail: 'OCR processing failed' }, { status: 500 }),
      ),
    )

    const file = new File(['content'], 'chart.pdf', { type: 'application/pdf' })
    await expect(uploadChart(file)).rejects.toThrow('OCR processing failed')
  })
})

describe('getSession', () => {
  it('fetches and returns SessionData', async () => {
    const data = await getSession(MOCK_SESSION_ID)

    expect(data.session_id).toBe(MOCK_SESSION_ID)
    expect(data.entities.medications).toHaveLength(2)
    expect(data.safety_checks).toHaveLength(2)
    expect(data.safety_checks[0].is_safe).toBe(false)
    expect(data.safety_checks[1].is_safe).toBe(true)
  })

  it('throws when session is not found (404)', async () => {
    server.use(
      http.get(`${BASE}/sessions/:id`, () =>
        HttpResponse.json({ detail: 'Session not found' }, { status: 404 }),
      ),
    )
    await expect(getSession('does-not-exist')).rejects.toThrow('Session not found')
  })
})

describe('deleteSession', () => {
  it('resolves without error on 204', async () => {
    await expect(deleteSession(MOCK_SESSION_ID)).resolves.toBeUndefined()
  })

  it('silently resolves on 404 (already deleted)', async () => {
    server.use(
      http.delete(`${BASE}/sessions/:id`, () =>
        HttpResponse.json({ detail: 'Session not found' }, { status: 404 }),
      ),
    )
    await expect(deleteSession(MOCK_SESSION_ID)).resolves.toBeUndefined()
  })

  it('throws on unexpected server errors', async () => {
    server.use(
      http.delete(`${BASE}/sessions/:id`, () =>
        HttpResponse.json({ detail: 'Internal server error' }, { status: 500 }),
      ),
    )
    await expect(deleteSession(MOCK_SESSION_ID)).rejects.toThrow('Internal server error')
  })
})

describe('getVoiceWsUrl', () => {
  it('returns a ws:// URL derived from the base URL', () => {
    const url = getVoiceWsUrl()
    expect(url).toMatch(/^ws:\/\//)
    expect(url).toContain('/voice-session')
  })
})
