import { useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import AppShell from '../components/layout/AppShell'
import Orb from '../components/ui/Orb'
import Avatar from '../components/ui/Avatar'
import Card from '../components/ui/Card'
import { useUploadChart } from '../hooks/useUploadChart'

const RECENT_PATIENTS = [
  { id: '#8492', name: 'John Smith', dept: 'Cardiology', updatedAgo: '2 min ago', initials: 'JS' },
  { id: '#7831', name: 'Maria Rodriguez', dept: 'Internal Med', updatedAgo: '15 min ago', initials: 'MR' },
  { id: '#9013', name: 'Alan Liu', dept: 'Pulmonology', updatedAgo: '1 hr ago', initials: 'AL' },
]

export default function HomePage() {
  const navigate = useNavigate()
  const { uploading, error, upload } = useUploadChart()
  const fileInputRef = useRef<HTMLInputElement>(null)
  const cameraInputRef = useRef<HTMLInputElement>(null)
  const [dragOver, setDragOver] = useState(false)

  async function handleFile(file: File | null) {
    if (!file) return
    const result = await upload(file)
    if (result) navigate(`/session/${result.session_id}`)
  }

  return (
    <AppShell activeTab="home">
      <div className="flex flex-col px-5 pt-12 pb-4 gap-6">
        {/* Header */}
        <header className="flex items-center justify-between">
          <button className="w-11 h-11 bg-white rounded-2xl flex items-center justify-center shadow-card border border-gray-100/60">
            <span className="material-symbols-outlined text-[22px] text-text-sub" style={{ fontVariationSettings: "'FILL' 0, 'wght' 300" }}>menu</span>
          </button>
          <span className="text-[11px] font-semibold uppercase tracking-[0.15em] text-primary/90">Medicore AI</span>
          <button className="w-11 h-11 bg-white rounded-2xl flex items-center justify-center shadow-card border border-gray-100/60">
            <span className="material-symbols-outlined text-[22px] text-text-sub" style={{ fontVariationSettings: "'FILL' 0, 'wght' 300" }}>notifications</span>
          </button>
        </header>

        {/* Hero Orb */}
        <section className="flex flex-col items-center gap-4 pt-2">
          <Orb variant="idle" size="lg" />
          <div className="text-center -mt-2">
            <h1 className="text-[28px] font-bold text-text-main leading-tight">New Consultation</h1>
            <p className="text-[15px] text-text-sub mt-1.5 font-medium leading-snug">
              I'm ready to assist with patient intake.
              <br />How should we begin?
            </p>
          </div>
        </section>

        {/* Upload error */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-600 text-sm px-4 py-3 rounded-2xl flex items-center gap-2">
            <span className="material-symbols-outlined text-[18px]">error</span>
            {error}
          </div>
        )}

        {/* Action cards */}
        <div className="grid grid-cols-2 gap-3">
          {/* Scan Chart */}
          <button
            onClick={() => cameraInputRef.current?.click()}
            disabled={uploading}
            className="h-[156px] bg-white rounded-3xl border border-gray-100/60 shadow-card flex flex-col items-center justify-center gap-3 transition-all duration-200 hover:-translate-y-0.5 hover:shadow-soft active:scale-[0.98] disabled:opacity-60"
          >
            <div className="w-14 h-14 bg-primary-soft rounded-2xl flex items-center justify-center">
              <span className="material-symbols-outlined text-[28px] text-primary" style={{ fontVariationSettings: "'FILL' 0, 'wght' 400" }}>qr_code_scanner</span>
            </div>
            <div className="text-center">
              <p className="text-[15px] font-semibold text-text-main">Scan Chart</p>
              <p className="text-[11px] font-medium uppercase tracking-widest text-text-sub mt-0.5">Camera</p>
            </div>
          </button>

          {/* Upload File */}
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={uploading}
            onDragOver={e => { e.preventDefault(); setDragOver(true) }}
            onDragLeave={() => setDragOver(false)}
            onDrop={e => { e.preventDefault(); setDragOver(false); handleFile(e.dataTransfer.files[0]) }}
            className={`h-[156px] bg-white rounded-3xl border shadow-card flex flex-col items-center justify-center gap-3 transition-all duration-200 hover:-translate-y-0.5 hover:shadow-soft active:scale-[0.98] disabled:opacity-60 ${dragOver ? 'border-primary/40 bg-primary-soft/30' : 'border-gray-100/60'}`}
          >
            {uploading ? (
              <div className="flex flex-col items-center gap-2">
                <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
                <p className="text-[13px] font-medium text-primary">Uploading…</p>
              </div>
            ) : (
              <>
                <div className="w-14 h-14 bg-primary-soft rounded-2xl flex items-center justify-center">
                  <span className="material-symbols-outlined text-[28px] text-primary" style={{ fontVariationSettings: "'FILL' 1, 'wght' 400" }}>upload_file</span>
                </div>
                <div className="text-center">
                  <p className="text-[15px] font-semibold text-text-main">Upload File</p>
                  <p className="text-[11px] font-medium uppercase tracking-widest text-text-sub mt-0.5">PDF / Image</p>
                </div>
              </>
            )}
          </button>
        </div>

        {/* Hidden file inputs */}
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,image/*"
          className="hidden"
          onChange={e => handleFile(e.target.files?.[0] ?? null)}
        />
        <input
          ref={cameraInputRef}
          type="file"
          accept="image/*"
          capture="environment"
          className="hidden"
          onChange={e => handleFile(e.target.files?.[0] ?? null)}
        />

        {/* Recent Patients */}
        <section>
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-[17px] font-bold text-text-main">Recent Patients</h2>
            <button className="text-[13px] font-semibold text-primary">View All</button>
          </div>

          <div className="flex gap-3 overflow-x-auto no-scrollbar pb-2 snap-x snap-mandatory">
            {RECENT_PATIENTS.map(patient => (
              <Card
                key={patient.id}
                className="min-w-[220px] flex-shrink-0 snap-start cursor-pointer hover:-translate-y-0.5 transition-transform duration-200"
              >
                <div className="flex items-center gap-3 mb-3">
                  <Avatar name={patient.name} size="md" />
                  <span className="bg-gray-50 text-text-sub text-[11px] font-semibold uppercase tracking-wider px-2.5 py-1 rounded-full">
                    ID {patient.id}
                  </span>
                </div>
                <p className="text-[16px] font-bold text-text-main leading-tight">{patient.name}</p>
                <p className="text-[13px] text-text-sub font-medium mt-0.5">{patient.dept}</p>
                <div className="flex items-center gap-1.5 mt-3 pt-3 border-t border-gray-100">
                  <span className="material-symbols-outlined text-[14px] text-text-sub" style={{ fontVariationSettings: "'FILL' 0, 'wght' 300" }}>schedule</span>
                  <span className="text-[12px] text-text-sub font-medium">Updated {patient.updatedAgo}</span>
                </div>
              </Card>
            ))}
          </div>
        </section>
      </div>
    </AppShell>
  )
}
