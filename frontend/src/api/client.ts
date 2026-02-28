import type { EntityData, DiscrepancyFlag } from '../types'

const BASE = '/api'

export async function uploadChart(file: File): Promise<{ raw_text: string }> {
  const form = new FormData()
  form.append('file', file)
  const res = await fetch(`${BASE}/upload-chart`, { method: 'POST', body: form })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export async function extractEntities(text: string): Promise<EntityData> {
  const res = await fetch(`${BASE}/extract-entities`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
  })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export async function crossReference(
  chartData: EntityData,
  spokenData: EntityData,
): Promise<{ flags: DiscrepancyFlag[] }> {
  const res = await fetch(`${BASE}/cross-reference`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ chart_data: chartData, spoken_data: spokenData }),
  })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}
