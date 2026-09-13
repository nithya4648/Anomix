import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { Metric, Anomaly } from '../api/client'

interface MetricChartProps {
  metric_name: string
  metrics: Metric[]
  anomalies: Anomaly[]
  height?: number
}

export const MetricChart = ({
  metric_name,
  metrics,
  anomalies,
  height = 400,
}: MetricChartProps) => {
  // Prepare data for chart
  const chartData = metrics.map((metric) => {
    const isAnomaly = anomalies.some(a => a.metric_id === metric.id)
    return {
      timestamp: new Date(metric.timestamp).toLocaleTimeString(),
      value: metric.value,
      isAnomaly,
    }
  })

  return (
    <div className="w-full bg-slate-900 rounded-lg border border-slate-800 p-4">
      <h3 className="text-lg font-semibold mb-4 text-white">{metric_name}</h3>

      <ResponsiveContainer width="100%" height={height}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
          <XAxis
            dataKey="timestamp"
            angle={-45}
            textAnchor="end"
            height={80}
            stroke="#94a3b8"
          />
          <YAxis stroke="#94a3b8" />
          <Tooltip
            contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', color: '#f8fafc' }}
            formatter={(value: any) => typeof value === 'number' ? value.toFixed(2) : value}
            labelFormatter={(label) => `Time: ${label}`}
          />
          <Legend wrapperStyle={{ color: '#cbd5e1' }} />
          <Line
            type="monotone"
            dataKey="value"
            stroke="#3b82f6"
            dot={{
              fill: '#3b82f6',
              r: 4,
            }}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>

      {anomalies.length > 0 && (
        <div className="mt-4 text-sm text-slate-300">
          Anomalies detected: {anomalies.length}
        </div>
      )}
    </div>
  )
}

