-- Reconcile existing PostgreSQL tables with the current SQLAlchemy models.
-- This migration changes columns only. It assumes the model tables already exist.
-- Run once with: psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f migrations/001_reconcile_model_schema.sql

BEGIN;

-- alerts
ALTER TABLE alerts ADD COLUMN IF NOT EXISTS id VARCHAR;
ALTER TABLE alerts ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE alerts ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE alerts ADD COLUMN IF NOT EXISTS anomaly_id VARCHAR(36);
ALTER TABLE alerts ADD COLUMN IF NOT EXISTS incident_id VARCHAR(36);
ALTER TABLE alerts ADD COLUMN IF NOT EXISTS severity VARCHAR(50);
ALTER TABLE alerts ADD COLUMN IF NOT EXISTS message VARCHAR(512);
ALTER TABLE alerts ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'new';
ALTER TABLE alerts ADD COLUMN IF NOT EXISTS acknowledged_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE alerts ADD COLUMN IF NOT EXISTS acknowledged_by VARCHAR(100);
ALTER TABLE alerts ADD COLUMN IF NOT EXISTS resolved_at TIMESTAMP WITH TIME ZONE;

ALTER TABLE alerts ALTER COLUMN id SET NOT NULL;
UPDATE alerts SET created_at = now() WHERE created_at IS NULL;
UPDATE alerts SET updated_at = now() WHERE updated_at IS NULL;
ALTER TABLE alerts ALTER COLUMN created_at SET NOT NULL;
ALTER TABLE alerts ALTER COLUMN updated_at SET NOT NULL;
ALTER TABLE alerts ALTER COLUMN anomaly_id SET NOT NULL;
ALTER TABLE alerts ALTER COLUMN incident_id DROP NOT NULL;
ALTER TABLE alerts ALTER COLUMN severity SET NOT NULL;
ALTER TABLE alerts ALTER COLUMN message SET NOT NULL;
UPDATE alerts SET status = 'new' WHERE status IS NULL;
ALTER TABLE alerts ALTER COLUMN status SET NOT NULL, ALTER COLUMN status DROP DEFAULT;
ALTER TABLE alerts ALTER COLUMN acknowledged_at DROP NOT NULL;
ALTER TABLE alerts ALTER COLUMN acknowledged_by DROP NOT NULL;
ALTER TABLE alerts ALTER COLUMN resolved_at DROP NOT NULL;

-- incidents
ALTER TABLE incidents ADD COLUMN IF NOT EXISTS id VARCHAR;
ALTER TABLE incidents ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE incidents ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE incidents ADD COLUMN IF NOT EXISTS title VARCHAR(256);
ALTER TABLE incidents ADD COLUMN IF NOT EXISTS description TEXT;
ALTER TABLE incidents ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'open';
ALTER TABLE incidents ADD COLUMN IF NOT EXISTS severity VARCHAR(50);
ALTER TABLE incidents ADD COLUMN IF NOT EXISTS detected_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE incidents ADD COLUMN IF NOT EXISTS resolved_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE incidents ADD COLUMN IF NOT EXISTS root_cause TEXT;
ALTER TABLE incidents ADD COLUMN IF NOT EXISTS correlated_metrics VARCHAR(1024);
ALTER TABLE incidents ADD COLUMN IF NOT EXISTS confidence FLOAT;
ALTER TABLE incidents ADD COLUMN IF NOT EXISTS progress_stage VARCHAR(50) DEFAULT 'detecting';
ALTER TABLE incidents ADD COLUMN IF NOT EXISTS progress_percent INTEGER DEFAULT 0;

ALTER TABLE incidents ALTER COLUMN id SET NOT NULL;
UPDATE incidents SET created_at = now() WHERE created_at IS NULL;
UPDATE incidents SET updated_at = now() WHERE updated_at IS NULL;
ALTER TABLE incidents ALTER COLUMN created_at SET NOT NULL;
ALTER TABLE incidents ALTER COLUMN updated_at SET NOT NULL;
ALTER TABLE incidents ALTER COLUMN title SET NOT NULL;
ALTER TABLE incidents ALTER COLUMN description DROP NOT NULL;
UPDATE incidents SET status = 'open' WHERE status IS NULL;
ALTER TABLE incidents ALTER COLUMN status SET NOT NULL, ALTER COLUMN status DROP DEFAULT;
ALTER TABLE incidents ALTER COLUMN severity SET NOT NULL;
ALTER TABLE incidents ALTER COLUMN detected_at SET NOT NULL;
ALTER TABLE incidents ALTER COLUMN resolved_at DROP NOT NULL;
ALTER TABLE incidents ALTER COLUMN root_cause DROP NOT NULL;
ALTER TABLE incidents ALTER COLUMN correlated_metrics DROP NOT NULL;
ALTER TABLE incidents ALTER COLUMN confidence DROP NOT NULL;
ALTER TABLE incidents ALTER COLUMN progress_stage DROP NOT NULL, ALTER COLUMN progress_stage DROP DEFAULT;
ALTER TABLE incidents ALTER COLUMN progress_percent DROP NOT NULL, ALTER COLUMN progress_percent DROP DEFAULT;

-- anomalies
ALTER TABLE anomalies ADD COLUMN IF NOT EXISTS id VARCHAR;
ALTER TABLE anomalies ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE anomalies ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE anomalies ADD COLUMN IF NOT EXISTS metric_name VARCHAR(256);
ALTER TABLE anomalies ADD COLUMN IF NOT EXISTS metric_id VARCHAR(36);
ALTER TABLE anomalies ADD COLUMN IF NOT EXISTS anomaly_timestamp TIMESTAMP WITH TIME ZONE;
ALTER TABLE anomalies ADD COLUMN IF NOT EXISTS value FLOAT;
ALTER TABLE anomalies ADD COLUMN IF NOT EXISTS confidence_score FLOAT;
ALTER TABLE anomalies ADD COLUMN IF NOT EXISTS detection_method VARCHAR(50);
ALTER TABLE anomalies ADD COLUMN IF NOT EXISTS z_score FLOAT;
ALTER TABLE anomalies ADD COLUMN IF NOT EXISTS expected_value FLOAT;
ALTER TABLE anomalies ADD COLUMN IF NOT EXISTS is_confirmed BOOLEAN DEFAULT false;
ALTER TABLE anomalies ADD COLUMN IF NOT EXISTS severity VARCHAR(50);
ALTER TABLE anomalies ADD COLUMN IF NOT EXISTS reasons TEXT;
ALTER TABLE anomalies ADD COLUMN IF NOT EXISTS ensemble_scores TEXT;
ALTER TABLE anomalies ADD COLUMN IF NOT EXISTS feedback_status VARCHAR(20) DEFAULT 'unreviewed';
ALTER TABLE anomalies ADD COLUMN IF NOT EXISTS feedback_note TEXT;
ALTER TABLE anomalies ADD COLUMN IF NOT EXISTS feedback_at TIMESTAMP WITH TIME ZONE;

ALTER TABLE anomalies ALTER COLUMN id SET NOT NULL;
UPDATE anomalies SET created_at = now() WHERE created_at IS NULL;
UPDATE anomalies SET updated_at = now() WHERE updated_at IS NULL;
ALTER TABLE anomalies ALTER COLUMN created_at SET NOT NULL;
ALTER TABLE anomalies ALTER COLUMN updated_at SET NOT NULL;
ALTER TABLE anomalies ALTER COLUMN metric_name SET NOT NULL;
ALTER TABLE anomalies ALTER COLUMN metric_id SET NOT NULL;
ALTER TABLE anomalies ALTER COLUMN anomaly_timestamp SET NOT NULL;
ALTER TABLE anomalies ALTER COLUMN value SET NOT NULL;
ALTER TABLE anomalies ALTER COLUMN confidence_score SET NOT NULL;
ALTER TABLE anomalies ALTER COLUMN detection_method SET NOT NULL;
ALTER TABLE anomalies ALTER COLUMN z_score DROP NOT NULL;
ALTER TABLE anomalies ALTER COLUMN expected_value DROP NOT NULL;
UPDATE anomalies SET is_confirmed = false WHERE is_confirmed IS NULL;
ALTER TABLE anomalies ALTER COLUMN is_confirmed SET NOT NULL, ALTER COLUMN is_confirmed DROP DEFAULT;
ALTER TABLE anomalies ALTER COLUMN severity DROP NOT NULL;
ALTER TABLE anomalies ALTER COLUMN reasons DROP NOT NULL;
ALTER TABLE anomalies ALTER COLUMN ensemble_scores DROP NOT NULL;
UPDATE anomalies SET feedback_status = 'unreviewed' WHERE feedback_status IS NULL;
ALTER TABLE anomalies ALTER COLUMN feedback_status SET NOT NULL;
ALTER TABLE anomalies ALTER COLUMN feedback_note DROP NOT NULL;
ALTER TABLE anomalies ALTER COLUMN feedback_at DROP NOT NULL;

-- metrics
ALTER TABLE metrics ADD COLUMN IF NOT EXISTS id VARCHAR;
ALTER TABLE metrics ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE metrics ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE metrics ADD COLUMN IF NOT EXISTS metric_name VARCHAR(256);
ALTER TABLE metrics ADD COLUMN IF NOT EXISTS value FLOAT;
ALTER TABLE metrics ADD COLUMN IF NOT EXISTS timestamp TIMESTAMP WITH TIME ZONE;
ALTER TABLE metrics ADD COLUMN IF NOT EXISTS labels JSON DEFAULT '{}'::json;

ALTER TABLE metrics ALTER COLUMN id SET NOT NULL;
UPDATE metrics SET created_at = now() WHERE created_at IS NULL;
UPDATE metrics SET updated_at = now() WHERE updated_at IS NULL;
ALTER TABLE metrics ALTER COLUMN created_at SET NOT NULL;
ALTER TABLE metrics ALTER COLUMN updated_at SET NOT NULL;
ALTER TABLE metrics ALTER COLUMN metric_name SET NOT NULL;
ALTER TABLE metrics ALTER COLUMN value SET NOT NULL;
ALTER TABLE metrics ALTER COLUMN timestamp SET NOT NULL;
UPDATE metrics SET labels = '{}'::json WHERE labels IS NULL;
ALTER TABLE metrics ALTER COLUMN labels SET NOT NULL, ALTER COLUMN labels DROP DEFAULT;

-- evaluation_metrics
ALTER TABLE evaluation_metrics ADD COLUMN IF NOT EXISTS id VARCHAR;
ALTER TABLE evaluation_metrics ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE evaluation_metrics ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE evaluation_metrics ADD COLUMN IF NOT EXISTS metric_name VARCHAR(256);
ALTER TABLE evaluation_metrics ADD COLUMN IF NOT EXISTS evaluation_period_start TIMESTAMP WITH TIME ZONE;
ALTER TABLE evaluation_metrics ADD COLUMN IF NOT EXISTS evaluation_period_end TIMESTAMP WITH TIME ZONE;
ALTER TABLE evaluation_metrics ADD COLUMN IF NOT EXISTS evaluated_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE evaluation_metrics ADD COLUMN IF NOT EXISTS precision FLOAT;
ALTER TABLE evaluation_metrics ADD COLUMN IF NOT EXISTS recall FLOAT;
ALTER TABLE evaluation_metrics ADD COLUMN IF NOT EXISTS f1_score FLOAT;
ALTER TABLE evaluation_metrics ADD COLUMN IF NOT EXISTS true_positives INTEGER;
ALTER TABLE evaluation_metrics ADD COLUMN IF NOT EXISTS false_positives INTEGER;
ALTER TABLE evaluation_metrics ADD COLUMN IF NOT EXISTS true_negatives INTEGER;
ALTER TABLE evaluation_metrics ADD COLUMN IF NOT EXISTS false_negatives INTEGER;
ALTER TABLE evaluation_metrics ADD COLUMN IF NOT EXISTS total_samples INTEGER;
ALTER TABLE evaluation_metrics ADD COLUMN IF NOT EXISTS anomaly_count INTEGER;
ALTER TABLE evaluation_metrics ADD COLUMN IF NOT EXISTS detection_method VARCHAR(50);

ALTER TABLE evaluation_metrics ALTER COLUMN id SET NOT NULL;
UPDATE evaluation_metrics SET created_at = now() WHERE created_at IS NULL;
UPDATE evaluation_metrics SET updated_at = now() WHERE updated_at IS NULL;
ALTER TABLE evaluation_metrics ALTER COLUMN created_at SET NOT NULL;
ALTER TABLE evaluation_metrics ALTER COLUMN updated_at SET NOT NULL;
ALTER TABLE evaluation_metrics ALTER COLUMN metric_name SET NOT NULL;
ALTER TABLE evaluation_metrics ALTER COLUMN evaluation_period_start SET NOT NULL;
ALTER TABLE evaluation_metrics ALTER COLUMN evaluation_period_end SET NOT NULL;
ALTER TABLE evaluation_metrics ALTER COLUMN evaluated_at SET NOT NULL;
ALTER TABLE evaluation_metrics ALTER COLUMN precision SET NOT NULL;
ALTER TABLE evaluation_metrics ALTER COLUMN recall SET NOT NULL;
ALTER TABLE evaluation_metrics ALTER COLUMN f1_score SET NOT NULL;
ALTER TABLE evaluation_metrics ALTER COLUMN true_positives SET NOT NULL;
ALTER TABLE evaluation_metrics ALTER COLUMN false_positives SET NOT NULL;
ALTER TABLE evaluation_metrics ALTER COLUMN true_negatives SET NOT NULL;
ALTER TABLE evaluation_metrics ALTER COLUMN false_negatives SET NOT NULL;
ALTER TABLE evaluation_metrics ALTER COLUMN total_samples SET NOT NULL;
ALTER TABLE evaluation_metrics ALTER COLUMN anomaly_count SET NOT NULL;
ALTER TABLE evaluation_metrics ALTER COLUMN detection_method SET NOT NULL;

-- rule_config
ALTER TABLE rule_config ADD COLUMN IF NOT EXISTS id UUID;
ALTER TABLE rule_config ADD COLUMN IF NOT EXISTS metric_name VARCHAR DEFAULT '*';
ALTER TABLE rule_config ADD COLUMN IF NOT EXISTS threshold_value FLOAT;
ALTER TABLE rule_config ADD COLUMN IF NOT EXISTS duration_minutes INTEGER DEFAULT 1;
ALTER TABLE rule_config ADD COLUMN IF NOT EXISTS severity VARCHAR DEFAULT 'warning';
ALTER TABLE rule_config ADD COLUMN IF NOT EXISTS enabled BOOLEAN DEFAULT true;
ALTER TABLE rule_config ADD COLUMN IF NOT EXISTS recovery_confirmation_minutes INTEGER DEFAULT 5;

ALTER TABLE rule_config ALTER COLUMN id SET NOT NULL;
UPDATE rule_config SET metric_name = '*' WHERE metric_name IS NULL;
ALTER TABLE rule_config ALTER COLUMN metric_name SET NOT NULL, ALTER COLUMN metric_name DROP DEFAULT;
ALTER TABLE rule_config ALTER COLUMN threshold_value SET NOT NULL;
UPDATE rule_config SET duration_minutes = 1 WHERE duration_minutes IS NULL;
ALTER TABLE rule_config ALTER COLUMN duration_minutes SET NOT NULL, ALTER COLUMN duration_minutes DROP DEFAULT;
UPDATE rule_config SET severity = 'warning' WHERE severity IS NULL;
ALTER TABLE rule_config ALTER COLUMN severity SET NOT NULL, ALTER COLUMN severity DROP DEFAULT;
UPDATE rule_config SET enabled = true WHERE enabled IS NULL;
ALTER TABLE rule_config ALTER COLUMN enabled SET NOT NULL, ALTER COLUMN enabled DROP DEFAULT;
ALTER TABLE rule_config ALTER COLUMN recovery_confirmation_minutes DROP NOT NULL, ALTER COLUMN recovery_confirmation_minutes DROP DEFAULT;

-- Model-declared indexes.
CREATE INDEX IF NOT EXISTS idx_alert_anomaly_id ON alerts (anomaly_id);
CREATE INDEX IF NOT EXISTS idx_alert_incident_id ON alerts (incident_id);
CREATE INDEX IF NOT EXISTS idx_alert_severity ON alerts (severity);
CREATE INDEX IF NOT EXISTS idx_alert_status ON alerts (status);
CREATE INDEX IF NOT EXISTS idx_incident_status ON incidents (status);
CREATE INDEX IF NOT EXISTS idx_incident_severity ON incidents (severity);
CREATE INDEX IF NOT EXISTS idx_incident_detected_at ON incidents (detected_at);
CREATE INDEX IF NOT EXISTS idx_anomaly_metric_timestamp ON anomalies (metric_name, anomaly_timestamp);
CREATE INDEX IF NOT EXISTS idx_anomaly_timestamp ON anomalies (anomaly_timestamp);
CREATE INDEX IF NOT EXISTS idx_anomaly_metric_name ON anomalies (metric_name);
CREATE INDEX IF NOT EXISTS idx_anomaly_is_confirmed ON anomalies (is_confirmed);
CREATE INDEX IF NOT EXISTS idx_metric_name_timestamp ON metrics (metric_name, timestamp);
CREATE INDEX IF NOT EXISTS idx_metric_timestamp ON metrics (timestamp);
CREATE INDEX IF NOT EXISTS idx_metric_name ON metrics (metric_name);
CREATE INDEX IF NOT EXISTS idx_eval_metric_name ON evaluation_metrics (metric_name);
CREATE INDEX IF NOT EXISTS idx_eval_evaluated_at ON evaluation_metrics (evaluated_at);

COMMIT;