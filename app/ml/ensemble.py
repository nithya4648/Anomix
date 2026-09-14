"""
Ensemble anomaly detector.

Combines Z-score, IsolationForest, and TrendDetector results into a
single verdict with a unified confidence score, severity level, and
human-readable list of reasons.
"""

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime
from app.ml.anomaly_detector import AnomalyDetector, AnomalyResult
from app.ml.trend_detector import TrendDetector
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class EnsembleResult:
    """Final combined detection output."""
    is_anomaly: bool
    confidence: float
    severity: str                         # "info" | "warning" | "critical"
    reasons: list[str] = field(default_factory=list)
    per_method_scores: dict[str, float] = field(default_factory=dict)


class EnsembleDetector:
    """
    Runs Z-score, IsolationForest, and TrendDetector on the same data,
    combines their confidence scores via a weighted average, and produces
    a final EnsembleResult.
    """

    # Default weights (must sum to 1.0)
    DEFAULT_WEIGHTS = {
        "zscore": 0.35,
        "isolation_forest": 0.40,
        "trend": 0.25,
    }

    # Severity thresholds (applied to combined confidence)
    SEVERITY_THRESHOLDS = {
        "critical": 0.75,
        "warning": 0.50,
        "info": 0.0,
    }

    def __init__(
        self,
        z_score_threshold: float = 3.0,
        contamination: float = 0.1,
        min_samples: int = 50,
        window_size: int = 100,
        trend_window: int = 10,
        trend_pct_threshold: float = 50.0,
        weights: Optional[dict[str, float]] = None,
    ):
        self.weights = weights or self.DEFAULT_WEIGHTS.copy()

        # Sub-detectors
        self._zscore = AnomalyDetector(
            method="z_score",
            z_score_threshold=z_score_threshold,
            min_samples=min_samples,
            window_size=window_size,
        )
        self._iforest = AnomalyDetector(
            method="isolation_forest",
            contamination=contamination,
            min_samples=min_samples,
            window_size=window_size,
        )
        self._trend = TrendDetector(
            window_size=trend_window,
            pct_threshold=trend_pct_threshold,
            min_samples=min_samples,
        )

    def detect(
        self,
        metric_name: str,
        current_value: float,
        historical_values: list[float],
        timestamps: Optional[list[datetime]] = None,
    ) -> EnsembleResult:
        """
        Run all three sub-detectors and combine their outputs.

        Args:
            metric_name: Name of the metric.
            current_value: The latest data point.
            historical_values: Previous values (oldest first).
            timestamps: Optional timestamps for the trend detector.

        Returns:
            EnsembleResult with combined verdict.
        """

        # --- run sub-detectors ------------------------------------------------
        z_result = self._zscore.detect(
            metric_name, current_value, historical_values, timestamps
        )
        iso_result = self._iforest.detect(
            metric_name, current_value, historical_values, timestamps
        )
        trend_result = self._trend.detect(
            metric_name, current_value, historical_values, timestamps
        )

        # --- per-method scores ------------------------------------------------
        per_method_scores = {
            "zscore": z_result.confidence_score,
            "isolation_forest": iso_result.confidence_score,
            "trend": trend_result.confidence_score,
        }

        # --- weighted average -------------------------------------------------
        combined_confidence = sum(
            self.weights[method] * score
            for method, score in per_method_scores.items()
        )
        combined_confidence = max(0.0, min(1.0, combined_confidence))

        # --- any sub-detector flagged? ----------------------------------------
        any_flagged = z_result.is_anomaly or iso_result.is_anomaly or trend_result.is_anomaly
        is_anomaly = any_flagged and combined_confidence >= 0.4

        # --- severity ---------------------------------------------------------
        severity = self._compute_severity(combined_confidence)

        # --- human-readable reasons -------------------------------------------
        reasons: list[str] = []

        if z_result.is_anomaly and z_result.z_score is not None:
            reasons.append(f"{z_result.z_score:.1f}σ above baseline")
        if iso_result.is_anomaly:
            reasons.append("Isolation Forest flagged as anomalous")
        reasons.extend(trend_result.reason)

        return EnsembleResult(
            is_anomaly=is_anomaly,
            confidence=combined_confidence,
            severity=severity,
            reasons=reasons,
            per_method_scores=per_method_scores,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _compute_severity(confidence: float) -> str:
        """Map combined confidence to a severity label."""
        if confidence >= 0.75:
            return "critical"
        elif confidence >= 0.50:
            return "warning"
        return "info"
