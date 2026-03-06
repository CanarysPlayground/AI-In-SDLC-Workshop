"""
Core domain logic for SmartCafé BrewMaster.

Contains pure business logic for detecting alerts, calculating brewing states,
and other core domain operations with no IO dependencies.
"""

from datetime import datetime, timedelta
from typing import List, Tuple

from .models import Alert, BrewSchedule, TemperatureEvent


class BurnDetector:
    """Detects burn conditions based on temperature and duration.
    
    A burn condition is detected when temperature exceeds the threshold
    for a sustained duration while a brew is active.
    """

    def __init__(self, temp_threshold_c: float, duration_sec: float):
        """Initialize detector with thresholds.
        
        Args:
            temp_threshold_c: Temperature threshold in Celsius.
            duration_sec: Duration in seconds for threshold violation.
        """
        self.temp_threshold = temp_threshold_c
        self.duration = duration_sec

    def detect_burn(
        self,
        brew: BrewSchedule,
        events: List[TemperatureEvent],
    ) -> Tuple[bool, float]:
        """Detect if a burn condition exists.
        
        Args:
            brew: The brew schedule being monitored.
            events: List of recent temperature events.
        
        Returns:
            Tuple[bool, float]: (is_burn_detected, max_temp_observed)
        """
        if not brew.is_active() or not events:
            return False, 0.0

        # Filter events from this brew
        brew_events = [e for e in events if e.brew_id == brew.id]
        if not brew_events:
            return False, 0.0

        max_temp = max(e.temp_c for e in brew_events)
        if max_temp <= self.temp_threshold:
            return False, max_temp

        # Check duration: has temp been high for long enough?
        first_high_event = next(
            (e for e in brew_events if e.temp_c > self.temp_threshold),
            None,
        )
        if not first_high_event:
            return False, max_temp

        last_high_event = next(
            (e for e in reversed(brew_events) if e.temp_c > self.temp_threshold),
            None,
        )
        if not last_high_event:
            return False, max_temp

        duration_elapsed = (
            last_high_event.observed_at - first_high_event.observed_at
        ).total_seconds()
        is_burned = duration_elapsed >= self.duration

        return is_burned, max_temp


class OverBrewDetector:
    """Detects over-brew conditions.
    
    An over-brew condition occurs when:
    1. Brew exceeds scheduled duration + grace period
    2. Temperature remains above serving range after completion
    """

    def __init__(
        self,
        grace_percent: float,
        serving_temp_min: float,
        serving_temp_max: float,
    ):
        """Initialize detector with thresholds.
        
        Args:
            grace_percent: Grace period as percentage of duration.
            serving_temp_min: Minimum serving temperature in Celsius.
            serving_temp_max: Maximum serving temperature in Celsius.
        """
        self.grace_percent = grace_percent
        self.serving_temp_min = serving_temp_min
        self.serving_temp_max = serving_temp_max

    def detect_overbrew(
        self,
        brew: BrewSchedule,
        current_time: datetime,
        recent_events: List[TemperatureEvent],
    ) -> Tuple[bool, str]:
        """Detect if an over-brew condition exists.
        
        Args:
            brew: The brew schedule being monitored.
            current_time: Current time in UTC.
            recent_events: List of recent temperature events.
        
        Returns:
            Tuple[bool, str]: (is_overbrew, reason)
        """
        grace_minutes = brew.duration_min * self.grace_percent / 100
        allowed_end = brew.expected_end_time() + timedelta(minutes=grace_minutes)

        # Check duration exceeded
        if current_time > allowed_end:
            return True, f"Brew exceeded scheduled duration + {grace_minutes}min grace"

        # Check temperature above serving range after completion
        if not brew.is_active():
            brew_events = [e for e in recent_events if e.brew_id == brew.id]
            if brew_events:
                last_event = max(brew_events, key=lambda e: e.observed_at)
                if last_event.temp_c > self.serving_temp_max:
                    return True, f"Temperature {last_event.temp_c}°C still above serving range"

        return False, ""


class AlertDeduplicator:
    """Prevents duplicate alert generation for the same condition.
    
    Uses time-window and context-based deduplication to avoid alert spam.
    """

    def __init__(self, dedup_window_sec: float = 300.0):
        """Initialize deduplicator.
        
        Args:
            dedup_window_sec: Time window for deduplication in seconds.
        """
        self.dedup_window = dedup_window_sec

    def should_alert(
        self,
        alert_type: str,
        brew_id: int,
        recent_alerts: List[Alert],
    ) -> bool:
        """Determine if a new alert should be generated.
        
        Args:
            alert_type: Type of alert (burn|overbrew|system).
            brew_id: ID of associated brew.
            recent_alerts: List of alerts from recent time window.
        
        Returns:
            bool: True if alert should be generated.
        """
        # Check if same alert type exists for same brew in dedup window
        matching_alerts = [
            a for a in recent_alerts
            if a.alert_type == alert_type
            and a.brew_id == brew_id
        ]
        return len(matching_alerts) == 0
