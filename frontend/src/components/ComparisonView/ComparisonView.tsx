import FlagCard from '../FlagCard/FlagCard'
import type { DiscrepancyFlag } from '../../types'

interface Props {
  chartData?: Record<string, string[]>
  spokenData?: Record<string, string[]>
  flags?: DiscrepancyFlag[]
}

export default function ComparisonView({ chartData, spokenData, flags = [] }: Props) {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '1rem' }}>
      <div>
        <h2>Chart</h2>
        {/* TODO: render chartData */}
      </div>
      <div>
        <h2>Flags</h2>
        {flags.map((flag, i) => <FlagCard key={i} flag={flag} />)}
      </div>
      <div>
        <h2>Spoken</h2>
        {/* TODO: render spokenData */}
      </div>
    </div>
  )
}
