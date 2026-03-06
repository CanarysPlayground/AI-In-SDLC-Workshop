"""
Test fixtures and configuration.

Shared test utilities and database fixtures.
"""

import tempfile
from pathlib import Path

import pytest

from smartcafe_brewmaster.adapters import DatabaseAdapter


@pytest.fixture
def temp_database():
    """Create a temporary database for each test.
    
    Yields:
        DatabaseAdapter: Connected database with schema initialized.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = DatabaseAdapter(db_path)
        
        # Initialize schema
        schema_path = Path(__file__).parent.parent / "sql" / "schema.sql"
        db.init_schema(schema_path)
        
        yield db


@pytest.fixture
def temp_directories():
    """Create temporary directories for testing.
    
    Yields:
        Tuple[Path, Path, Path, Path]: (dropbox, processed, failed, reports)
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        dropbox = base / "dropbox"
        processed = dropbox / "processed"
        failed = dropbox / "failed"
        reports = base / "reports"
        
        dropbox.mkdir()
        processed.mkdir()
        failed.mkdir()
        reports.mkdir()
        
        yield dropbox, processed, failed, reports
