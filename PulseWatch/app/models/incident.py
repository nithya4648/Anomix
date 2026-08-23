from sqlalchemy import String, DateTime, Index, Boolean, Text, Float
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from app.models.base import Base, TimestampMixin, UUIDMixin


class Incident(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "incidents"
    __table_args__ = (
        Index("idx_incident_status", "status"),
        Index("idx_incident_severity", "severity"),
        Index("idx_incident_detected_at", "detected_at"),
    )

    title: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="open", nullable=False)  # open, investigating, resolved
    severity: Mapped[str] = mapped_column(String(50), nullable=False)  # critical, warning, info
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    resolved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Root cause analysis
    root_cause: Mapped[str] = mapped_column(Text, nullable=True)
    correlated_metrics: Mapped[list] = mapped_column(String(1024), nullable=True)  # comma-separated
    confidence: Mapped[float] = mapped_column(Float, nullable=True)
    
    def __repr__(self) -> str:
        return f"<Incident {self.title} ({self.status})>"
