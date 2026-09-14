from fastapi import status
from fastapi import APIRouter, Depends, HTTPException, status as http_status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional
from app.core.database import get_db
from app.utils.security import verify_api_key
from app.schemas import (
    AnomalyResponse,
    AlertResponse,
    IncidentCreate,
    IncidentUpdate,
    IncidentResponse,
)
from app.services.metric_service import AnomalyService
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1", tags=["anomalies", "incidents"])


@router.get("/anomalies", response_model=list[AnomalyResponse])
async def get_anomalies(
    metric_name: str,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = 100,
    db: Session = Depends(get_db),
    _: str = Depends(verify_api_key),
) -> list[AnomalyResponse]:
    """Get anomalies for a specific metric"""

    try:
        anomaly_service = AnomalyService(db)
        anomalies = anomaly_service.get_anomalies(
            metric_name=metric_name,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
        )

        return [
            AnomalyResponse(
                id=a.id,
                metric_name=a.metric_name,
                metric_id=a.metric_id,
                anomaly_timestamp=a.anomaly_timestamp,
                value=a.value,
                confidence_score=a.confidence_score,
                detection_method=a.detection_method,
                z_score=a.z_score,
                expected_value=a.expected_value,
                is_confirmed=a.is_confirmed,
                severity=a.severity,
                reasons=a.reasons,
                ensemble_scores=a.ensemble_scores,
                created_at=a.created_at,
            )
            for a in anomalies
        ]

    except Exception as e:
        logger.error(f"Error getting anomalies: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch anomalies",
        )


@router.get("/anomalies/recent", response_model=list[AnomalyResponse])
async def get_recent_anomalies(
    limit: int = 50,
    db: Session = Depends(get_db),
    _: str = Depends(verify_api_key),
) -> list[AnomalyResponse]:
    """Get recent anomalies across all metrics"""

    try:
        anomaly_service = AnomalyService(db)
        anomalies = anomaly_service.get_recent_anomalies(limit=limit)

        return [
            AnomalyResponse(
                id=a.id,
                metric_name=a.metric_name,
                metric_id=a.metric_id,
                anomaly_timestamp=a.anomaly_timestamp,
                value=a.value,
                confidence_score=a.confidence_score,
                detection_method=a.detection_method,
                z_score=a.z_score,
                expected_value=a.expected_value,
                is_confirmed=a.is_confirmed,
                severity=a.severity,
                reasons=a.reasons,
                ensemble_scores=a.ensemble_scores,
                created_at=a.created_at,
            )
            for a in anomalies
        ]

    except Exception as e:
        logger.error(f"Error getting recent anomalies: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch anomalies",
        )


@router.get("/incidents", response_model=list[IncidentResponse])
async def get_incidents(
    status: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db),
    _: str = Depends(verify_api_key),
) -> list[IncidentResponse]:
    """Get incidents with optional status filter"""

    try:
        anomaly_service = AnomalyService(db)
        incidents = anomaly_service.get_incidents(status=status, limit=limit)

        return [
            IncidentResponse(
                id=i.id,
                title=i.title,
                description=i.description,
                status=i.status,
                severity=i.severity,
                detected_at=i.detected_at,
                resolved_at=i.resolved_at,
                root_cause=i.root_cause,
                correlated_metrics=i.correlated_metrics,
                confidence=i.confidence,
                progress_stage=i.progress_stage,
                progress_percent=i.progress_percent,
                created_at=i.created_at,
            )
            for i in incidents
        ]

    except Exception as e:
        logger.error(f"Error getting incidents: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch incidents",
        )


@router.post("/incidents/{incident_id}/resolve", response_model=IncidentResponse)
async def resolve_incident(
    incident_id: str,
    update: IncidentUpdate,
    db: Session = Depends(get_db),
    _: str = Depends(verify_api_key),
) -> IncidentResponse:
    """Resolve an incident"""

    try:
        anomaly_service = AnomalyService(db)
        incident = anomaly_service.resolve_incident(
            incident_id=incident_id,
            root_cause=update.root_cause,
        )

        return IncidentResponse(
            id=incident.id,
            title=incident.title,
            description=incident.description,
            status=incident.status,
            severity=incident.severity,
            detected_at=incident.detected_at,
            resolved_at=incident.resolved_at,
            root_cause=incident.root_cause,
            correlated_metrics=incident.correlated_metrics,
            confidence=incident.confidence,
            progress_stage=incident.progress_stage,
            progress_percent=incident.progress_percent,
            created_at=incident.created_at,
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error resolving incident: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to resolve incident",
        )
