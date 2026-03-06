# SmartCafé BrewMaster

**MVP for IoT-Enabled Brew Management System**

An intelligent coffee brewing system that monitors temperature sensors, tracks inventory, schedules brews, and detects quality issues in real-time.

## Features

### Core MVP Features
- **Inventory Tracking**: CRUD operations for inventory items with low-stock alerts
- **Brew Scheduling**: Create, manage, and monitor brew schedules
- **IoT Sensor Integration**: Ingest temperature data from CSV drop-folder system
- **Burn Detection**: Alert when brew temperature exceeds safe thresholds for sustained periods
- **Over-Brew Detection**: Alert when brew exceeds scheduled duration or stays warm too long
- **CSV Reporting**: Generate daily inventory, brew, and alert reports

### Quality Assurance
- Clean, testable architecture with separation of concerns
- Comprehensive unit and integration tests
- Domain-driven design for business logic
- Adapter pattern for IO operations

### Planned Enhancements (Not in MVP)
- Usage & refill predictions
- Anomaly intelligence and ML integration
- Flavor recommendations
- Maintenance guidance
- RESTful API

## Project Structure

```
smartcafe_brewmaster/
├── config.py                 # Configuration management
├── domain/                   # Pure business logic (no IO)
│   ├── models.py            # Domain entities
│   └── logic.py             # Core algorithms
├── adapters/                # IO and external integrations
│   └── db.py               # SQLite database adapter
├── services/               # Business logic with IO
│   ├── inventory.py        # Inventory management
│   ├── brew.py            # Brew scheduling
│   ├── alerts.py          # Alert detection
│   ├── iot_ingestion.py   # IoT data processing
│   └── reports.py         # Report generation
├── api/
│   └── cli.py            # Command-line interface
├── sql/
│   └── schema.sql        # Database schema
├── data/
│   └── iot_dropbox/      # IoT sensor data drop-folder
│       ├── processed/    # Successfully processed files
│       └── failed/       # Failed processing files
├── reports/              # Generated CSV reports
├── tests/                # Test suite
└── requirements.txt      # Python dependencies
```

## Installation

### Prerequisites
- Python 3.8+
- pip

### Setup

1. Clone the repository:
```bash
cd smartcafe_brewmaster
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Initialize the database:
```bash
python -m smartcafe_brewmaster.api.cli init-db
```

## Usage

### Command-Line Interface

#### Initialize Database
```bash
python -m smartcafe_brewmaster.api.cli init-db
```

#### Schedule a Brew
```bash
# Schedule brew starting now
python -m smartcafe_brewmaster.api.cli schedule-brew "Espresso" 92.5 3

# Schedule brew with 10 minute delay
python -m smartcafe_brewmaster.api.cli schedule-brew "Americano" 90.0 5 10
```

#### Manage Brew Status
```bash
# List all scheduled brews
python -m smartcafe_brewmaster.api.cli list-brews scheduled

# List active (brewing) brews
python -m smartcafe_brewmaster.api.cli list-brews brewing

# Start a brew (transition from scheduled to brewing)
python -m smartcafe_brewmaster.api.cli start-brew 1

# Complete a brew
python -m smartcafe_brewmaster.api.cli complete-brew 1
```

#### Manage Inventory
```bash
# Add inventory item
python -m smartcafe_brewmaster.api.cli inventory-add "BEAN-001" "Ethiopian Beans" 500 grams 100

# List all inventory
python -m smartcafe_brewmaster.api.cli inventory-list
```

#### Process IoT Data
Place CSV files in `data/iot_dropbox/` with format:
```csv
sensor_id,observed_at,temp_c
sensor1,2026-03-06T10:00:00,92.5
sensor1,2026-03-06T10:01:00,93.0
```

Then process:
```bash
python -m smartcafe_brewmaster.api.cli ingest
```

#### Check Alerts
```bash
python -m smartcafe_brewmaster.api.cli check-alerts
```

#### Generate Reports
```bash
python -m smartcafe_brewmaster.api.cli report
```

Reports are generated in `reports/` directory as CSV files.

## IoT Data Format

### Input: Temperature Events CSV
Place CSV files in `data/iot_dropbox/` with the following format:

**Headers**: `sensor_id,observed_at,temp_c`

**Example**:
```csv
sensor_id,observed_at,temp_c
sensor1,2026-03-06T10:00:00,92.5
sensor1,2026-03-06T10:01:00,93.0
sensor1,2026-03-06T10:02:00,94.1
```

**Notes**:
- `observed_at` must be ISO8601 format (UTC)
- `temp_c` must be a valid float
- Files are moved to `processed/` or `failed/` after processing

## Configuration

Configuration values can be set via environment variables in `config.py`:

```python
# Alert Thresholds
BURN_TEMP_THRESHOLD = 98.0  # Celsius
BURN_DURATION_SEC = 30.0    # Seconds

# Over-brew Configuration
OVERBREW_GRACE_PERCENT = 10.0  # Percentage of scheduled duration
SERVING_TEMP_MIN = 50.0        # Celsius
SERVING_TEMP_MAX = 75.0        # Celsius

# Ingestion
IOT_WATCH_INTERVAL_SEC = 5.0   # Check dropbox every N seconds
```

Override with environment variables:
```bash
export BURN_TEMP_THRESHOLD=95.0
export BURN_DURATION_SEC=45.0
python -m smartcafe_brewmaster.api.cli check-alerts
```

## Database Schema

### Tables

**inventory**
- `id` (INTEGER PK)
- `item_sku` (TEXT UNIQUE)
- `item_name` (TEXT)
- `quantity` (INTEGER)
- `unit` (TEXT) - e.g., grams, ml
- `reorder_level` (INTEGER)
- `updated_at` (TEXT ISO8601)

**brew_schedule**
- `id` (INTEGER PK)
- `recipe_name` (TEXT)
- `start_time` (TEXT ISO8601)
- `target_temp_c` (REAL)
- `duration_min` (INTEGER)
- `status` (TEXT) - scheduled|brewing|done|canceled
- `created_at` (TEXT ISO8601)

**temperature_events**
- `id` (INTEGER PK)
- `sensor_id` (TEXT)
- `brew_id` (INTEGER FK)
- `observed_at` (TEXT ISO8601)
- `temp_c` (REAL)
- `raw_file` (TEXT)

**alerts**
- `id` (INTEGER PK)
- `alert_type` (TEXT) - burn|overbrew|system
- `brew_id` (INTEGER FK)
- `message` (TEXT)
- `severity` (TEXT) - info|warn|error
- `created_at` (TEXT ISO8601)

## Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=smartcafe_brewmaster tests/

# Run specific test file
pytest tests/test_domain.py

# Run with verbose output
pytest -v
```

### Test Coverage

- **test_domain.py**: Pure domain logic and models
- **test_inventory.py**: Inventory service operations
- **test_brew.py**: Brew scheduling service
- **test_alerts.py**: Alert detection and generation
- **test_iot_ingestion.py**: CSV file ingestion and parsing
- **test_reports.py**: Report generation

## Alert Detection Logic

### Burn Alert
Triggered when:
- Brew is currently active (status = "brewing")
- Temperature exceeds `BURN_TEMP_THRESHOLD` (default 98°C)
- Temperature stays above threshold for `BURN_DURATION_SEC` (default 30 seconds)
- Severity: ERROR

### Over-Brew Alert
Triggered when:
1. Brew exceeds scheduled end time + grace period (default 10% of duration)
   - Severity: WARNING

2. Brew is completed but temperature stays above `SERVING_TEMP_MAX` (default 75°C)
   - Severity: WARNING

### Alert Deduplication
Identical alerts for the same brew within a 5-minute window are deduplicated to prevent alert spam.

## Architecture Decisions

### Domain-Driven Design
- Pure domain logic in `domain/` module with no IO dependencies
- Testable business rules independent of framework/database
- Models (InventoryItem, BrewSchedule, etc.) represent business concepts

### Adapter Pattern
- `adapters/` module decouples domain logic from data persistence
- SQLite adapter implements data operations
- Easy to swap implementations (e.g., PostgreSQL in future)

### Service Layer
- Services orchestrate domain logic with IO operations
- Each service has a single responsibility
- Dependency injection for testability

### Configuration Management
- Centralized `config.py` for all settings
- Environment variable overrides for deployment
- Safe defaults for all thresholds

## Future Enhancements

While maintaining backward compatibility with the MVP:

### Phase 2: Intelligence
- **Predictive Analytics**: Predict inventory needs based on brew patterns
- **Anomaly Detection**: Identify unusual brewing conditions
- **Recommendations**: Suggest optimal brewing parameters

### Phase 3: Advanced Features
- **RESTful API**: HTTP endpoints for integration
- **Web Dashboard**: Real-time monitoring interface
- **Maintenance Scheduling**: Predict maintenance needs
- **Flavor Profiles**: Track and recommend flavor characteristics

### Design for Extensibility
- New intelligence modules read current database
- Extension tables/views added without modifying core schema
- Microservice-ready architecture
- Plugin system for custom alert types

## Development

### Code Style
- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/)
- Type hints for public functions
- Google-style docstrings
- Line length: 95 characters

### Adding Tests
All new features must include tests:
```bash
pytest tests/test_my_feature.py
```

### Git Workflow
- Feature branches: `feature/description`
- Fix branches: `fix/issue-number`
- Conventional commits: `feat:`, `fix:`, `docs:`, `test:`, `refactor:`

## Troubleshooting

### Database Lock Issues
- Ensure only one process is running at a time
- Check `data/brewmaster.db` is not open in another application

### CSV Ingestion Failures
- Verify CSV headers: `sensor_id,observed_at,temp_c`
- Check timestamp format: ISO8601 UTC (e.g., `2026-03-06T10:00:00`)
- Review `data/iot_dropbox/failed/` for rejected files

### No Temperature Events
- Confirm CSV files are in `data/iot_dropbox/`
- Run `python -m smartcafe_brewmaster.api.cli ingest`
- Check logs for parsing errors

## Support

For issues or questions, please refer to the documentation or create an issue in the repository.

## License

Proprietary - SmartCafé Inc.

## Version

**Current Version**: 0.1.0 (MVP)

**Last Updated**: March 2026
