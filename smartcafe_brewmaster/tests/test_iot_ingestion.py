"""
Integration tests for IoT Ingestion Service.

Tests CSV file processing, parsing, and database persistence.
"""

import tempfile
from pathlib import Path
from datetime import datetime

import pytest

from smartcafe_brewmaster.adapters import DatabaseAdapter
from smartcafe_brewmaster.services import IOTIngestionService


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = DatabaseAdapter(db_path)
        
        schema_path = Path(__file__).parent.parent / "sql" / "schema.sql"
        db.init_schema(schema_path)
        
        yield db


@pytest.fixture
def temp_dropbox():
    """Create temporary IoT dropbox directories."""
    with tempfile.TemporaryDirectory() as tmpdir:
        dropbox = Path(tmpdir) / "dropbox"
        processed = dropbox / "processed"
        failed = dropbox / "failed"
        dropbox.mkdir()
        processed.mkdir()
        failed.mkdir()
        
        yield dropbox, processed, failed


class TestIOTIngestionService:
    """Tests for IoT ingestion service."""

    def test_process_valid_csv(self, temp_db, temp_dropbox):
        """Test processing a valid CSV file."""
        dropbox, processed, failed = temp_dropbox
        service = IOTIngestionService(temp_db, dropbox, processed, failed)
        
        # Create test CSV
        csv_file = dropbox / "test_sensors.csv"
        csv_file.write_text(
            "sensor_id,observed_at,temp_c\n"
            "sensor1,2026-03-06T10:00:00,92.5\n"
            "sensor1,2026-03-06T10:01:00,93.0\n"
        )
        
        files, rows, errors = service.ingest_files()
        
        assert files == 1
        assert rows == 2
        assert errors == 0
        assert not csv_file.exists()
        assert (processed / "test_sensors.csv").exists()

    def test_process_csv_with_invalid_rows(self, temp_db, temp_dropbox):
        """Test CSV processing with some invalid rows."""
        dropbox, processed, failed = temp_dropbox
        service = IOTIngestionService(temp_db, dropbox, processed, failed)
        
        # CSV with one valid and one invalid row
        csv_file = dropbox / "test_sensors.csv"
        csv_file.write_text(
            "sensor_id,observed_at,temp_c\n"
            "sensor1,2026-03-06T10:00:00,92.5\n"
            "sensor1,invalid_date,93.0\n"
        )
        
        files, rows, errors = service.ingest_files()
        
        assert files == 1
        assert rows == 1  # Only valid row
        assert errors == 1  # One invalid row

    def test_missing_required_field(self, temp_db, temp_dropbox):
        """Test CSV with missing required field."""
        dropbox, processed, failed = temp_dropbox
        service = IOTIngestionService(temp_db, dropbox, processed, failed)
        
        # CSV missing temp_c column
        csv_file = dropbox / "test_sensors.csv"
        csv_file.write_text(
            "sensor_id,observed_at\n"
            "sensor1,2026-03-06T10:00:00\n"
        )
        
        files, rows, errors = service.ingest_files()
        
        assert files == 1
        assert rows == 0
        assert errors > 0

    def test_empty_dropbox(self, temp_db, temp_dropbox):
        """Test behavior with empty dropbox."""
        dropbox, processed, failed = temp_dropbox
        service = IOTIngestionService(temp_db, dropbox, processed, failed)
        
        files, rows, errors = service.ingest_files()
        
        assert files == 0
        assert rows == 0
        assert errors == 0
