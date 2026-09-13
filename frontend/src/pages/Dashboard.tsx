import { useState, useEffect, useMemo } from 'react'
import { metricAPI, anomalyAPI, incidentAPI, Incident, Anomaly, Metric } from '../api/client'
import { MetricChart } from '../components/MetricChart'
import { IncidentTimeline } from '../components/IncidentTimeline'
import { 
  AlertCircle, 
  TrendingUp, 
  TrendingDown, 
  Cpu, 
  HardDrive, 
  Activity, 
  RefreshCw, 
  CheckCircle2, 
  XCircle, 
  Clock, 
  ShieldAlert, 
  Radio
} from 'lucide-react'
import { useWebSocket } from '../hooks/useWebSocket'

const METRIC_NAMES = ['cpu_usage', 'memory_usage', 'api_latency', 'disk_io', 'request_rate']

interface MetricCardProps {
  title: string
  value: string | number
  unit?: string
  trend?: number
  icon: React.ReactNode
  bgColor: string
  subText?: string
}

const MetricCard: React.FC<MetricCardProps> = ({ title, value, unit, trend, icon, bgColor, subText }) => {
  const isPositiveTrend = trend && trend > 0
  const isNegativeTrend = trend && trend < 0

  return (
    <div className={`relative overflow-hidden rounded-lg ${bgColor} p-6 text-white shadow-md border border-slate-700/50`}>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-white/80">{title}</p>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-3xl font-bold tracking-tight">{value}</span>
            {unit && <span className="text-sm font-medium text-white/80">{unit}</span>}
          </div>
        </div>
        <div className="rounded-lg bg-white/10 p-3 backdrop-blur-sm">
          {icon}
        </div>
      </div>
      
      <div className="mt-4 flex items-center justify-between border-t border-white/10 pt-3 text-xs text-white/90">
        {trend !== undefined ? (
          <div className="flex items-center gap-1 font-semibold">
            {isPositiveTrend ? (
              <TrendingUp className="h-4 w-4 text-emerald-300" />
            ) : isNegativeTrend ? (
              <TrendingDown className="h-4 w-4 text-rose-300" />
            ) : (
              <Activity className="h-4 w-4 text-white/70" />
            )}
            <span className={isPositiveTrend ? 'text-emerald-300' : isNegativeTrend ? 'text-rose-300' : 'text-white/80'}>
              {trend > 0 ? `+${trend.toFixed(1)}%` : `${trend.toFixed(1)}%`}
            </span>
            <span className="text-white/60 font-normal">vs last period</span>
          </div>
        ) : (
          <span>{subText || 'Live telemetry'}</span>
        )}
        <span className="rounded bg-white/20 px-2 py-0.5 text-[10px] font-medium backdrop-blur-md">
          Real-time
        </span>
      </div>
    </div>
  )
}

export const Dashboard = () => {
  const [metrics, setMetrics] = useState<Record<string, Metric[]>>({})
  const [anomalies, setAnomalies] = useState<Anomaly[]>([])
  const [incidents, setIncidents] = useState<Incident[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedMetric, setSelectedMetric] = useState<string>(METRIC_NAMES[0])
  const [autoRefresh, setAutoRefresh] = useState(true)
  const [lastRefreshedAt, setLastRefreshedAt] = useState<Date>(new Date())

  const wsUrl = import.meta.env.VITE_WS_URL || `ws://${window.location.hostname}:8000/ws/api/v1/updates`
  const { connected, subscribe, unsubscribe, onMessage } = useWebSocket(wsUrl)

  const fetchData = async () => {
    try {
      setError(null)
      const metricsData: Record<string, Metric[]> = {}
      
      await Promise.all(
        METRIC_NAMES.map(async (metricName) => {
          try {
            const response = await metricAPI.getRecent(metricName, 100)
            metricsData[metricName] = response.data
          } catch (err) {
            console.error(`Error fetching ${metricName}:`, err)
          }
        })
      )
      setMetrics(metricsData)

      try {
        const anomalyResponse = await anomalyAPI.getRecent(50)
        setAnomalies(anomalyResponse.data)
      } catch (err) {
        console.error('Error fetching anomalies:', err)
      }

      try {
        const incidentResponse = await incidentAPI.getIncidents(undefined, 50)
        setIncidents(incidentResponse.data)
      } catch (err) {
        console.error('Error fetching incidents:', err)
      }

      setLastRefreshedAt(new Date())
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error occurred while fetching metrics')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  useEffect(() => {
    if (!autoRefresh) return
    const interval = setInterval(() => {
      fetchData()
    }, 10000)
    return () => clearInterval(interval)
  }, [autoRefresh])

  useEffect(() => {
    if (connected) {
      METRIC_NAMES.forEach((metric) => subscribe(metric))
    }
    return () => {
      if (connected) {
        METRIC_NAMES.forEach((metric) => unsubscribe(metric))
      }
    }
  }, [connected, subscribe, unsubscribe])

  useEffect(() => {
    const cleanupMetric = onMessage('metric_ingested', (data) => {
      setMetrics((prev) => {
        const metricName = data.metric.metric_name
        const currentMetrics = prev[metricName] || []
        const updated = [data.metric, ...currentMetrics].slice(0, 100)
        return { ...prev, [metricName]: updated }
      })
    })

    return () => {
      cleanupMetric()
    }
  }, [onMessage])

  const activeAnomalies = useMemo(() => anomalies.filter((a) => !a.is_confirmed), [anomalies])
  const criticalIncidents = useMemo(
    () => incidents.filter((i) => i.severity === 'critical' && i.status !== 'resolved'),
    [incidents]
  )

  const calculateTrend = (metricName: string) => {
    const list = metrics[metricName]
    if (!list || list.length < 2) return 0
    const current = list[0].value
    const previous = list[Math.min(10, list.length - 1)].value
    if (previous === 0) return 0
    return ((current - previous) / previous) * 100
  }

  const latestCpu = metrics['cpu_usage']?.[0]?.value?.toFixed(1) || '0.0'
  const latestMem = metrics['memory_usage']?.[0]?.value?.toFixed(1) || '0.0'

  if (loading && Object.keys(metrics).length === 0) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-950 text-slate-200">
        <div className="text-center">
          <p className="text-base font-medium text-slate-300">Loading metrics dashboard...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      {/* Header */}
      <header className="sticky top-0 z-50 border-b border-slate-800 bg-slate-900">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-slate-800 border border-slate-700 text-blue-400">
              <Radio className="h-5 w-5" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-white tracking-tight">Anomix Anomaly Detector</h1>
              <p className="text-xs text-slate-400">System Metrics & Anomaly Detection Dashboard</p>
            </div>
          </div>

          <div className="flex items-center gap-4">
            {/* Connection Status Badge */}
            <div className={`flex items-center gap-2 rounded-md px-2.5 py-1 text-xs font-semibold border ${
              connected 
                ? 'bg-emerald-950 border-emerald-700 text-emerald-300' 
                : 'bg-rose-950 border-rose-700 text-rose-300'
            }`}>
              <span className={`inline-block h-2 w-2 rounded-full ${connected ? 'bg-emerald-400' : 'bg-rose-400'}`}></span>
              <span>{connected ? 'WebSocket Connected' : 'Disconnected'}</span>
            </div>

            {/* Auto Refresh Switch */}
            <div className="flex items-center gap-2 rounded-lg border border-slate-800 bg-slate-900 px-3 py-1.5 text-xs text-slate-300">
              <Clock className="h-3.5 w-3.5 text-slate-400" />
              <span>Auto-refresh</span>
              <button
                onClick={() => setAutoRefresh(!autoRefresh)}
                className={`relative inline-flex h-5 w-9 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
                  autoRefresh ? 'bg-blue-600' : 'bg-slate-700'
                }`}
              >
                <span
                  className={`pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                    autoRefresh ? 'translate-x-4' : 'translate-x-0'
                  }`}
                />
              </button>
              <button
                onClick={() => fetchData()}
                title="Manual refresh"
                className="ml-1 rounded p-1 hover:bg-slate-800 text-slate-400 hover:text-white transition"
              >
                <RefreshCw className="h-3.5 w-3.5" />
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Dashboard Container */}
      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        {/* Error Banner */}
        {error && (
          <div className="mb-6 flex items-center justify-between rounded-lg border border-rose-700 bg-rose-950 p-4 text-rose-200 shadow-md">
            <div className="flex items-center gap-3">
              <XCircle className="h-5 w-5 flex-shrink-0 text-rose-400" />
              <p className="text-sm font-medium">{error}</p>
            </div>
            <button
              onClick={() => setError(null)}
              className="rounded-lg bg-rose-900 px-3 py-1 text-xs font-semibold hover:bg-rose-800 text-white"
            >
              Dismiss
            </button>
          </div>
        )}

        {/* Status Cards */}
        <div className="mb-8 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
          <MetricCard
            title="CPU Usage"
            value={latestCpu}
            unit="%"
            trend={calculateTrend('cpu_usage')}
            icon={<Cpu className="h-6 w-6" />}
            bgColor="bg-blue-600"
          />
          <MetricCard
            title="Memory Usage"
            value={latestMem}
            unit="%"
            trend={calculateTrend('memory_usage')}
            icon={<HardDrive className="h-6 w-6" />}
            bgColor="bg-purple-600"
          />
          <MetricCard
            title="Active Anomalies"
            value={activeAnomalies.length}
            subText="Requires Attention"
            icon={<AlertCircle className="h-6 w-6" />}
            bgColor={activeAnomalies.length > 0 ? "bg-amber-600" : "bg-teal-600"}
          />
          <MetricCard
            title="Critical Incidents"
            value={criticalIncidents.length}
            subText="High Severity"
            icon={<ShieldAlert className="h-6 w-6" />}
            bgColor={criticalIncidents.length > 0 ? "bg-red-600" : "bg-slate-800"}
          />
        </div>

        {/* Metric Selector & Main Visualizer Chart */}
        <div className="mb-8 rounded-lg border border-slate-800 bg-slate-900 p-6 shadow-md">
          <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h2 className="text-lg font-bold text-white">Metric Stream Analyzer</h2>
              <p className="text-xs text-slate-400">Choose a metric to view anomalies</p>
            </div>
            
            <div className="flex flex-wrap gap-2">
              {METRIC_NAMES.map((metric) => (
                <button
                  key={metric}
                  onClick={() => setSelectedMetric(metric)}
                  className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition-colors duration-150 ${
                    selectedMetric === metric
                      ? 'bg-blue-600 text-white'
                      : 'bg-slate-800 text-slate-300 hover:bg-slate-700 hover:text-white border border-slate-700'
                  }`}
                >
                  {metric.replace(/_/g, ' ').toUpperCase()}
                </button>
              ))}
            </div>
          </div>

          <div className="rounded-lg bg-slate-950 p-4 border border-slate-800">
            {selectedMetric && metrics[selectedMetric] && (
              <MetricChart
                metric_name={selectedMetric}
                metrics={metrics[selectedMetric]}
                anomalies={anomalies.filter((a) => a.metric_name === selectedMetric)}
                height={400}
              />
            )}
          </div>
        </div>

        {/* Incident Timeline Component */}
        <div className="mb-8">
          <IncidentTimeline incidents={incidents} />
        </div>

        {/* Enhanced Anomalies Table */}
        <div className="overflow-hidden rounded-lg border border-slate-800 bg-slate-900 shadow-md">
          <div className="flex items-center justify-between border-b border-slate-800 px-6 py-4">
            <div>
              <h3 className="text-lg font-bold text-white">Recent Anomalies Log</h3>
              <p className="text-xs text-slate-400">Real-time flagged metric deviations</p>
            </div>
            <span className="rounded-md bg-slate-800 px-2.5 py-1 text-xs font-medium text-slate-300 border border-slate-700">
              Showing {activeAnomalies.slice(0, 10).length} of {activeAnomalies.length}
            </span>
          </div>

          {activeAnomalies.length === 0 ? (
            <div className="flex flex-col items-center justify-center px-6 py-12 text-center">
              <CheckCircle2 className="mb-3 h-12 w-12 text-emerald-500 opacity-80" />
              <h4 className="text-base font-semibold text-slate-200">System Healthy</h4>
              <p className="mt-1 text-xs text-slate-400">No active anomalies detected across all telemetry feeds.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm text-slate-300">
                <thead className="border-b border-slate-800 bg-slate-950 text-xs uppercase tracking-wider text-slate-400">
                  <tr>
                    <th className="px-6 py-3.5 font-semibold">Metric</th>
                    <th className="px-6 py-3.5 font-semibold">Detection Method</th>
                    <th className="px-6 py-3.5 font-semibold">Value</th>
                    <th className="px-6 py-3.5 font-semibold">Confidence</th>
                    <th className="px-6 py-3.5 font-semibold">Timestamp</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800">
                  {activeAnomalies.slice(0, 10).map((anomaly) => (
                    <tr key={anomaly.id} className="transition-colors hover:bg-slate-800/60">
                      <td className="px-6 py-4 font-semibold text-white">
                        <div className="flex items-center gap-2">
                          <span className="h-2 w-2 rounded-full bg-blue-500"></span>
                          {anomaly.metric_name}
                        </div>
                      </td>
                      <td className="px-6 py-4 text-xs font-medium">
                        <span className="rounded-md bg-slate-800 px-2.5 py-1 text-slate-300 border border-slate-700">
                          {anomaly.detection_method || 'Z-Score / Autoencoder'}
                        </span>
                      </td>
                      <td className="px-6 py-4 font-mono font-bold text-blue-400">
                        {anomaly.value.toFixed(2)}
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-3">
                          <div className="h-2 w-28 overflow-hidden rounded bg-slate-800">
                            <div
                              className={`h-full rounded transition-all duration-300 ${
                                anomaly.confidence_score > 0.8
                                  ? 'bg-rose-500'
                                  : anomaly.confidence_score > 0.5
                                  ? 'bg-amber-500'
                                  : 'bg-blue-500'
                              }`}
                              style={{ width: `${Math.min(100, Math.max(10, anomaly.confidence_score * 100))}%` }}
                            />
                          </div>
                          <span className="font-mono text-xs font-semibold text-slate-300">
                            {(anomaly.confidence_score * 100).toFixed(0)}%
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4 text-xs text-slate-400">
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

