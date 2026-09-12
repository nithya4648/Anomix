import asyncio
import json
import redis.asyncio as aioredis
from datetime import datetime
from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.database import SessionLocal
from app.services.metric_service import MetricService, AnomalyService
from app.websocket.manager import WebSocketManager

logger = get_logger(__name__)
settings = get_settings()
ws_manager = WebSocketManager()


async def start_stream_consumer():
    """
    Background worker that consumes raw metrics from Redis Stream ('metrics:ingest'),
    persists them, runs anomaly detection, and broadcasts updates via WebSocket.
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

                            # Execute database operations in a fresh session
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
                            finally:
                                db.close()

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
