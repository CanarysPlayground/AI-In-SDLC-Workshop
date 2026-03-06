"""
Tests for brew scheduling service.

Tests brew schedule creation, status management, and lifecycle.
"""

from datetime import datetime, timedelta

import pytest

from smartcafe_brewmaster.services import BrewScheduleService


class TestBrewScheduleService:
    """Tests for brew scheduling service."""

    def test_create_brew_schedule(self, temp_database):
        """Test creating a brew schedule."""
        service = BrewScheduleService(temp_database)
        
        start = datetime.utcnow()
        brew_id = service.create_brew(
            recipe_name="Espresso",
            start_time=start,
            target_temp_c=92.0,
            duration_min=3,
        )
        
        assert brew_id is not None
        
        brew = service.get_brew(brew_id)
        assert brew.recipe_name == "Espresso"
        assert brew.target_temp_c == 92.0
        assert brew.status == "scheduled"

    def test_get_nonexistent_brew(self, temp_database):
        """Test retrieving non-existent brew."""
        service = BrewScheduleService(temp_database)
        
        with pytest.raises(ValueError):
            service.get_brew(999)

    def test_brew_status_transitions(self, temp_database):
        """Test brew status transitions."""
        service = BrewScheduleService(temp_database)
        
        start = datetime.utcnow()
        brew_id = service.create_brew("Espresso", start, 92.0, 3)
        
        service.start_brew(brew_id)
        brew = service.get_brew(brew_id)
        assert brew.status == "brewing"
        
        service.complete_brew(brew_id)
        brew = service.get_brew(brew_id)
        assert brew.status == "done"

    def test_list_brews_by_status(self, temp_database):
        """Test listing brews filtered by status."""
        service = BrewScheduleService(temp_database)
        
        start = datetime.utcnow()
        brew1_id = service.create_brew("Espresso", start, 92.0, 3)
        brew2_id = service.create_brew("Americano", start, 90.0, 5)
        
        service.start_brew(brew1_id)
        
        brewing = service.list_brews(status="brewing")
        assert len(brewing) == 1
        assert brewing[0].recipe_name == "Espresso"
        
        scheduled = service.list_brews(status="scheduled")
        assert len(scheduled) == 1
        assert scheduled[0].recipe_name == "Americano"

    def test_list_active_brews(self, temp_database):
        """Test listing active brews."""
        service = BrewScheduleService(temp_database)
        
        start = datetime.utcnow()
        brew1_id = service.create_brew("Espresso", start, 92.0, 3)
        brew2_id = service.create_brew("Americano", start, 90.0, 5)
        
        service.start_brew(brew1_id)
        
        active = service.list_active_brews()
        assert len(active) == 1
        assert active[0].recipe_name == "Espresso"

    def test_cancel_brew(self, temp_database):
        """Test canceling a brew."""
        service = BrewScheduleService(temp_database)
        
        start = datetime.utcnow()
        brew_id = service.create_brew("Espresso", start, 92.0, 3)
        
        service.start_brew(brew_id)
        service.cancel_brew(brew_id)
        
        brew = service.get_brew(brew_id)
        assert brew.status == "canceled"

    def test_get_brew_status(self, temp_database):
        """Test getting detailed brew status."""
        service = BrewScheduleService(temp_database)
        
        start = datetime.utcnow()
        brew_id = service.create_brew("Espresso", start, 92.0, 3)
        
        status = service.get_brew_status(brew_id)
        assert status["brew_id"] == brew_id
        assert status["recipe_name"] == "Espresso"
        assert status["status"] == "scheduled"
        assert status["event_count"] == 0
        assert status["alert_count"] == 0
