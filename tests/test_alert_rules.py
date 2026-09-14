import pytest
from datetime import datetime, timedelta
from app.services.alert_rules import AlertRuleEngine, AlertRule, IncidentRule

def test_alert_rules_evaluation():
    engine = AlertRuleEngine(
        alert_rules=[
            AlertRule(
                metric_name="cpu_usage",
                threshold_value=0.7,
                duration_minutes=0,
                severity="critical",
                enabled=True,
            )
        ]
    )
    now = datetime.utcnow()
    
    # Below threshold -> no match
    matches_below = engine.evaluate("cpu_usage", 0.5, "warning", now)
    assert len(matches_below) == 0
    
    # Above threshold -> match
    matches_above = engine.evaluate("cpu_usage", 0.85, "critical", now)
    assert len(matches_above) == 1
    assert matches_above[0].severity == "critical"

def test_incident_rule_clustering():
    engine = AlertRuleEngine(
        incident_rule=IncidentRule(min_anomalies=2, time_window_minutes=5, severity="warning")
    )
    now = datetime.utcnow()
    
    # 1 anomaly -> no incident
    engine.evaluate("memory_usage", 0.8, "warning", now)
    assert not engine.should_create_incident("memory_usage", now)
    
    # 2nd anomaly within 5 min -> create incident
    engine.evaluate("memory_usage", 0.9, "critical", now + timedelta(minutes=2))
    assert engine.should_create_incident("memory_usage", now + timedelta(minutes=2))
