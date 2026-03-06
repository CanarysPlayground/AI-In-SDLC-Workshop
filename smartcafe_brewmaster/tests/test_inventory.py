"""
Tests for inventory service.

Tests inventory CRUD operations and stock management.
"""

import pytest

from smartcafe_brewmaster.services import InventoryService


class TestInventoryService:
    """Tests for inventory service."""

    def test_create_and_retrieve_item(self, temp_database):
        """Test creating and retrieving an inventory item."""
        service = InventoryService(temp_database)
        
        item_id = service.create_item(
            sku="BEAN-001",
            name="Ethiopian Beans",
            quantity=500,
            unit="grams",
            reorder_level=100,
        )
        
        assert item_id is not None
        
        item = service.get_item(item_id)
        assert item.item_sku == "BEAN-001"
        assert item.item_name == "Ethiopian Beans"
        assert item.quantity == 500

    def test_get_by_sku(self, temp_database):
        """Test retrieving item by SKU."""
        service = InventoryService(temp_database)
        
        service.create_item(
            sku="BEAN-001",
            name="Ethiopian Beans",
            quantity=500,
            unit="grams",
        )
        
        item = service.get_by_sku("BEAN-001")
        assert item.item_sku == "BEAN-001"

    def test_get_by_sku_not_found(self, temp_database):
        """Test retrieving non-existent SKU."""
        service = InventoryService(temp_database)
        
        with pytest.raises(ValueError):
            service.get_by_sku("NONEXISTENT")

    def test_adjust_stock(self, temp_database):
        """Test adjusting inventory stock."""
        service = InventoryService(temp_database)
        
        item_id = service.create_item(
            sku="BEAN-001",
            name="Ethiopian Beans",
            quantity=500,
            unit="grams",
        )
        
        service.adjust_stock(item_id, -100)
        
        item = service.get_item(item_id)
        assert item.quantity == 400

    def test_list_all_items(self, temp_database):
        """Test listing all inventory items."""
        service = InventoryService(temp_database)
        
        service.create_item("BEAN-001", "Ethiopian Beans", 500, "grams")
        service.create_item("BEAN-002", "Colombian Beans", 300, "grams")
        
        items = service.list_all()
        assert len(items) == 2
        assert items[0].item_sku == "BEAN-001"
        assert items[1].item_sku == "BEAN-002"

    def test_get_low_stock_items(self, temp_database):
        """Test getting low stock items."""
        service = InventoryService(temp_database)
        
        service.create_item("BEAN-001", "Ethiopian Beans", 500, "grams", reorder_level=100)
        service.create_item("BEAN-002", "Colombian Beans", 50, "grams", reorder_level=100)
        
        low_stock = service.get_low_stock_items()
        assert len(low_stock) == 1
        assert low_stock[0].item_sku == "BEAN-002"

    def test_stock_summary(self, temp_database):
        """Test inventory stock summary."""
        service = InventoryService(temp_database)
        
        service.create_item("BEAN-001", "Ethiopian Beans", 500, "grams", reorder_level=100)
        service.create_item("BEAN-002", "Colombian Beans", 50, "grams", reorder_level=100)
        
        summary = service.get_stock_summary()
        assert summary["total_items"] == 2
        assert summary["low_stock_count"] == 1
        assert len(summary["low_stock_items"]) == 1
