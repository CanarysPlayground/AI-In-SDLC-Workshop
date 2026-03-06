"""
Database adapter for SQLite using sqlite3 module.

Handles all database operations with proper connection management
and transaction handling.
"""

import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from ..domain import InventoryItem, BrewSchedule, TemperatureEvent, Alert

logger = logging.getLogger(__name__)


class DatabaseAdapter:
    """SQLite database adapter for BrewMaster application."""

    def __init__(self, db_path: Path):
        """Initialize database adapter.
        
        Args:
            db_path: Path to SQLite database file.
        """
        self.db_path = db_path
        self._init_connection()

    def _init_connection(self) -> None:
        """Initialize database connection and enable foreign keys."""
        # Test connection
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("PRAGMA foreign_keys = ON")
        conn.close()
        logger.info(f"Database initialized at {self.db_path}")

    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection.
        
        Returns:
            sqlite3.Connection: Connected database.
        """
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def init_schema(self, schema_path: Path) -> None:
        """Initialize database schema from SQL file.
        
        Args:
            schema_path: Path to SQL schema file.
        """
        with open(schema_path, "r") as f:
            schema = f.read()

        conn = self._get_connection()
        try:
            conn.executescript(schema)
            conn.commit()
            logger.info("Database schema initialized successfully")
        except sqlite3.Error as e:
            logger.error(f"Failed to initialize schema: {e}")
            raise
        finally:
            conn.close()

    # Inventory operations
    def create_inventory_item(self, item: InventoryItem) -> int:
        """Create a new inventory item.
        
        Args:
            item: InventoryItem to create.
        
        Returns:
            int: ID of created item.
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO inventory
                (item_sku, item_name, quantity, unit, reorder_level, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    item.item_sku,
                    item.item_name,
                    item.quantity,
                    item.unit,
                    item.reorder_level,
                    (item.updated_at or datetime.utcnow()).isoformat(),
                ),
            )
            conn.commit()
            item_id = cursor.lastrowid
            logger.debug(f"Created inventory item {item_id}: {item.item_sku}")
            return item_id
        except sqlite3.Error as e:
            logger.error(f"Failed to create inventory item: {e}")
            raise
        finally:
            conn.close()

    def get_inventory_item(self, item_id: int) -> Optional[InventoryItem]:
        """Retrieve an inventory item by ID.
        
        Args:
            item_id: ID of item to retrieve.
        
        Returns:
            InventoryItem or None if not found.
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM inventory WHERE id = ?", (item_id,))
            row = cursor.fetchone()
            if row:
                return InventoryItem(
                    id=row["id"],
                    item_sku=row["item_sku"],
                    item_name=row["item_name"],
                    quantity=row["quantity"],
                    unit=row["unit"],
                    reorder_level=row["reorder_level"],
                    updated_at=datetime.fromisoformat(row["updated_at"]),
                )
            return None
        finally:
            conn.close()

    def get_inventory_by_sku(self, sku: str) -> Optional[InventoryItem]:
        """Retrieve an inventory item by SKU.
        
        Args:
            sku: Item SKU.
        
        Returns:
            InventoryItem or None if not found.
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM inventory WHERE item_sku = ?", (sku,))
            row = cursor.fetchone()
            if row:
                return InventoryItem(
                    id=row["id"],
                    item_sku=row["item_sku"],
                    item_name=row["item_name"],
                    quantity=row["quantity"],
                    unit=row["unit"],
                    reorder_level=row["reorder_level"],
                    updated_at=datetime.fromisoformat(row["updated_at"]),
                )
            return None
        finally:
            conn.close()

    def list_inventory(self) -> List[InventoryItem]:
        """List all inventory items.
        
        Returns:
            List of InventoryItem objects.
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM inventory ORDER BY item_sku")
            items = []
            for row in cursor.fetchall():
                items.append(
                    InventoryItem(
                        id=row["id"],
                        item_sku=row["item_sku"],
                        item_name=row["item_name"],
                        quantity=row["quantity"],
                        unit=row["unit"],
                        reorder_level=row["reorder_level"],
                        updated_at=datetime.fromisoformat(row["updated_at"]),
                    )
                )
            return items
        finally:
            conn.close()

    def update_inventory_item(self, item: InventoryItem) -> None:
        """Update an inventory item.
        
        Args:
            item: InventoryItem to update (must have id set).
        """
        if not item.id:
            raise ValueError("Item must have id set for update")

        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE inventory
                SET quantity = ?, reorder_level = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    item.quantity,
                    item.reorder_level,
                    (item.updated_at or datetime.utcnow()).isoformat(),
                    item.id,
                ),
            )
            conn.commit()
            logger.debug(f"Updated inventory item {item.id}")
        except sqlite3.Error as e:
            logger.error(f"Failed to update inventory item: {e}")
            raise
        finally:
            conn.close()

    def get_low_stock_items(self) -> List[InventoryItem]:
        """Get items at or below reorder level.
        
        Returns:
            List of low-stock InventoryItem objects.
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM inventory WHERE quantity <= reorder_level")
            items = []
            for row in cursor.fetchall():
                items.append(
                    InventoryItem(
                        id=row["id"],
                        item_sku=row["item_sku"],
                        item_name=row["item_name"],
                        quantity=row["quantity"],
                        unit=row["unit"],
                        reorder_level=row["reorder_level"],
                        updated_at=datetime.fromisoformat(row["updated_at"]),
                    )
                )
            return items
        finally:
            conn.close()

    # Brew schedule operations
    def create_brew_schedule(self, brew: BrewSchedule) -> int:
        """Create a new brew schedule.
        
        Args:
            brew: BrewSchedule to create.
        
        Returns:
            int: ID of created schedule.
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO brew_schedule
                (recipe_name, start_time, target_temp_c, duration_min, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    brew.recipe_name,
                    brew.start_time.isoformat(),
                    brew.target_temp_c,
                    brew.duration_min,
                    brew.status,
                    (brew.created_at or datetime.utcnow()).isoformat(),
                ),
            )
            conn.commit()
            brew_id = cursor.lastrowid
            logger.debug(f"Created brew schedule {brew_id}: {brew.recipe_name}")
            return brew_id
        except sqlite3.Error as e:
            logger.error(f"Failed to create brew schedule: {e}")
            raise
        finally:
            conn.close()

    def get_brew_schedule(self, brew_id: int) -> Optional[BrewSchedule]:
        """Retrieve a brew schedule by ID.
        
        Args:
            brew_id: ID of schedule to retrieve.
        
        Returns:
            BrewSchedule or None if not found.
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM brew_schedule WHERE id = ?", (brew_id,))
            row = cursor.fetchone()
            if row:
                return BrewSchedule(
                    id=row["id"],
                    recipe_name=row["recipe_name"],
                    start_time=datetime.fromisoformat(row["start_time"]),
                    target_temp_c=row["target_temp_c"],
                    duration_min=row["duration_min"],
                    status=row["status"],
                    created_at=datetime.fromisoformat(row["created_at"]),
                )
            return None
        finally:
            conn.close()

    def list_brew_schedules(self, status: Optional[str] = None) -> List[BrewSchedule]:
        """List brew schedules, optionally filtered by status.
        
        Args:
            status: Optional status filter.
        
        Returns:
            List of BrewSchedule objects.
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            if status:
                cursor.execute(
                    "SELECT * FROM brew_schedule WHERE status = ? ORDER BY start_time DESC",
                    (status,),
                )
            else:
                cursor.execute("SELECT * FROM brew_schedule ORDER BY start_time DESC")

            schedules = []
            for row in cursor.fetchall():
                schedules.append(
                    BrewSchedule(
                        id=row["id"],
                        recipe_name=row["recipe_name"],
                        start_time=datetime.fromisoformat(row["start_time"]),
                        target_temp_c=row["target_temp_c"],
                        duration_min=row["duration_min"],
                        status=row["status"],
                        created_at=datetime.fromisoformat(row["created_at"]),
                    )
                )
            return schedules
        finally:
            conn.close()

    def update_brew_schedule(self, brew: BrewSchedule) -> None:
        """Update a brew schedule.
        
        Args:
            brew: BrewSchedule to update (must have id set).
        """
        if not brew.id:
            raise ValueError("Brew must have id set for update")

        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE brew_schedule SET status = ? WHERE id = ?",
                (brew.status, brew.id),
            )
            conn.commit()
            logger.debug(f"Updated brew schedule {brew.id} to status {brew.status}")
        except sqlite3.Error as e:
            logger.error(f"Failed to update brew schedule: {e}")
            raise
        finally:
            conn.close()

    # Temperature events operations
    def create_temperature_event(self, event: TemperatureEvent) -> int:
        """Create a new temperature event.
        
        Args:
            event: TemperatureEvent to create.
        
        Returns:
            int: ID of created event.
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO temperature_events
                (sensor_id, brew_id, observed_at, temp_c, raw_file)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    event.sensor_id,
                    event.brew_id,
                    event.observed_at.isoformat(),
                    event.temp_c,
                    event.raw_file,
                ),
            )
            conn.commit()
            event_id = cursor.lastrowid
            logger.debug(f"Created temperature event {event_id}")
            return event_id
        except sqlite3.Error as e:
            logger.error(f"Failed to create temperature event: {e}")
            raise
        finally:
            conn.close()

    def get_events_by_brew(self, brew_id: int) -> List[TemperatureEvent]:
        """Get temperature events for a brew.
        
        Args:
            brew_id: ID of brew.
        
        Returns:
            List of TemperatureEvent objects.
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM temperature_events WHERE brew_id = ? ORDER BY observed_at",
                (brew_id,),
            )
            events = []
            for row in cursor.fetchall():
                events.append(
                    TemperatureEvent(
                        id=row["id"],
                        sensor_id=row["sensor_id"],
                        brew_id=row["brew_id"],
                        observed_at=datetime.fromisoformat(row["observed_at"]),
                        temp_c=row["temp_c"],
                        raw_file=row["raw_file"],
                    )
                )
            return events
        finally:
            conn.close()

    def get_recent_events(self, minutes: int = 60) -> List[TemperatureEvent]:
        """Get temperature events from the last N minutes.
        
        Args:
            minutes: Number of minutes to look back.
        
        Returns:
            List of TemperatureEvent objects.
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            # Calculate cutoff time
            from datetime import timedelta
            cutoff = (
                datetime.utcnow() - timedelta(minutes=minutes)
            ).isoformat()
            cursor.execute(
                "SELECT * FROM temperature_events WHERE observed_at > ? ORDER BY observed_at DESC",
                (cutoff,),
            )
            events = []
            for row in cursor.fetchall():
                events.append(
                    TemperatureEvent(
                        id=row["id"],
                        sensor_id=row["sensor_id"],
                        brew_id=row["brew_id"],
                        observed_at=datetime.fromisoformat(row["observed_at"]),
                        temp_c=row["temp_c"],
                        raw_file=row["raw_file"],
                    )
                )
            return events
        finally:
            conn.close()

    # Alert operations
    def create_alert(self, alert: Alert) -> int:
        """Create a new alert.
        
        Args:
            alert: Alert to create.
        
        Returns:
            int: ID of created alert.
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO alerts
                (alert_type, brew_id, message, severity, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    alert.alert_type,
                    alert.brew_id,
                    alert.message,
                    alert.severity,
                    (alert.created_at or datetime.utcnow()).isoformat(),
                ),
            )
            conn.commit()
            alert_id = cursor.lastrowid
            logger.info(f"Created alert {alert_id}: {alert.alert_type} - {alert.message}")
            return alert_id
        except sqlite3.Error as e:
            logger.error(f"Failed to create alert: {e}")
            raise
        finally:
            conn.close()

    def get_recent_alerts(self, minutes: int = 60) -> List[Alert]:
        """Get alerts from the last N minutes.
        
        Args:
            minutes: Number of minutes to look back.
        
        Returns:
            List of Alert objects.
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            from datetime import timedelta
            cutoff = (
                datetime.utcnow() - timedelta(minutes=minutes)
            ).isoformat()
            cursor.execute(
                "SELECT * FROM alerts WHERE created_at > ? ORDER BY created_at DESC",
                (cutoff,),
            )
            alerts = []
            for row in cursor.fetchall():
                alerts.append(
                    Alert(
                        id=row["id"],
                        alert_type=row["alert_type"],
                        brew_id=row["brew_id"],
                        message=row["message"],
                        severity=row["severity"],
                        created_at=datetime.fromisoformat(row["created_at"]),
                    )
                )
            return alerts
        finally:
            conn.close()

    def get_alerts_by_brew(self, brew_id: int) -> List[Alert]:
        """Get all alerts for a brew.
        
        Args:
            brew_id: ID of brew.
        
        Returns:
            List of Alert objects.
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM alerts WHERE brew_id = ? ORDER BY created_at DESC",
                (brew_id,),
            )
            alerts = []
            for row in cursor.fetchall():
                alerts.append(
                    Alert(
                        id=row["id"],
                        alert_type=row["alert_type"],
                        brew_id=row["brew_id"],
                        message=row["message"],
                        severity=row["severity"],
                        created_at=datetime.fromisoformat(row["created_at"]),
                    )
                )
            return alerts
        finally:
            conn.close()

    def list_all_alerts(self) -> List[Alert]:
        """Get all alerts.
        
        Returns:
            List of Alert objects.
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM alerts ORDER BY created_at DESC")
            alerts = []
            for row in cursor.fetchall():
                alerts.append(
                    Alert(
                        id=row["id"],
                        alert_type=row["alert_type"],
                        brew_id=row["brew_id"],
                        message=row["message"],
                        severity=row["severity"],
                        created_at=datetime.fromisoformat(row["created_at"]),
                    )
                )
            return alerts
        finally:
            conn.close()
