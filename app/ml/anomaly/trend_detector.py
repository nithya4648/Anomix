"""
Trend-based anomaly detector.

Detects sustained directional changes over a rolling window
(e.g. a metric that rose 72% in 10 minutes).
"""

import numpy as np
from typing import Optional
from datetime import datetime
from app.ml.anomaly.anomaly_detector import AnomalyResult

from app.core.logging import get_logger

logger = get_logger(__name__)


class TrendDetector:
    """
    Detects sustained directional change over a rolling window.

    Flags when the percentage change over the last `window_size` points
    exceeds `pct_threshold`.  Confidence is proportional to how far
    the observed change exceeds the threshold.
    """

    def __init__(
        self,
        window_size: int = 10,
        pct_threshold: float = 50.0,
        min_samples: int = 10,
    ):
        """
        Args:
            window_size: Number of recent points to measure the trend over.
            pct_threshold: Percentage change threshold to consider anomalous.
            min_samples: Minimum number of historical values required.
        """
        self.window_size = window_size
        self.pct_threshold = pct_threshold
        self.min_samples = min_samples

    def detect(
        self,
        metric_name: str,
        current_value: float,
        historical_values: list[float],
        timestamps: Optional[list[datetime]] = None,
    ) -> AnomalyResult:
        """
        Detect trend-based anomalies.

        Args:
            metric_name: Name of the metric.
            current_value: The latest value.
            historical_values: Previous values (oldest first).
            timestamps: Optional list of timestamps for human-readable reasons.

        Returns:
            AnomalyResult with trend detection details.
        """

        if len(historical_values) < self.min_samples:
            return AnomalyResult(
                is_anomaly=False,
                confidence_score=0.0,
                detection_method="trend",
            )

        try:
            # Combine historical + current for the window
            all_values = historical_values + [current_value]
            window = all_values[-self.window_size:]

            if len(window) < 2:
                return AnomalyResult(
                    is_anomaly=False,
                    confidence_score=0.0,
                    detection_method="trend",
                )

            baseline = window[0]

            # Avoid division by zero
            if baseline == 0:
                baseline = 1e-9

            pct_change = ((current_value - baseline) / abs(baseline)) * 100.0

            abs_pct = abs(pct_change)
            is_anomaly = abs_pct > self.pct_threshold

            # Confidence: 0 at threshold, 1 at 2× threshold, capped at 1
            confidence = min(1.0, abs_pct / (self.pct_threshold * 2)) if is_anomaly else abs_pct / (self.pct_threshold * 2)
            confidence = max(0.0, min(1.0, confidence))

            # Build human-readable reason
            reason: list[str] = []
            if is_anomaly:
                direction = "rose" if pct_change > 0 else "fell"

                if timestamps and len(timestamps) >= self.window_size:
                    start_ts = timestamps[-self.window_size]
                    end_ts = timestamps[-1]
                    delta = end_ts - start_ts
                    minutes = max(1, int(delta.total_seconds() / 60))
                    reason.append(
                        f"value {direction} {abs_pct:.0f}% in {minutes} minutes"
                    )
                else:
                    reason.append(
                        f"value {direction} {abs_pct:.0f}% over last {self.window_size} points"
                    )

            return AnomalyResult(
                is_anomaly=is_anomaly,
                confidence_score=confidence,
                detection_method="trend",
                expected_value=float(baseline),
                reason=reason,
            )

        except Exception as e:
            logger.error(f"Error in trend detection for {metric_name}: {e}")
            return AnomalyResult(
                is_anomaly=False,
                confidence_score=0.0,
                detection_method="trend",
            )
