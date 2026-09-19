import { BrowserRouter, Routes, Route, Link } from 'react-router-dom'
import Navbar from './components/Navbar'
import Landing from './pages/Landing'
import Dashboard from './pages/Dashboard'
import ReportIncident from './pages/ReportIncident'
import AIAnalysis from './pages/AIAnalysis'
import IncidentDetails from './pages/IncidentDetails'
import CampusMap from './pages/CampusMap'
import Analytics from './pages/Analytics'

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-[#030303] text-slate-200 selection:bg-amber-400/30 font-sans">
        <Navbar />
        <main>
          <Routes>
            <Route path="/" element={<Landing />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/report" element={<ReportIncident />} />
            <Route path="/analysis" element={<AIAnalysis />} />
            <Route path="/details/:id" element={<IncidentDetails />} />
            <Route path="/map" element={<CampusMap />} />
            <Route path="/analytics" element={<Analytics />} />
          </Routes>
        </main>
        <footer className="border-t border-white/10 bg-[#030303]/80">
          <div className="mx-auto max-w-7xl px-6 lg:px-8 py-10 flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="text-center md:text-left">
              <div className="text-base font-bold text-white">CampusFix</div>
              <p className="mt-1 text-sm text-slate-500">
                Campus incident reporting and facilities coordination — report an issue, track it to resolution.
              </p>
            </div>
            <nav className="flex flex-wrap items-center justify-center gap-x-6 gap-y-2 text-sm text-slate-400">
              <Link to="/dashboard" className="hover:text-white transition-colors">Dashboard</Link>
              <Link to="/report" className="hover:text-white transition-colors">Report Incident</Link>
              <Link to="/map" className="hover:text-white transition-colors">Campus Map</Link>
              <Link to="/analytics" className="hover:text-white transition-colors">Analytics</Link>
            </nav>
          </div>
          <div className="border-t border-white/5">
            <div className="mx-auto max-w-7xl px-6 lg:px-8 py-4 flex flex-col sm:flex-row items-center justify-between gap-2 text-xs text-slate-600">
              <span>© 2026 CampusFix. All rights reserved.</span>
              <span>Facilities Operations · v1.0</span>
            </div>
          </div>
        </footer>
      </div>
    </BrowserRouter>
  )
}
