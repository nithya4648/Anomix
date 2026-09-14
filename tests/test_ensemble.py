import pytest
import numpy as np
from app.ml.anomaly_detector import AnomalyDetector

def test_ensemble_detection_voting():
    """Test ensemble voting combining IsolationForest and Z-Score methods."""
    detector = AnomalyDetector(method="hybrid", z_score_threshold=2.0, min_samples=20)
    
    # 50 normal values
    normal_values = [50.0 + np.random.normal(0, 2.0) for _ in range(50)]
    
    # Normal reading
    normal_res = detector.detect("cpu_usage", 51.0, normal_values)
    assert not normal_res.is_anomaly
    
    # Extreme anomaly reading
    anom_res = detector.detect("cpu_usage", 120.0, normal_values)
    assert anom_res.is_anomaly
    assert anom_res.confidence_score > 0.5
