import { useState, useEffect } from 'react'
import { metricAPI, anomalyAPI, incidentAPI, Incident, Anomaly, Metric } from '../api/client'
import { MetricChart } from '../components/MetricChart'
import { IncidentTimeline } from '../components/IncidentTimeline'
import { AlertCircle, TrendingUp } from 'lucide-react'
import { useWebSocket } from '../hooks/useWebSocket'

const METRIC_NAMES = ['cpu_usage', 'memory_usage', 'api_latency', 'disk_io', 'request_rate']

export const Dashboard = () => {
  const [metrics, setMetrics] = useState<Record<string, Metric[]>>({})
  const [anomalies, setAnomalies] = useState<Anomaly[]>([])
  const [incidents, setIncidents] = useState<Incident[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedMetric, setSelectedMetric] = useState<string>(METRIC_NAMES[0])
  const wsUrl = import.meta.env.VITE_WS_URL || `ws://${window.location.hostname}:8000/ws/api/v1/updates`
  const { connected, subscribe, unsubscribe, onMessage } = useWebSocket(wsUrl)

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true)
        setError(null)

        // Fetch metrics for all metric types
        const metricsData: Record<string, Metric[]> = {}
        for (const metricName of METRIC_NAMES) {
          try {
            const response = await metricAPI.getRecent(metricName, 100)
            metricsData[metricName] = response.data
          } catch (err) {
            console.error(`Error fetching ${metricName}:`, err)
          }
        }
        setMetrics(metricsData)

        // Fetch recent anomalies
        try {
          const anomalyResponse = await anomalyAPI.getRecent(50)
          setAnomalies(anomalyResponse.data)
        } catch (err) {
          console.error('Error fetching anomalies:', err)
        }

        // Fetch incidents
        try {
          const incidentResponse = await incidentAPI.getIncidents(undefined, 50)
          setIncidents(incidentResponse.data)
        } catch (err) {
          console.error('Error fetching incidents:', err)
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error occurred')
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [])

  useEffect(() => {
    if (connected) {
      METRIC_NAMES.forEach(metric => subscribe(metric))
    }
    return () => {
      if (connected) {
        METRIC_NAMES.forEach(metric => unsubscribe(metric))
      }
    }
  }, [connected, subscribe, unsubscribe])

  useEffect(() => {
    const cleanupMetric = onMessage('metric_ingested', (data) => {
      setMetrics(prev => {
        const metricName = data.metric.metric_name;
        const currentMetrics = prev[metricName] || [];
        // Keep only last 100
        const updated = [data.metric, ...currentMetrics].slice(0, 100);
        return { ...prev, [metricName]: updated };
      });
      if (data.anomaly_detected && data.alert) {
         // Optionally handle new anomalies, but the instructions focus on charts.
         // Let's refetch anomalies for simplicity or just let the user see it on refresh for now.
      }
    });
    
    return () => {
      cleanupMetric();
    }
  }, [onMessage])

  const activeAnomalies = anomalies.filter(a => !a.is_confirmed)
  const criticalIncidents = incidents.filter(i => i.severity === 'critical' && i.status !== 'resolved')

  if (loading && Object.keys(metrics).length === 0) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 py-6 sm:px-6 lg:px-8">
          <h1 className="text-3xl font-bold text-gray-900">PulseWatch Dashboard</h1>
          <p className="mt-2 text-gray-600">Real-time anomaly detection and monitoring</p>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
        {error && (
          <div className="mb-4 bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-red-700">{error}</p>
          </div>
        )}

        {/* Status Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="flex-1">
                <p className="text-gray-600 text-sm">Active Anomalies</p>
                <p className="text-3xl font-bold text-blue-600">{activeAnomalies.length}</p>
              </div>
              <AlertCircle className="w-10 h-10 text-blue-500 opacity-20" />
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="flex-1">
                <p className="text-gray-600 text-sm">Critical Incidents</p>
                <p className="text-3xl font-bold text-red-600">{criticalIncidents.length}</p>
              </div>
              <AlertCircle className="w-10 h-10 text-red-500 opacity-20" />
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="flex-1">
                <p className="text-gray-600 text-sm">Total Incidents</p>
                <p className="text-3xl font-bold text-gray-600">{incidents.length}</p>
              </div>
              <TrendingUp className="w-10 h-10 text-gray-500 opacity-20" />
            </div>
          </div>
        </div>

        {/* Metric Charts */}
        <div className="mb-8">
          <div className="flex gap-2 mb-4 overflow-x-auto pb-2">
            {METRIC_NAMES.map((metric) => (
              <button
                key={metric}
                onClick={() => setSelectedMetric(metric)}
                className={`px-4 py-2 rounded-lg font-medium whitespace-nowrap transition ${
                  selectedMetric === metric
                    ? 'bg-blue-500 text-white'
                    : 'bg-white text-gray-700 border border-gray-200 hover:bg-gray-50'
                }`}
              >
                {metric.replace(/_/g, ' ')}
              </button>
            ))}
          </div>

          {selectedMetric && metrics[selectedMetric] && (
            <MetricChart
              metric_name={selectedMetric}
              metrics={metrics[selectedMetric]}
              anomalies={anomalies.filter(a => a.metric_name === selectedMetric)}
              height={400}
            />
          )}
        </div>

        {/* Incident Timeline */}
        <div className="mb-8">
          <IncidentTimeline incidents={incidents} />
        </div>

        {/* Anomalies Table */}
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-semibold">Recent Anomalies</h3>
          </div>

          {activeAnomalies.length === 0 ? (
            <div className="px-6 py-8 text-center text-gray-500">
              No active anomalies. System operating normally.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 border-b border-gray-200">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">Metric</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">Value</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">Confidence</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">Time</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {activeAnomalies.slice(0, 10).map((anomaly) => (
                    <tr key={anomaly.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 text-sm font-medium text-gray-900">{anomaly.metric_name}</td>
                      <td className="px-6 py-4 text-sm text-gray-600">{anomaly.value.toFixed(2)}</td>
                      <td className="px-6 py-4 text-sm">
                        <div className="flex items-center">
                          <div className="w-24 bg-gray-200 rounded-full h-2">
                            <div
                              className="bg-red-500 h-2 rounded-full"
                              style={{ width: `${anomaly.confidence_score * 100}%` }}
                            ></div>
                          </div>
                          <span className="ml-2 text-xs font-medium text-gray-700">
                            {(anomaly.confidence_score * 100).toFixed(0)}%
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-600">
                        {new Date(anomaly.anomaly_timestamp).toLocaleString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </main>
    </div>
  )
}
