import { useEffect, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import AppShell from '../components/layout/AppShell'
import Orb from '../components/ui/Orb'
import { getSession } from '../api/client'
import { useSession } from '../context/SessionContext'

type Phase = 'analyzing' | 'generating'

const PHASES: { id: Phase; heading: string; subtext: string; duration: number }[] = [
  {
    id: 'analyzing',
    heading: 'Analyzing…',
    subtext: 'Processing consultation data',
    duration: 2500,
  },
  {
    id: 'generating',
    heading: 'Generating Draft Summary…',
    subtext: 'Cross-referencing with patient medical chart',
    duration: 2000,
  },
]

export default function AnalyzingPage() {
  const { sessionId } = useParams<{ sessionId: string }>()
  const navigate = useNavigate()
  const { setSafetyChecks } = useSession()
  const [phaseIndex, setPhaseIndex] = useState(0)
  const [visible, setVisible] = useState(true)
  // Track whether the backend fetch has completed so we don't navigate before
  // we have fresh safety-check data.
  const dataReadyRef = useRef(false)
  const animationDoneRef = useRef(false)

  // Fetch the latest session data (real safety checks) while the animation plays
  useEffect(() => {
    if (!sessionId) return
    getSession(sessionId)
      .then(data => {
        setSafetyChecks(data.safety_checks)
        dataReadyRef.current = true
        if (animationDoneRef.current) {
          navigate(`/summary/${sessionId}`, { replace: true })
        }
      })
      .catch(() => {
        // On error, proceed anyway — the summary will use whatever is already in context
        dataReadyRef.current = true
        if (animationDoneRef.current) {
          navigate(`/summary/${sessionId}`, { replace: true })
        }
      })
  }, [sessionId, setSafetyChecks, navigate])

  // Drive the two-phase animation, then navigate when both animation + fetch are done
  useEffect(() => {
    const phase = PHASES[phaseIndex]
    const timer = setTimeout(() => {
      if (phaseIndex < PHASES.length - 1) {
        setVisible(false)
        setTimeout(() => {
          setPhaseIndex(i => i + 1)
          setVisible(true)
        }, 350)
      } else {
        // Animation finished — navigate immediately if data is ready, otherwise
        // mark as done and let the fetch callback navigate.
        animationDoneRef.current = true
        if (dataReadyRef.current) {
          navigate(`/summary/${sessionId}`, { replace: true })
        }
      }
    }, phase.duration)

    return () => clearTimeout(timer)
  }, [phaseIndex, sessionId, navigate])

  const { heading, subtext } = PHASES[phaseIndex]

  return (
    <AppShell activeTab="history" className="relative">
      {/* Full-bleed gradient overlay */}
      <div
        className="pointer-events-none absolute inset-0"
        style={{ background: 'linear-gradient(180deg, #fbfaff 0%, #f0f4ff 100%)', zIndex: 0 }}
      />

      <div className="flex-1 flex flex-col items-center justify-center gap-8 relative z-10 px-6 py-12">
        {/* Orb */}
        <div className="relative">
          <Orb variant="analyzing" size="lg" />
        </div>

        {/* Phase text */}
        <div
          className="text-center transition-all duration-300"
          style={{ opacity: visible ? 1 : 0, transform: visible ? 'translateY(0)' : 'translateY(6px)' }}
        >
          <p className="text-[18px] font-normal text-gray-800 tracking-tight">{heading}</p>
          <p className="text-[13px] text-gray-400 font-light mt-1.5">{subtext}</p>
        </div>
      </div>
    </AppShell>
  )
}
