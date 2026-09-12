from unittest.mock import MagicMock
import pytest
from scripts.real_metrics_bridge import collect_system_metrics, post_metric

def test_collect_system_metrics():
    metrics = collect_system_metrics()
    assert "cpu_usage" in metrics
    assert "memory_usage" in metrics
    assert "disk_io" in metrics
    assert 0.0 <= metrics["cpu_usage"] <= 100.0
    assert 0.0 <= metrics["memory_usage"] <= 100.0

def test_post_metric():
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_client.post.return_value = mock_response

    post_metric(mock_client, "cpu_usage", 45.5)
    mock_client.post.assert_called_once()
    args, kwargs = mock_client.post.call_args
    assert "cpu_usage" in kwargs["json"]["metric_name"]
    assert kwargs["json"]["value"] == 45.5
