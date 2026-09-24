import pytest
import asyncio
from datetime import datetime, timedelta
import numpy as np
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.models.base import Base
from app.models.metric import Metric
from app.models.incident import Incident
from app.models.rule_config import RuleConfig
from app.services.metrics import MetricService, AnomalyService
from app.services.stream.stream_consumer import check_and_auto_recover_incidents



@pytest.fixture
def test_db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.mark.asyncio
async def test_auto_recovery_does_not_resolve_while_anomalous(test_db):
    """(a) Incident does NOT resolve while telemetry is still anomalous."""
    now = datetime.utcnow()
    metric_name = "cpu_usage"

    # Create an open incident
    incident = Incident(
        title="CRITICAL: cpu_usage Anomaly",
        description="High CPU usage detected",
        status="open",
        severity="critical",
        detected_at=now - timedelta(minutes=15),
        correlated_metrics=metric_name,
        progress_stage="open",
    )
    test_db.add(incident)

    # Configure rule with 5 min recovery confirmation
    rule = RuleConfig(
        metric_name=metric_name,
        threshold_value=0.5,
        duration_minutes=1,
        severity="critical",
        enabled=True,
        recovery_confirmation_minutes=5,
    )
    test_db.add(rule)
    test_db.commit()

    # Seed baseline historical data (50 normal points around 50.0)
    for i in range(50):
        t = now - timedelta(minutes=30 - i * 0.5)
        m = Metric(
            metric_name=metric_name,
            value=50.0 + (i % 3),
            timestamp=t,
            labels={},
        )
        test_db.add(m)

    # Seed recent anomalous point in confirmation window (e.g. value=100.0)
    anom_metric = Metric(
        metric_name=metric_name,
        value=100.0,
        timestamp=now - timedelta(minutes=2),
        labels={},
    )
    test_db.add(anom_metric)
    test_db.commit()

    metric_service = MetricService(test_db)
    anomaly_service = AnomalyService(test_db)

    # Attempt recovery
    recovered = await check_and_auto_recover_incidents(
        db=test_db,
        metric_name=metric_name,
        current_timestamp=now,
        anomaly_service=anomaly_service,
        metric_service=metric_service,
    )

    # Should not recover
    assert len(recovered) == 0
    test_db.refresh(incident)
    assert incident.status == "open"
    assert incident.resolved_at is None
    assert incident.progress_stage != "resolved"


@pytest.mark.asyncio
async def test_auto_recovery_resolves_after_confirmation_window(test_db):
    """(b) Incident DOES resolve after confirmation window passes with normal readings."""
    now = datetime.utcnow()
    metric_name = "cpu_usage"

    # Create an open incident
    incident = Incident(
        title="CRITICAL: cpu_usage Anomaly",
        description="High CPU usage detected",
        status="open",
        severity="critical",
        detected_at=now - timedelta(minutes=20),
        correlated_metrics=metric_name,
        progress_stage="open",
    )
    test_db.add(incident)

    # Configure rule with 5 min recovery confirmation
    rule = RuleConfig(
        metric_name=metric_name,
        threshold_value=0.5,
        duration_minutes=1,
        severity="critical",
        enabled=True,
        recovery_confirmation_minutes=5,
    )
    test_db.add(rule)
    test_db.commit()

    # Seed 60 normal points up to now (clean baseline and clean recent window)
    for i in range(60):
        t = now - timedelta(minutes=15 - i * 0.25)
        m = Metric(
            metric_name=metric_name,
            value=50.0 + (i % 2),
            timestamp=t,
            labels={},
        )
        test_db.add(m)
    test_db.commit()

    metric_service = MetricService(test_db)
    anomaly_service = AnomalyService(test_db)

    # Attempt recovery
    recovered = await check_and_auto_recover_incidents(
        db=test_db,
        metric_name=metric_name,
        current_timestamp=now,
        anomaly_service=anomaly_service,
        metric_service=metric_service,
    )

    # Should recover
    assert len(recovered) == 1
    assert recovered[0].id == incident.id
    test_db.refresh(incident)
    assert incident.status == "resolved"
    assert incident.resolved_at is not None
    assert incident.progress_stage == "resolved"
    assert incident.progress_percent == 100
