import type { UploadChartResponse, SessionData } from '../types'

const BASE = (import.meta.env.VITE_API_URL as string | undefined) ?? 'http://localhost:8000'

// ── Helpers ───────────────────────────────────────────────────────────────────

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error((body as { detail?: string }).detail ?? res.statusText)
  }
  return res.json() as Promise<T>
}

// ── Chart ─────────────────────────────────────────────────────────────────────

export async function uploadChart(file: File): Promise<UploadChartResponse> {
  const form = new FormData()
  form.append('file', file)
  const res = await fetch(`${BASE}/upload-chart`, { method: 'POST', body: form })
  return handleResponse<UploadChartResponse>(res)
}

// ── Sessions ──────────────────────────────────────────────────────────────────

export async function getSession(sessionId: string): Promise<SessionData> {
  const res = await fetch(`${BASE}/sessions/${sessionId}`)
  return handleResponse<SessionData>(res)
}

export async function deleteSession(sessionId: string): Promise<void> {
  const res = await fetch(`${BASE}/sessions/${sessionId}`, { method: 'DELETE' })
  if (!res.ok && res.status !== 404) {
    const body = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error((body as { detail?: string }).detail ?? res.statusText)
  }
}

// ── Voice WebSocket ───────────────────────────────────────────────────────────

export function getVoiceWsUrl(): string {
  return `${BASE.replace(/^http/, 'ws')}/voice-session`
}
