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
    <div className="w-full bg-white rounded-lg shadow p-4">
      <h3 className="text-lg font-semibold mb-4">{metric_name}</h3>

      <ResponsiveContainer width="100%" height={height}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            dataKey="timestamp"
            angle={-45}
            textAnchor="end"
            height={80}
          />
          <YAxis />
          <Tooltip
            formatter={(value) => value.toFixed(2)}
            labelFormatter={(label) => `Time: ${label}`}
          />
          <Legend />
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
        <div className="mt-4 text-sm text-gray-600">
          Anomalies detected: {anomalies.length}
        </div>
      )}
    </div>
  )
}
