"""
Alert lifecycle API endpoints.

Provides acknowledge, resolve, and filtered listing for alerts.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional
from app.core.database import get_db
from app.utils.security import verify_api_key
from app.schemas import AlertResponse
from app.models.alert import Alert
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1", tags=["alerts"])


@router.get("/alerts", response_model=list[AlertResponse])
async def list_alerts(
    status_filter: Optional[str] = None,
    severity: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db),
    _: str = Depends(verify_api_key),
) -> list[AlertResponse]:
    """List alerts with optional status and severity filters."""
    try:
        query = db.query(Alert)

        if status_filter:
            query = query.filter(Alert.status == status_filter)
        if severity:
            query = query.filter(Alert.severity == severity)

        alerts = query.order_by(Alert.created_at.desc()).limit(limit).all()

        return [
            AlertResponse(
                id=a.id,
                anomaly_id=a.anomaly_id,
                incident_id=a.incident_id,
                severity=a.severity,
                message=a.message,
                status=a.status,
                acknowledged_at=a.acknowledged_at,
                acknowledged_by=a.acknowledged_by,
                resolved_at=a.resolved_at,
                created_at=a.created_at,
            )
            for a in alerts
        ]

    except Exception as e:
        logger.error(f"Error listing alerts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch alerts",
        )


@router.post("/alerts/{alert_id}/acknowledge", response_model=AlertResponse)
async def acknowledge_alert(
    alert_id: str,
    acknowledged_by: Optional[str] = "system",
    db: Session = Depends(get_db),
    _: str = Depends(verify_api_key),
) -> AlertResponse:
    """Acknowledge an alert."""
    try:
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        if not alert:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Alert {alert_id} not found",
            )

        if alert.status == "resolved":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot acknowledge an already resolved alert",
            )

        alert.status = "acknowledged"
        alert.acknowledged_at = datetime.utcnow()
        alert.acknowledged_by = acknowledged_by

        db.commit()
        db.refresh(alert)

        logger.info(f"Alert {alert_id} acknowledged by {acknowledged_by}")

        return AlertResponse(
            id=alert.id,
            anomaly_id=alert.anomaly_id,
            incident_id=alert.incident_id,
            severity=alert.severity,
            message=alert.message,
            status=alert.status,
            acknowledged_at=alert.acknowledged_at,
            acknowledged_by=alert.acknowledged_by,
            resolved_at=alert.resolved_at,
            created_at=alert.created_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error acknowledging alert: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to acknowledge alert",
        )


@router.post("/alerts/{alert_id}/resolve", response_model=AlertResponse)
async def resolve_alert(
    alert_id: str,
    db: Session = Depends(get_db),
    _: str = Depends(verify_api_key),
) -> AlertResponse:
    """Resolve an alert."""
    try:
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        if not alert:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Alert {alert_id} not found",
            )

        alert.status = "resolved"
        alert.resolved_at = datetime.utcnow()

        db.commit()
        db.refresh(alert)

        logger.info(f"Alert {alert_id} resolved")

        return AlertResponse(
            id=alert.id,
            anomaly_id=alert.anomaly_id,
            incident_id=alert.incident_id,
            severity=alert.severity,
            message=alert.message,
            status=alert.status,
            acknowledged_at=alert.acknowledged_at,
            acknowledged_by=alert.acknowledged_by,
            resolved_at=alert.resolved_at,
            created_at=alert.created_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resolving alert: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to resolve alert",
        )
