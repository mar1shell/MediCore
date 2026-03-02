import type { Entities, UploadChartResponse, SessionData, SafetyCheckRecord } from '../types'

export const MOCK_ENTITIES: Entities = {
  source: 'test-chart.pdf',
  patient_name: 'John Doe',
  allergies: ['Penicillin'],
  medications: [
    { name: 'Amoxicillin', dose: '500mg' },
    { name: 'Ibuprofen', dose: '400mg' },
  ],
  diagnosis: 'Upper Respiratory Infection',
  extraction_notes: null,
  diagrams: false,
}

export const MOCK_SESSION_ID = 'abc12345-0000-0000-0000-000000000001'

export const MOCK_UPLOAD_RESPONSE: UploadChartResponse = {
  session_id: MOCK_SESSION_ID,
  filename: 'test-chart.pdf',
  ocr_text: 'Patient: John Doe\nAllergies: Penicillin\nMedications: Amoxicillin 500mg',
  pages_processed: 1,
  entities: MOCK_ENTITIES,
}

export const MOCK_SAFETY_CHECK_UNSAFE: SafetyCheckRecord = {
  drug_name: 'Amoxicillin',
  is_safe: false,
  issue: 'Patient is allergic to Penicillin — Amoxicillin is a penicillin-type antibiotic.',
  recommendation: 'Consider Azithromycin as an alternative.',
}

export const MOCK_SAFETY_CHECK_SAFE: SafetyCheckRecord = {
  drug_name: 'Ibuprofen',
  is_safe: true,
  issue: null,
  recommendation: null,
}

export const MOCK_SESSION_DATA: SessionData = {
  session_id: MOCK_SESSION_ID,
  entities: MOCK_ENTITIES,
  safety_checks: [MOCK_SAFETY_CHECK_UNSAFE, MOCK_SAFETY_CHECK_SAFE],
}
