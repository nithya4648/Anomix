import { Routes, Route } from 'react-router-dom'
import { AppShell } from './components/AppShell'
import { Overview } from './pages/Overview'
import { Anomalies } from './pages/Anomalies'
import { Incidents } from './pages/Incidents'
import { IncidentDetail } from './pages/IncidentDetail'
import { AlertRules } from './pages/AlertRules'
import { PrivacyPolicy } from './pages/PrivacyPolicy'
import { TermsAndConditions } from './pages/TermsAndConditions'

function App() {
  return (
    <AppShell>
      <Routes>
        <Route path="/" element={<Overview />} />
        <Route path="/anomalies" element={<Anomalies />} />
        <Route path="/incidents" element={<Incidents />} />
        <Route path="/incidents/:id" element={<IncidentDetail />} />
        <Route path="/rules" element={<AlertRules />} />
        <Route path="/privacy" element={<PrivacyPolicy />} />
        <Route path="/terms" element={<TermsAndConditions />} />
      </Routes>
    </AppShell>
  )
}

export default App

