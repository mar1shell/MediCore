import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import AppShell from '../components/layout/AppShell'
import Orb from '../components/ui/Orb'
import Badge from '../components/ui/Badge'
import Button from '../components/ui/Button'
import Card from '../components/ui/Card'
import { useSession } from '../context/SessionContext'
import { useVoiceSession } from '../hooks/useVoiceSession'
import type { SafetyCheckRecord } from '../types'

export default function SessionPage() {
  const { sessionId } = useParams<{ sessionId: string }>()
  const navigate = useNavigate()
  const { entities, safetyChecks } = useSession()
  const { connected, micError, connect, disconnect } = useVoiceSession()
  const [dismissedAlerts, setDismissedAlerts] = useState<Set<string>>(new Set())

  // Auto-connect on mount
  useEffect(() => {
    connect()
    return () => disconnect()
  }, [connect, disconnect])

  // Most recent unsafe alert that hasn't been dismissed
  const activeAlert: SafetyCheckRecord | null =
    safetyChecks
      .filter(sc => !sc.is_safe && !dismissedAlerts.has(sc.drug_name))
      .at(-1) ?? null

  const hasAlert = activeAlert !== null
  function handleEndSession() {
    disconnect()
    navigate(`/analyzing/${sessionId}`)
  }

  function dismissAlert() {
    if (activeAlert) {
      setDismissedAlerts(prev => new Set([...prev, activeAlert.drug_name]))
    }
  }

  return (
    <AppShell activeTab="home" showNav={!hasAlert}>
      {/* Status bar */}
      <div className="flex items-center justify-between px-5 pt-4 pb-2">
        <span className="text-[13px] font-semibold text-text-main">9:41</span>
        <div className="flex items-center gap-1">
          <span className="material-symbols-outlined text-[16px] text-text-sub" style={{ fontVariationSettings: "'FILL' 1" }}>signal_cellular_alt</span>
          <span className="material-symbols-outlined text-[16px] text-text-sub" style={{ fontVariationSettings: "'FILL' 1" }}>wifi</span>
          <span className="material-symbols-outlined text-[16px] text-text-sub" style={{ fontVariationSettings: "'FILL' 1" }}>battery_full</span>
        </div>
      </div>

      {/* Header */}
      <header className="flex items-center justify-between px-5 pb-4">
        <button
          onClick={() => navigate('/')}
          className="w-10 h-10 flex items-center justify-center rounded-xl hover:bg-gray-100 transition-colors"
        >
          <span className="material-symbols-outlined text-[22px] text-text-sub">arrow_back_ios</span>
        </button>
        <div className="text-center">
          <p className="text-[10px] font-semibold uppercase tracking-[0.15em] text-primary/80">Medicore AI</p>
          <p className="text-[15px] font-semibold text-text-main">
            Session #{sessionId?.slice(0, 4).toUpperCase() ?? '----'}
          </p>
        </div>
        <button className="w-10 h-10 flex items-center justify-center rounded-xl hover:bg-gray-100 transition-colors">
          <span className="material-symbols-outlined text-[22px] text-text-sub">more_vert</span>
        </button>
      </header>

      {/* Patient info card */}
      <div className="px-5 pb-4">
        <Card variant="glass" className="flex items-center gap-3">
          <div className="w-10 h-10 bg-indigo-50 rounded-xl flex items-center justify-center flex-shrink-0">
            <span className="material-symbols-outlined text-[20px] text-indigo-500" style={{ fontVariationSettings: "'FILL' 1" }}>person</span>
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-[15px] font-semibold text-text-main truncate">
              {entities?.patient_name ?? 'Unknown Patient'}
            </p>
            <p className="text-[13px] text-text-sub font-medium">
              {entities?.diagnosis ?? 'General Consultation'}
            </p>
          </div>
          <Badge variant="active">Active</Badge>
        </Card>
      </div>

      {/* Orb — switches to alert variant when safety alert is present */}
      <div className="flex-1 flex flex-col items-center justify-center gap-6 px-5">
        <Orb variant={hasAlert ? 'alert' : 'listening'} size="lg" />

        {/* Mic error banner */}
        {micError && (
          <div className="w-full bg-red-50 border border-red-200 rounded-2xl px-4 py-3 flex items-start gap-2">
            <span className="material-symbols-outlined text-[18px] text-red-500 flex-shrink-0 mt-0.5" style={{ fontVariationSettings: "'FILL' 1" }}>mic_off</span>
            <div>
              <p className="text-[13px] font-semibold text-red-600">Microphone access denied</p>
              <p className="text-[12px] text-red-500 mt-0.5 leading-snug">
                Allow microphone access in your browser settings and tap End Session to retry.
              </p>
            </div>
          </div>
        )}

        {/* Connection / listening status */}
        {!micError && (
          <div className="flex items-center gap-2 bg-white/60 backdrop-blur-md border border-white/40 rounded-full px-4 py-2">
            <span
              className={`w-2 h-2 rounded-full ${connected ? 'bg-primary animate-pulse' : 'bg-gray-300'}`}
            />
            <span className="text-[13px] font-semibold text-text-main tracking-wider uppercase">
              {connected ? 'Listening…' : 'Connecting…'}
            </span>
          </div>
        )}
      </div>

      {/* End Session button */}
      {!hasAlert && (
        <div className="px-5 pb-4 flex justify-center">
          <Button
            variant="danger"
            size="md"
            onClick={handleEndSession}
            className="px-10"
          >
            <span className="material-symbols-outlined text-[18px]" style={{ fontVariationSettings: "'FILL' 1" }}>stop_circle</span>
            End Session
          </Button>
        </div>
      )}

      {/* Safety Alert overlay */}
      {hasAlert && activeAlert && (
        <div className="absolute inset-0 z-50 flex flex-col">
          {/* Dimmed backdrop */}
          <div className="flex-1 bg-black/10 backdrop-blur-sm" onClick={dismissAlert} />

          {/* Alert card slides up */}
          <div className="animate-slide-up bg-white/95 backdrop-blur-xl border-t border-orange-100 rounded-t-4xl px-5 pt-6 pb-8 shadow-floating">
            <div className="flex items-start gap-4 mb-5">
              {/* Warning icon */}
              <div className="w-12 h-12 bg-orange-50 border border-orange-200 rounded-2xl flex items-center justify-center flex-shrink-0">
                <span className="material-symbols-outlined text-[24px] text-warning" style={{ fontVariationSettings: "'FILL' 1" }}>warning</span>
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <h3 className="text-[17px] font-bold text-text-main">Safety Alert</h3>
                  <Badge variant="action">Action Required</Badge>
                </div>
                <p className="text-[14px] text-text-sub leading-snug">
                  {activeAlert.issue ?? `${activeAlert.drug_name} — safety concern detected.`}
                </p>
                {activeAlert.recommendation && (
                  <p className="text-[14px] font-semibold text-text-main mt-1.5">
                    {activeAlert.recommendation}
                  </p>
                )}
              </div>
            </div>

            <div className="flex gap-3">
              <Button
                variant="warning"
                fullWidth
                onClick={dismissAlert}
              >
                Modify Rx
              </Button>
              <Button
                variant="secondary"
                fullWidth
                onClick={dismissAlert}
              >
                Dismiss
              </Button>
            </div>
          </div>
        </div>
      )}
    </AppShell>
  )
}
