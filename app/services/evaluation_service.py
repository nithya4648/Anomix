from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import numpy as np
from typing import Optional
from sqlalchemy import and_, desc
from app.models.metric import Metric
from app.models.anomaly import Anomaly
from app.models.evaluation import EvaluationMetric
from app.ml import MetricsEvaluator

from app.core.logging import get_logger

logger = get_logger(__name__)


class EvaluationService:
    """Evaluate anomaly detection model performance"""

    def __init__(self, db: Session):
        self.db = db
        self.evaluator = MetricsEvaluator()

    def evaluate_metric(
        self,
        metric_name: str,
        period_hours: int = 24,
        confidence_threshold: float = 0.5,
    ) -> Optional[EvaluationMetric]:
        """
        Evaluate anomaly detection performance for a metric.

        Creates synthetic ground truth based on detected anomalies with high confidence.
        In production, this would use labeled data.

        Args:
            metric_name: Metric to evaluate
            period_hours: Hours to look back
            confidence_threshold: Threshold for considering detection as true positive

        Returns:
            EvaluationMetric record
        """

        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=period_hours)

        # Get metrics in period
        metrics = (
            self.db.query(Metric)
            .filter(
                and_(
                    Metric.metric_name == metric_name,
                    Metric.timestamp >= start_time,
                    Metric.timestamp <= end_time,
                )
            )
            .order_by(Metric.timestamp)
            .all()
        )

        if len(metrics) < 10:
            logger.warning(f"Insufficient metrics for evaluation: {metric_name}")
            return None

        # Create predictions from detector
        y_pred = np.zeros(len(metrics))

        for i, metric in enumerate(metrics):
            anomaly = (
                self.db.query(Anomaly)
                .filter(
                    and_(
                        Anomaly.metric_id == metric.id,
                        Anomaly.anomaly_timestamp == metric.timestamp,
                    )
                )
                .first()
            )

            if anomaly and anomaly.confidence_score >= confidence_threshold:
                y_pred[i] = 1

        # Create synthetic ground truth (labels with confidence >= 0.8 are true anomalies)
        y_true = np.zeros(len(metrics))
        high_confidence_anomalies = (
            self.db.query(Anomaly)
            .filter(
                and_(
                    Anomaly.metric_name == metric_name,
                    Anomaly.anomaly_timestamp >= start_time,
                    Anomaly.anomaly_timestamp <= end_time,
                    Anomaly.confidence_score >= 0.8,
                )
            )
            .all()
        )

        for anomaly in high_confidence_anomalies:
            matching_idx = next(
                (i for i, m in enumerate(metrics) if m.timestamp == anomaly.anomaly_timestamp),
                None,
            )
            if matching_idx is not None:
                y_true[matching_idx] = 1

        # Calculate metrics
        eval_metrics = self.evaluator.calculate_metrics(y_true, y_pred)

        # Store evaluation
        eval_record = EvaluationMetric(
            metric_name=metric_name,
            evaluation_period_start=start_time,
            evaluation_period_end=end_time,
            evaluated_at=datetime.utcnow(),
            precision=eval_metrics.precision,
            recall=eval_metrics.recall,
            f1_score=eval_metrics.f1_score,
            true_positives=eval_metrics.true_positives,
            false_positives=eval_metrics.false_positives,
            true_negatives=eval_metrics.true_negatives,
            false_negatives=eval_metrics.false_negatives,
            total_samples=len(metrics),
            anomaly_count=int(np.sum(y_true)),
            detection_method="isolation_forest",
        )

        self.db.add(eval_record)
        self.db.commit()
        self.db.refresh(eval_record)

        logger.info(
            f"Evaluated {metric_name}: Precision={eval_metrics.precision:.3f}, "
            f"Recall={eval_metrics.recall:.3f}, F1={eval_metrics.f1_score:.3f}"
        )

        return eval_record

    def get_evaluation_history(
        self,
        metric_name: str,
        limit: int = 10,
    ) -> list[EvaluationMetric]:
        """Get evaluation history for a metric"""

        return (
            self.db.query(EvaluationMetric)
            .filter(EvaluationMetric.metric_name == metric_name)
            .order_by(desc(EvaluationMetric.evaluated_at))
            .limit(limit)
            .all()
        )

    def get_latest_evaluation(
        self,
        metric_name: str,
    ) -> Optional[EvaluationMetric]:
        """Get latest evaluation for a metric"""

        return (
            self.db.query(EvaluationMetric)
            .filter(EvaluationMetric.metric_name == metric_name)
            .order_by(desc(EvaluationMetric.evaluated_at))
            .first()
        )
