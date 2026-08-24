import axios, { AxiosInstance } from 'axios'

const API_KEY = import.meta.env.VITE_API_KEY || 'pulsewatch_dev_key_change_in_prod'
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const client: AxiosInstance = axios.create({
  baseURL: API_BASE,
  headers: {
    'X-API-Key': API_KEY,
    'Content-Type': 'application/json',
  },
})

export interface Metric {
  id: string
  metric_name: string
  value: number
  timestamp: string
  labels: Record<string, any>
  created_at: string
}

export interface Anomaly {
  id: string
  metric_name: string
  metric_id: string
  anomaly_timestamp: string
  value: number
  confidence_score: number
  detection_method: string
  z_score: number | null
  expected_value: number | null
  is_confirmed: boolean
  created_at: string
}

export interface Alert {
  id: string
  anomaly_id: string
  incident_id: string | null
  severity: 'critical' | 'warning' | 'info'
  message: string
  is_resolved: boolean
  resolved_at: string | null
  created_at: string
}

export interface Incident {
  id: string
  title: string
  description: string | null
  status: 'open' | 'investigating' | 'resolved'
  severity: 'critical' | 'warning' | 'info'
  detected_at: string
  resolved_at: string | null
  root_cause: string | null
  correlated_metrics: string | null
  confidence: number | null
  created_at: string
}

export interface EvaluationMetric {
  id: string
  metric_name: string
  evaluation_period_start: string
  evaluation_period_end: string
  evaluated_at: string
  precision: number
  recall: number
  f1_score: number
  confusion_matrix: {
    true_positives: number
    false_positives: number
    true_negatives: number
    false_negatives: number
  }
  total_samples: number
  anomaly_count: number
  detection_method: string
  created_at: string
}

export const metricAPI = {
  getRecent: (metric_name: string, limit: number = 100) =>
    client.get<Metric[]>(`/api/v1/metrics/recent`, {
      params: { metric_name, limit },
    }),

  getRange: (metric_name: string, start_time: string, end_time: string) =>
    client.get<Metric[]>(`/api/v1/metrics/range`, {
      params: { metric_name, start_time, end_time },
    }),
}

export const anomalyAPI = {
  getAnomalies: (metric_name: string, limit: number = 100) =>
    client.get<Anomaly[]>(`/api/v1/anomalies`, {
      params: { metric_name, limit },
    }),

  getRecent: (limit: number = 50) =>
    client.get<Anomaly[]>(`/api/v1/anomalies/recent`, {
      params: { limit },
    }),
}

export const incidentAPI = {
  getIncidents: (status?: string, limit: number = 100) =>
    client.get<Incident[]>(`/api/v1/incidents`, {
      params: { status, limit },
    }),

  resolve: (incident_id: string, root_cause?: string) =>
    client.post<Incident>(`/api/v1/incidents/${incident_id}/resolve`, {
      root_cause,
    }),
}

export const mlAPI = {
  evaluate: (metric_name: string, period_hours: number = 24) =>
    client.post<EvaluationMetric>(`/api/v1/ml/evaluation/${metric_name}`, {
      period_hours,
    }),

  getEvaluationHistory: (metric_name: string, limit: number = 10) =>
    client.get<EvaluationMetric[]>(`/api/v1/ml/evaluation/${metric_name}`, {
      params: { limit },
    }),

  getLatestEvaluation: (metric_name: string) =>
    client.get<EvaluationMetric | null>(`/api/v1/ml/evaluation/${metric_name}/latest`),
}

export default client
