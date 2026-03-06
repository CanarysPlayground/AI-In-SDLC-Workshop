"""
IoT Ingestion Service for temperature sensor data.

Handles CSV file ingestion from the drop-folder, parses temperature events,
and persists them to the database with proper error handling and file routing.
"""

import csv
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

from ..adapters import DatabaseAdapter
from ..domain import TemperatureEvent

logger = logging.getLogger(__name__)


class IOTIngestionService:
    """Service for ingesting IoT temperature sensor data from CSV files."""

    def __init__(
        self,
        db: DatabaseAdapter,
        dropbox_dir: Path,
        processed_dir: Path,
        failed_dir: Path,
    ):
        """Initialize IoT ingestion service.
        
        Args:
            db: Database adapter for persistence.
            dropbox_dir: Source directory for new CSV files.
            processed_dir: Directory for successfully processed files.
            failed_dir: Directory for failed processing.
        """
        self.db = db
        self.dropbox_dir = dropbox_dir
        self.processed_dir = processed_dir
        self.failed_dir = failed_dir

    def ingest_files(self) -> Tuple[int, int, int]:
        """Process all CSV files in dropbox directory.
        
        Returns:
            Tuple[int, int, int]: (files_processed, rows_inserted, errors)
        """
        csv_files = list(self.dropbox_dir.glob("*.csv"))
        if not csv_files:
            logger.debug("No CSV files to process")
            return 0, 0, 0

        processed_count = 0
        total_rows = 0
        error_count = 0

        for csv_file in csv_files:
            rows, errors = self._process_file(csv_file)
            total_rows += rows
            error_count += errors
            processed_count += 1

        logger.info(
            f"Ingestion complete: {processed_count} files, "
            f"{total_rows} rows inserted, {error_count} errors"
        )
        return processed_count, total_rows, error_count

    def _process_file(self, file_path: Path) -> Tuple[int, int]:
        """Process a single CSV file.
        
        Args:
            file_path: Path to CSV file to process.
        
        Returns:
            Tuple[int, int]: (rows_inserted, errors)
        """
        logger.info(f"Processing file: {file_path.name}")
        rows_inserted = 0
        error_count = 0

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                
                # Validate headers
                expected_headers = {"sensor_id", "observed_at", "temp_c"}
                if not reader.fieldnames or not expected_headers.issubset(
                    set(reader.fieldnames)
                ):
                    raise ValueError(
                        f"Invalid CSV headers. Expected: {expected_headers}"
                    )

                for row_num, row in enumerate(reader, start=2):
                    try:
                        event = self._parse_event(row, file_path.name)
                        self.db.create_temperature_event(event)
                        rows_inserted += 1
                    except ValueError as e:
                        logger.warning(f"Row {row_num} in {file_path.name}: {e}")
                        error_count += 1
                    except Exception as e:
                        logger.error(f"Unexpected error at row {row_num}: {e}")
                        error_count += 1

            # Move file to processed directory if successful
            if error_count == 0:
                self._move_file(file_path, self.processed_dir)
            else:
                # Still move, but log it had errors
                self._move_file(file_path, self.processed_dir)
                logger.warning(
                    f"{file_path.name} moved to processed with {error_count} row errors"
                )

        except Exception as e:
            logger.error(f"Failed to process {file_path.name}: {e}")
            self._move_file(file_path, self.failed_dir)
            error_count += 1

        return rows_inserted, error_count

    def _parse_event(self, row: dict, file_name: str) -> TemperatureEvent:
        """Parse a CSV row into a TemperatureEvent.
        
        Args:
            row: Dictionary from CSV reader.
            file_name: Name of source file.
        
        Returns:
            TemperatureEvent object.
        
        Raises:
            ValueError: If row data is invalid.
        """
        try:
            sensor_id = row.get("sensor_id", "").strip()
            if not sensor_id:
                raise ValueError("sensor_id is required and cannot be empty")

            observed_at_str = row.get("observed_at", "").strip()
            if not observed_at_str:
                raise ValueError("observed_at is required")

            temp_c_str = row.get("temp_c", "").strip()
            if not temp_c_str:
                raise ValueError("temp_c is required")

            # Parse ISO8601 timestamp
            observed_at = datetime.fromisoformat(observed_at_str)

            # Parse temperature
            temp_c = float(temp_c_str)

            return TemperatureEvent(
                sensor_id=sensor_id,
                observed_at=observed_at,
                temp_c=temp_c,
                raw_file=file_name,
                brew_id=None,
            )

        except datetime.fromisoformat as e:
            raise ValueError(f"Invalid observed_at timestamp: {e}")
        except ValueError as e:
            if "could not convert" in str(e).lower():
                raise ValueError(f"Invalid temp_c value: {e}")
            raise

    def _move_file(self, source: Path, dest_dir: Path) -> None:
        """Move file to destination directory.
        
        Args:
            source: Source file path.
            dest_dir: Destination directory.
        """
        try:
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest_path = dest_dir / source.name
            source.rename(dest_path)
            logger.debug(f"Moved {source.name} to {dest_dir.name}/")
        except Exception as e:
            logger.error(f"Failed to move file {source.name}: {e}")
            raise
