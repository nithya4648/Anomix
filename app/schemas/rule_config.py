from pydantic import BaseModel, Field
from typing import Optional

class RuleConfigBase(BaseModel):
    metric_name: str = Field(..., description="Metric name, * for all")
    threshold_value: float = Field(..., gt=0, description="Confidence threshold")
    duration_minutes: int = Field(..., gt=0, description="Duration in minutes")
    severity: str = Field(..., description="critical, warning, info")
    enabled: bool = Field(default=True)
    recovery_confirmation_minutes: int = Field(default=5, description="Minutes to auto‑recover")

class RuleConfigCreate(RuleConfigBase):
    pass

class RuleConfigUpdate(BaseModel):
    metric_name: Optional[str] = None
    threshold_value: Optional[float] = None
    duration_minutes: Optional[int] = None
    severity: Optional[str] = None
    enabled: Optional[bool] = None
    recovery_confirmation_minutes: Optional[int] = None

class RuleConfigResponse(RuleConfigBase):
    id: str
    class Config:
        from_attributes = True
