import React, { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { AlertTriangle, Check, CheckCircle, Circle, Loader2, ShieldCheck } from 'lucide-react'
import {
  alertAPI,
  anomalyAPI,
  Incident,
  incidentAPI,
  Alert,
  Anomaly,
  metricAPI,
  Metric,
} from '../api/client'
import { IncidentTimeline } from '../components/IncidentTimeline'
import { MetricChart } from '../components/MetricChart'
import { useWebSocket } from '../hooks/useWebSocket'

const progressStages = [
  'detecting',
  'comparing_baseline',
  'running_secondary_models',
  'correlating',
  'root_cause',
  'alerting',
  'resolved',
]

const formatStage = (stage: string) => stage.replaceAll('_', ' ')

const formatConfidence = (confidence: number | null) => {
  if (confidence === null) return 'Pending'
  return `${Math.round(confidence <= 1 ? confidence * 100 : confidence)}%`
}

const getWebSocketUrl = () => {
  if (import.meta.env.VITE_WS_URL) return import.meta.env.VITE_WS_URL
  const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws'
  return `${protocol}://${window.location.host}/ws`
}

export const IncidentDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  const [incident, setIncident] = useState<Incident | null>(null)
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [anomalies, setAnomalies] = useState<Anomaly[]>([])
  const [metrics, setMetrics] = useState<Metric[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [actionPending, setActionPending] = useState(false)
  const { lastMessage, connected } = useWebSocket(getWebSocketUrl())

  useEffect(() => {
    if (!id) return

    const loadIncident = async () => {
      try {
        setLoading(true)
        const [incidentResponse, alertResponse, anomalyResponse] = await Promise.all([
          incidentAPI.getIncident(id),
          alertAPI.getAlerts(undefined, undefined, 100),
          anomalyAPI.getRecent(100),
        ])
        const nextIncident = incidentResponse.data
        const nextAlerts = alertResponse.data.filter((alert) => alert.incident_id === id)
        const incidentAnomalyIds = new Set(nextAlerts.map((alert) => alert.anomaly_id))
        const nextAnomalies = anomalyResponse.data.filter((anomaly) => incidentAnomalyIds.has(anomaly.id))
        const metricName = nextAnomalies[0]?.metric_name ?? nextIncident.correlated_metrics?.split(',')[0]?.trim()

        setIncident(nextIncident)
        setAlerts(nextAlerts)
        setAnomalies(nextAnomalies)

        if (metricName) {
          const end = new Date()
          const start = new Date(end.getTime() - 24 * 60 * 60 * 1000)
          const metricResponse = await metricAPI.getRange(metricName, start.toISOString(), end.toISOString())
          setMetrics(metricResponse.data)
        }
      } catch {
        setError('Unable to load this incident investigation.')
      } finally {
        setLoading(false)
      }
    }

    void loadIncident()
  }, [id])

  useEffect(() => {
    if (!incident || !lastMessage || lastMessage.type !== 'progress_update' || lastMessage.incident_id !== incident.id) {
      return
    }
    setIncident((current) => current ? {
      ...current,
      progress_stage: lastMessage.stage ?? current.progress_stage,
      progress_percent: lastMessage.percent ?? current.progress_percent,
      status: lastMessage.stage === 'resolved' ? 'resolved' : current.status,
    } : current)
  }, [incident, lastMessage])

  const runAlertAction = async (action: 'investigate' | 'acknowledge' | 'resolve') => {
    if (!incident || alerts.length === 0) return
    try {
      setActionPending(true)
      const activeAlert = alerts.find((alert) => alert.status !== 'resolved') ?? alerts[0]
      if (action === 'resolve') {
        await alertAPI.resolve(activeAlert.id)
        await incidentAPI.resolve(incident.id, incident.root_cause ?? undefined)
        setIncident({ ...incident, status: 'resolved', progress_stage: 'resolved', progress_percent: 100 })
      } else {
        await alertAPI.acknowledge(activeAlert.id, action === 'investigate' ? 'investigator' : 'operator')
        setAlerts(alerts.map((alert) => alert.id === activeAlert.id ? { ...alert, status: 'acknowledged' } : alert))
        setIncident({ ...incident, status: 'investigating' })
      }
    } finally {
      setActionPending(false)
    }
  }

  if (loading) return <div className="p-6 text-slate-300">Loading investigation...</div>
  if (error || !incident) return <div className="p-6 text-red-300">{error ?? 'Incident not found.'}</div>

  const currentStageIndex = progressStages.indexOf(incident.progress_stage ?? '')
  const anomaly = anomalies[0]
  const expectedValue = anomaly?.expected_value
  const actualValue = anomaly?.value
  const relatedMetrics = incident.correlated_metrics?.split(',').map((metric) => metric.trim()).filter(Boolean) ?? []

  return (
    <div className="min-h-screen bg-slate-950 p-6 text-slate-200">
      <div className="mx-auto max-w-7xl space-y-6">
        <Link to="/incidents" className="text-sm text-slate-400 hover:text-white">&larr; Back to incidents</Link>

        <header className="flex flex-col gap-4 rounded-lg border border-slate-800 bg-slate-900 p-6 md:flex-row md:items-start md:justify-between">
          <div>
            <div className="mb-3 flex flex-wrap items-center gap-3">
              <span className="rounded-md bg-red-500/15 px-2 py-1 text-xs font-semibold uppercase text-red-300">{incident.severity}</span>
              <span className="text-sm text-slate-400">{incident.status}</span>
              {connected && <span className="text-xs text-emerald-400">Live progress connected</span>}
            </div>
            <h1 className="text-3xl font-bold text-white">{incident.title}</h1>
            <p className="mt-2 text-slate-400">Detected {new Date(incident.detected_at).toLocaleString()}</p>
          </div>
          <div className="text-left md:text-right">
            <p className="text-xs uppercase tracking-wider text-slate-500">Detection confidence</p>
            <p className="mt-1 text-3xl font-bold text-white">{formatConfidence(incident.confidence)}</p>
          </div>
        </header>

        <section className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
          <div className="rounded-lg border border-slate-800 bg-slate-900 p-6">
            <h2 className="mb-4 text-lg font-semibold text-white">What changed</h2>
            <div className="grid grid-cols-2 gap-4">
              <div className="rounded-md bg-slate-800 p-4"><p className="text-xs uppercase text-slate-500">Expected</p><p className="mt-2 text-2xl font-semibold text-slate-200">{expectedValue === null || expectedValue === undefined ? 'Unavailable' : expectedValue.toFixed(2)}</p></div>
              <div className="rounded-md bg-red-950/40 p-4"><p className="text-xs uppercase text-red-300">Actual</p><p className="mt-2 text-2xl font-semibold text-white">{actualValue === undefined ? 'Unavailable' : actualValue.toFixed(2)}</p></div>
            </div>
            <p className="mt-4 text-sm text-slate-400">{incident.description ?? 'The detection pipeline flagged a meaningful deviation from the baseline.'}</p>
          </div>

          <div className="rounded-lg border border-slate-800 bg-slate-900 p-6">
            <div className="mb-4 flex items-center justify-between"><h2 className="text-lg font-semibold text-white">Investigation progress</h2><span className="text-sm text-slate-400">{incident.progress_percent ?? 0}%</span></div>
            <div className="space-y-3">
              {progressStages.map((stage, index) => {
                const complete = currentStageIndex >= index || incident.progress_percent === 100
                const current = currentStageIndex === index
                return <div key={stage} className="flex items-center gap-3 text-sm"><span className={complete ? 'text-emerald-400' : current ? 'text-amber-300' : 'text-slate-600'}>{complete ? <CheckCircle className="h-4 w-4" /> : current ? <Loader2 className="h-4 w-4 animate-spin" /> : <Circle className="h-4 w-4" />}</span><span className={complete || current ? 'text-slate-200' : 'text-slate-500'}>{formatStage(stage)}</span></div>
              })}
            </div>
          </div>
        </section>

        <div className="flex flex-wrap gap-3">
          <button onClick={() => void runAlertAction('investigate')} disabled={actionPending || alerts.length === 0} className="inline-flex items-center gap-2 rounded-md bg-amber-500 px-4 py-2 font-semibold text-slate-950 disabled:cursor-not-allowed disabled:opacity-50"><AlertTriangle className="h-4 w-4" /> Investigate</button>
          <button onClick={() => void runAlertAction('acknowledge')} disabled={actionPending || alerts.length === 0} className="inline-flex items-center gap-2 rounded-md border border-slate-700 px-4 py-2 font-semibold text-white disabled:cursor-not-allowed disabled:opacity-50"><ShieldCheck className="h-4 w-4" /> Acknowledge</button>
          <button onClick={() => void runAlertAction('resolve')} disabled={actionPending || alerts.length === 0 || incident.status === 'resolved'} className="inline-flex items-center gap-2 rounded-md border border-emerald-700 px-4 py-2 font-semibold text-emerald-300 disabled:cursor-not-allowed disabled:opacity-50"><Check className="h-4 w-4" /> Resolve</button>
        </div>

        <section className="grid gap-6 lg:grid-cols-[0.8fr_1.2fr]">
          <div className="space-y-6">
            <div className="rounded-lg border border-slate-800 bg-slate-900 p-6"><h2 className="mb-3 text-lg font-semibold text-white">Related signals</h2><p className="text-sm text-slate-400">Root cause: <span className="text-slate-200">{incident.root_cause ?? 'Still being correlated'}</span></p><div className="mt-4 flex flex-wrap gap-2">{relatedMetrics.length ? relatedMetrics.map((metric) => <span key={metric} className="rounded-md bg-slate-800 px-3 py-1 text-sm text-slate-300">{metric}</span>) : <span className="text-sm text-slate-500">No correlated metrics yet.</span>}</div></div>
            <IncidentTimeline incidents={[incident]} />
          </div>
          <div>{metrics.length && anomaly?.metric_name ? <MetricChart metric_name={anomaly.metric_name} metrics={metrics} anomalies={anomalies} height={340} /> : <div className="rounded-lg border border-slate-800 bg-slate-900 p-6 text-slate-500">Evidence chart will appear when metric history is available.</div>}</div>
        </section>
      </div>
    </div>
  )
}
