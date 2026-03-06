"""
CLI module for SmartCafé BrewMaster application.

Provides command-line interface for database initialization, ingestion,
scheduling, and reporting operations.
"""

import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path

from .. import config
from ..adapters import DatabaseAdapter
from ..services import (
    InventoryService,
    BrewScheduleService,
    AlertService,
    IOTIngestionService,
    ReportService,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format=config.LOG_FORMAT,
)
logger = logging.getLogger(__name__)


class BrewMasterCLI:
    """Command-line interface for BrewMaster application."""

    def __init__(self):
        """Initialize CLI and database adapter."""
        self.db = DatabaseAdapter(config.DB_PATH)
        self.inventory = InventoryService(self.db)
        self.brew = BrewScheduleService(self.db)
        self.alerts = AlertService(
            self.db,
            burn_temp_threshold=config.BURN_TEMP_THRESHOLD,
            burn_duration_sec=config.BURN_DURATION_SEC,
            overbrew_grace_percent=config.OVERBREW_GRACE_PERCENT,
            serving_temp_min=config.SERVING_TEMP_MIN,
            serving_temp_max=config.SERVING_TEMP_MAX,
        )
        self.ingestion = IOTIngestionService(
            self.db,
            config.IOT_DROPBOX,
            config.IOT_PROCESSED,
            config.IOT_FAILED,
        )
        self.reports = ReportService(self.db, config.REPORTS_DIR)

    def init_db(self) -> None:
        """Initialize database schema."""
        schema_path = Path(__file__).parent.parent / "sql" / "schema.sql"
        self.db.init_schema(schema_path)
        print("[OK] Database initialized successfully")

    def ingest(self) -> None:
        """Process IoT ingestion files."""
        files, rows, errors = self.ingestion.ingest_files()
        print(f"[OK] Ingestion complete: {files} files, {rows} rows, {errors} errors")

    def report(self) -> None:
        """Generate daily reports."""
        results = self.reports.generate_all_reports()
        print("[OK] Reports generated:")
        for report_type, path in results.items():
            print(f"  - {report_type}: {path}")

    def schedule_brew(
        self, recipe: str, temp: float, duration: int, delay_min: int = 0
    ) -> None:
        """Schedule a new brew.
        
        Args:
            recipe: Recipe name.
            temp: Target temperature in Celsius.
            duration: Duration in minutes.
            delay_min: Minutes to delay start (default 0 = start now).
        """
        start_time = datetime.utcnow() + timedelta(minutes=delay_min)
        brew_id = self.brew.create_brew(recipe, start_time, temp, duration)
        print(f"[OK] Brew scheduled: ID {brew_id} - {recipe} at {temp} degC for {duration}min")

    def list_brews(self, status: str = None) -> None:
        """List brew schedules.
        
        Args:
            status: Optional status filter.
        """
        brews = self.brew.list_brews(status=status)
        if not brews:
            print("No brews found")
            return

        print(f"\n{'ID':<5} {'Recipe':<20} {'Start Time':<20} {'Status':<10}")
        print("-" * 55)
        for brew in brews:
            start = brew.start_time.strftime("%Y-%m-%d %H:%M")
            print(f"{brew.id:<5} {brew.recipe_name:<20} {start:<20} {brew.status:<10}")

    def start_brew(self, brew_id: int) -> None:
        """Start a brew.
        
        Args:
            brew_id: ID of brew to start.
        """
        self.brew.start_brew(brew_id)
        print(f"[OK] Brew {brew_id} started")

    def complete_brew(self, brew_id: int) -> None:
        """Complete a brew.
        
        Args:
            brew_id: ID of brew to complete.
        """
        self.brew.complete_brew(brew_id)
        print(f"[OK] Brew {brew_id} completed")

    def check_alerts(self) -> None:
        """Check for active brew alerts."""
        self.alerts.check_all_active_brews()
        alerts = self.alerts.get_recent_alerts(minutes=60)
        
        if not alerts:
            print("[OK] No alerts in the last hour")
            return

        summary = self.alerts.get_alerts_summary()
        print(f"\n[OK] Alert Summary (last 1 hour):")
        print(f"  Total: {summary['total_alerts_1h']}")
        print(f"  Critical: {summary['critical_count']}")
        print(f"  Warnings: {summary['warning_count']}")
        print(f"  By type: {summary['by_type']}")

    def inventory_add(self, sku: str, name: str, qty: int, unit: str, reorder: int) -> None:
        """Add inventory item.
        
        Args:
            sku: Stock keeping unit.
            name: Item name.
            qty: Initial quantity.
            unit: Unit of measurement.
            reorder: Reorder level.
        """
        item_id = self.inventory.create_item(sku, name, qty, unit, reorder)
        print(f"[OK] Inventory item added: ID {item_id} - {name}")

    def inventory_list(self) -> None:
        """List all inventory items."""
        items = self.inventory.list_all()
        if not items:
            print("No inventory items found")
            return

        print(f"\n{'SKU':<15} {'Name':<25} {'Qty':<8} {'Unit':<8} {'Status':<10}")
        print("-" * 66)
        for item in items:
            status = "LOW_STOCK" if item.is_low_stock() else "OK"
            print(f"{item.item_sku:<15} {item.item_name:<25} {item.quantity:<8} "
                  f"{item.unit:<8} {status:<10}")

    def print_help(self) -> None:
        """Print help message."""
        help_text = """
SmartCafé BrewMaster CLI
========================

Usage: python cli.py <command> [options]

Commands:
  init-db                    Initialize database schema
  
  ingest                     Process IoT CSV files from dropbox
  
  report                     Generate daily CSV reports
  
  schedule-brew <recipe> <temp> <duration> [delay]
                             Schedule a new brew
                             - recipe: Recipe name
                             - temp: Target temperature (°C)
                             - duration: Duration (minutes)
                             - delay: Start delay in minutes (optional, default 0)
  
  list-brews [status]        List brew schedules
                             - status: optional (scheduled|brewing|done|canceled)
  
  start-brew <id>            Start a brew
  
  complete-brew <id>         Complete a brew
  
  check-alerts               Check and display recent alerts
  
  inventory-add <sku> <name> <qty> <unit> <reorder>
                             Add inventory item
  
  inventory-list             List all inventory items
  
  help                       Display this help message

Examples:
  python cli.py init-db
  python cli.py schedule-brew "Espresso" 92 3
  python cli.py start-brew 1
  python cli.py inventory-add "BEAN-001" "Ethiopian Beans" 500 grams 100
  python cli.py list-brews brewing
  python cli.py check-alerts
"""
        print(help_text)


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Error: No command specified. Use 'help' for usage.")
        sys.exit(1)

    cli = BrewMasterCLI()
    command = sys.argv[1].lower()

    try:
        if command == "init-db":
            cli.init_db()

        elif command == "ingest":
            cli.ingest()

        elif command == "report":
            cli.report()

        elif command == "schedule-brew":
            if len(sys.argv) < 5:
                print("Error: schedule-brew requires recipe, temp, and duration")
                sys.exit(1)
            recipe = sys.argv[2]
            temp = float(sys.argv[3])
            duration = int(sys.argv[4])
            delay = int(sys.argv[5]) if len(sys.argv) > 5 else 0
            cli.schedule_brew(recipe, temp, duration, delay)

        elif command == "list-brews":
            status = sys.argv[2] if len(sys.argv) > 2 else None
            cli.list_brews(status=status)

        elif command == "start-brew":
            if len(sys.argv) < 3:
                print("Error: start-brew requires brew ID")
                sys.exit(1)
            brew_id = int(sys.argv[2])
            cli.start_brew(brew_id)

        elif command == "complete-brew":
            if len(sys.argv) < 3:
                print("Error: complete-brew requires brew ID")
                sys.exit(1)
            brew_id = int(sys.argv[2])
            cli.complete_brew(brew_id)

        elif command == "check-alerts":
            cli.check_alerts()

        elif command == "inventory-add":
            if len(sys.argv) < 7:
                print("Error: inventory-add requires sku, name, qty, unit, and reorder level")
                sys.exit(1)
            sku = sys.argv[2]
            name = sys.argv[3]
            qty = int(sys.argv[4])
            unit = sys.argv[5]
            reorder = int(sys.argv[6])
            cli.inventory_add(sku, name, qty, unit, reorder)

        elif command == "inventory-list":
            cli.inventory_list()

        elif command == "help":
            cli.print_help()

        else:
            print(f"Error: Unknown command '{command}'. Use 'help' for usage.")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Command failed: {e}")
        print(f"[ERROR] Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
