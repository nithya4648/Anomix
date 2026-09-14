import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { anomalyAPI, Anomaly } from '../api/client'
import { useWebSocket } from '../hooks/useWebSocket'
import { AnomalyFeedbackModal } from '../components/AnomalyFeedbackModal'
import { 
  AlertTriangle, 
  Sparkles, 
  CheckCircle2, 
  XCircle, 
  HelpCircle, 
  ArrowRight,
  RefreshCw,
  SlidersHorizontal,
  Activity
} from 'lucide-react'

export const Anomalies: React.FC = () => {
  const [anomalies, setAnomalies] = useState<Anomaly[]>([])
  const [loading, setLoading] = useState(true)
  const [filterSeverity, setFilterSeverity] = useState<string>('all')
  const [selectedFeedbackAnomaly, setSelectedFeedbackAnomaly] = useState<Anomaly | null>(null)
  
  const navigate = useNavigate()
  const wsUrl = import.meta.env.VITE_WS_URL || `ws://${window.location.hostname}:8000/ws/api/v1/updates`
  const { connected, lastMessage } = useWebSocket(wsUrl)

  const fetchAnomalies = async () => {
    try {
      setLoading(true)
      const res = await anomalyAPI.getRecent(100)
      setAnomalies(res.data)
    } catch (err) {
      console.error('Error fetching anomalies stream:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchAnomalies()
  }, [])

  useEffect(() => {
    if (lastMessage && lastMessage.event === 'anomaly_detected' && lastMessage.anomaly) {
      setAnomalies((prev) => [lastMessage.anomaly, ...prev])
    }
  }, [lastMessage])

  const filteredAnomalies = anomalies.filter((a) => {
    if (filterSeverity === 'all') return true
    return a.severity?.toLowerCase() === filterSeverity
  })

  const getSeverityBadge = (severity?: string) => {
    switch (severity?.toLowerCase()) {
      case 'critical':
        return 'bg-red-500/20 text-red-400 border-red-500/30'
      case 'warning':
        return 'bg-amber-500/20 text-amber-400 border-amber-500/30'
      case 'info':
        return 'bg-blue-500/20 text-blue-400 border-blue-500/30'
      default:
        return 'bg-slate-800 text-slate-400 border-slate-700'
    }
  }

  const getSeverityDot = (severity?: string) => {
    switch (severity?.toLowerCase()) {
      case 'critical':
        return 'bg-red-500 shadow-red-500/50'
      case 'warning':
        return 'bg-amber-500 shadow-amber-500/50'
      default:
        return 'bg-blue-500 shadow-blue-500/50'
    }
  }

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-800 pb-6">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold text-white tracking-tight">Anomalies Telemetry Feed</h1>
            <span className="rounded-full bg-blue-500/10 px-2.5 py-0.5 text-xs font-semibold text-blue-400 border border-blue-500/20">
              Live Feed
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">Real-time flagged metric deviations, ensemble scores, and feedback logs</p>
        </div>

        <div className="flex items-center gap-3">
          {/* Severity Filter Tabs */}
          <div className="flex items-center rounded-xl bg-slate-900 border border-slate-800 p-1 text-xs">
            {['all', 'critical', 'warning', 'info'].map((sev) => (
              <button
                key={sev}
                onClick={() => setFilterSeverity(sev)}
                className={`rounded-lg px-3 py-1.5 font-semibold capitalize transition ${
                  filterSeverity === sev
                    ? 'bg-blue-600 text-white shadow-sm'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {sev}
              </button>
            ))}
          </div>

          <button
            onClick={fetchAnomalies}
            className="rounded-xl border border-slate-800 bg-slate-900 p-2.5 text-slate-400 hover:bg-slate-800 hover:text-white transition"
            title="Refresh Feed"
          >
            <RefreshCw className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Feed List Container */}
      <div className="rounded-2xl border border-slate-800 bg-slate-900/60 backdrop-blur-xl overflow-hidden shadow-2xl">
        {loading ? (
          <div className="p-12 text-center text-xs text-slate-400 flex items-center justify-center gap-2">
            <Activity className="h-4 w-4 animate-spin text-blue-400" />
            <span>Fetching real-time anomaly stream...</span>
          </div>
        ) : filteredAnomalies.length === 0 ? (
          <div className="p-12 text-center text-xs text-slate-400 space-y-2">
            <AlertTriangle className="h-8 w-8 text-slate-600 mx-auto" />
            <p className="font-semibold text-slate-300">No anomalies flagged</p>
            <p className="text-slate-500">System telemetry stream is operating cleanly within normal parameters.</p>
          </div>
        ) : (
          <div className="divide-y divide-slate-800/80">
            {filteredAnomalies.map((anomaly) => {
              let parsedReasons: string[] = []
              if (anomaly.reasons) {
                try {
                  parsedReasons = JSON.parse(anomaly.reasons)
                } catch {
                  parsedReasons = [anomaly.reasons]
                }
              }

              return (
                <div
                  key={anomaly.id}
                  className="p-5 hover:bg-slate-800/40 transition flex flex-col md:flex-row md:items-center justify-between gap-4"
                >
                  {/* Left Column: Metric & Ensemble Reasons */}
                  <div className="flex items-start gap-4">
                    <span className={`mt-1.5 h-2.5 w-2.5 rounded-full flex-shrink-0 shadow-lg ${getSeverityDot(anomaly.severity)}`} />
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-sm text-white font-mono">{anomaly.metric_name}</span>
                        {anomaly.severity && (
                          <span className={`rounded px-2 py-0.5 text-[10px] font-bold uppercase border ${getSeverityBadge(anomaly.severity)}`}>
                            {anomaly.severity}
                          </span>
                        )}
                        <span className="text-xs font-semibold text-slate-400 font-mono">
                          Val: <span className="text-blue-400 font-bold">{anomaly.value.toFixed(2)}</span>
                        </span>
                      </div>

                      {/* Reasons / Ensemble Breakdown */}
                      <p className="text-xs text-slate-300">
                        {parsedReasons.length > 0
                          ? parsedReasons.join(' | ')
                          : `Flagged via ${anomaly.detection_method || 'Ensemble Voting'}`}
                      </p>

                      <div className="flex items-center gap-3 text-[11px] text-slate-500 pt-0.5">
                        <span>{new Date(anomaly.anomaly_timestamp).toLocaleString()}</span>
                        <span>•</span>
                        <span>Method: {anomaly.detection_method}</span>
                      </div>
                    </div>
                  </div>

                  {/* Right Column: Confidence, Feedback & Actions */}
                  <div className="flex items-center gap-4 self-end md:self-center">
                    {/* Confidence Meter */}
                    <div className="flex items-center gap-2">
                      <div className="h-1.5 w-20 overflow-hidden rounded-full bg-slate-800">
                        <div
                          className={`h-full rounded-full transition-all duration-300 ${
                            anomaly.confidence_score > 0.8
                              ? 'bg-rose-500'
                              : anomaly.confidence_score > 0.5
                              ? 'bg-amber-500'
                              : 'bg-blue-500'
                          }`}
                          style={{ width: `${Math.min(100, Math.max(10, anomaly.confidence_score * 100))}%` }}
                        />
                      </div>
                      <span className="font-mono text-xs font-semibold text-slate-300 w-10 text-right">
                        {(anomaly.confidence_score * 100).toFixed(0)}%
                      </span>
                    </div>

                    {/* Feedback Status */}
                    <div className="text-xs">
                      {anomaly.feedback_status === 'true_positive' ? (
                        <span className="inline-flex items-center gap-1 rounded-md bg-emerald-950/60 border border-emerald-800 px-2 py-0.5 text-emerald-300 text-[11px]">
                          <CheckCircle2 className="h-3 w-3 text-emerald-400" /> True Positive
                        </span>
                      ) : anomaly.feedback_status === 'false_positive' ? (
                        <span className="inline-flex items-center gap-1 rounded-md bg-rose-950/60 border border-rose-800 px-2 py-0.5 text-rose-300 text-[11px]">
                          <XCircle className="h-3 w-3 text-rose-400" /> False Alarm
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 rounded-md bg-slate-800/80 border border-slate-700 px-2 py-0.5 text-slate-400 text-[11px]">
                          <HelpCircle className="h-3 w-3 text-slate-500" /> Unreviewed
                        </span>
                      )}
                    </div>

                    {/* Actions */}
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => setSelectedFeedbackAnomaly(anomaly)}
                        className="rounded-lg border border-slate-700 bg-slate-800/80 px-2.5 py-1.5 text-xs font-semibold text-slate-200 hover:border-indigo-500/50 hover:bg-indigo-950/40 hover:text-indigo-300 transition"
                        title="Provide ML Feedback"
                      >
                        <Sparkles className="h-3.5 w-3.5" />
                      </button>

                      <button
                        onClick={() => navigate(`/incidents`)}
                        className="flex items-center gap-1 rounded-lg border border-slate-700 bg-slate-800/80 px-3 py-1.5 text-xs font-semibold text-slate-200 hover:bg-slate-700 hover:text-white transition"
                      >
                        <span>Investigate</span>
                        <ArrowRight className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>

      {/* Anomaly Feedback Modal */}
      {selectedFeedbackAnomaly && (
        <AnomalyFeedbackModal
          anomaly={selectedFeedbackAnomaly}
          onClose={() => setSelectedFeedbackAnomaly(null)}
          onFeedbackSubmitted={(updated) => {
            setAnomalies((prev) =>
              prev.map((a) => (a.id === updated.id ? { ...a, ...updated } : a))
            )
          }}
        />
      )}
    </div>
  )
}
