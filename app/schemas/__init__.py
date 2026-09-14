from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Any


# Metric Schemas
class MetricCreate(BaseModel):
    metric_name: str = Field(..., min_length=1, max_length=256)
    value: float = Field(..., description="Metric value")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    labels: Optional[dict[str, Any]] = Field(default_factory=dict)


class MetricResponse(BaseModel):
    id: str
    metric_name: str
    value: float
    timestamp: datetime
    labels: dict[str, Any]
    created_at: datetime

    model_config = {"from_attributes": True}


class MetricsRangeQuery(BaseModel):
    metric_name: str
    start_time: datetime
    end_time: datetime


# Anomaly Schemas
class AnomalyResponse(BaseModel):
    id: str
    metric_name: str
    metric_id: str
    anomaly_timestamp: datetime
    value: float
    confidence_score: float
    detection_method: str
    z_score: Optional[float] = None
    expected_value: Optional[float] = None
    is_confirmed: bool
    severity: Optional[str] = None
    reasons: Optional[str] = None
    ensemble_scores: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# Alert Schemas
class AlertResponse(BaseModel):
    id: str
    anomaly_id: str
    incident_id: Optional[str] = None
    severity: str
    message: str
    status: str  # new, acknowledged, resolved
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# Incident Schemas
class IncidentCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=256)
    description: Optional[str] = None
    severity: str = Field(..., pattern="^(critical|warning|info)$")


class IncidentUpdate(BaseModel):
    status: Optional[str] = Field(None, pattern="^(open|investigating|resolved)$")
    root_cause: Optional[str] = None
    description: Optional[str] = None


class IncidentResponse(BaseModel):
    id: str
    title: str
    description: Optional[str]
    status: str
    severity: str
    detected_at: datetime
    resolved_at: Optional[datetime]
    root_cause: Optional[str]
    correlated_metrics: Optional[str]
    confidence: Optional[float]
    progress_stage: Optional[str] = None
    progress_percent: Optional[int] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# Evaluation Metrics Schemas
class ConfusionMatrix(BaseModel):
    true_positives: int
    false_positives: int
    true_negatives: int
    false_negatives: int


class EvaluationMetricResponse(BaseModel):
    id: str
    metric_name: str
    evaluation_period_start: datetime
    evaluation_period_end: datetime
    evaluated_at: datetime
    precision: float
    recall: float
    f1_score: float
    confusion_matrix: ConfusionMatrix
    total_samples: int
    anomaly_count: int
    detection_method: str
    created_at: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_db_model(cls, db_model):
        return cls(
            id=db_model.id,
            metric_name=db_model.metric_name,
            evaluation_period_start=db_model.evaluation_period_start,
            evaluation_period_end=db_model.evaluation_period_end,
            evaluated_at=db_model.evaluated_at,
            precision=db_model.precision,
            recall=db_model.recall,
            f1_score=db_model.f1_score,
            confusion_matrix=ConfusionMatrix(
                true_positives=db_model.true_positives,
                false_positives=db_model.false_positives,
                true_negatives=db_model.true_negatives,
                false_negatives=db_model.false_negatives,
            ),
            total_samples=db_model.total_samples,
            anomaly_count=db_model.anomaly_count,
            detection_method=db_model.detection_method,
            created_at=db_model.created_at,
        )


# WebSocket Message Schemas
class MetricUpdate(BaseModel):
    event: str = "metric_ingested"
    metric: MetricResponse


class AnomalyDetected(BaseModel):
    event: str = "anomaly_detected"
    anomaly: AnomalyResponse
    alert: AlertResponse


class IncidentCreated(BaseModel):
    event: str = "incident_created"
    incident: IncidentResponse
