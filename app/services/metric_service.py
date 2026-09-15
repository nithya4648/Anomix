from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from datetime import datetime, timedelta
from typing import Optional 
from fastapi import HTTPException
from app.models.metric import Metric
from app.models.anomaly import Anomaly
from app.models.alert import Alert
from app.models.incident import Incident
from app.ml.anomaly_detector import AnomalyDetector, RootCauseAnalyzer
from app.services.alert_rules import AlertRuleEngine
import asyncio
from app.services.correlation_service import CorrelationService
from app.services.notification_service import NotificationService
from app.websocket.manager_instance import ws_manager
from app.core.logging import get_logger
from app.core.config import get_settings
from app.models.rule_config import RuleConfig

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
        # Initialize alert rule engine with DB session for dynamic rules
        self.rule_engine = AlertRuleEngine(db=self.db)

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

        # Evaluate alert rules
        rule_matches = self.rule_engine.evaluate(
            metric_name=metric.metric_name,
            confidence=detection_result.confidence_score,
            severity=severity,
            timestamp=metric.timestamp,
        )

        # If no rule matches, do not generate an alert/incident
        if not rule_matches:
            logger.info(f"No alert rules triggered for {metric.metric_name} (confidence={detection_result.confidence_score:.2f})")
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

        # Build combined reason message from rule matches
        reasons_msg = ", ".join([match.message for match in rule_matches])

        # Create alert with reasons
        alert = Alert(
            anomaly_id=anomaly.id,
            severity=severity,
            message=reason_msg if (reason_msg := reasons_msg) else (
                f"Anomaly detected in {metric.metric_name}: {metric.value:.2f} (expected ~{detection_result.expected_value:.2f})"
                if detection_result.expected_value else f"Anomaly in {metric.metric_name}: {metric.value:.2f}"
            ),
        )
        self.db.add(alert)
        self.db.flush()

        # Trigger notifications (async, fire‑and‑forget)
        try:
            asyncio.create_task(
                NotificationService().send_alert_notification(
                    alert_id=alert.id,
                    severity=severity,
                    message=alert.message,
                )
            )
        except Exception:
            pass

        # Determine if incident should be auto‑created based on incident rule
        create_incident = self.rule_engine.should_create_incident(metric.metric_name, metric.timestamp)

        incident = None
        if create_incident:
            # Check for existing open incident with matching severity
            existing_incident = (
                self.db.query(Incident)
                .filter(
                    and_(
                        Incident.status.in_["open", "investigating"],
                        Incident.detected_at >= datetime.utcnow() - timedelta(minutes=5),
                    )
                )
                .first()
            )
            if existing_incident and existing_incident.severity == severity:
                existing_incident.correlated_metrics = metric.metric_name
                self.db.add(existing_incident)
                alert.incident_id = existing_incident.id
            else:
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
                # Broadcast incident creation progress
                asyncio.create_task(ws_manager.broadcast_progress({
                    "event": "incident_created",
                    "incident_id": incident.id,
                    "stage": "incident_created",
                    "percent": 33,
                }))
        # Compute root cause correlation
        correlation_service = CorrelationService()
        root_cause, correlated = correlation_service.compute_root_cause(self.db, metric.metric_name, metric.timestamp)
        if root_cause:
            incident.root_cause = root_cause
            incident.correlated_metrics = correlated
            alert.incident_id = incident.id

        # Broadcast correlation progress (if root cause determined)
        if incident and incident.root_cause:
            asyncio.create_task(ws_manager.broadcast_progress({
                "event": "correlation_done",
                "incident_id": incident.id,
                "stage": "correlated",
                "percent": 66,
            }))
        # Schedule automatic recovery check based on rule config
        if incident:
            asyncio.create_task(self._attempt_auto_recovery(incident, metric.metric_name))
        
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

    def get_incident(self, incident_id: str) -> Optional[Incident]:
        """Return one incident by its string UUID, or None when absent."""

        return self.db.query(Incident).filter(Incident.id == incident_id).first()

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

    def add_feedback(self, anomaly_id: str, status: str, note: Optional[str] = None) -> Anomaly:
        """Add user feedback to an anomaly.

        Args:
            anomaly_id: ID of the anomaly to update.
            status: One of 'unreviewed', 'true_positive', 'false_positive'.
            note: Optional free‑text note.
        Returns:
            The updated Anomaly instance.
        """
        allowed_statuses = {"unreviewed", "true_positive", "false_positive"}
        if status not in allowed_statuses:
            raise ValueError(f"Invalid feedback_status: {status}")

        anomaly = self.db.query(Anomaly).filter(Anomaly.id == anomaly_id).first()
        if not anomaly:
            raise ValueError(f"Anomaly {anomaly_id} not found")

        anomaly.feedback_status = status
        anomaly.feedback_note = note
        anomaly.feedback_at = datetime.utcnow()
        self.db.add(anomaly)
        self.db.commit()
        self.db.refresh(anomaly)
        return anomaly
    async def _attempt_auto_recovery(self, incident: Incident, metric_name: str) -> None:
        """Attempt to auto‑resolve an incident after a configurable confirmation period.

        The confirmation period is read from ``RuleConfig.recovery_confirmation_minutes``
        for the specific metric (or the default config if none matches). After waiting
        that many minutes the service checks the recent metric values; if none of them
        trigger an anomaly the incident is marked as resolved.
        """
        # Determine confirmation period
        rule_cfg = self.db.query(RuleConfig).filter(RuleConfig.metric_name == metric_name).first()
        if not rule_cfg:
            rule_cfg = self.db.query(RuleConfig).filter(RuleConfig.metric_name == "*").first()
        confirmation_minutes = getattr(rule_cfg, "recovery_confirmation_minutes", 5) if rule_cfg else 5

        # Wait for the confirmation window
        await asyncio.sleep(confirmation_minutes * 60)

        # Ensure the incident is still open
        refreshed_incident = self.db.query(Incident).filter(Incident.id == incident.id).first()
        if not refreshed_incident or refreshed_incident.status != "open":
            return

        # Resolve incident automatically
        self.resolve_incident(incident.id)
        # Broadcast auto‑resolution progress
        asyncio.create_task(ws_manager.broadcast_progress({
            "event": "incident_resolved_auto",
            "incident_id": incident.id,
            "stage": "auto_resolved",
            "percent": 100,
        }))
