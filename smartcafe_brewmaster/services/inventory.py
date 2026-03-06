"""
Inventory Service for managing inventory items and stocks.

Provides CRUD operations and inventory analytics.
"""

import logging
from typing import List

from ..adapters import DatabaseAdapter
from ..domain import InventoryItem

logger = logging.getLogger(__name__)


class InventoryService:
    """Service for managing inventory operations."""

    def __init__(self, db: DatabaseAdapter):
        """Initialize inventory service.
        
        Args:
            db: Database adapter.
        """
        self.db = db

    def create_item(
        self,
        sku: str,
        name: str,
        quantity: int,
        unit: str,
        reorder_level: int = 0,
    ) -> int:
        """Create a new inventory item.
        
        Args:
            sku: Stock keeping unit (unique identifier).
            name: Item name.
            quantity: Initial quantity.
            unit: Unit of measurement (grams, ml, units, etc).
            reorder_level: Quantity threshold for reordering.
        
        Returns:
            int: ID of created item.
        """
        item = InventoryItem(
            item_sku=sku,
            item_name=name,
            quantity=quantity,
            unit=unit,
            reorder_level=reorder_level,
        )
        return self.db.create_inventory_item(item)

    def get_item(self, item_id: int) -> InventoryItem:
        """Get an inventory item by ID.
        
        Args:
            item_id: Item ID.
        
        Returns:
            InventoryItem.
        
        Raises:
            ValueError: If item not found.
        """
        item = self.db.get_inventory_item(item_id)
        if not item:
            raise ValueError(f"Item {item_id} not found")
        return item

    def get_by_sku(self, sku: str) -> InventoryItem:
        """Get an inventory item by SKU.
        
        Args:
            sku: Item SKU.
        
        Returns:
            InventoryItem.
        
        Raises:
            ValueError: If item not found.
        """
        item = self.db.get_inventory_by_sku(sku)
        if not item:
            raise ValueError(f"Item with SKU {sku} not found")
        return item

    def list_all(self) -> List[InventoryItem]:
        """List all inventory items.
        
        Returns:
            List of InventoryItem objects.
        """
        return self.db.list_inventory()

    def adjust_stock(self, item_id: int, delta: int) -> None:
        """Adjust inventory quantity.
        
        Args:
            item_id: ID of item to adjust.
            delta: Amount to add (positive) or remove (negative).
        
        Raises:
            ValueError: If adjustment is invalid.
        """
        item = self.get_item(item_id)
        item.adjust_quantity(delta)
        self.db.update_inventory_item(item)
        logger.info(f"Adjusted item {item.item_sku} by {delta} {item.unit}")

    def get_low_stock_items(self) -> List[InventoryItem]:
        """Get items at or below reorder level.
        
        Returns:
            List of low-stock InventoryItem objects.
        """
        return self.db.get_low_stock_items()

    def get_stock_summary(self) -> dict:
        """Get inventory summary statistics.
        
        Returns:
            Dictionary with summary stats.
        """
        items = self.list_all()
        low_stock = self.get_low_stock_items()
        
        return {
            "total_items": len(items),
            "low_stock_count": len(low_stock),
            "low_stock_items": [
                {"sku": item.item_sku, "name": item.item_name, "quantity": item.quantity}
                for item in low_stock
            ],
        }
