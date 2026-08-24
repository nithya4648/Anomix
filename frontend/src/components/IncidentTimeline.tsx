import { Incident } from '../api/client'
import { AlertCircle, CheckCircle, Clock } from 'lucide-react'

interface IncidentTimelineProps {
  incidents: Incident[]
}

const getSeverityColor = (severity: string) => {
  switch (severity) {
    case 'critical':
      return 'bg-red-100 border-red-500'
    case 'warning':
      return 'bg-yellow-100 border-yellow-500'
    case 'info':
      return 'bg-blue-100 border-blue-500'
    default:
      return 'bg-gray-100 border-gray-500'
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
      <div className="bg-white rounded-lg shadow p-6 text-center text-gray-500">
        No incidents detected. System operating normally.
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-6">Incident Timeline</h3>

      <div className="space-y-4">
        {incidents.map((incident) => (
          <div
            key={incident.id}
            className={`border-l-4 p-4 rounded ${getSeverityColor(incident.severity)}`}
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  {getStatusIcon(incident.status)}
                  <h4 className="font-semibold text-lg">{incident.title}</h4>
                  <span className={`px-2 py-1 rounded text-xs font-medium ${getSeverityBadgeColor(incident.severity)}`}>
                    {incident.severity.toUpperCase()}
                  </span>
                </div>

                {incident.description && (
                  <p className="text-sm text-gray-700 mb-2">{incident.description}</p>
                )}

                <div className="text-xs text-gray-600">
                  <p>Detected: {new Date(incident.detected_at).toLocaleString()}</p>
                  {incident.resolved_at && (
                    <p>Resolved: {new Date(incident.resolved_at).toLocaleString()}</p>
                  )}
                </div>

                {incident.root_cause && (
                  <div className="mt-3 p-3 bg-gray-50 rounded text-sm">
                    <p className="font-semibold text-gray-700">Root Cause:</p>
                    <p className="text-gray-600">{incident.root_cause}</p>
                  </div>
                )}

                {incident.correlated_metrics && (
                  <div className="mt-2 text-sm">
                    <p className="font-semibold text-gray-700">Affected Metrics:</p>
                    <p className="text-gray-600">{incident.correlated_metrics}</p>
                  </div>
                )}
              </div>

              <span className="text-xs font-medium text-gray-500 px-2 py-1 bg-gray-100 rounded">
                {incident.status}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
