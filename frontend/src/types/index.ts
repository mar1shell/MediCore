// ── Medication ────────────────────────────────────────────────────────────────

export interface Medication {
  name: string
  dose: string | null
}

// ── Extracted Entities ────────────────────────────────────────────────────────

export interface Entities {
  source: string
  patient_name: string | null
  allergies: string[]
  medications: Medication[]
  diagnosis: string | null
  extraction_notes: string | null
  diagrams: boolean
}

// ── Safety Check ──────────────────────────────────────────────────────────────

export interface SafetyCheckRecord {
  drug_name: string
  is_safe: boolean
  issue: string | null
  recommendation: string | null
}

// ── Session ───────────────────────────────────────────────────────────────────

export interface SessionData {
  session_id: string
  entities: Entities
  safety_checks: SafetyCheckRecord[]
}

// ── Upload Chart Response ─────────────────────────────────────────────────────

export interface UploadChartResponse {
  session_id: string
  filename: string
  ocr_text: string
  pages_processed: number
  entities: Entities
}

// ── Transcript ────────────────────────────────────────────────────────────────

export interface TranscriptLine {
  role: 'doctor' | 'agent'
  text: string
  time: string   // e.g. "09:42 AM" — recorded client-side when event arrives
}

// ── Orb variant ───────────────────────────────────────────────────────────────

export type OrbVariant = 'idle' | 'listening' | 'analyzing' | 'alert'

// ── Navigation ────────────────────────────────────────────────────────────────

export type NavTab = 'home' | 'history' | 'profile'
