from sqlalchemy import Column, String, Float, Integer, Boolean
from sqlalchemy.dialects.postgresql import UUID
import uuid

from .base import Base

class RuleConfig(Base):
    __tablename__ = "rule_config"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    metric_name = Column(String, nullable=False, default="*")
    threshold_value = Column(Float, nullable=False)
    duration_minutes = Column(Integer, nullable=False, default=1)
    severity = Column(String, nullable=False, default="warning")
    enabled = Column(Boolean, nullable=False, default=True)
    recovery_confirmation_minutes = Column(Integer, nullable=True, default=5)  # for auto-recovery
