/**
 * Anomix shared domain types.
 * Imported by api/client.ts and re-exported from there so all existing
 * `from '../api/client'` imports continue to work without change.
 */

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
