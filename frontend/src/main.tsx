import { createRoot } from 'react-dom/client'
import './styles/index.css'
import App from './App'

// StrictMode is intentionally omitted: in development it double-fires every
// useEffect, which opens two sequential ElevenLabs WebSocket sessions and causes
// the agent's greeting to play twice. Production builds are unaffected (they
// never double-invoke). Re-enable StrictMode once the voice session uses a
// stable, cancellable connection pattern.
createRoot(document.getElementById('root')!).render(<App />)
