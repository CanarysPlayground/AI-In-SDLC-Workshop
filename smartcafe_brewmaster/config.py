"""
Configuration module for SmartCafé BrewMaster application.

Handles environment-specific settings and defaults for the application.
All configuration values can be overridden via environment variables.
"""

import os
from pathlib import Path

# Project Paths
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
IOT_DROPBOX = DATA_DIR / "iot_dropbox"
IOT_PROCESSED = IOT_DROPBOX / "processed"
IOT_FAILED = IOT_DROPBOX / "failed"
REPORTS_DIR = PROJECT_ROOT / "reports"
DB_PATH = DATA_DIR / "brewmaster.db"

# Ensure directories exist
for directory in [DATA_DIR, IOT_DROPBOX, IOT_PROCESSED, IOT_FAILED, REPORTS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DB_PATH}")

# Alert Thresholds (Celsius)
BURN_TEMP_THRESHOLD = float(os.getenv("BURN_TEMP_THRESHOLD", 98.0))
BURN_DURATION_SEC = float(os.getenv("BURN_DURATION_SEC", 30.0))

# Over-brew Configuration
OVERBREW_GRACE_PERCENT = float(os.getenv("OVERBREW_GRACE_PERCENT", 10.0))
SERVING_TEMP_MIN = float(os.getenv("SERVING_TEMP_MIN", 50.0))
SERVING_TEMP_MAX = float(os.getenv("SERVING_TEMP_MAX", 75.0))

# IoT Ingestion Configuration
IOT_WATCH_INTERVAL_SEC = float(os.getenv("IOT_WATCH_INTERVAL_SEC", 5.0))
IOT_FILE_PATTERN = "*.csv"

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Report Configuration
REPORT_TIME_FORMAT = "%Y%m%d"
