import { useChartUpload } from '../../hooks/useChartUpload'

export default function ChartUpload() {
  const { upload, isLoading } = useChartUpload()

  return (
    <div>
      <h2>Upload Chart</h2>
      {/* TODO: drag-drop PDF upload UI */}
      <input type="file" accept=".pdf" onChange={(e) => e.target.files && upload(e.target.files[0])} />
      {isLoading && <p>Processing...</p>}
    </div>
  )
}
