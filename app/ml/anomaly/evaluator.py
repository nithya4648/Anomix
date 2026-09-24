import numpy as np
from typing import Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class EvaluationMetrics:
    precision: float
    recall: float
    f1_score: float
    true_positives: int
    false_positives: int
    true_negatives: int
    false_negatives: int


class MetricsEvaluator:
    """Evaluate anomaly detection performance against ground truth"""

    @staticmethod
    def calculate_metrics(
        y_true: np.ndarray,  # 1 = anomaly, 0 = normal
        y_pred: np.ndarray,  # 1 = detected, 0 = not detected
    ) -> EvaluationMetrics:
        """
        Calculate precision, recall, F1, and confusion matrix.

        Args:
            y_true: Ground truth labels (1=anomaly, 0=normal)
            y_pred: Predicted labels (1=detected, 0=not detected)

        Returns:
            EvaluationMetrics object
        """

        # Compute confusion matrix
        tp = np.sum((y_true == 1) & (y_pred == 1))
        fp = np.sum((y_true == 0) & (y_pred == 1))
        tn = np.sum((y_true == 0) & (y_pred == 0))
        fn = np.sum((y_true == 1) & (y_pred == 0))

        # Calculate metrics
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (
            2 * (precision * recall) / (precision + recall)
            if (precision + recall) > 0
            else 0.0
        )

        return EvaluationMetrics(
            precision=float(precision),
            recall=float(recall),
            f1_score=float(f1),
            true_positives=int(tp),
            false_positives=int(fp),
            true_negatives=int(tn),
            false_negatives=int(fn),
        )

    @staticmethod
    def compute_anomaly_score_distribution(
        scores: np.ndarray,
    ) -> dict:
        """Compute statistics about anomaly confidence scores"""

        return {
            "mean": float(np.mean(scores)),
            "std": float(np.std(scores)),
            "min": float(np.min(scores)),
            "max": float(np.max(scores)),
            "median": float(np.median(scores)),
            "p95": float(np.percentile(scores, 95)),
            "p99": float(np.percentile(scores, 99)),
        }
