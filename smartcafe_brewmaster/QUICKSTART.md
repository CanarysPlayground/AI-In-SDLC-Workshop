# Quick Start Guide

Get up and running with SmartCafé BrewMaster in 5 minutes.

## 1. Install & Setup (1 minute)

```bash
cd smartcafe_brewmaster

# Install dependencies
pip install -r requirements.txt

# Initialize database
python -m smartcafe_brewmaster.api.cli init-db
```

Output:
```
✓ Database initialized successfully
```

## 2. Add Inventory (1 minute)

```bash
# Add some items to track
python -m smartcafe_brewmaster.api.cli inventory-add "BEAN-001" "Ethiopian Beans" 500 grams 100
python -m smartcafe_brewmaster.api.cli inventory-add "BEAN-002" "Colombian Beans" 300 grams 100
python -m smartcafe_brewmaster.api.cli inventory-add "SUGAR-001" "Brown Sugar" 200 grams 50

# List inventory
python -m smartcafe_brewmaster.api.cli inventory-list
```

Output:
```
✓ Inventory item added: ID 1 - Ethiopian Beans
✓ Inventory item added: ID 2 - Colombian Beans
✓ Inventory item added: ID 3 - Brown Sugar

SKU             Name                      Qty      Unit     Status    
------------------------------------------------------------------
BEAN-001        Ethiopian Beans           500      grams    OK        
BEAN-002        Colombian Beans           300      grams    OK        
SUGAR-001       Brown Sugar               200      grams    OK        
```

## 3. Schedule a Brew (1 minute)

```bash
# Schedule brew starting in 5 minutes
python -m smartcafe_brewmaster.api.cli schedule-brew "Espresso" 92.5 3 5

# Schedule another brew immediately
python -m smartcafe_brewmaster.api.cli schedule-brew "Americano" 90.0 5 0

# List scheduled brews
python -m smartcafe_brewmaster.api.cli list-brews scheduled
```

Output:
```
✓ Brew scheduled: ID 1 - Espresso at 92.5°C for 3min
✓ Brew scheduled: ID 2 - Americano at 90.0°C for 5min

ID    Recipe              Start Time           Status    
---------------------------------------------------------
1     Espresso            2026-03-06 10:05     scheduled 
2     Americano           2026-03-06 10:00     scheduled 
```

## 4. Start & Monitor Brew (1 minute)

```bash
# Start a brew
python -m smartcafe_brewmaster.api.cli start-brew 1

# Check status of active brews
python -m smartcafe_brewmaster.api.cli list-brews brewing

# Complete the brew
python -m smartcafe_brewmaster.api.cli complete-brew 1
```

Output:
```
✓ Brew 1 started
✓ Brew 1 completed

ID    Recipe              Start Time           Status    
---------------------------------------------------------
2     Americano           2026-03-06 10:00     brewing   
```

## 5. IoT Integration (Optional)

Create a CSV file with temperature sensor data:

**File**: `data/iot_dropbox/sensor_readings.csv`
```csv
sensor_id,observed_at,temp_c
sensor-kitchen-01,2026-03-06T10:05:00,92.5
sensor-kitchen-01,2026-03-06T10:05:15,93.0
sensor-kitchen-01,2026-03-06T10:05:30,92.8
sensor-kitchen-01,2026-03-06T10:05:45,99.0
sensor-kitchen-01,2026-03-06T10:06:00,98.5
```

Process the sensor data:

```bash
# Ingest temperature readings
python -m smartcafe_brewmaster.api.cli ingest

# Check for alerts (high temperature)
python -m smartcafe_brewmaster.api.cli check-alerts
```

Output:
```
✓ Ingestion complete: 1 files, 5 rows, 0 errors

✓ Alert Summary (last 1 hour):
  Total: 1
  Critical: 1
  Warnings: 0
  By type: {'burn': 1}
```

## 6. Generate Reports

```bash
# Generate daily reports
python -m smartcafe_brewmaster.api.cli report
```

Output:
```
✓ Reports generated:
  - inventory: reports/inventory_snapshot_20260306.csv
  - brew_runs: reports/brew_runs_20260306.csv
  - alerts: reports/alerts_20260306.csv
```

Check the CSV files:

```bash
# View inventory report
cat reports/inventory_snapshot_20260306.csv

# View brew report
cat reports/brew_runs_20260306.csv

# View alerts report
cat reports/alerts_20260306.csv
```

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=smartcafe_brewmaster

# Run specific test file
pytest tests/test_domain.py -v
```

## Key Concepts

### Brew Statuses
- **scheduled**: Waiting to start
- **brewing**: Currently brewing
- **done**: Finished successfully
- **canceled**: Canceled before completion

### Alert Types
- **burn**: Temperature exceeds safe threshold
- **overbrew**: Brew exceeded duration or temp too high after completion  
- **system**: General system alerts

### Temperature Thresholds
- **Burn threshold**: 98°C by default (configurable)
- **Serving range**: 50-75°C by default (configurable)

## Configuration

Edit `config.py` or use environment variables:

```bash
export BURN_TEMP_THRESHOLD=95.0    # Lower threshold
export LOG_LEVEL=DEBUG              # More verbose logging
python -m smartcafe_brewmaster.api.cli check-alerts
```

## Troubleshooting

**"Database already exists"**
- Delete `data/brewmaster.db` and reinitialize
- Or use a different database path

**"No brews found"**
- Make sure you've created brews with `schedule-brew`
- Check the start time is in the past

**"Files not processed"**
- Check CSV headers: `sensor_id,observed_at,temp_c`
- Verify timestamp format is ISO8601 (e.g., `2026-03-06T10:00:00`)
- Look in `data/iot_dropbox/failed/` for error files

**"No alerts detected"**
- Try higher temperatures in CSV (>98°C)
- Ensure brew is in "brewing" status
- Run `check-alerts` manually

## Next Steps

1. **Explore the codebase**: Check `domain/`, `services/`, and `adapters/` directories
2. **Review tests**: See `tests/` for examples of using the services
3. **Extend functionality**: Add new brewing recipes, inventory types, etc.
4. **Read documentation**: See [README.md](README.md) and [DEVELOPMENT.md](DEVELOPMENT.md)
5. **Deploy**: Set environment variables for production use

## Common Workflows

### Workflow: Daily Brew Session

```bash
# Start of day
python -m smartcafe_brewmaster.api.cli ingest     # Process overnight sensor data
python -m smartcafe_brewmaster.api.cli check-alerts

# Throughout day
python -m smartcafe_brewmaster.api.cli schedule-brew "Morning Blend" 91.0 4 0
python -m smartcafe_brewmaster.api.cli start-brew 1
python -m smartcafe_brewmaster.api.cli complete-brew 1

# End of day
python -m smartcafe_brewmaster.api.cli ingest     # Final update
python -m smartcafe_brewmaster.api.cli report     # Generate daily reports
```

### Workflow: Monitor Production Brew

```bash
# Create schedule
python -m smartcafe_brewmaster.api.cli schedule-brew "Espresso" 92.0 3 0

# Start brewing
python -m smartcafe_brewmaster.api.cli start-brew 1

# Monitor (run periodically)
python -m smartcafe_brewmaster.api.cli check-alerts

# Complete
python -m smartcafe_brewmaster.api.cli complete-brew 1
```

### Workflow: Inventory Management

```bash
# Add new item
python -m smartcafe_brewmaster.api.cli inventory-add "BEAN-NEW" "New Blend" 250 grams 75

# View all
python -m smartcafe_brewmaster.api.cli inventory-list

# Run reports
python -m smartcafe_brewmaster.api.cli report
```

Happy brewing! 🍵
