import { useState } from 'react'
import { uploadChart } from '../api/client'

export function useChartUpload() {
  const [isLoading, setIsLoading] = useState(false)

  async function upload(file: File) {
    setIsLoading(true)
    try {
      await uploadChart(file)
    } finally {
      setIsLoading(false)
    }
  }

  return { upload, isLoading }
}
