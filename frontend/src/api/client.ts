import axios, { AxiosInstance } from 'axios'

const API_KEY = import.meta.env.VITE_API_KEY || 'pulsewatch_dev_key_change_in_prod'
const API_BASE = import.meta.env.VITE_API_URL || '/api'

const client: AxiosInstance = axios.create({
  baseURL: API_BASE,
  headers: {
    'X-API-Key': API_KEY,
    'Content-Type': 'application/json',
  },
})

export interface RuleConfig {
  id?: string
  metric_name: string
  threshold_value: number
  duration_minutes: number
  severity: string
  enabled: boolean
  recovery_confirmation_minutes?: number | null
}

export interface AnalyticsHealth {
  critical: number
  warning: number
  info: number
}

export interface AnalyticsSummary {
  anomalies: number
  incidents: number
  resolved_incidents: number
  active_alerts: number
  resolved_alerts: number
}

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
  severity?: string
  reasons?: string
  ensemble_scores?: string
  feedback_status?: 'unreviewed' | 'true_positive' | 'false_positive' | string | null
  feedback_note?: string | null
  feedback_at?: string | null
  created_at: string
}

export interface Alert {
  id: string
  anomaly_id: string
  incident_id: string | null
  severity: 'critical' | 'warning' | 'info'
  message: string
  status: 'new' | 'acknowledged' | 'resolved'
  acknowledged_at: string | null
  acknowledged_by: string | null
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
  progress_stage: string | null
  progress_percent: number | null
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
