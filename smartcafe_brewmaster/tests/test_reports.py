"""
Tests for report generation service.

Tests CSV report generation for inventory, brews, and alerts.
"""

from datetime import datetime, timedelta
from pathlib import Path

import pytest

from smartcafe_brewmaster.services import (
    ReportService,
    InventoryService,
    BrewScheduleService,
)


class TestReportService:
    """Tests for report generation service."""

    def test_generate_inventory_report(self, temp_database, temp_directories):
        """Test generating inventory snapshot report."""
        _, _, _, reports = temp_directories
        report_service = ReportService(temp_database, reports)
        inventory_service = InventoryService(temp_database)
        
        # Create some inventory items
        inventory_service.create_item("BEAN-001", "Ethiopian Beans", 500, "grams", 100)
        inventory_service.create_item("BEAN-002", "Colombian Beans", 50, "grams", 100)
        
        report_path = report_service.generate_inventory_report("20260306")
        
        assert Path(report_path).exists()
        content = Path(report_path).read_text()
        assert "BEAN-001" in content
        assert "BEAN-002" in content
        assert "LOW_STOCK" in content

    def test_generate_brew_report(self, temp_database, temp_directories):
        """Test generating brew runs report."""
        _, _, _, reports = temp_directories
        report_service = ReportService(temp_database, reports)
        brew_service = BrewScheduleService(temp_database)
        
        # Create brew schedules
        start = datetime.utcnow()
        brew_service.create_brew("Espresso", start, 92.0, 3)
        brew_service.create_brew("Americano", start, 90.0, 5)
        
        report_path = report_service.generate_brew_report("20260306")
        
        assert Path(report_path).exists()
        content = Path(report_path).read_text()
        assert "scheduled" in content

    def test_generate_alerts_report(self, temp_database, temp_directories):
        """Test generating alerts report."""
        _, _, _, reports = temp_directories
        report_service = ReportService(temp_database, reports)
        
        # Create some alerts
        from smartcafe_brewmaster.domain import Alert
        
        for i in range(3):
            alert = Alert(
                alert_type="burn" if i < 2 else "overbrew",
                brew_id=1,
                message=f"Test alert {i}",
                severity="error" if i == 0 else "warn",
            )
            temp_database.create_alert(alert)
        
        report_path = report_service.generate_alerts_report("20260306")
        
        assert Path(report_path).exists()
        content = Path(report_path).read_text()
        assert "burn" in content or "overbrew" in content

    def test_generate_all_reports(self, temp_database, temp_directories):
        """Test generating all reports at once."""
        _, _, _, reports = temp_directories
        report_service = ReportService(temp_database, reports)
        
        results = report_service.generate_all_reports()
        
        assert "inventory" in results
        assert "brew_runs" in results
        assert "alerts" in results
        
        for path in results.values():
            assert Path(path).exists()

    def test_report_files_created_in_correct_location(self, temp_database, temp_directories):
        """Test that reports are created in the correct directory."""
        _, _, _, reports = temp_directories
        report_service = ReportService(temp_database, reports)
        
        path = report_service.generate_inventory_report("20260306")
        
        assert reports in Path(path).parents
        assert Path(path).parent == reports
