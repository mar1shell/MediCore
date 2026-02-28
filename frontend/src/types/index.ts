// Shared data shapes — kept in sync with shared/schemas/

export interface EntityData {
  allergies: string[]
  medications: string[]
  diagnosis: string[]
}

export type Severity = 'high' | 'medium' | 'low'

export interface DiscrepancyFlag {
  severity: Severity
  field: string
  chart_val: string
  spoken_val: string
  message: string
}
