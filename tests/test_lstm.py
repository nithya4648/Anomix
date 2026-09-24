import pytest
import numpy as np
from app.ml.models import PyTorchLSTMAutoencoder
from app.ml import AnomalyDetector


def test_lstm_autoencoder_reconstruction():
    model = PyTorchLSTMAutoencoder(sequence_length=10)
    normal_seq = [50.0 + np.random.normal(0, 1) for _ in range(50)]
    seqs = [np.array(normal_seq[i:i+10]) for i in range(len(normal_seq)-10)]
    model.fit(seqs)

    # Test normal sequence
    is_anomaly, conf, mse = model.detect_sequence_anomaly(normal_seq)
    assert isinstance(is_anomaly, bool)
    assert 0.0 <= conf <= 1.0

def test_anomaly_detector_lstm_method():
    detector = AnomalyDetector(method="lstm_autoencoder", min_samples=20)
    normal_values = [50.0 + np.random.normal(0, 2) for _ in range(30)]
    result = detector.detect("cpu_usage", 51.0, normal_values)
    assert result.detection_method == "lstm_autoencoder"
