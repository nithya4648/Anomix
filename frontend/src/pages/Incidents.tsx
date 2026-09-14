import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { AlertCircle, ArrowRight, Loader2 } from 'lucide-react'
import { incidentAPI, Incident } from '../api/client'

export const Incidents: React.FC = () => {
  const [incidents, setIncidents] = useState<Incident[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const loadIncidents = async () => {
      try {
        const response = await incidentAPI.getIncidents(undefined, 100)
        setIncidents(response.data)
      } catch {
        setError('Unable to load incidents.')
      } finally {
        setLoading(false)
      }
    }

    void loadIncidents()
  }, [])

  const sortedIncidents = [...incidents].sort(
    (left, right) => new Date(right.detected_at).getTime() - new Date(left.detected_at).getTime(),
  )

  return (
    <div className="min-h-screen bg-slate-950 p-6 text-slate-200">
      <div className="mx-auto max-w-6xl space-y-6">
        <div>
          <p className="text-sm uppercase tracking-wider text-slate-500">Operations</p>
          <h1 className="mt-2 text-3xl font-bold text-white">Incidents</h1>
          <p className="mt-2 text-slate-400">Active and resolved investigations across monitored services.</p>
        </div>

        <div className="overflow-hidden rounded-lg border border-slate-800 bg-slate-900">
          {loading && <div className="flex items-center gap-2 p-6 text-slate-400"><Loader2 className="h-4 w-4 animate-spin" /> Loading incidents...</div>}
          {error && <div className="p-6 text-red-300">{error}</div>}
          {!loading && !error && sortedIncidents.length === 0 && <div className="p-10 text-center text-slate-500">No incidents detected.</div>}
          {!loading && !error && sortedIncidents.length > 0 && <div className="divide-y divide-slate-800">
            {sortedIncidents.map((incident) => {
              const service = incident.root_cause ?? incident.correlated_metrics?.split(',')[0]?.trim() ?? 'Unknown service'
              return <Link key={incident.id} to={`/incidents/${incident.id}`} className="grid gap-3 p-5 transition-colors hover:bg-slate-800/60 md:grid-cols-[minmax(0,1fr)_150px_170px_170px_24px] md:items-center">
                <div className="min-w-0"><div className="flex items-center gap-3"><AlertCircle className={`h-4 w-4 shrink-0 ${incident.severity === 'critical' ? 'text-red-400' : incident.severity === 'warning' ? 'text-amber-400' : 'text-blue-400'}`} /><p className="truncate font-semibold text-white">{incident.title}</p></div><p className="mt-1 truncate pl-7 text-sm text-slate-500">{incident.description ?? 'Investigation details available'}</p></div>
                <span className="text-sm capitalize text-slate-300">{incident.severity}</span>
                <span className="truncate text-sm text-slate-400">{service}</span>
                <span className="text-sm text-slate-500">{new Date(incident.detected_at).toLocaleString()}</span>
                <ArrowRight className="h-4 w-4 text-slate-600" />
              </Link>
            })}
          </div>}
        </div>
      </div>
    </div>
  )
}
