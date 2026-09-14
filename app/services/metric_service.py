from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from datetime import datetime, timedelta
from typing import Optional 
from app.models.metric import Metric
from app.models.anomaly import Anomaly
from app.models.alert import Alert
from app.models.incident import Incident
from app.ml.anomaly_detector import AnomalyDetector, RootCauseAnalyzer
from app.core.logging import get_logger
from app.core.config import get_settings

logger = get_logger(__name__)
settings = get_settings()


class MetricService:
    """Handles metric ingestion and storage"""

    def __init__(self, db: Session):
        self.db = db

    def ingest_metric(
        self,
        metric_name: str,
        value: float,
        timestamp: datetime,
        labels: dict = None,
    ) -> Metric:
        """Store a new metric in database"""

        metric = Metric(
            metric_name=metric_name,
            value=value,
            timestamp=timestamp,
            labels=labels or {},
        )
        self.db.add(metric)
        self.db.commit()
        self.db.refresh(metric)

        logger.debug(f"Ingested metric: {metric_name}={value}")
        return metric

    def get_recent_values(
        self,
        metric_name: str,
        limit: int = 200,
    ) -> list[float]:
        """Get recent metric values for anomaly detection"""

        metrics = (
            self.db.query(Metric)
            .filter(Metric.metric_name == metric_name)
            .order_by(desc(Metric.timestamp))
            .limit(limit)
            .all()
        )

        return [m.value for m in reversed(metrics)]

    def get_metrics_range(
        self,
        metric_name: str,
        start_time: datetime,
        end_time: datetime,
    ) -> list[Metric]:
        """Get metrics within a time range"""

        return (
            self.db.query(Metric)
            .filter(
                and_(
                    Metric.metric_name == metric_name,
                    Metric.timestamp >= start_time,
                    Metric.timestamp <= end_time,
                )
            )
            .order_by(Metric.timestamp)
            .all()
        )

    def cleanup_old_metrics(self, days: int = 30):
        """Remove metrics older than retention period"""

        cutoff = datetime.utcnow() - timedelta(days=days)
        deleted = (
            self.db.query(Metric)
            .filter(Metric.timestamp < cutoff)
            .delete()
        )
        self.db.commit()
        logger.info(f"Cleaned up {deleted} old metrics")


class AnomalyService:
    """Handles anomaly detection, alerts, and incidents"""

    def __init__(self, db: Session):
        self.db = db
        self.detector = AnomalyDetector(
            method=settings.anomaly_detection_method,
            z_score_threshold=settings.z_score_threshold,
            contamination=settings.isolation_forest_contamination,
            min_samples=settings.min_samples_for_detection,
        )
        self.root_cause_analyzer = RootCauseAnalyzer()
        from app.services.alert_dampener import AlertDampener
        self.dampener = AlertDampener()

    def detect_and_create_alert(
        self,
        metric: Metric,
        metric_service: MetricService,
    ) -> tuple[Optional[Anomaly], Optional[Alert], Optional[Incident]]:
        """
        Run anomaly detection on a metric and create alert/incident if needed.

        Returns:
            Tuple of (anomaly, alert, incident) - any can be None if no anomaly
        """

        historical_values = metric_service.get_recent_values(metric.metric_name, limit=200)

        if len(historical_values) < settings.min_samples_for_detection:
            return None, None, None

        # Detect anomaly
        detection_result = self.detector.detect(
            metric_name=metric.metric_name,
            current_value=metric.value,
            historical_values=historical_values,
        )

        if not detection_result.is_anomaly:
            return None, None, None

        # Determine severity based on confidence
        if detection_result.confidence_score > 0.8:
            severity = "critical"
        elif detection_result.confidence_score > 0.6:
            severity = "warning"
        else:
            severity = "info"

        # Apply alert fatigue dampening
        if self.dampener.should_suppress(metric.metric_name, severity, metric.timestamp):
            logger.info(f"Alert suppressed due to fatigue dampening for {metric.metric_name} ({severity})")
            return None, None, None

        # Create anomaly record
        anomaly = Anomaly(
            metric_name=metric.metric_name,
            metric_id=metric.id,
            anomaly_timestamp=metric.timestamp,
            value=metric.value,
            confidence_score=detection_result.confidence_score,
            detection_method=detection_result.detection_method,
            z_score=detection_result.z_score,
            expected_value=detection_result.expected_value,
        )
        self.db.add(anomaly)
        self.db.flush()

        # Create alert
        alert = Alert(
            anomaly_id=anomaly.id,
            severity=severity,
            message=f"Anomaly detected in {metric.metric_name}: {metric.value:.2f} (expected ~{detection_result.expected_value:.2f})" if detection_result.expected_value else f"Anomaly in {metric.metric_name}: {metric.value:.2f}",
        )
        self.db.add(alert)
        self.db.flush()

        # Check for existing open incident
        existing_incident = (
            self.db.query(Incident)
            .filter(
                and_(
                    Incident.status.in_(["open", "investigating"]),
                    Incident.detected_at >= datetime.utcnow() - timedelta(minutes=5),
                )
            )
            .first()
        )

        incident = None
        if existing_incident and existing_incident.severity == severity:
            # Update existing incident
            existing_incident.correlated_metrics = metric.metric_name
            self.db.add(existing_incident)
            alert.incident_id = existing_incident.id
        else:
            # Create new incident
            incident = Incident(
                title=f"{severity.upper()}: {metric.metric_name} Anomaly",
                description=f"Anomaly detected in metric {metric.metric_name}",
                status="open",
                severity=severity,
                detected_at=metric.timestamp,
                correlated_metrics=metric.metric_name,
            )
            self.db.add(incident)
            self.db.flush()
            alert.incident_id = incident.id

        self.db.commit()
        self.db.refresh(anomaly)
        self.db.refresh(alert)

        logger.info(
            f"Anomaly detected: {metric.metric_name}={metric.value} "
            f"(confidence={detection_result.confidence_score:.2f})"
        )

        return anomaly, alert, incident

    def get_anomalies(
        self,
        metric_name: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
    ) -> list[Anomaly]:
        """Get anomalies for a metric"""

        query = self.db.query(Anomaly).filter(Anomaly.metric_name == metric_name)

        if start_time:
            query = query.filter(Anomaly.anomaly_timestamp >= start_time)
        if end_time:
            query = query.filter(Anomaly.anomaly_timestamp <= end_time)

        return query.order_by(desc(Anomaly.anomaly_timestamp)).limit(limit).all()

    def get_recent_anomalies(self, limit: int = 50) -> list[Anomaly]:
        """Get recent anomalies across all metrics"""

        return (
            self.db.query(Anomaly)
            .order_by(desc(Anomaly.anomaly_timestamp))
            .limit(limit)
            .all()
        )

    def get_incidents(
        self,
        status: Optional[str] = None,
        limit: int = 100,
    ) -> list[Incident]:
        """Get incidents with optional status filter"""

        query = self.db.query(Incident)

        if status:
            query = query.filter(Incident.status == status)

        return query.order_by(desc(Incident.detected_at)).limit(limit).all()

    def resolve_incident(self, incident_id: str, root_cause: str = None) -> Incident:
        """Mark incident as resolved"""

        incident = self.db.query(Incident).filter(Incident.id == incident_id).first()

        if not incident:
            raise ValueError(f"Incident {incident_id} not found")

        incident.status = "resolved"
        incident.resolved_at = datetime.utcnow()
        if root_cause:
            incident.root_cause = root_cause

        # Resolve related alerts
        alerts = self.db.query(Alert).filter(Alert.incident_id == incident_id).all()
        for alert in alerts:
            alert.status = "resolved"
            alert.resolved_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(incident)

        logger.info(f"Incident {incident_id} resolved")
        return incident
