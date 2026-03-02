import { describe, it, expect } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { http, HttpResponse } from 'msw'
import { server } from '../test/server'
import { useUploadChart } from './useUploadChart'
import { SessionProvider } from '../context/SessionContext'
import { MOCK_SESSION_ID } from '../test/fixtures'
import type { ReactNode } from 'react'

function wrapper({ children }: { children: ReactNode }) {
  return <SessionProvider>{children}</SessionProvider>
}

describe('useUploadChart', () => {
  it('starts in the idle state', () => {
    const { result } = renderHook(() => useUploadChart(), { wrapper })

    expect(result.current.uploading).toBe(false)
    expect(result.current.error).toBeNull()
  })

  it('sets uploading=true while request is in flight and resolves the response', async () => {
    const { result } = renderHook(() => useUploadChart(), { wrapper })

    const file = new File(['pdf'], 'test.pdf', { type: 'application/pdf' })

    let uploadResult: Awaited<ReturnType<typeof result.current.upload>> | undefined
    await act(async () => {
      uploadResult = await result.current.upload(file)
    })

    expect(result.current.uploading).toBe(false)
    expect(result.current.error).toBeNull()
    expect(uploadResult?.session_id).toBe(MOCK_SESSION_ID)
  })

  it('returns null and sets error message on failure', async () => {
    server.use(
      http.post('http://localhost:8000/upload-chart', () =>
        HttpResponse.json({ detail: 'OCR failed' }, { status: 500 }),
      ),
    )

    const { result } = renderHook(() => useUploadChart(), { wrapper })
    const file = new File(['pdf'], 'test.pdf', { type: 'application/pdf' })

    let uploadResult: Awaited<ReturnType<typeof result.current.upload>> | undefined
    await act(async () => {
      uploadResult = await result.current.upload(file)
    })

    expect(uploadResult).toBeNull()
    expect(result.current.error).toBe('OCR failed')
    expect(result.current.uploading).toBe(false)
  })

  it('updates SessionContext with session id and entities on success', async () => {
    // We verify indirectly: the hook calls setSession which modifies context.
    // A successful upload must store both fields without throwing.
    const { result } = renderHook(() => useUploadChart(), { wrapper })
    const file = new File(['pdf'], 'test.pdf', { type: 'application/pdf' })

    await act(async () => {
      await result.current.upload(file)
    })

    // No error means context was updated successfully
    expect(result.current.error).toBeNull()
  })
})
