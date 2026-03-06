"""
Brew Scheduling Service for managing brew operations.

Handles brew schedule creation, status management, and brew lifecycle.
"""

import logging
from datetime import datetime, timedelta
from typing import List

from ..adapters import DatabaseAdapter
from ..domain import BrewSchedule

logger = logging.getLogger(__name__)


class BrewScheduleService:
    """Service for managing brew scheduling."""

    def __init__(self, db: DatabaseAdapter):
        """Initialize brew schedule service.
        
        Args:
            db: Database adapter.
        """
        self.db = db

    def create_brew(
        self,
        recipe_name: str,
        start_time: datetime,
        target_temp_c: float,
        duration_min: int,
    ) -> int:
        """Create a new brew schedule.
        
        Args:
            recipe_name: Name of the recipe being brewed.
            start_time: When the brew should start (UTC).
            target_temp_c: Target temperature in Celsius.
            duration_min: Expected duration in minutes.
        
        Returns:
            int: ID of created brew schedule.
        """
        brew = BrewSchedule(
            recipe_name=recipe_name,
            start_time=start_time,
            target_temp_c=target_temp_c,
            duration_min=duration_min,
            status="scheduled",
        )
        brew_id = self.db.create_brew_schedule(brew)
        logger.info(f"Created brew schedule {brew_id}: {recipe_name}")
        return brew_id

    def get_brew(self, brew_id: int) -> BrewSchedule:
        """Get a brew schedule by ID.
        
        Args:
            brew_id: ID of brew schedule.
        
        Returns:
            BrewSchedule.
        
        Raises:
            ValueError: If brew not found.
        """
        brew = self.db.get_brew_schedule(brew_id)
        if not brew:
            raise ValueError(f"Brew schedule {brew_id} not found")
        return brew

    def list_brews(self, status: str = None) -> List[BrewSchedule]:
        """List brew schedules.
        
        Args:
            status: Optional status filter (scheduled|brewing|done|canceled).
        
        Returns:
            List of BrewSchedule objects.
        """
        return self.db.list_brew_schedules(status=status)

    def list_active_brews(self) -> List[BrewSchedule]:
        """Get active (brewing) brew schedules.
        
        Returns:
            List of active BrewSchedule objects.
        """
        return self.db.list_brew_schedules(status="brewing")

    def start_brew(self, brew_id: int) -> None:
        """Start a brew (transition to brewing status).
        
        Args:
            brew_id: ID of brew to start.
        """
        brew = self.get_brew(brew_id)
        brew.mark_as_brewing()
        self.db.update_brew_schedule(brew)
        logger.info(f"Started brew {brew_id}: {brew.recipe_name}")

    def complete_brew(self, brew_id: int) -> None:
        """Complete a brew (transition to done status).
        
        Args:
            brew_id: ID of brew to complete.
        """
        brew = self.get_brew(brew_id)
        brew.mark_as_done()
        self.db.update_brew_schedule(brew)
        logger.info(f"Completed brew {brew_id}: {brew.recipe_name}")

    def cancel_brew(self, brew_id: int) -> None:
        """Cancel a brew (transition to canceled status).
        
        Args:
            brew_id: ID of brew to cancel.
        """
        brew = self.get_brew(brew_id)
        brew.mark_as_canceled()
        self.db.update_brew_schedule(brew)
        logger.warning(f"Cancelled brew {brew_id}: {brew.recipe_name}")

    def get_brew_status(self, brew_id: int) -> dict:
        """Get detailed status of a brew.
        
        Args:
            brew_id: ID of brew.
        
        Returns:
            Dictionary with brew status details.
        """
        brew = self.get_brew(brew_id)
        events = self.db.get_events_by_brew(brew_id)
        alerts = self.db.get_alerts_by_brew(brew_id)
        
        current_time = datetime.utcnow()
        elapsed = current_time - brew.start_time
        expected_end = brew.expected_end_time()
        
        latest_temp = None
        if events:
            latest_temp = events[-1].temp_c
        
        return {
            "brew_id": brew_id,
            "recipe_name": brew.recipe_name,
            "status": brew.status,
            "start_time": brew.start_time.isoformat(),
            "expected_end": expected_end.isoformat(),
            "target_temp_c": brew.target_temp_c,
            "duration_min": brew.duration_min,
            "elapsed_min": elapsed.total_seconds() / 60,
            "latest_temp": latest_temp,
            "event_count": len(events),
            "alert_count": len(alerts),
        }
