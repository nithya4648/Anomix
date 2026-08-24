from sqlalchemy import String, Float, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from app.models.base import Base, TimestampMixin, UUIDMixin


class EvaluationMetric(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "evaluation_metrics"
    __table_args__ = (
        Index("idx_eval_metric_name", "metric_name"),
        Index("idx_eval_evaluated_at", "evaluated_at"),
    )

    metric_name: Mapped[str] = mapped_column(String(256), nullable=False)
    evaluation_period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    evaluation_period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    # Evaluation metrics
    precision: Mapped[float] = mapped_column(Float, nullable=False)
    recall: Mapped[float] = mapped_column(Float, nullable=False)
    f1_score: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Confusion matrix
    true_positives: Mapped[int] = mapped_column(nullable=False)
    false_positives: Mapped[int] = mapped_column(nullable=False)
    true_negatives: Mapped[int] = mapped_column(nullable=False)
    false_negatives: Mapped[int] = mapped_column(nullable=False)
    
    # Metadata
    total_samples: Mapped[int] = mapped_column(nullable=False)
    anomaly_count: Mapped[int] = mapped_column(nullable=False)
    detection_method: Mapped[str] = mapped_column(String(50), nullable=False)
    
    def __repr__(self) -> str:
        return f"<EvaluationMetric {self.metric_name} F1={self.f1_score:.3f}>"
