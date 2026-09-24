"""
Alert rule evaluation engine.

Rules are simple config objects that define conditions for triggering alerts
and auto-creating incidents from anomaly clusters.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional
from collections import defaultdict
from sqlalchemy.orm import Session
from app.core.logging import get_logger

logger = get_logger(__name__)

@dataclass
class AlertRule:
    """A single alert rule definition."""
    metric_name: str  # "*" for all metrics
    threshold_value: float  # confidence score threshold
    duration_minutes: int  # how long condition must persist
    severity: str  # critical, warning, info
    enabled: bool = True
    description: str = ""


@dataclass
class IncidentRule:
    """Rule for auto-creating incidents from anomaly clusters."""
    min_anomalies: int  # K anomalies required
    time_window_minutes: int  # within T minutes
    severity: str = "warning"  # minimum severity of anomalies to count
    enabled: bool = True


@dataclass
class RuleMatch:
    """Result of a rule evaluation."""
    rule: AlertRule
    metric_name: str
    severity: str
    message: str
    confidence: float
    timestamp: datetime


# Default built-in rules
DEFAULT_ALERT_RULES = [
    AlertRule(
        metric_name="*",
        threshold_value=0.75,
        duration_minutes=1,
        severity="critical",
        description="Any metric with confidence >= 0.75",
    ),
    AlertRule(
        metric_name="*",
        threshold_value=0.50,
        duration_minutes=3,
        severity="warning",
        description="Any metric with confidence >= 0.50 for 3+ minutes",
    ),
    AlertRule(
        metric_name="cpu_usage",
        threshold_value=0.60,
        duration_minutes=5,
        severity="critical",
        description="CPU anomaly score >= 0.60 for 5+ minutes",
    ),
]

DEFAULT_INCIDENT_RULE = IncidentRule(
    min_anomalies=3,
    time_window_minutes=10,
    severity="warning",
)


class AlertRuleEngine:
    """
    Evaluates alert rules against incoming anomaly results.

    Tracks per-metric anomaly history to support duration-based rules
    and anomaly clustering for auto-incident creation.
    """

    def __init__(
        self,
        db: Optional[Session] = None,
        alert_rules: Optional[list[AlertRule]] = None,
        incident_rule: Optional[IncidentRule] = None,
    ):
        """Initialize the engine.
        If a database session is provided and no explicit alert_rules list is given,
        the engine will load rules from the `rule_config` table.
        """
        if db is not None and alert_rules is None:
            # Load RuleConfig entries from DB and convert to AlertRule objects
            try:
                from app.models.rule_config import RuleConfig
                configs = db.query(RuleConfig).all()
                alert_rules = [
                    AlertRule(
                        metric_name=c.metric_name,
                        threshold_value=c.threshold_value,
                        duration_minutes=c.duration_minutes,
                        severity=c.severity,
                        enabled=c.enabled,
                        description="",
                    )
                    for c in configs
                ]
            except Exception as e:
                logger.warning(f"Could not load alert rules from DB, falling back to defaults: {e}")
                alert_rules = None
        self.alert_rules = alert_rules or list(DEFAULT_ALERT_RULES)
        self.incident_rule = incident_rule or DEFAULT_INCIDENT_RULE

        # Per-metric tracking: metric_name -> list of (timestamp, confidence, severity)
        self._anomaly_history: dict[str, list[tuple[datetime, float, str]]] = defaultdict(list)

    def evaluate(
        self,
        metric_name: str,
        confidence: float,
        severity: str,
        timestamp: Optional[datetime] = None,
    ) -> list[RuleMatch]:
        """
        Evaluate all enabled alert rules for a given anomaly detection result.
        Returns a list of RuleMatch objects for rules that fired.
        """
        now = timestamp or datetime.utcnow()
        matches: list[RuleMatch] = []

        # Record this anomaly in history
        self._anomaly_history[metric_name].append((now, confidence, severity))
        self._prune_history(metric_name, now)

        for rule in self.alert_rules:
            if not rule.enabled:
                continue

            # Check if rule applies to this metric
            if rule.metric_name != "*" and rule.metric_name != metric_name:
                continue

            # Check confidence threshold
            if confidence < rule.threshold_value:
                continue

            # Check duration requirement
            if rule.duration_minutes > 0 and not self._check_duration(
                metric_name, rule.threshold_value, rule.duration_minutes, now
            ):
                continue

            matches.append(
                RuleMatch(
                    rule=rule,
                    metric_name=metric_name,
                    severity=rule.severity,
                    message=self._build_message(rule, metric_name, confidence),
                    confidence=confidence,
                    timestamp=now,
                )
            )

        return matches

    def should_create_incident(
        self, metric_name: str, timestamp: Optional[datetime] = None
    ) -> bool:
        """
        Check if enough anomalies have accumulated within the time window
        to warrant auto-creating an incident.
        """
        rule = self.incident_rule
        if not rule.enabled:
            return False

        now = timestamp or datetime.utcnow()
        cutoff = now - timedelta(minutes=rule.time_window_minutes)

        severity_rank = {"info": 0, "warning": 1, "critical": 2}
        min_rank = severity_rank.get(rule.severity, 1)

        qualifying = [
            entry
            for entry in self._anomaly_history.get(metric_name, [])
            if entry[0] >= cutoff and severity_rank.get(entry[2], 0) >= min_rank
        ]

        return len(qualifying) >= rule.min_anomalies

    def _check_duration(
        self,
        metric_name: str,
        threshold: float,
        duration_minutes: int,
        now: datetime,
    ) -> bool:
        """Check if confidence has been above threshold for duration_minutes."""
        cutoff = now - timedelta(minutes=duration_minutes)
        history = self._anomaly_history.get(metric_name, [])

        # Need at least one entry before the cutoff to confirm sustained condition
        entries_in_window = [e for e in history if e[0] >= cutoff and e[1] >= threshold]
        return len(entries_in_window) >= 1

    def _prune_history(self, metric_name: str, now: datetime):
        """Remove entries older than the max relevant window (60 min)."""
        cutoff = now - timedelta(minutes=60)
        self._anomaly_history[metric_name] = [
            e for e in self._anomaly_history[metric_name] if e[0] >= cutoff
        ]

    def _build_message(self, rule: AlertRule, metric_name: str, confidence: float) -> str:
        """Build a human-readable alert message."""
        if rule.metric_name == "*":
            return (
                f"Anomaly detected on '{metric_name}' with confidence {confidence:.2f} "
                f"(threshold: {rule.threshold_value}, severity: {rule.severity})"
            )
        return (
            f"Rule '{rule.description}' triggered on '{metric_name}' "
            f"with confidence {confidence:.2f}"
        )

    def add_rule(self, rule: AlertRule):
        """Add a new alert rule."""
        self.alert_rules.append(rule)

    def remove_rule(self, index: int):
        """Remove an alert rule by index."""
        if 0 <= index < len(self.alert_rules):
            self.alert_rules.pop(index)
