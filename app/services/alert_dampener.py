from datetime import datetime, timedelta
from typing import Optional, Dict

class AlertDampener:
    """
    Dampens duplicate alerts using a dynamic window and exponential backoff.
    """

    def __init__(self, base_window_minutes: int = 5, max_window_minutes: int = 60):
        self.base_window_minutes = base_window_minutes
        self.max_window_minutes = max_window_minutes
        # Key: (metric_name, severity) -> dict state
        self._state: Dict[tuple, dict] = {}

    def should_suppress(self, metric_name: str, severity: str, timestamp: Optional[datetime] = None) -> bool:
        now = timestamp or datetime.utcnow()
        key = (metric_name, severity)

        if key not in self._state:
            self._state[key] = {
                "last_alert_time": now,
                "consecutive_count": 1,
                "current_window_minutes": self.base_window_minutes,
            }
            return False

        state = self._state[key]
        elapsed_minutes = (now - state["last_alert_time"]).total_seconds() / 60.0

        if elapsed_minutes < state["current_window_minutes"]:
            # Suppress duplicate alert within backoff window
            state["consecutive_count"] += 1
            return True
        else:
            # Window expired, allow alert and update exponential backoff window
            state["consecutive_count"] += 1
            state["last_alert_time"] = now
            state["current_window_minutes"] = min(
                self.max_window_minutes,
                state["current_window_minutes"] * 2
            )
            return False

    def reset(self, metric_name: str, severity: str):
        key = (metric_name, severity)
        if key in self._state:
            del self._state[key]
