import asyncio
import json
import redis.asyncio as aioredis
from datetime import datetime, timedelta
from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.database import SessionLocal
from app.services.metric_service import MetricService, AnomalyService
from app.services.notification_service import NotificationService
from app.websocket.manager_instance import ws_manager

logger = get_logger(__name__)
settings = get_settings()
notification_service = NotificationService()


async def check_and_auto_recover_incidents(
    db,
    metric_name: str,
    current_timestamp: datetime,
    anomaly_service: AnomalyService,
    metric_service: MetricService,
) -> list:
    """
    Evaluate open/investigating incidents for metric_name.
    If the metric readings stay normal/below threshold for the confirmation window,
    auto-transition Incident.status -> 'resolved', resolved_at -> now, progress_stage -> 'resolved'.
    """
    from app.models.incident import Incident
    from app.models.rule_config import RuleConfig
    from sqlalchemy import and_, or_

    open_incidents = (
        db.query(Incident)
        .filter(
            and_(
                Incident.status.in_(["open", "investigating"]),
                or_(
                    Incident.correlated_metrics == metric_name,
                    Incident.correlated_metrics.like(f"%{metric_name}%"),
                ),
            )
        )
        .all()
    )

    if not open_incidents:
        return []

    # Look up recovery confirmation window
    rule = (
        db.query(RuleConfig)
        .filter(RuleConfig.metric_name.in_([metric_name, "*"]), RuleConfig.enabled == True)
        .first()
    )
    conf_minutes = (
        rule.recovery_confirmation_minutes
        if (rule and rule.recovery_confirmation_minutes is not None)
        else settings.recovery_confirmation_minutes
    )

    cutoff = current_timestamp - timedelta(minutes=conf_minutes)

    # Fetch recent metrics in the confirmation window
    recent_metrics = metric_service.get_metrics_range(
        metric_name=metric_name,
        start_time=cutoff,
        end_time=current_timestamp,
    )

    if not recent_metrics:
        return []

    historical_values = metric_service.get_recent_values(metric_name, limit=200)
    if len(historical_values) < settings.min_samples_for_detection:
        return []

    # Check if ALL points in the confirmation window are normal (non-anomalous / below threshold)
    threshold = rule.threshold_value if rule else settings.eval_threshold_confidence
    for m in recent_metrics:
        # Use baseline metrics excluding the evaluated point to avoid self-contamination
        baseline = [h for h in historical_values if h != m.value]
        if not baseline:
            baseline = historical_values
        detection = anomaly_service.detector.detect(
            metric_name=metric_name,
            current_value=m.value,
            historical_values=baseline,
        )
        if detection.is_anomaly or detection.confidence_score >= threshold:
            # Still anomalous within recovery window
            return []

    # All points in confirmation window are normal: auto-resolve
    resolved_incidents = []
    for inc in open_incidents:
        inc.status = "resolved"
        inc.resolved_at = current_timestamp
        inc.progress_stage = "resolved"
        inc.progress_percent = 100
        inc.root_cause = inc.root_cause or "Auto-recovered: Sustained normal telemetry"
        db.add(inc)
        resolved_incidents.append(inc)

    db.commit()
    for inc in resolved_incidents:
        db.refresh(inc)

    return resolved_incidents


async def process_single_metric(
    metric_name: str,
    value: float,
    timestamp: datetime,
    labels: dict,
):
    """
    Process an ingested metric: persists, runs anomaly detection, checks auto-recovery, and broadcasts via WS.
    """
    db = SessionLocal()
    try:
        metric_service = MetricService(db)
        anomaly_service = AnomalyService(db)

        stored_metric = metric_service.ingest_metric(
            metric_name=metric_name,
            value=value,
            timestamp=timestamp,
            labels=labels,
        )

        anomaly, alert, incident = anomaly_service.detect_and_create_alert(
            stored_metric,
            metric_service,
        )

        # Broadcast via WebSocket
        await ws_manager.broadcast({
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

        if alert:
            # Trigger notifications asynchronously
            asyncio.create_task(
                notification_service.send_alert_notification(
                    alert_id=alert.id,
                    severity=alert.severity,
                    message=alert.message,
                )
            )

        # Check for automatic incident recovery
        recovered_incidents = await check_and_auto_recover_incidents(
            db=db,
            metric_name=metric_name,
            current_timestamp=timestamp,
            anomaly_service=anomaly_service,
            metric_service=metric_service,
        )

        for recovered in recovered_incidents:
            await ws_manager.broadcast({
                "type": "progress_update",
                "event": "incident_resolved",
                "incident_id": str(recovered.id),
                "stage": "resolved",
                "percent": 100,
                "status": "resolved",
                "auto_recovered": True,
                "resolved_at": recovered.resolved_at.isoformat() if recovered.resolved_at else None,
            })

    finally:
        db.close()


async def start_stream_consumer():
    """
    Background worker that consumes raw metrics from Redis Stream ('metrics:ingest'),
    persists them, runs anomaly detection, checks auto-recovery, and broadcasts updates via WebSocket.
    """
    if not settings.use_redis:
        logger.info("Redis is disabled. Stream consumer will not start.")
        return

    redis_client = None
    stream_name = "metrics:ingest"
    consumer_group = "anomaly_detectors"
    consumer_name = "consumer_1"

    while True:
        try:
            logger.info(f"Connecting to Redis at {settings.redis_url}...")
            redis_client = aioredis.from_url(settings.redis_url, decode_responses=True)

            # Create consumer group if it doesn't exist
            try:
                await redis_client.xgroup_create(stream_name, consumer_group, id="0", mkstream=True)
            except Exception as e:
                # Group might already exist
                if "BUSYGROUP" not in str(e):
                    logger.warning(f"Consumer group notice: {e}")

            logger.info(f"Redis Stream Consumer listening on {stream_name}...")

            while True:
                # Read new messages from the consumer group
                entries = await redis_client.xreadgroup(
                    groupname=consumer_group,
                    consumername=consumer_name,
                    streams={stream_name: ">"},
                    count=10,
                    block=2000,
                )

                if not entries:
                    await asyncio.sleep(0.1)
                    continue

                for stream, messages in entries:
                    for msg_id, payload in messages:
                        try:
                            # Process message payload
                            metric_name = payload.get("metric_name")
                            value = float(payload.get("value"))
                            timestamp_str = payload.get("timestamp")
                            timestamp = (
                                datetime.fromisoformat(timestamp_str)
                                if timestamp_str
                                else datetime.utcnow()
                            )
                            labels_str = payload.get("labels")
                            labels = json.loads(labels_str) if labels_str else {}

                            await process_single_metric(
                                metric_name=metric_name,
                                value=value,
                                timestamp=timestamp,
                                labels=labels,
                            )

                            # Acknowledge processed message
                            await redis_client.xack(stream_name, consumer_group, msg_id)

                        except Exception as proc_err:
                            logger.error(f"Error processing stream message {msg_id}: {proc_err}")

        except asyncio.CancelledError:
            logger.info("Stream consumer task cancelled.")
            break
        except Exception as e:
            logger.error(f"Redis stream consumer error: {e}. Retrying in 5 seconds...")
            await asyncio.sleep(5)
        finally:
            if redis_client:
                await redis_client.close()
