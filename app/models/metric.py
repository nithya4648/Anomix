from sqlalchemy import Column, String, Float, DateTime, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from app.models.base import Base, TimestampMixin, UUIDMixin
import json


class Metric(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "metrics"
    __table_args__ = (
        Index("idx_metric_name_timestamp", "metric_name", "timestamp"),
        Index("idx_metric_timestamp", "timestamp"),
        Index("idx_metric_name", "metric_name"),
    )

    metric_name: Mapped[str] = mapped_column(String(256), nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    labels: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    
    def __repr__(self) -> str:
        return f"<Metric {self.metric_name}={self.value} at {self.timestamp}>"
