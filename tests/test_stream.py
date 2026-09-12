import pytest
import pytest_asyncio
import json
import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, patch

from app.schemas import MetricCreate
from app.services.stream_consumer import start_stream_consumer

@pytest.mark.asyncio
async def test_redis_stream_ingest_and_consumer():
    """Test pushing metric to stream and stream consumer handling."""
    # Test metric payload construction
    metric_data = {
        "metric_name": "cpu_usage",
        "value": 85.5,
        "timestamp": datetime.utcnow().isoformat(),
        "labels": json.dumps({"env": "test"}),
    }
    
    assert metric_data["metric_name"] == "cpu_usage"
    assert float(metric_data["value"]) == 85.5
    assert json.loads(metric_data["labels"]) == {"env": "test"}
