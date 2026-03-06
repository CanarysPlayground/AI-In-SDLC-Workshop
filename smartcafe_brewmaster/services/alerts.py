"""
Alert Service for managing brew quality alerts.

Detects burn and over-brew conditions, generates alerts with deduplication.
"""

import logging
from datetime import datetime, timedelta
from typing import List

from ..adapters import DatabaseAdapter
from ..domain import Alert, BurnDetector, OverBrewDetector, AlertDeduplicator
from ..domain import BrewSchedule

logger = logging.getLogger(__name__)


class AlertService:
    """Service for detecting and managing alerts."""

    def __init__(
        self,
        db: DatabaseAdapter,
        burn_temp_threshold: float = 98.0,
        burn_duration_sec: float = 30.0,
        overbrew_grace_percent: float = 10.0,
        serving_temp_min: float = 50.0,
        serving_temp_max: float = 75.0,
        dedup_window_sec: float = 300.0,
    ):
        """Initialize alert service.
        
        Args:
            db: Database adapter.
            burn_temp_threshold: Temperature threshold for burn detection.
            burn_duration_sec: Duration threshold for burn detection.
            overbrew_grace_percent: Grace period for over-brew detection.
            serving_temp_min: Min serving temperature.
            serving_temp_max: Max serving temperature.
            dedup_window_sec: Deduplication window in seconds.
        """
        self.db = db
        self.burn_detector = BurnDetector(burn_temp_threshold, burn_duration_sec)
        self.overbrew_detector = OverBrewDetector(
            overbrew_grace_percent, serving_temp_min, serving_temp_max
        )
        self.deduplicator = AlertDeduplicator(dedup_window_sec)

    def check_brew_alerts(self, brew_id: int) -> None:
        """Check for alerts on a specific brew.
        
        Args:
            brew_id: ID of brew to check.
        """
        brew = self.db.get_brew_schedule(brew_id)
        if not brew:
            logger.warning(f"Brew {brew_id} not found for alert check")
            return

        events = self.db.get_events_by_brew(brew_id)
        recent_alerts = self.db.get_recent_alerts(minutes=5)

        # Check for burn condition
        is_burned, max_temp = self.burn_detector.detect_burn(brew, events)
        if is_burned and self.deduplicator.should_alert("burn", brew_id, recent_alerts):
            alert = Alert(
                alert_type="burn",
                brew_id=brew_id,
                message=f"BURN ALERT: Brew {brew.recipe_name} exceeded {self.burn_detector.temp_threshold}°C "
                        f"(reached {max_temp:.1f}°C) for > {self.burn_detector.duration}sec",
                severity="error",
            )
            self.db.create_alert(alert)
            logger.error(alert.message)

        # Check for over-brew condition
        is_overbrew, reason = self.overbrew_detector.detect_overbrew(
            brew, datetime.utcnow(), events
        )
        if is_overbrew and self.deduplicator.should_alert("overbrew", brew_id, recent_alerts):
            alert = Alert(
                alert_type="overbrew",
                brew_id=brew_id,
                message=f"OVERBREW ALERT: Brew {brew.recipe_name} - {reason}",
                severity="warn",
            )
            self.db.create_alert(alert)
            logger.warning(alert.message)

    def check_all_active_brews(self) -> None:
        """Check alerts for all active brews."""
        active_brews = self.db.list_brew_schedules(status="brewing")
        for brew in active_brews:
            self.check_brew_alerts(brew.id)

    def get_recent_alerts(self, minutes: int = 60) -> List[Alert]:
        """Get recent alerts.
        
        Args:
            minutes: Number of minutes to look back.
        
        Returns:
            List of Alert objects.
        """
        return self.db.get_recent_alerts(minutes=minutes)

    def get_alerts_summary(self) -> dict:
        """Get summary of recent alert activity.
        
        Returns:
            Dictionary with alert summary statistics.
        """
        recent = self.get_recent_alerts(minutes=60)
        critical = [a for a in recent if a.is_critical()]
        warnings = [a for a in recent if a.severity == "warn"]

        return {
            "total_alerts_1h": len(recent),
            "critical_count": len(critical),
            "warning_count": len(warnings),
            "by_type": self._count_by_type(recent),
        }

    def _count_by_type(self, alerts: List[Alert]) -> dict:
        """Count alerts by type.
        
        Args:
            alerts: List of alerts.
        
        Returns:
            Dictionary with count by alert_type.
        """
        counts = {}
        for alert in alerts:
            counts[alert.alert_type] = counts.get(alert.alert_type, 0) + 1
        return counts
