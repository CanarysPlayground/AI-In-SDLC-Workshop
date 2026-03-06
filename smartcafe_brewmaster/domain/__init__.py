"""Package initialization for domain module."""

from .models import Alert, BrewSchedule, InventoryItem, TemperatureEvent
from .logic import BurnDetector, OverBrewDetector, AlertDeduplicator

__all__ = [
    "Alert",
    "BrewSchedule",
    "InventoryItem",
    "TemperatureEvent",
    "BurnDetector",
    "OverBrewDetector",
    "AlertDeduplicator",
]
