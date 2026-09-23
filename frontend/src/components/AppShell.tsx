import React, { useState, useEffect } from 'react'
import { NavLink, useLocation } from 'react-router-dom'
import { 
  LayoutDashboard, 
  AlertTriangle, 
  ShieldAlert, 
  Sliders, 
  Radio, 
  RefreshCw,
} from 'lucide-react'
import { anomalyAPI, incidentAPI } from '../api/client'
import { useWebSocket } from '../hooks/useWebSocket'
import { Footer } from './Footer'

interface AppShellProps {
  children: React.ReactNode
}

export const AppShell: React.FC<AppShellProps> = ({ children }) => {
  const [activeAnomalyCount, setActiveAnomalyCount] = useState<number>(0)
  const [activeIncidentCount, setActiveIncidentCount] = useState<number>(0)
  
  const wsUrl = import.meta.env.VITE_WS_URL || `ws://${window.location.hostname}:8000/ws/api/v1/updates`
  const { connected } = useWebSocket(wsUrl)

  const fetchBadgeCounts = async () => {
    try {
      const [anomRes, incRes] = await Promise.all([
        anomalyAPI.getRecent(50),
        incidentAPI.getIncidents(undefined, 50),
      ])
      const activeAnomalies = anomRes.data.filter((a) => !a.is_confirmed).length
      const activeIncidents = incRes.data.filter((i) => i.status !== 'resolved').length
      setActiveAnomalyCount(activeAnomalies)
      setActiveIncidentCount(activeIncidents)
    } catch (err) {
      console.error('Failed to fetch badge counts:', err)
    }
  }

  useEffect(() => {
    fetchBadgeCounts()
    const interval = setInterval(fetchBadgeCounts, 15000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="flex min-h-screen bg-slate-950 text-slate-100 font-sans antialiased">
      {/* Left Sidebar Nav */}
      <aside className="w-64 flex-shrink-0 border-r border-slate-800 bg-slate-900/90 flex flex-col justify-between">
        <div>
          {/* Brand Header */}
          <div className="flex items-center gap-3 px-6 py-5 border-b border-slate-800">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-blue-600/20 text-blue-400 border border-blue-500/30">
              <Radio className="h-5 w-5" />
            </div>
            <div>
              <h1 className="text-base font-bold text-white tracking-tight">Anomix</h1>
              <p className="text-[10px] font-medium text-slate-400 uppercase tracking-wider">Telemetry Console</p>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="p-4 space-y-1 text-xs font-semibold">
            <NavLink
              to="/"
              end
              className={({ isActive }) =>
                `flex items-center justify-between rounded-lg px-3 py-2 transition-all ${
                  isActive
                    ? 'bg-blue-600/15 text-blue-400 border border-blue-500/20'
                    : 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-200'
                }`
              }
            >
              <div className="flex items-center gap-3">
                <LayoutDashboard className="h-4 w-4" />
                <span>Overview</span>
              </div>
            </NavLink>

            <NavLink
              to="/anomalies"
              className={({ isActive }) =>
                `flex items-center justify-between rounded-lg px-3 py-2 transition-all ${
                  isActive
                    ? 'bg-blue-600/15 text-blue-400 border border-blue-500/20'
                    : 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-200'
                }`
              }
            >
              <div className="flex items-center gap-3">
                <AlertTriangle className="h-4 w-4" />
                <span>Anomalies</span>
              </div>
                {activeAnomalyCount > 0 && (
                  <span className="rounded bg-amber-500/20 text-amber-400 border border-amber-500/30 px-2 py-0.5 text-[10px] font-bold">
                  {activeAnomalyCount}
                </span>
              )}
            </NavLink>

            <NavLink
              to="/incidents"
              className={({ isActive }) =>
                `flex items-center justify-between rounded-lg px-3 py-2 transition-all ${
                  isActive
                    ? 'bg-blue-600/15 text-blue-400 border border-blue-500/20'
                    : 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-200'
                }`
              }
            >
              <div className="flex items-center gap-3">
                <ShieldAlert className="h-4 w-4" />
                <span>Incidents</span>
              </div>
              {activeIncidentCount > 0 && (
                <span className="rounded bg-rose-500/20 text-rose-400 border border-rose-500/30 px-2 py-0.5 text-[10px] font-bold">
                  {activeIncidentCount}
                </span>
              )}
            </NavLink>

            <NavLink
              to="/rules"
              className={({ isActive }) =>
                `flex items-center justify-between rounded-lg px-3 py-2 transition-all ${
                  isActive
                    ? 'bg-blue-600/15 text-blue-400 border border-blue-500/20'
                    : 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-200'
                }`
              }
            >
              <div className="flex items-center gap-3">
                <Sliders className="h-4 w-4" />
                <span>Alert Rules</span>
              </div>
            </NavLink>
          </nav>
        </div>

        {/* Sidebar Footer Status */}
        <div className="p-4 border-t border-slate-800">
          <div className="flex items-center justify-between rounded-lg bg-slate-950/80 p-3 border border-slate-800 text-xs">
            <div className="flex items-center gap-2">
              <span className={`h-2 w-2 rounded-full ${connected ? 'bg-emerald-400' : 'bg-rose-400'}`} />
              <span className="text-slate-300 font-medium">{connected ? 'Live Sync' : 'Offline'}</span>
            </div>
            <button
              onClick={fetchBadgeCounts}
              title="Refresh telemetry status"
              className="text-slate-500 hover:text-white transition"
            >
              <RefreshCw className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>
      </aside>

      {/* Main Content Viewport */}
      <main className="flex-1 overflow-y-auto bg-slate-950">
        {children}
        <Footer />
      </main>
    </div>
  )
}
