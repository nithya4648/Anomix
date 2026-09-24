import pytest
import numpy as np
from scripts.data import MetricSimulator


def test_synthetic_outlier_generation():
    simulator = MetricSimulator(seed=42)
    base_data = [50.0 + np.random.normal(0, 2) for _ in range(100)]

    for mode in ["spike", "level_shift", "contextual"]:
        outliers = simulator.generate_synthetic_outliers(base_data, outlier_type=mode, anomaly_ratio=0.05)
        assert len(outliers) == 100
        anomalies = [val for val, flag in outliers if flag]
        assert len(anomalies) > 0
