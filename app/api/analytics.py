# app/api/analytics.py
"""Analytics endpoints for the Anomix service.

Provides high‑level health and summary metrics for the monitoring UI.
"""

from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.anomaly import Anomaly
from app.models.incident import Incident
from app.models.alert import Alert

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/health")
def get_health(db: Session = Depends(get_db)):
    """Return percentages of incident severities over the last 24 h.

    The result contains keys ``critical``, ``warning`` and ``info`` with
    percentage values (0‑100). If there are no incidents in the window,
    all percentages are ``0``.
    """
    cutoff = datetime.utcnow() - timedelta(hours=24)
    total = db.query(Incident).filter(Incident.detected_at >= cutoff).count()
    if total == 0:
        return {"critical": 0, "warning": 0, "info": 0}
    crit = (
        db.query(Incident)
        .filter(Incident.detected_at >= cutoff, Incident.severity == "critical")
        .count()
    )
    warn = (
        db.query(Incident)
        .filter(Incident.detected_at >= cutoff, Incident.severity == "warning")
        .count()
    )
    info = (
        db.query(Incident)
        .filter(Incident.detected_at >= cutoff, Incident.severity == "info")
        .count()
    )
    return {
        "critical": round(crit / total * 100, 2),
        "warning": round(warn / total * 100, 2),
        "info": round(info / total * 100, 2),
    }


@router.get("/summary")
def get_summary(db: Session = Depends(get_db)):
    """Return high‑level counts for anomalies, incidents and alerts.

    ``resolved_alerts`` counts alerts with status ``resolved``; ``active_alerts``
    counts alerts that are not resolved. ``resolved_incidents`` counts incidents
    with status ``resolved``.
    """
    anomalies_cnt = db.query(Anomaly).count()
    incidents_cnt = db.query(Incident).count()
    resolved_incidents_cnt = (
        db.query(Incident).filter(Incident.status == "resolved").count()
    )
    active_alerts_cnt = (
        db.query(Alert).filter(Alert.status != "resolved").count()
    )
    resolved_alerts_cnt = (
        db.query(Alert).filter(Alert.status == "resolved").count()
    )
    return {
        "anomalies": anomalies_cnt,
        "incidents": incidents_cnt,
        "resolved_incidents": resolved_incidents_cnt,
        "active_alerts": active_alerts_cnt,
        "resolved_alerts": resolved_alerts_cnt,
    }


@router.get("/methods")
def get_methods(db: Session = Depends(get_db)):
    """Return a breakdown of anomaly detection methods used.

    The ``detection_method`` column on the ``Anomaly`` model stores the
    method name (e.g. ``isolation_forest``, ``z_score``). The response is a
    mapping from method name to count.
    """
    results = (
        db.query(Anomaly.detection_method, func.count(Anomaly.id))
        .group_by(Anomaly.detection_method)
        .all()
    )
    return {method: count for method, count in results}
