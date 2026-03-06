"""
Report Generation Service for creating CSV reports.

Generates static CSV reports for inventory, brew runs, and alerts.
"""

import csv
import logging
from datetime import datetime
from pathlib import Path
from typing import List

from ..adapters import DatabaseAdapter
from ..domain import InventoryItem, BrewSchedule, Alert

logger = logging.getLogger(__name__)


class ReportService:
    """Service for generating CSV reports."""

    def __init__(self, db: DatabaseAdapter, reports_dir: Path):
        """Initialize report service.
        
        Args:
            db: Database adapter.
            reports_dir: Directory where reports will be saved.
        """
        self.db = db
        self.reports_dir = reports_dir
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def generate_all_reports(self) -> dict:
        """Generate all daily reports.
        
        Returns:
            Dictionary with report generation results.
        """
        today = datetime.utcnow().strftime("%Y%m%d")
        
        results = {
            "inventory": self.generate_inventory_report(today),
            "brew_runs": self.generate_brew_report(today),
            "alerts": self.generate_alerts_report(today),
        }
        
        logger.info(f"Generated all reports for {today}")
        return results

    def generate_inventory_report(self, date_str: str = None) -> str:
        """Generate inventory snapshot report.
        
        Args:
            date_str: Date string (YYYYMMDD). Defaults to today.
        
        Returns:
            str: Path to generated report file.
        """
        if not date_str:
            date_str = datetime.utcnow().strftime("%Y%m%d")

        filename = f"inventory_snapshot_{date_str}.csv"
        filepath = self.reports_dir / filename

        items = self.db.list_inventory()

        try:
            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=[
                        "sku",
                        "item_name",
                        "quantity",
                        "unit",
                        "reorder_level",
                        "status",
                        "updated_at",
                    ],
                )
                writer.writeheader()

                for item in items:
                    status = "LOW_STOCK" if item.is_low_stock() else "OK"
                    writer.writerow(
                        {
                            "sku": item.item_sku,
                            "item_name": item.item_name,
                            "quantity": item.quantity,
                            "unit": item.unit,
                            "reorder_level": item.reorder_level,
                            "status": status,
                            "updated_at": item.updated_at.isoformat() if item.updated_at else "",
                        }
                    )

            logger.info(f"Generated inventory report: {filename}")
            return str(filepath)

        except Exception as e:
            logger.error(f"Failed to generate inventory report: {e}")
            raise

    def generate_brew_report(self, date_str: str = None) -> str:
        """Generate brew runs summary report.
        
        Args:
            date_str: Date string (YYYYMMDD). Defaults to today.
        
        Returns:
            str: Path to generated report file.
        """
        if not date_str:
            date_str = datetime.utcnow().strftime("%Y%m%d")

        filename = f"brew_runs_{date_str}.csv"
        filepath = self.reports_dir / filename

        # Get brews completed/done today
        all_brews = self.db.list_brew_schedules()
        
        # Filter brews from today
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_brews = [
            b for b in all_brews 
            if b.created_at and b.created_at >= today_start
        ]

        try:
            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=[
                        "recipe_name",
                        "start_time",
                        "scheduled_duration_min",
                        "target_temp_c",
                        "status",
                        "event_count",
                        "alert_count",
                    ],
                )
                writer.writeheader()

                for brew in today_brews:
                    events = self.db.get_events_by_brew(brew.id)
                    alerts = self.db.get_alerts_by_brew(brew.id)

                    writer.writerow(
                        {
                            "recipe_name": brew.recipe_name,
                            "start_time": brew.start_time.isoformat(),
                            "scheduled_duration_min": brew.duration_min,
                            "target_temp_c": brew.target_temp_c,
                            "status": brew.status,
                            "event_count": len(events),
                            "alert_count": len(alerts),
                        }
                    )

            logger.info(f"Generated brew report: {filename}")
            return str(filepath)

        except Exception as e:
            logger.error(f"Failed to generate brew report: {e}")
            raise

    def generate_alerts_report(self, date_str: str = None) -> str:
        """Generate alerts log report.
        
        Args:
            date_str: Date string (YYYYMMDD). Defaults to today.
        
        Returns:
            str: Path to generated report file.
        """
        if not date_str:
            date_str = datetime.utcnow().strftime("%Y%m%d")

        filename = f"alerts_{date_str}.csv"
        filepath = self.reports_dir / filename

        # Get all alerts
        all_alerts = self.db.list_all_alerts()
        
        # Filter alerts from today
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_alerts = [
            a for a in all_alerts
            if a.created_at and a.created_at >= today_start
        ]

        try:
            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=[
                        "alert_type",
                        "brew_id",
                        "severity",
                        "message",
                        "created_at",
                    ],
                )
                writer.writeheader()

                for alert in today_alerts:
                    writer.writerow(
                        {
                            "alert_type": alert.alert_type,
                            "brew_id": alert.brew_id or "",
                            "severity": alert.severity,
                            "message": alert.message,
                            "created_at": alert.created_at.isoformat() if alert.created_at else "",
                        }
                    )

            logger.info(f"Generated alerts report: {filename}")
            return str(filepath)

        except Exception as e:
            logger.error(f"Failed to generate alerts report: {e}")
            raise
