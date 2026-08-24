from sqlalchemy import String, Float, DateTime, Index, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from app.models.base import Base, TimestampMixin, UUIDMixin


class Anomaly(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "anomalies"
    __table_args__ = (
        Index("idx_anomaly_metric_timestamp", "metric_name", "anomaly_timestamp"),
        Index("idx_anomaly_timestamp", "anomaly_timestamp"),
        Index("idx_anomaly_metric_name", "metric_name"),
        Index("idx_anomaly_is_confirmed", "is_confirmed"),
    )

    metric_name: Mapped[str] = mapped_column(String(256), nullable=False)
    metric_id: Mapped[str] = mapped_column(String(36), nullable=False)
    anomaly_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)  # 0-1
    detection_method: Mapped[str] = mapped_column(String(50), nullable=False)  # isolation_forest, zscore
    z_score: Mapped[float] = mapped_column(Float, nullable=True)
    expected_value: Mapped[float] = mapped_column(Float, nullable=True)
    is_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    
    def __repr__(self) -> str:
        return f"<Anomaly {self.metric_name}={self.value} (confidence={self.confidence_score:.2f})>"
