import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import AppShell from '../components/layout/AppShell'
import Orb from '../components/ui/Orb'
import Avatar from '../components/ui/Avatar'
import Badge from '../components/ui/Badge'
import Button from '../components/ui/Button'
import Card from '../components/ui/Card'
import { useSession } from '../context/SessionContext'
import { deleteSession, getSession } from '../api/client'
import type { SafetyCheckRecord } from '../types'

function getPatientId(sessionId: string): string {
  return `#${sessionId.replace(/-/g, '').slice(0, 4).toUpperCase()}-MED`
}

export default function SummaryPage() {
  const { sessionId } = useParams<{ sessionId: string }>()
  const navigate = useNavigate()
  const { entities, safetyChecks, transcript, setSafetyChecks, clearSession } = useSession()
  const [saving, setSaving] = useState(false)

  // Fetch latest session data (in case we navigated here from analyzing without real-time state)
  useEffect(() => {
    if (!sessionId) return
    getSession(sessionId)
      .then(data => setSafetyChecks(data.safety_checks))
      .catch(() => {})
  }, [sessionId, setSafetyChecks])

  const unsafeChecks: SafetyCheckRecord[] = safetyChecks.filter(sc => !sc.is_safe)
  const hasConflict = unsafeChecks.length > 0
  const primaryConflict = unsafeChecks[0]

  const patientName = entities?.patient_name ?? null
  const diagnosis = entities?.diagnosis ?? null
  const allergies = entities?.allergies ?? []
  const medications = entities?.medications ?? []

  async function handleAcknowledge() {
    if (!sessionId) return
    setSaving(true)
    try {
      await deleteSession(sessionId)
    } catch {
      // Continue even if delete fails
    } finally {
      clearSession()
      setSaving(false)
      navigate('/', { replace: true })
    }
  }

  return (
    <AppShell activeTab="home">
      {/* Header */}
      <header className="flex items-center justify-between px-5 pt-6 pb-4">
        <button
          onClick={() => navigate(-1)}
          className="w-10 h-10 flex items-center justify-center rounded-xl hover:bg-gray-100 transition-colors"
        >
          <span className="material-symbols-outlined text-[22px] text-text-sub">arrow_back_ios</span>
        </button>

        {/* Small orb in header */}
        <div className="flex flex-col items-center gap-0.5">
          <Orb variant="idle" size="sm" />
          <h1 className="text-[15px] font-bold text-text-main">Consultation Summary</h1>
        </div>

        <button className="w-10 h-10 flex items-center justify-center rounded-xl hover:bg-gray-100 transition-colors">
          <span className="material-symbols-outlined text-[22px] text-text-sub">more_horiz</span>
        </button>
      </header>

      <div className="flex flex-col gap-4 px-5 pb-6">
        {/* Patient card */}
        <Card>
          <div className="flex items-center gap-3">
            <Avatar name={patientName ?? diagnosis ?? 'Patient'} size="md" />
            <div className="flex-1 min-w-0">
              <p className="text-[17px] font-bold text-text-main truncate">
                {patientName ?? 'Unknown Patient'}
              </p>
              <p className="text-[13px] text-text-sub font-medium">
                {sessionId ? getPatientId(sessionId) : ''} · {diagnosis ?? 'General Consultation'}
              </p>
            </div>
            <Badge variant="followup">Follow-Up</Badge>
          </div>

          {/* Entities summary */}
          {(allergies.length > 0 || medications.length > 0) && (
            <div className="mt-3 pt-3 border-t border-gray-100 flex flex-wrap gap-2">
              {allergies.map(a => (
                <span key={a} className="text-[12px] bg-red-50 text-red-500 border border-red-100 px-2.5 py-0.5 rounded-full font-medium">
                  ⚠ {a}
                </span>
              ))}
              {medications.slice(0, 3).map(m => (
                <span key={m.name} className="text-[12px] bg-blue-50 text-blue-600 border border-blue-100 px-2.5 py-0.5 rounded-full font-medium">
                  {m.name} {m.dose ? `· ${m.dose}` : ''}
                </span>
              ))}
            </div>
          )}
        </Card>

        {/* Conflict Detected card */}
        {hasConflict && primaryConflict && (
          <Card variant="warning" className="animate-fade-in">
            <div className="flex items-start gap-3 mb-3">
              <div className="w-10 h-10 bg-red-50 border border-red-200 rounded-2xl flex items-center justify-center flex-shrink-0">
                <span className="material-symbols-outlined text-[20px] text-red-500" style={{ fontVariationSettings: "'FILL' 1" }}>warning</span>
              </div>
              <div className="flex-1">
                <h3 className="text-[15px] font-bold text-text-main">Conflict Detected</h3>
                <p className="text-[13px] text-text-sub mt-0.5 leading-snug">
                  {primaryConflict.issue ?? 'The prescribed medication contradicts the patient\'s listed allergies.'}
                </p>
              </div>
            </div>
            <div className="flex flex-wrap gap-2">
              <span className="flex items-center gap-1.5 text-[12px] font-semibold text-red-500 bg-red-50 border border-red-100 px-2.5 py-1 rounded-full">
                <span className="w-1.5 h-1.5 bg-red-400 rounded-full" />
                Conflict: {primaryConflict.drug_name}
              </span>
              <Badge variant="source">Source: Patient History</Badge>
            </div>

            {/* All unsafe checks */}
            {unsafeChecks.length > 1 && (
              <div className="mt-3 pt-3 border-t border-orange-100 space-y-2">
                {unsafeChecks.slice(1).map((sc, i) => (
                  <div key={i} className="text-[12px] text-text-sub">
                    <span className="font-semibold text-red-500">{sc.drug_name}</span>: {sc.issue}
                  </div>
                ))}
              </div>
            )}
          </Card>
        )}

        {/* Transcript */}
        <Card>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-[15px] font-bold text-text-main">Transcript</h3>
            <span className="text-[12px] text-text-sub font-medium">{transcript.length} lines</span>
          </div>

          {transcript.length === 0 ? (
            <p className="text-[13px] text-text-sub text-center py-4">No transcript recorded for this session.</p>
          ) : (
            <div className="space-y-3">
              {transcript.map((line, i) => {
                const isDr = line.role === 'doctor'
                return (
                  <div key={i}>
                    <div className={`rounded-2xl px-4 py-3 ${isDr ? 'bg-purple-50/60 border border-purple-100/50' : 'bg-gray-50 border border-gray-100'}`}>
                      <div className="flex items-center gap-2 mb-1.5">
                        <span className={`text-[11px] font-semibold uppercase tracking-wide ${isDr ? 'text-primary' : 'text-text-sub'}`}>
                          {isDr ? 'Doctor' : 'MediCore AI'}
                        </span>
                        <span className="text-[11px] text-text-sub">{line.time}</span>
                      </div>
                      <p className="text-[13px] text-text-main leading-snug">{line.text}</p>
                    </div>

                    {/* Inject safety alert callout after a doctor line that mentions a conflicting drug */}
                    {isDr && hasConflict && primaryConflict &&
                      line.text.toLowerCase().includes(primaryConflict.drug_name.toLowerCase()) && (
                      <div className="mx-2 my-2 bg-red-50 border border-red-100 rounded-2xl px-4 py-2.5 flex items-start gap-2">
                        <span className="w-2 h-2 bg-red-400 rounded-full mt-1.5 flex-shrink-0" />
                        <div>
                          <p className="text-[11px] font-bold text-red-500 uppercase tracking-wide">Safety Check Triggered</p>
                          <p className="text-[12px] text-text-sub mt-0.5">
                            {primaryConflict.issue ?? `${primaryConflict.drug_name} flagged against patient allergies`}
                          </p>
                        </div>
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          )}
        </Card>

        {/* Vitals */}
        <div className="grid grid-cols-2 gap-3">
          <Card className="flex flex-col items-center py-4">
            <span className="material-symbols-outlined text-[22px] text-blue-500 mb-2" style={{ fontVariationSettings: "'FILL' 1" }}>favorite</span>
            <p className="text-[28px] font-bold text-text-main leading-none">72</p>
            <p className="text-[11px] font-medium uppercase tracking-wider text-text-sub mt-1.5">BPM Heart Rate</p>
          </Card>
          <Card className="flex flex-col items-center py-4">
            <span className="material-symbols-outlined text-[22px] text-blue-400 mb-2" style={{ fontVariationSettings: "'FILL' 1" }}>water_drop</span>
            <p className="text-[28px] font-bold text-text-main leading-none">98%</p>
            <p className="text-[11px] font-medium uppercase tracking-wider text-text-sub mt-1.5">O₂ Saturation</p>
          </Card>
        </div>

        {/* Acknowledge & Save */}
        <Button
          variant="primary"
          size="lg"
          fullWidth
          onClick={handleAcknowledge}
          disabled={saving}
          className="mt-2"
        >
          {saving ? (
            <span className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
          ) : (
            <span className="material-symbols-outlined text-[18px]" style={{ fontVariationSettings: "'FILL' 1" }}>check_circle</span>
          )}
          Acknowledge &amp; Save
        </Button>
      </div>
    </AppShell>
  )
}
