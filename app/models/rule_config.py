from sqlalchemy import Column, String, Float, Integer, Boolean
from .base import Base, UUIDMixin


class RuleConfig(Base, UUIDMixin):
    __tablename__ = "rule_config"

    metric_name = Column(String, nullable=False, default="*")
    threshold_value = Column(Float, nullable=False)
    duration_minutes = Column(Integer, nullable=False, default=1)
    severity = Column(String, nullable=False, default="warning")
    enabled = Column(Boolean, nullable=False, default=True)
    recovery_confirmation_minutes = Column(Integer, nullable=True, default=5)  # for auto-recovery

