import React, { useEffect, useState } from 'react'
import { Activity, AlertTriangle, ClipboardList, Loader2 } from 'lucide-react'
import { analyticsAPI, incidentAPI, Incident, AnalyticsSummary } from '../api/client'

export const Overview: React.FC = () => {
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null)
  const [recentIncidents, setRecentIncidents] = useState<Incident[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const loadOverview = async () => {
      try {
        const [summaryResponse, incidentResponse] = await Promise.all([
          analyticsAPI.getSummary(),
          incidentAPI.getIncidents(undefined, 10),
        ])
        setSummary(summaryResponse.data)
        setRecentIncidents(incidentResponse.data.sort((left, right) => new Date(right.detected_at).getTime() - new Date(left.detected_at).getTime()))
      } catch {
        setError('Unable to load overview.')
      } finally {
        setLoading(false)
      }
    }

    void loadOverview()
  }, [])

  const today = new Date().toDateString()
  const investigationsToday = recentIncidents.filter((incident) => new Date(incident.detected_at).toDateString() === today).length

  return (
    <div className="min-h-screen bg-slate-950 p-6 text-slate-200">
      <div className="mx-auto max-w-6xl space-y-8">
        <div><p className="text-sm uppercase tracking-wider text-slate-500">Anomix</p><h1 className="mt-2 text-3xl font-bold text-white">Overview</h1><p className="mt-2 text-slate-400">A concise read on what needs attention now.</p></div>
        {loading && <div className="flex items-center gap-2 text-slate-400"><Loader2 className="h-4 w-4 animate-spin" /> Loading overview...</div>}
        {error && <div className="text-red-300">{error}</div>}
        {!loading && !error && summary && <>
          <section className="grid gap-4 md:grid-cols-3">
            <div className="rounded-lg border border-slate-800 bg-slate-900 p-5"><div className="flex items-center justify-between"><span className="text-sm text-slate-400">Active anomalies</span><AlertTriangle className="h-5 w-5 text-amber-400" /></div><p className="mt-4 text-3xl font-bold text-white">{summary.anomalies}</p></div>
            <div className="rounded-lg border border-slate-800 bg-slate-900 p-5"><div className="flex items-center justify-between"><span className="text-sm text-slate-400">Active incidents</span><Activity className="h-5 w-5 text-red-400" /></div><p className="mt-4 text-3xl font-bold text-white">{summary.incidents}</p></div>
            <div className="rounded-lg border border-slate-800 bg-slate-900 p-5"><div className="flex items-center justify-between"><span className="text-sm text-slate-400">Investigations today</span><ClipboardList className="h-5 w-5 text-blue-400" /></div><p className="mt-4 text-3xl font-bold text-white">{investigationsToday}</p></div>
          </section>
          <section className="max-w-3xl"><h2 className="mb-3 text-lg font-semibold text-white">Recent activity</h2><div className="divide-y divide-slate-800 rounded-lg border border-slate-800 bg-slate-900">{recentIncidents.length === 0 && <p className="p-5 text-slate-500">No recent activity.</p>}{recentIncidents.map((incident) => <div key={incident.id} className="flex items-start justify-between gap-4 p-5"><div><p className="text-sm text-slate-200">{incident.title}</p><p className="mt-1 text-xs capitalize text-slate-500">{incident.status} · {incident.severity}</p></div><time className="shrink-0 text-xs text-slate-500">{new Date(incident.detected_at).toLocaleString()}</time></div>)}</div></section>
        </>}
      </div>
    </div>
  )
}
