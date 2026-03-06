"""
Unit tests for domain logic and models.

Tests core business logic with pure functions and domain models.
"""

import pytest
from datetime import datetime, timedelta

from smartcafe_brewmaster.domain import (
    InventoryItem,
    BrewSchedule,
    TemperatureEvent,
    Alert,
    BurnDetector,
    OverBrewDetector,
    AlertDeduplicator,
)


class TestInventoryItem:
    """Tests for InventoryItem model."""

    def test_create_inventory_item(self):
        """Test creating an inventory item."""
        item = InventoryItem(
            item_sku="BEAN-001",
            item_name="Ethiopian Beans",
            quantity=500,
            unit="grams",
            reorder_level=100,
        )
        assert item.item_sku == "BEAN-001"
        assert item.quantity == 500
        assert not item.is_low_stock()

    def test_low_stock_detection(self):
        """Test low stock detection."""
        item = InventoryItem(
            item_sku="BEAN-001",
            item_name="Ethiopian Beans",
            quantity=50,
            unit="grams",
            reorder_level=100,
        )
        assert item.is_low_stock()

    def test_adjust_quantity(self):
        """Test adjusting quantity."""
        item = InventoryItem(
            item_sku="BEAN-001",
            item_name="Ethiopian Beans",
            quantity=500,
            unit="grams",
        )
        item.adjust_quantity(-100)
        assert item.quantity == 400

    def test_adjust_quantity_negative_raises(self):
        """Test that negative adjustment raises error."""
        item = InventoryItem(
            item_sku="BEAN-001",
            item_name="Ethiopian Beans",
            quantity=50,
            unit="grams",
        )
        with pytest.raises(ValueError):
            item.adjust_quantity(-100)


class TestBrewSchedule:
    """Tests for BrewSchedule model."""

    def test_create_brew_schedule(self):
        """Test creating a brew schedule."""
        start = datetime.utcnow()
        brew = BrewSchedule(
            recipe_name="Espresso",
            start_time=start,
            target_temp_c=92.0,
            duration_min=3,
        )
        assert brew.recipe_name == "Espresso"
        assert brew.status == "scheduled"
        assert not brew.is_active()

    def test_brew_status_transitions(self):
        """Test brew status transitions."""
        start = datetime.utcnow()
        brew = BrewSchedule(
            recipe_name="Espresso",
            start_time=start,
            target_temp_c=92.0,
            duration_min=3,
        )
        
        brew.mark_as_brewing()
        assert brew.status == "brewing"
        assert brew.is_active()
        
        brew.mark_as_done()
        assert brew.status == "done"
        assert not brew.is_active()

    def test_expected_end_time(self):
        """Test expected end time calculation."""
        start = datetime(2026, 3, 6, 10, 0, 0)
        brew = BrewSchedule(
            recipe_name="Espresso",
            start_time=start,
            target_temp_c=92.0,
            duration_min=3,
        )
        
        end = brew.expected_end_time()
        assert end == datetime(2026, 3, 6, 10, 3, 0)


class TestBurnDetector:
    """Tests for BurnDetector logic."""

    def test_no_burn_when_temp_normal(self):
        """Test that normal temps don't trigger burn alert."""
        detector = BurnDetector(temp_threshold_c=98.0, duration_sec=30.0)
        
        start = datetime.utcnow()
        brew = BrewSchedule(
            recipe_name="Espresso",
            start_time=start,
            target_temp_c=92.0,
            duration_min=3,
            status="brewing",
            id=1,
        )
        
        events = [
            TemperatureEvent(
                sensor_id="sensor1",
                observed_at=start + timedelta(seconds=10),
                temp_c=92.0,
                raw_file="test.csv",
                brew_id=1,
            ),
        ]
        
        is_burned, max_temp = detector.detect_burn(brew, events)
        assert not is_burned
        assert max_temp == 92.0

    def test_burn_detected_when_high_temp_sustained(self):
        """Test that sustained high temp triggers burn alert."""
        detector = BurnDetector(temp_threshold_c=98.0, duration_sec=10.0)
        
        start = datetime.utcnow()
        brew = BrewSchedule(
            recipe_name="Espresso",
            start_time=start,
            target_temp_c=92.0,
            duration_min=10,
            status="brewing",
            id=1,
        )
        
        # Create events with temp above threshold for duration
        events = [
            TemperatureEvent(
                sensor_id="sensor1",
                observed_at=start + timedelta(seconds=i * 5),
                temp_c=100.0,  # Above threshold
                raw_file="test.csv",
                brew_id=1,
            )
            for i in range(4)  # Total 15 seconds > 10 second threshold
        ]
        
        is_burned, max_temp = detector.detect_burn(brew, events)
        assert is_burned
        assert max_temp == 100.0

    def test_burn_not_detected_when_brew_inactive(self):
        """Test that burn doesn't trigger for inactive brew."""
        detector = BurnDetector(temp_threshold_c=98.0, duration_sec=10.0)
        
        start = datetime.utcnow()
        brew = BrewSchedule(
            recipe_name="Espresso",
            start_time=start,
            target_temp_c=92.0,
            duration_min=3,
            status="done",  # Not brewing
            id=1,
        )
        
        events = [
            TemperatureEvent(
                sensor_id="sensor1",
                observed_at=start,
                temp_c=100.0,
                raw_file="test.csv",
                brew_id=1,
            ),
        ]
        
        is_burned, max_temp = detector.detect_burn(brew, events)
        assert not is_burned


class TestOverBrewDetector:
    """Tests for OverBrewDetector logic."""

    def test_no_overbrew_when_on_time(self):
        """Test no overbrew when brew finishes on time."""
        detector = OverBrewDetector(
            grace_percent=10.0,
            serving_temp_min=50.0,
            serving_temp_max=75.0,
        )
        
        start = datetime.utcnow()
        brew = BrewSchedule(
            recipe_name="Espresso",
            start_time=start,
            target_temp_c=92.0,
            duration_min=3,
            status="brewing",
            id=1,
        )
        
        events = []
        current = start + timedelta(minutes=3)  # On time
        
        is_overbrew, reason = detector.detect_overbrew(brew, current, events)
        assert not is_overbrew

    def test_overbrew_when_duration_exceeded(self):
        """Test overbrew when duration exceeded."""
        detector = OverBrewDetector(
            grace_percent=10.0,
            serving_temp_min=50.0,
            serving_temp_max=75.0,
        )
        
        start = datetime.utcnow()
        brew = BrewSchedule(
            recipe_name="Espresso",
            start_time=start,
            target_temp_c=92.0,
            duration_min=3,  # 3 minutes, 10% grace = 3.3 minutes total
            status="brewing",
            id=1,
        )
        
        events = []
        current = start + timedelta(minutes=4)  # Over grace period
        
        is_overbrew, reason = detector.detect_overbrew(brew, current, events)
        assert is_overbrew
        assert "exceeded" in reason.lower()

    def test_overbrew_when_temp_too_high_after_completion(self):
        """Test overbrew when temp stays high after completion."""
        detector = OverBrewDetector(
            grace_percent=10.0,
            serving_temp_min=50.0,
            serving_temp_max=75.0,
        )
        
        start = datetime.utcnow()
        brew = BrewSchedule(
            recipe_name="Espresso",
            start_time=start,
            target_temp_c=92.0,
            duration_min=3,
            status="done",  # Completed
            id=1,
        )
        
        # Event with temp above serving max
        events = [
            TemperatureEvent(
                sensor_id="sensor1",
                observed_at=start + timedelta(minutes=3),
                temp_c=80.0,  # Above serving max of 75
                raw_file="test.csv",
                brew_id=1,
            ),
        ]
        
        is_overbrew, reason = detector.detect_overbrew(brew, datetime.utcnow(), events)
        assert is_overbrew
        assert "serving range" in reason.lower()


class TestAlertDeduplicator:
    """Tests for AlertDeduplicator logic."""

    def test_allows_first_alert(self):
        """Test that first alert is allowed."""
        dedup = AlertDeduplicator(dedup_window_sec=300.0)
        
        recent_alerts = []
        should_alert = dedup.should_alert("burn", brew_id=1, recent_alerts=recent_alerts)
        assert should_alert

    def test_blocks_duplicate_alert(self):
        """Test that duplicate alerts are blocked."""
        dedup = AlertDeduplicator(dedup_window_sec=300.0)
        
        recent_alerts = [
            Alert(
                alert_type="burn",
                brew_id=1,
                message="Burn detected",
                severity="error",
                created_at=datetime.utcnow(),
            ),
        ]
        
        should_alert = dedup.should_alert("burn", brew_id=1, recent_alerts=recent_alerts)
        assert not should_alert

    def test_allows_different_alert_type(self):
        """Test that different alert types are not deduplicated."""
        dedup = AlertDeduplicator(dedup_window_sec=300.0)
        
        recent_alerts = [
            Alert(
                alert_type="burn",
                brew_id=1,
                message="Burn detected",
                severity="error",
                created_at=datetime.utcnow(),
            ),
        ]
        
        should_alert = dedup.should_alert("overbrew", brew_id=1, recent_alerts=recent_alerts)
        assert should_alert

    def test_allows_different_brew(self):
        """Test that different brews are not deduplicated."""
        dedup = AlertDeduplicator(dedup_window_sec=300.0)
        
        recent_alerts = [
            Alert(
                alert_type="burn",
                brew_id=1,
                message="Burn detected",
                severity="error",
                created_at=datetime.utcnow(),
            ),
        ]
        
        should_alert = dedup.should_alert("burn", brew_id=2, recent_alerts=recent_alerts)
        assert should_alert
