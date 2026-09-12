from datetime import datetime, timedelta
from app.services.alert_dampener import AlertDampener

def test_alert_dampener_suppression():
    dampener = AlertDampener(base_window_minutes=5)
    now = datetime.utcnow()

    # First alert should NOT be suppressed
    suppress1 = dampener.should_suppress("cpu_usage", "critical", now)
    assert suppress1 is False

    # Second alert 1 minute later SHOULD be suppressed
    suppress2 = dampener.should_suppress("cpu_usage", "critical", now + timedelta(minutes=1))
    assert suppress2 is True

    # Alert 6 minutes later SHOULD pass and expand backoff window
    suppress3 = dampener.should_suppress("cpu_usage", "critical", now + timedelta(minutes=6))
    assert suppress3 is False
