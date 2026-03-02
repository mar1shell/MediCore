import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { SessionProvider } from './context/SessionContext'

import HomePage from './pages/HomePage'
import SessionPage from './pages/SessionPage'
import AnalyzingPage from './pages/AnalyzingPage'
import SummaryPage from './pages/SummaryPage'
import HistoryPage from './pages/HistoryPage'
import ProfilePage from './pages/ProfilePage'

export default function App() {
  return (
    <BrowserRouter>
      <SessionProvider>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/session/:sessionId" element={<SessionPage />} />
          <Route path="/analyzing/:sessionId" element={<AnalyzingPage />} />
          <Route path="/summary/:sessionId" element={<SummaryPage />} />
          <Route path="/history" element={<HistoryPage />} />
          <Route path="/profile" element={<ProfilePage />} />
          {/* Fallback */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </SessionProvider>
    </BrowserRouter>
  )
}
