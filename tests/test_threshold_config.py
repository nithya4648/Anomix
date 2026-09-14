import pytest
from app.schemas.rule_config import RuleConfigCreate, RuleConfigUpdate

def test_rule_config_schemas():
    rule_create = RuleConfigCreate(
        metric_name="disk_io",
        threshold_value=0.85,
        duration_minutes=5,
        severity="critical",
        enabled=True,
        recovery_confirmation_minutes=10,
    )
    assert rule_create.metric_name == "disk_io"
    assert rule_create.threshold_value == 0.85
    assert rule_create.recovery_confirmation_minutes == 10

    rule_update = RuleConfigUpdate(threshold_value=0.90)
    assert rule_update.threshold_value == 0.90
    assert rule_update.metric_name is None
