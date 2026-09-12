import pytest
from scripts.real_metrics_bridge import collect_system_metrics

def test_collect_system_metrics():
    metrics = collect_system_metrics()
    assert "cpu_usage" in metrics
    assert "memory_usage" in metrics
    assert "disk_io" in metrics
    assert 0.0 <= metrics["cpu_usage"] <= 100.0
    assert 0.0 <= metrics["memory_usage"] <= 100.0
