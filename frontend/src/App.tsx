import ChartUpload from './components/ChartUpload/ChartUpload'
import VoiceSession from './components/VoiceSession/VoiceSession'
import ComparisonView from './components/ComparisonView/ComparisonView'

export default function App() {
  return (
    <main>
      <h1>MedRound</h1>
      <ChartUpload />
      <VoiceSession />
      <ComparisonView />
    </main>
  )
}
