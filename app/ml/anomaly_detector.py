import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from scipy import stats
from typing import Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class AnomalyResult:
    is_anomaly: bool
    confidence_score: float
    detection_method: str
    z_score: Optional[float] = None
    expected_value: Optional[float] = None


class AnomalyDetector:
    """
    Real-time anomaly detection using multiple methods:
    - IsolationForest: Unsupervised, good for outlier detection
    - Z-Score: Statistical, based on rolling mean/std
    """

    def __init__(
        self,
        method: str = "isolation_forest",
        z_score_threshold: float = 3.0,
        contamination: float = 0.1,
        min_samples: int = 50,
        window_size: int = 100,
    ):
        self.method = method
        self.z_score_threshold = z_score_threshold
        self.contamination = contamination
        self.min_samples = min_samples
        self.window_size = window_size
        self.models = {}  # Per-metric isolation forest models

    def detect(
        self,
        metric_name: str,
        current_value: float,
        historical_values: list[float],
        timestamps: Optional[list[datetime]] = None,
    ) -> AnomalyResult:
        """
        Detect anomalies in real-time using configured method.

        Args:
            metric_name: Name of the metric
            current_value: Current metric value
            historical_values: List of historical values
            timestamps: Optional timestamps for temporal context

        Returns:
            AnomalyResult with detection details
        """

        if len(historical_values) < self.min_samples:
            logger.debug(
                f"Insufficient samples for {metric_name}: {len(historical_values)}/{self.min_samples}"
            )
            return AnomalyResult(
                is_anomaly=False,
                confidence_score=0.0,
                detection_method=self.method,
            )

        if self.method == "isolation_forest":
            return self._detect_isolation_forest(metric_name, current_value, historical_values)
        elif self.method == "z_score":
            return self._detect_z_score(current_value, historical_values)
        elif self.method == "lstm_autoencoder":
            return self._detect_lstm(metric_name, current_value, historical_values)
        else:
            return self._detect_hybrid(
                metric_name, current_value, historical_values, historical_values
            )

    def _detect_lstm(
        self,
        metric_name: str,
        current_value: float,
        historical_values: list[float],
    ) -> AnomalyResult:
        """LSTM Autoencoder sequence anomaly detection"""
        from app.ml.lstm_autoencoder import PyTorchLSTMAutoencoder

        try:
            if metric_name not in self.models:
                lstm_model = PyTorchLSTMAutoencoder(sequence_length=10)
                # Calibrate baseline
                window = historical_values[-50:]
                seqs = [np.array(window[i:i+10]) for i in range(len(window)-10)]
                if seqs:
                    lstm_model.fit(seqs)
                self.models[metric_name] = lstm_model
            else:
                lstm_model = self.models[metric_name]

            full_seq = historical_values + [current_value]
            is_anomaly, confidence, mse = lstm_model.detect_sequence_anomaly(full_seq)

            return AnomalyResult(
                is_anomaly=is_anomaly,
                confidence_score=confidence,
                detection_method="lstm_autoencoder",
                expected_value=float(np.mean(historical_values[-10:])) if historical_values else None,
            )

        except Exception as e:
            logger.error(f"Error in LSTM detection for {metric_name}: {e}")
            return AnomalyResult(
                is_anomaly=False,
                confidence_score=0.0,
                detection_method="lstm_autoencoder",
            )

    def _detect_isolation_forest(
        self,
        metric_name: str,
        current_value: float,
        historical_values: list[float],
    ) -> AnomalyResult:
        """IsolationForest-based anomaly detection"""

        try:
            # Use recent window for training
            window = np.array(historical_values[-self.window_size :]).reshape(-1, 1)

            # Train or reuse model
            if metric_name not in self.models or len(self.models[metric_name]) % 50 == 0:
                model = IsolationForest(
                    contamination=self.contamination,
                    random_state=42,
                    n_estimators=100,
                )
                model.fit(window)
                self.models[metric_name] = model
            else:
                model = self.models[metric_name]

            # Score current value
            score = model.score_samples([[current_value]])[0]
            prediction = model.predict([[current_value]])[0]

            # Normalize score to 0-1 confidence
            confidence = max(0.0, min(1.0, -score / 3))

            is_anomaly = prediction == -1 and confidence > 0.5

            return AnomalyResult(
                is_anomaly=is_anomaly,
                confidence_score=confidence,
                detection_method="isolation_forest",
            )

        except Exception as e:
            logger.error(f"Error in IsolationForest detection for {metric_name}: {e}")
            return AnomalyResult(
                is_anomaly=False,
                confidence_score=0.0,
                detection_method="isolation_forest",
            )

    def _detect_z_score(
        self,
        current_value: float,
        historical_values: list[float],
    ) -> AnomalyResult:
        """Z-Score based anomaly detection"""

        try:
            values = np.array(historical_values)
            mean = np.mean(values)
            std = np.std(values)

            if std == 0:
                return AnomalyResult(
                    is_anomaly=False,
                    confidence_score=0.0,
                    detection_method="zscore",
                    expected_value=mean,
                    z_score=0.0,
                )

            z_score = abs((current_value - mean) / std)
            confidence = min(1.0, z_score / self.z_score_threshold)

            is_anomaly = z_score > self.z_score_threshold

            return AnomalyResult(
                is_anomaly=is_anomaly,
                confidence_score=confidence,
                detection_method="zscore",
                expected_value=mean,
                z_score=z_score,
            )

        except Exception as e:
            logger.error(f"Error in Z-Score detection: {e}")
            return AnomalyResult(
                is_anomaly=False,
                confidence_score=0.0,
                detection_method="zscore",
            )

    def _detect_hybrid(
        self,
        metric_name: str,
        current_value: float,
        historical_values: list[float],
        fallback_values: list[float],
    ) -> AnomalyResult:
        """Hybrid detection: IsolationForest + Z-Score voting"""

        iso_result = self._detect_isolation_forest(metric_name, current_value, historical_values)
        z_result = self._detect_z_score(current_value, fallback_values)

        # Average confidence if both detect anomaly
        is_anomaly = iso_result.is_anomaly or z_result.is_anomaly
        confidence = max(iso_result.confidence_score, z_result.confidence_score)

        return AnomalyResult(
            is_anomaly=is_anomaly,
            confidence_score=confidence,
            detection_method="hybrid",
            z_score=z_result.z_score,
            expected_value=z_result.expected_value,
        )


class RootCauseAnalyzer:
    """Correlate related metrics to identify root causes"""

    def __init__(self, correlation_threshold: float = 0.7):
        self.correlation_threshold = correlation_threshold

    def analyze(
        self, primary_metric: str, metric_values: dict[str, list[float]]
    ) -> Tuple[list[str], float]:
        """
        Find correlated metrics that may explain the primary metric's anomaly.

        Args:
            primary_metric: Name of the metric with anomaly
            metric_values: Dict of metric_name -> list of values

        Returns:
            Tuple of (correlated_metrics, confidence)
        """

        if primary_metric not in metric_values or len(metric_values) < 2:
            return [], 0.0

        try:
            primary_series = np.array(metric_values[primary_metric])

            correlations = {}
            for metric_name, values in metric_values.items():
                if metric_name == primary_metric or len(values) != len(primary_series):
                    continue

                correlation = abs(np.corrcoef(primary_series, values)[0, 1])
                if correlation > self.correlation_threshold:
                    correlations[metric_name] = correlation

            correlated = sorted(correlations.items(), key=lambda x: x[1], reverse=True)
            metric_names = [m[0] for m in correlated]
            avg_correlation = (
                np.mean([c[1] for c in correlated]) if correlated else 0.0
            )

            return metric_names, min(1.0, avg_correlation)

        except Exception as e:
            logger.error(f"Error in root cause analysis: {e}")
            return [], 0.0
