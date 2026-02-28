import type { DiscrepancyFlag } from '../../types'

interface Props {
  flag: DiscrepancyFlag
}

export default function FlagCard({ flag }: Props) {
  return (
    <div style={{ border: `2px solid ${flag.severity === 'high' ? 'red' : flag.severity === 'medium' ? 'orange' : 'yellow'}`, padding: '0.5rem', marginBottom: '0.5rem' }}>
      <strong>[{flag.severity.toUpperCase()}] {flag.field}</strong>
      <p>{flag.message}</p>
      <p>Chart: <code>{flag.chart_val}</code> | Spoken: <code>{flag.spoken_val}</code></p>
      <button onClick={() => {/* TODO: dismiss */}}>Dismiss</button>
      <button onClick={() => {/* TODO: add to note */}}>Add to Note</button>
    </div>
  )
}
