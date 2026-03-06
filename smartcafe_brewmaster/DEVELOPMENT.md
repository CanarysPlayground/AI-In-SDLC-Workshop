# Development Guide

## Architecture Overview

SmartCafé BrewMaster follows a **layered architecture** with clear separation of concerns:

```
┌─────────────────────────────────────────┐
│         CLI Interface (api/cli.py)      │
├─────────────────────────────────────────┤
│         Services Layer                   │
│  ├─ InventoryService                    │
│  ├─ BrewScheduleService                 │
│  ├─ AlertService                        │
│  ├─ IOTIngestionService                 │
│  └─ ReportService                       │
├─────────────────────────────────────────┤
│      Domain Logic Layer (domain/)       │
│  ├─ Models (pure data)                  │
│  └─ Business Logic (no IO)              │
├─────────────────────────────────────────┤
│         Adapter Layer (adapters/)       │
│         DatabaseAdapter (SQLite)        │
├─────────────────────────────────────────┤
│         External Systems                │
│  ├─ SQLite Database                     │
│  ├─ File System (IoT drop-folder)       │
│  └─ CSV Files (reports)                 │
└─────────────────────────────────────────┘
```

## Design Patterns Used

### 1. Domain-Driven Design (DDD)
- Pure domain logic separated from IO operations
- Models represent business concepts
- Logic classes implement algorithms independent of persistence

### 2. Adapter Pattern
- `DatabaseAdapter` abstracts SQLite operations
- Easy to swap implementations (PostgreSQL, etc.) without changing services

### 3. Service Locator / Dependency Injection
- Services receive dependencies through constructor
- `IOTIngestionService`, `AlertService`, etc. receive `DatabaseAdapter`

### 4. Repository Pattern
- `DatabaseAdapter` acts as repository for all entities
- Provides data access abstraction

## Module Responsibilities

### `domain/models.py`
- **InventoryItem**: Represents an inventory item
- **BrewSchedule**: Represents a scheduled brew
- **TemperatureEvent**: Represents a sensor reading
- **Alert**: Represents an alert condition

Each model has business logic methods:
```python
item.is_low_stock()           # Check if below reorder level
item.adjust_quantity(delta)   # Update quantity with validation
brew.is_active()              # Check if currently brewing
brew.expected_end_time()      # Calculate when brew should complete
alert.is_critical()           # Check if severe
```

### `domain/logic.py`
Pure algorithms with no IO:
- **BurnDetector**: Detects sustained high temperature
- **OverBrewDetector**: Detects over-brew conditions
- **AlertDeduplicator**: Prevents alert spam

### `adapters/db.py`
SQLite operations:
- Create/read/update operations for all entities
- List and filter operations
- Transaction management

### `services/*.py`
Business orchestration:
- Combine domain logic with adapter operations
- Provide high-level business operations
- Handle errors and logging

## Testing Strategy

### Unit Tests (`test_domain.py`)
Test pure logic with no IO:
```python
def test_burn_detection():
    detector = BurnDetector(98.0, 30.0)
    brew = BrewSchedule(...)
    events = [TemperatureEvent(...), ...]
    is_burned, max_temp = detector.detect_burn(brew, events)
    assert is_burned
```

### Integration Tests (`test_*.py`)
Test services with real database:
```python
def test_create_and_retrieve_item(temp_database):
    service = InventoryService(temp_database)
    item_id = service.create_item(...)
    item = service.get_item(item_id)
    assert item.item_sku == "BEAN-001"
```

### Fixtures (`conftest.py`)
- `temp_database`: Isolated database for each test
- `temp_directories`: Isolated file system for each test

## Extending the Application

### Adding a New Service

1. **Create domain model** (`domain/models.py`)
```python
@dataclass
class NewEntity:
    name: str
    value: str
    id: Optional[int] = None
```

2. **Add database operations** (`adapters/db.py`)
```python
def create_new_entity(self, entity: NewEntity) -> int:
    cursor = conn.cursor()
    cursor.execute("INSERT INTO new_entities ...")
    return cursor.lastrowid
```

3. **Create service class** (`services/new_service.py`)
```python
class NewService:
    def __init__(self, db: DatabaseAdapter):
        self.db = db
    
    def create(self, name: str, value: str) -> int:
        return self.db.create_new_entity(NewEntity(name, value))
```

4. **Add tests** (`tests/test_new_service.py`)
```python
def test_create_entity(temp_database):
    service = NewService(temp_database)
    entity_id = service.create("name", "value")
    assert entity_id is not None
```

5. **Update CLI** (`api/cli.py`)
```python
def new_command(self, arg: str) -> None:
    """Handle new command."""
    result = self.new_service.do_something(arg)
    print(f"✓ Done: {result}")
```

### Adding Alert Type

1. **Update logic** (`domain/logic.py`)
```python
class NewConditionDetector:
    def detect_condition(self, ...) -> Tuple[bool, str]:
        # Detection logic
```

2. **Update alert service** (`services/alerts.py`)
```python
def check_brew_alerts(self, brew_id: int) -> None:
    # ... existing checks ...
    
    # New condition check
    is_condition, reason = self.new_detector.detect_condition(...)
    if is_condition and self.deduplicator.should_alert("new_type", brew_id, recent_alerts):
        alert = Alert(alert_type="new_type", ...)
        self.db.create_alert(alert)
```

3. **Add tests** (`tests/test_alerts.py`)
```python
def test_detect_new_condition(temp_database):
    service = AlertService(temp_database)
    # Test detection logic
```

### Migrating to PostgreSQL

1. Create new adapter class `PostgreSQLAdapter` in `adapters/postgres.py`
2. Implement same interface as `DatabaseAdapter`
3. Update `services/` to optionally accept either adapter
4. Add tests with PostgreSQL test database

### Adding ML Intelligence Module

1. Create `intelligence/` module with pure prediction logic
2. Create `IntelligenceService` that reads from DB and writes to new tables
3. Deploy as separate microservice if needed
4. Keep existing systems unchanged

## Configuration Best Practices

### Development
```bash
export LOG_LEVEL=DEBUG
export BURN_TEMP_THRESHOLD=98.0
python -m smartcafe_brewmaster.api.cli init-db
```

### Production
```bash
export LOG_LEVEL=INFO
export DATABASE_URL="postgresql://user:pass@host/db"
export BURN_TEMP_THRESHOLD=98.0
export OVERBREW_GRACE_PERCENT=10.0
```

## Performance Considerations

### Database Indexes
Current schema includes indexes on:
- `inventory.item_sku` - frequent lookups
- `brew_schedule.status` - status filtering
- `brew_schedule.start_time` - chronological queries
- `temperature_events.observed_at` - time range queries
- `temperature_events.brew_id` - brew association
- `alerts.alert_type` - alert filtering

### Caching
For future enhancement:
- Cache low-stock items (invalidate on inventory update)
- Cache active brews (invalidate on status change)
- Cache recent alerts (time-based TTL)

### Batch Operations
- `ingest_files()` processes all files in one pass
- `check_all_active_brews()` checks all in one service call
- `generate_all_reports()` generates all reports together

## Backward Compatibility

### Schema Evolution
All schema changes must be **additive only**:
```sql
-- ✓ OK: Add new column with default
ALTER TABLE alerts ADD COLUMN source TEXT DEFAULT 'system';

-- ✓ OK: Create new table
CREATE TABLE alerts_v2 AS SELECT * FROM alerts;

-- ✗ NOT OK: Remove or rename column
ALTER TABLE alerts DROP COLUMN brew_id;
```

### API Stability
- Query structure returned by services must remain stable
- New fields can be added but existing ones must not change
- New service methods can be added, not replaced

### File Format Stability
- CSV headers are contracts - cannot change
- New files can be added (e.g., `alerts_v2_YYYYMMDD.csv`)
- Existing files must maintain structure

## Debugging

### Enable Debug Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.debug("Detailed info for debugging")
```

### Database Inspection
```bash
sqlite3 data/brewmaster.db
.tables
.schema brew_schedule
SELECT * FROM brew_schedule LIMIT 5;
```

### Manual Testing
```bash
# Test database operations
python -m smartcafe_brewmaster.api.cli init-db

# Create test data
python -m smartcafe_brewmaster.api.cli schedule-brew "Test" 92.0 3

# List data
python -m smartcafe_brewmaster.api.cli list-brews

# Check for alerts
python -m smartcafe_brewmaster.api.cli check-alerts
```

## Common Issues & Solutions

### Issue: "database is locked"
**Cause**: Multiple processes accessing database simultaneously
**Solution**: Ensure only one CLI/service is running at a time

### Issue: "No such table"
**Cause**: Schema not initialized
**Solution**: Run `python -m smartcafe_brewmaster.api.cli init-db`

### Issue: CSV files not processing
**Cause**: Incorrect headers or timestamp format
**Solution**: Verify file in `data/iot_dropbox/failed/` and check format

### Issue: No alerts generated
**Cause**: Alert thresholds too high or brew not active
**Solution**: Scale down thresholds or check brew status

## Performance Monitoring

### Metrics to Track
- Ingestion throughput (rows/second)
- Alert detection latency (seconds)
- Query performance (database operations/second)
- Report generation time

### Logging Best Practices
```python
logger.info(f"Processing file: {file_path.name}")  # Start of operation
logger.debug(f"Parsed {row_count} rows")           # Intermediate progress
logger.info(f"Completed: {results}")               # End of operation
logger.error(f"Failed: {error_message}")           # Errors with context
```

## Version Management

**Current Version**: 0.1.0 (MVP)

**Version Strategy**:
- MAJOR.MINOR.PATCH
- MAJOR: Breaking changes (rare, with deprecation path)
- MINOR: New features (backward compatible)
- PATCH: Bug fixes

**Release Checklist**:
- [ ] All tests passing
- [ ] README updated
- [ ] CHANGELOG updated
- [ ] Version bumped in `__init__.py`
- [ ] Database schema documented if changed
