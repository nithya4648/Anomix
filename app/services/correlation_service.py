# app/services/correlation_service.py
"""Root‑cause correlation service.

This service analyses recent anomalies around a given metric and selects a
candidate root cause. The implementation is intentionally simple – it
queries anomalies that occurred within a configurable time window and
returns the earliest anomaly's metric name as the guessed root cause.

The service is used by :class:`MetricService` after an incident is
created. If a root‑cause is found the ``Incident.root_cause`` and
``Incident.correlated_metrics`` fields are populated.
"""

from datetime import datetime, timedelta
from typing import Optional, Tuple

from sqlalchemy.orm import Session

from app.models.anomaly import Anomaly
from app.models.incident import Incident
from app.core.config import get_settings


class CorrelationService:
    """Service to determine a root‑cause for an incident.

    The algorithm:
    1. Look back a configurable number of minutes (``correlation_window``).
    2. Retrieve all anomalies in that window ordered by timestamp.
    3. Choose the earliest anomaly as the root‑cause candidate.
    4. Return the metric name and a comma‑separated list of involved
       metrics (for now we simply return the single metric).
    """

    def __init__(self) -> None:
        self.settings = get_settings()
        # Default to 30 minutes if not defined in env.
        self.window_minutes = getattr(self.settings, "correlation_window_minutes", 30)

    def compute_root_cause(
        self, db: Session, metric_name: str, timestamp: datetime
    ) -> Tuple[Optional[str], Optional[str]]:
        """Return ``(root_cause_metric, correlated_metrics)``.

        * ``root_cause_metric`` – the metric name that is considered the
          root cause (or ``None`` if not found).
        * ``correlated_metrics`` – a comma‑separated string of metric names
          involved in the correlation (currently just the root‑cause).
        """
        start_time = timestamp - timedelta(minutes=self.window_minutes)
        # Fetch anomalies in the window, ordered oldest first.
        anomalies = (
            db.query(Anomaly)
            .filter(
                Anomaly.anomaly_timestamp >= start_time,
                Anomaly.anomaly_timestamp <= timestamp,
            )
            .order_by(Anomaly.anomaly_timestamp)
            .all()
        )
        if not anomalies:
            return None, None
        # Choose the earliest anomaly as the root cause.
        root = anomalies[0]
        return root.metric_name, root.metric_name
