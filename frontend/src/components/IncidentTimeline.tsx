import { Incident } from '../api/client'
import { AlertCircle, CheckCircle, Clock } from 'lucide-react'

interface IncidentTimelineProps {
  incidents: Incident[]
}

const getSeverityColor = (severity: string) => {
  switch (severity) {
    case 'critical':
      return 'bg-red-950 border-red-600'
    case 'warning':
      return 'bg-amber-950 border-amber-600'
    case 'info':
      return 'bg-blue-950 border-blue-600'
    default:
      return 'bg-slate-800 border-slate-600'
  }
}

const getSeverityBadgeColor = (severity: string) => {
  switch (severity) {
    case 'critical':
      return 'bg-red-500 text-white'
    case 'warning':
      return 'bg-yellow-500 text-white'
    case 'info':
      return 'bg-blue-500 text-white'
    default:
      return 'bg-gray-500 text-white'
  }
}

const getStatusIcon = (status: string) => {
  switch (status) {
    case 'resolved':
      return <CheckCircle className="w-5 h-5 text-green-500" />
    case 'investigating':
      return <Clock className="w-5 h-5 text-yellow-500" />
    default:
      return <AlertCircle className="w-5 h-5 text-red-500" />
  }
}

export const IncidentTimeline = ({ incidents }: IncidentTimelineProps) => {
  if (incidents.length === 0) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-lg p-6 text-center text-slate-400">
        No incidents detected. System operating normally.
      </div>
    )
  }

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-lg p-6">
      <h3 className="text-lg font-bold text-white mb-6">Incident Timeline</h3>

      <div className="space-y-4">
        {incidents.map((incident) => (
          <div
            key={incident.id}
            className={`border-l-4 p-4 rounded-lg ${getSeverityColor(incident.severity)}`}
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  {getStatusIcon(incident.status)}
                  <h4 className="font-semibold text-lg text-white">{incident.title}</h4>
                  <span className={`px-2 py-1 rounded-md text-xs font-medium ${getSeverityBadgeColor(incident.severity)}`}>
                    {incident.severity.toUpperCase()}
                  </span>
                </div>

                {incident.description && (
                  <p className="text-sm text-slate-200 mb-2">{incident.description}</p>
                )}

                <div className="text-xs text-slate-400">
                  <p>Detected: {new Date(incident.detected_at).toLocaleString()}</p>
                  {incident.resolved_at && (
                    <p>Resolved: {new Date(incident.resolved_at).toLocaleString()}</p>
                  )}
                </div>

                {incident.root_cause && (
                  <div className="mt-3 p-3 bg-slate-800 rounded-lg text-sm border border-slate-700">
                    <p className="font-semibold text-slate-200">Root Cause:</p>
                    <p className="text-slate-300">{incident.root_cause}</p>
                  </div>
                )}

                {incident.correlated_metrics && (
                  <div className="mt-2 text-sm">
                    <p className="font-semibold text-slate-200">Affected Metrics:</p>
                    <p className="text-slate-300">{incident.correlated_metrics}</p>
                  </div>
                )}
              </div>

              <span className="text-xs font-medium text-slate-300 px-2 py-1 bg-slate-800 border border-slate-700 rounded-md">
                {incident.status}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

