"""
Domain models for SmartCafé BrewMaster application.

These models represent core business entities and are designed to be
database-agnostic to support future enhancement and testing.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class InventoryItem:
    """Represents an inventory item in the system."""

    item_sku: str
    item_name: str
    quantity: int
    unit: str
    reorder_level: int = 0
    updated_at: Optional[datetime] = None
    id: Optional[int] = None

    def is_low_stock(self) -> bool:
        """Check if inventory is below reorder level.
        
        Returns:
            bool: True if quantity is at or below reorder level.
        """
        return self.quantity <= self.reorder_level

    def adjust_quantity(self, delta: int) -> None:
        """Adjust inventory quantity.
        
        Args:
            delta: Amount to add (positive) or remove (negative).
        
        Raises:
            ValueError: If adjustment would result in negative quantity.
        """
        new_quantity = self.quantity + delta
        if new_quantity < 0:
            raise ValueError(
                f"Cannot adjust quantity: would result in {new_quantity}"
            )
        self.quantity = new_quantity
        self.updated_at = datetime.utcnow()


@dataclass
class BrewSchedule:
    """Represents a scheduled brew operation."""

    recipe_name: str
    start_time: datetime
    target_temp_c: float
    duration_min: int
    status: str = "scheduled"
    created_at: Optional[datetime] = None
    id: Optional[int] = None

    def is_active(self) -> bool:
        """Check if brew is currently active.
        
        Returns:
            bool: True if status is 'brewing'.
        """
        return self.status == "brewing"

    def mark_as_brewing(self) -> None:
        """Transition brew to brewing status."""
        self.status = "brewing"

    def mark_as_done(self) -> None:
        """Transition brew to done status."""
        self.status = "done"

    def mark_as_canceled(self) -> None:
        """Transition brew to canceled status."""
        self.status = "canceled"

    def expected_end_time(self) -> datetime:
        """Calculate expected brew end time.
        
        Returns:
            datetime: Expected end time in UTC.
        """
        from datetime import timedelta
        return self.start_time + timedelta(minutes=self.duration_min)


@dataclass
class TemperatureEvent:
    """Represents a temperature reading from an IoT sensor."""

    sensor_id: str
    observed_at: datetime
    temp_c: float
    raw_file: str
    brew_id: Optional[int] = None
    id: Optional[int] = None


@dataclass
class Alert:
    """Represents an alert condition detected in the system."""

    alert_type: str  # burn|overbrew|system
    message: str
    severity: str  # info|warn|error
    created_at: Optional[datetime] = None
    brew_id: Optional[int] = None
    id: Optional[int] = None

    def is_critical(self) -> bool:
        """Check if alert is critical.
        
        Returns:
            bool: True if severity is 'error'.
        """
        return self.severity == "error"
