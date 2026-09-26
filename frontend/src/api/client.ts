import axios, { AxiosInstance } from 'axios'

// Domain types live in src/types — re-exported here so all existing
// `from '../api/client'` imports continue to work without change.
export type {
  RuleConfig,
  AnalyticsHealth,
  AnalyticsSummary,
  Metric,
  Anomaly,
  Alert,
  Incident,
  EvaluationMetric,
} from '../types'

// IMPORTANT: VITE_API_KEY must be configured in Vercel's environment variables and must
// exactly match the backend's API_KEY environment variable set on Render.
// Note: Vite bakes environment variables into client bundles at build time, so a full
// rebuild (re-deploy) is required on Vercel whenever VITE_API_KEY is updated.
const API_KEY = import.meta.env.VITE_API_KEY || 'anomix_dev_key_change_in_prod'
const API_BASE = import.meta.env.VITE_API_URL || '/api'

const client: AxiosInstance = axios.create({
  baseURL: API_BASE,
  headers: {
    'X-API-Key': API_KEY,
    'Content-Type': 'application/json',
  },
})

// Automatically attach JWT authorization token if available in localStorage
client.interceptors.request.use((config) => {
  const token =
    localStorage.getItem('authToken') ||
    localStorage.getItem('access_token') ||
    localStorage.getItem('token')
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})


export const metricAPI = {
  getRecent: (metric_name: string, limit: number = 100) =>
    client.get<Metric[]>(`/v1/metrics/recent`, {
      params: { metric_name, limit },
    }),

  getRange: (metric_name: string, start_time: string, end_time: string) =>
    client.get<Metric[]>(`/v1/metrics/range`, {
      params: { metric_name, start_time, end_time },
    }),
}

export const anomalyAPI = {
  getAnomalies: (metric_name: string, limit: number = 100) =>
    client.get<Anomaly[]>(`/v1/anomalies`, {
      params: { metric_name, limit },
    }),

  getRecent: (limit: number = 50) =>
    client.get<Anomaly[]>(`/v1/anomalies/recent`, {
      params: { limit },
    }),

  addFeedback: (anomalyId: string, feedback_status: string, feedback_note?: string) =>
    client.post<Anomaly>(`/v1/anomalies/${anomalyId}/feedback`, {
      feedback_status,
      feedback_note,
    }),
}

export const alertAPI = {
  getAlerts: (status_filter?: string, severity?: string, limit: number = 100) =>
    client.get<Alert[]>(`/v1/alerts`, {
      params: { status_filter, severity, limit },
    }),

  acknowledge: (alert_id: string, acknowledged_by: string = 'system') =>
    client.post<Alert>(`/v1/alerts/${alert_id}/acknowledge`, null, {
      params: { acknowledged_by },
    }),

  resolve: (alert_id: string) =>
    client.post<Alert>(`/v1/alerts/${alert_id}/resolve`),
}

export const incidentAPI = {
  getIncidents: (status?: string, limit: number = 100) =>
    client.get<Incident[]>(`/v1/incidents`, {
      params: { status, limit },
    }),

  getIncident: (incident_id: string) =>
    client.get<Incident>(`/v1/incidents/${incident_id}`),

  resolve: (incident_id: string, root_cause?: string) =>
    client.post<Incident>(`/v1/incidents/${incident_id}/resolve`, {
      root_cause,
    }),
}

export const ruleAPI = {
  getRules: () =>
    client.get<RuleConfig[]>(`/config/rules/`),

  createRule: (rule: RuleConfig) =>
    client.post<RuleConfig>(`/config/rules/`, rule),

  updateRule: (rule_id: string, rule: Partial<RuleConfig>) =>
    client.put<RuleConfig>(`/config/rules/${rule_id}`, rule),

  deleteRule: (rule_id: string) =>
    client.delete<{ detail: string }>(`/config/rules/${rule_id}`),
}

export const analyticsAPI = {
  getHealth: () =>
    client.get<AnalyticsHealth>(`/analytics/health`),

  getSummary: () =>
    client.get<AnalyticsSummary>(`/analytics/summary`),

  getMethods: () =>
    client.get<Record<string, number>>(`/analytics/methods`),
}

export const mlAPI = {
  evaluate: (metric_name: string, period_hours: number = 24) =>
    client.post<EvaluationMetric>(`/v1/ml/evaluation/${metric_name}`, {
      period_hours,
    }),

  getEvaluationHistory: (metric_name: string, limit: number = 10) =>
    client.get<EvaluationMetric[]>(`/v1/ml/evaluation/${metric_name}`, {
      params: { limit },
    }),

  getLatestEvaluation: (metric_name: string) =>
    client.get<EvaluationMetric | null>(`/v1/ml/evaluation/${metric_name}/latest`),
}

export default client
