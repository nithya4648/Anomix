from fastapi import APIRouter, Depends, HTTPException, status
import sqlalchemy
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional
from app.core.database import get_db
from app.models import Metric
from app.utils.auth import get_current_user
from app.schemas import MetricCreate, MetricResponse, MetricsRangeQuery
from app.services.metrics import MetricService, AnomalyService

from app.websocket.manager import ws_manager
import redis.asyncio as aioredis
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/metrics", tags=["metrics"])



from app.core.limiter import limiter
from fastapi import Request

@router.post("/ingest", response_model=MetricResponse)
@limiter.limit("1000/minute")
async def ingest_metric(
    request: Request,
    metric: MetricCreate,
    db: Session = Depends(get_db),
    _: str = Depends(get_current_user),
) -> MetricResponse:
    """
    Ingest a new metric and run anomaly detection.
    
    This endpoint:
    1. Stores the metric (or pushes to Redis stream if enabled)
    2. Runs real-time anomaly detection
    3. Creates alerts/incidents if anomalies detected
    4. Broadcasts updates via WebSocket
    """
    from app.core.config import get_settings
    import json
    import redis.asyncio as aioredis
    settings = get_settings()

    try:
        if settings.use_redis:
            try:
                # Asynchronous ingestion pipeline via Redis Stream
                redis_client = aioredis.from_url(settings.redis_url, decode_responses=True)
                try:
                    msg_payload = {
                        "metric_name": metric.metric_name,
                        "value": str(metric.value),
                        "timestamp": metric.timestamp.isoformat() if metric.timestamp else datetime.utcnow().isoformat(),
                        "labels": json.dumps(metric.labels or {}),
                    }
                    await redis_client.xadd("metrics:ingest", msg_payload)
                finally:
                    await redis_client.close()
    
                # Return preliminary accepted response
                return MetricResponse(
                    id="0",
                    metric_name=metric.metric_name,
                    value=metric.value,
                    timestamp=metric.timestamp or datetime.utcnow(),
                    labels=metric.labels or {},
                    created_at=datetime.utcnow(),
                )
            except Exception as e:
                logger.warning(f"Redis connection failed, falling back to DB: {e}")

        metric_service = MetricService(db)
        anomaly_service = AnomalyService(db)

        # Store metric
        stored_metric = metric_service.ingest_metric(
            metric_name=metric.metric_name,
            value=metric.value,
            timestamp=metric.timestamp,
            labels=metric.labels,
        )

        # Run anomaly detection
        anomaly, alert, incident = anomaly_service.detect_and_create_alert(
            stored_metric,
            metric_service,
        )

        # Broadcast update (fire and forget)
        import asyncio
        asyncio.create_task(
            ws_manager.broadcast({
                "event": "metric_ingested",
                "metric": {
                    "id": stored_metric.id,
                    "metric_name": stored_metric.metric_name,
                    "value": stored_metric.value,
                    "timestamp": stored_metric.timestamp.isoformat(),
                },
                "anomaly_detected": anomaly is not None,
                "alert": {
                    "severity": alert.severity,
                    "message": alert.message,
                } if alert else None,
            })
        )

        return MetricResponse(**{
            "id": stored_metric.id,
            "metric_name": stored_metric.metric_name,
            "value": stored_metric.value,
            "timestamp": stored_metric.timestamp,
            "labels": stored_metric.labels,
            "created_at": stored_metric.created_at,
        })

    except sqlalchemy.exc.SQLAlchemyError as e:
        logger.error(f"Database error ingesting metric: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection error",
        )
    except Exception as e:
        logger.error(f"Error ingesting metric: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to ingest metric",
        )


@router.get("/range", response_model=list[MetricResponse])
async def get_metrics_range(
    metric_name: str,
    start_time: datetime,
    end_time: datetime,
    db: Session = Depends(get_db),
    _: str = Depends(get_current_user),
) -> list[MetricResponse]:
    """Get metrics within a time range"""

    try:
        metric_service = MetricService(db)
        metrics = metric_service.get_metrics_range(metric_name, start_time, end_time)

        return [
            MetricResponse(
                id=m.id,
                metric_name=m.metric_name,
                value=m.value,
                timestamp=m.timestamp,
                labels=m.labels,
                created_at=m.created_at,
            )
            for m in metrics
        ]

    except Exception as e:
        logger.error(f"Error getting metrics range: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch metrics",
        )


@router.get("/recent", response_model=list[MetricResponse])
async def get_recent_metrics(
    metric_name: str,
    limit: int = 100,
    db: Session = Depends(get_db),
    _: str = Depends(get_current_user),
) -> list[MetricResponse]:
    """Get recent metrics for a metric name"""

    try:
        metric_service = MetricService(db)
        metrics = (
            metric_service.db.query(Metric)
            .filter_by(metric_name=metric_name)
            .order_by(Metric.timestamp.desc())
            .limit(limit)
            .all()
        )

        return [
            MetricResponse(
                id=m.id,
                metric_name=m.metric_name,
                value=m.value,
                timestamp=m.timestamp,
                labels=m.labels,
                created_at=m.created_at,
            )
            for m in metrics
        ]

    except Exception as e:
        logger.error(f"Error getting recent metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch metrics",
        )
