import { createContext, useContext, useState, useCallback, type ReactNode } from 'react'
import type { Entities, SafetyCheckRecord } from '../types'

interface SessionState {
  sessionId: string | null
  entities: Entities | null
  safetyChecks: SafetyCheckRecord[]
}

interface SessionContextValue extends SessionState {
  setSession: (id: string, entities: Entities) => void
  addSafetyCheck: (record: SafetyCheckRecord) => void
  setSafetyChecks: (records: SafetyCheckRecord[]) => void
  clearSession: () => void
}

const SessionContext = createContext<SessionContextValue | null>(null)

export function SessionProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<SessionState>({
    sessionId: null,
    entities: null,
    safetyChecks: [],
  })

  const setSession = useCallback((id: string, entities: Entities) => {
    setState({ sessionId: id, entities, safetyChecks: [] })
  }, [])

  const addSafetyCheck = useCallback((record: SafetyCheckRecord) => {
    setState(prev => ({ ...prev, safetyChecks: [...prev.safetyChecks, record] }))
  }, [])

  const setSafetyChecks = useCallback((records: SafetyCheckRecord[]) => {
    setState(prev => ({ ...prev, safetyChecks: records }))
  }, [])

  const clearSession = useCallback(() => {
    setState({ sessionId: null, entities: null, safetyChecks: [] })
  }, [])

  return (
    <SessionContext.Provider value={{ ...state, setSession, addSafetyCheck, setSafetyChecks, clearSession }}>
      {children}
    </SessionContext.Provider>
  )
}

export function useSession(): SessionContextValue {
  const ctx = useContext(SessionContext)
  if (!ctx) throw new Error('useSession must be used within SessionProvider')
  return ctx
}
