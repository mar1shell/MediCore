import { useState, useCallback } from 'react'
import { uploadChart } from '../api/client'
import { useSession } from '../context/SessionContext'
import type { UploadChartResponse } from '../types'

interface UseUploadChart {
  uploading: boolean
  error: string | null
  upload: (file: File) => Promise<UploadChartResponse | null>
}

export function useUploadChart(): UseUploadChart {
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const { setSession } = useSession()

  const upload = useCallback(async (file: File): Promise<UploadChartResponse | null> => {
    setUploading(true)
    setError(null)
    try {
      const result = await uploadChart(file)
      setSession(result.session_id, result.entities)
      return result
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Upload failed'
      setError(msg)
      return null
    } finally {
      setUploading(false)
    }
  }, [setSession])

  return { uploading, error, upload }
}
