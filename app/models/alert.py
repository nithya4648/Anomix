from sqlalchemy import String, DateTime, Index, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from app.models.base import Base, TimestampMixin, UUIDMixin


class Alert(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "alerts"
    __table_args__ = (
        Index("idx_alert_anomaly_id", "anomaly_id"),
        Index("idx_alert_incident_id", "incident_id"),
        Index("idx_alert_severity", "severity"),
        Index("idx_alert_status", "status"),
    )

    anomaly_id: Mapped[str] = mapped_column(String(36), ForeignKey("anomalies.id"), nullable=False)
    incident_id: Mapped[str] = mapped_column(String(36), ForeignKey("incidents.id"), nullable=True)
    severity: Mapped[str] = mapped_column(String(50), nullable=False)  # critical, warning, info
    message: Mapped[str] = mapped_column(String(512), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="new", nullable=False)  # new, acknowledged, resolved
    acknowledged_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    acknowledged_by: Mapped[str] = mapped_column(String(100), nullable=True)
    resolved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self) -> str:
        return f"<Alert {self.severity}: {self.message}>"
