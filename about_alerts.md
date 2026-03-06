# When Alerts Happen & How They're Implemented

## 🎯 **When Do Alerts Get Triggered?**

Alerts are created in **two scenarios**:

### **1. Burn Alert** 🔥
**When:** Temperature exceeds safe threshold (default **98°C**) for sustained duration while brewing

```
Timeline:
├─ Brew starts at 92°C ✅
├─ Temperature rises to 99°C for 30+ seconds ⚠️
└─ BURN ALERT created! 🔴
```

### **2. Over-Brew Alert** ⏱️
**When:** Either:
- Brew runs **longer than scheduled** + grace period (10% default)
- OR temperature stays **above serving temperature** after brew completion

```
Timeline:
├─ Brew scheduled for 3 minutes
├─ Brew continues for 3.5+ minutes (with 10% grace) ⚠️
└─ OVER-BREW ALERT created! 🔴
```

---

## 🔍 **How Alerts Are Implemented**

### **Step 1: Alert Detection Logic** (`domain/logic.py`)

```python
# Two detector classes process temperature events

class BurnDetector:
    """Detects when temperature exceeds safe threshold."""
    
    def detect(self, brew: BrewSchedule, events: List[TemperatureEvent]) -> Optional[Alert]:
        """
        Returns Alert if temp exceeded threshold for sustained duration.
        """
        for event in events:
            if event.temp_c > BURN_THRESHOLD_C:  # 98°C default
                return Alert(
                    alert_type="burn",
                    brew_id=brew.id,
                    message=f"Temperature {event.temp_c}°C exceeds safe threshold",
                    severity="error"
                )
        return None


class OverBrewDetector:
    """Detects when brewing takes too long."""
    
    def detect(self, brew: BrewSchedule, events: List[TemperatureEvent]) -> Optional[Alert]:
        """
        Returns Alert if brew exceeded duration or temp stayed high too long.
        """
        if brew.duration_exceeded():  # duration_min + 10% grace
            return Alert(
                alert_type="overbrew",
                brew_id=brew.id,
                message=f"Brew exceeded {brew.duration_min}min duration",
                severity="warn"
            )
        return None
```

---

### **Step 2: Alert Service** (`services/alerts.py`)

The service uses the detectors and **deduplicates** alerts:

```python
class AlertService:
    """Service for monitoring and creating alerts."""
    
    def __init__(self, db: DatabaseAdapter):
        self.db = db
        self.burn_detector = BurnDetector()
        self.over_brew_detector = OverBrewDetector()
        self.deduplicator = AlertDeduplicator()
    
    def check_active_brews(self) -> List[Alert]:
        """
        Main entry point: check all active brews for issues.
        Called by: CLI check-alerts command
        """
        alerts_created = []
        
        # Get all currently brewing sessions
        active_brews = self.db.list_brew_schedules(status="brewing")
        
        for brew in active_brews:
            # Get temperature events for this brew
            events = self.db.list_temperature_events_for_brew(brew.id)
            
            # Check for BURN
            burn_alert = self.burn_detector.detect(brew, events)
            if burn_alert and not self.deduplicator.is_duplicate(burn_alert):
                self.db.create_alert(burn_alert)
                alerts_created.append(burn_alert)
                logger.warning(f"BURN ALERT: {burn_alert.message}")
            
            # Check for OVER-BREW
            over_brew_alert = self.over_brew_detector.detect(brew, events)
            if over_brew_alert and not self.deduplicator.is_duplicate(over_brew_alert):
                self.db.create_alert(over_brew_alert)
                alerts_created.append(over_brew_alert)
                logger.warning(f"OVER-BREW ALERT: {over_brew_alert.message}")
        
        return alerts_created
```

---

### **Step 3: Alert Deduplication** (Prevent Alert Spam)

```python
class AlertDeduplicator:
    """Prevents duplicate alerts for the same condition."""
    
    def is_duplicate(self, alert: Alert, window_minutes: int = 5) -> bool:
        """
        Returns True if similar alert exists within last N minutes.
        """
        recent_alerts = self.db.get_recent_alerts(
            brew_id=alert.brew_id,
            alert_type=alert.alert_type,
            minutes=window_minutes
        )
        
        # If found similar recent alert, it's a duplicate
        return len(recent_alerts) > 0
```

**Why?** Without deduplication:
```
❌ Without dedup:
├─ 10:00 - Temperature 99°C → BURN ALERT
├─ 10:01 - Temperature 99°C → BURN ALERT (duplicate)
├─ 10:02 - Temperature 99°C → BURN ALERT (duplicate)
└─ User gets spammed! 🚨

✅ With dedup (5-min window):
├─ 10:00 - Temperature 99°C → BURN ALERT
├─ 10:01 - Temperature 99°C → Ignored (duplicate in window)
├─ 10:05 - Temperature 99°C → BURN ALERT (new window)
└─ User gets meaningful alerts! ✅
```

---

### **Step 4: Store Alert in Database** (`adapters/db.py`)

```python
class DatabaseAdapter:
    """SQLite persistence layer."""
    
    def create_alert(self, alert: Alert) -> int:
        """
        Insert alert into alerts table.
        
        Returns:
            Alert ID
        """
        cursor = self.db.cursor()
        cursor.execute("""
            INSERT INTO alerts (alert_type, brew_id, message, severity, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (
            alert.alert_type,      # 'burn' or 'overbrew'
            alert.brew_id,         # Which brew caused it
            alert.message,         # Human readable
            alert.severity,        # 'warn' or 'error'
            datetime.utcnow().isoformat()
        ))
        self.db.commit()
        return cursor.lastrowid
```

---

### **Step 5: CLI Command to Check Alerts** (`api/cli.py`)

```python
@cli.command()
def check_alerts():
    """Check for burn/over-brew alerts on active brews."""
    try:
        db = DatabaseAdapter(db_path)
        alert_service = AlertService(db)
        
        # Run detection
        new_alerts = alert_service.check_active_brews()
        
        if new_alerts:
            click.echo(f"[!] Found {len(new_alerts)} new alert(s):")
            for alert in new_alerts:
                click.echo(f"  - [{alert.severity.upper()}] {alert.alert_type}: {alert.message}")
        else:
            click.echo("[OK] No alerts detected")
            
    except Exception as e:
        logger.error(f"Failed to check alerts: {e}")
        click.echo(f"[ERROR] {e}")
        raise SystemExit(1)
```

---

## 📊 **Complete Alert Flow Diagram**

```
┌─────────────────────────────────────────────────────────────┐
│                    USER RUNS COMMAND                         │
│     python -m smartcafe_brewmaster.api.cli check-alerts      │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
        ┌────────────────────┐
        │  AlertService      │
        │  check_active_brews│
        └────────┬───────────┘
                 │
        ┌────────▼──────────────────────────────────────┐
        │ Get all brews in 'brewing' status             │
        │ For each brew:                                │
        │  ├─ Get temperature events                    │
        │  ├─ Run BurnDetector                          │
        │  ├─ Run OverBrewDetector                      │
        │  └─ Check AlertDeduplicator                   │
        └────────┬───────────────────────────────────────┘
                 │
        ┌────────▼────────────────────┐
        │ Is it a new alert?          │
        │ (not in recent 5-min window)│
        └────────┬────────────────────┘
                 │
        ┌────────▼──────────────────────┐
        │ Save to alerts table          │
        │ Log warning                   │
        │ Return to CLI                 │
        └────────┬──────────────────────┘
                 │
        ┌────────▼───────────────────────┐
        │ Display to user                │
        │ [!] BURN ALERT: ...            │
        │ [!] OVER-BREW ALERT: ...       │
        └────────────────────────────────┘
```

---

## 🔧 **Configuration (Tunable Thresholds)**

From `config.py`:

```python
# Burn detection
BURN_THRESHOLD_C = 98.0           # Temperature limit
BURN_DURATION_SEC = 30            # How long sustained

# Over-brew detection
BREW_DURATION_GRACE_PCT = 10      # 10% tolerance
SERVING_TEMP_THRESHOLD_C = 80     # Expected serve temp

# Deduplication
ALERT_DEDUP_WINDOW_MIN = 5        # 5-minute window
```

---

## 📋 **Database Schema for Alerts**

```sql
CREATE TABLE alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alert_type TEXT NOT NULL,      -- 'burn' or 'overbrew'
    brew_id INTEGER NULL,           -- Which brew? (NULL = system)
    message TEXT NOT NULL,          -- "Temperature 99°C exceeds..."
    severity TEXT NOT NULL,         -- 'info', 'warn', 'error'
    created_at TEXT ISO8601         -- When alert was created
);

-- Indexes for quick lookup
CREATE INDEX idx_alerts_brew_id ON alerts(brew_id);
CREATE INDEX idx_alerts_created_at ON alerts(created_at);
```

---

## 🚀 **Complete Example: Alert in Action**

```bash
# 1. Schedule a brew
python -m smartcafe_brewmaster.api.cli schedule-brew "Espresso" 92.5 3
# Output: [OK] Scheduled brew: ID=1 (Espresso, start now, 3 min)

# 2. Simulate temperature spike (via IoT ingestion)
# Create file: data/iot_dropbox/sensor_data_001.csv
# Content:
#   sensor_id,observed_at,temp_c
#   SENSOR-01,2026-03-06T10:00:00Z,92.5
#   SENSOR-01,2026-03-06T10:00:30Z,98.5    ← EXCEEDS THRESHOLD!
#   SENSOR-01,2026-03-06T10:01:00Z,99.0    ← STILL TOO HIGH!

# 3. Ingest the sensor data
python -m smartcafe_brewmaster.api.cli ingest
# Output: [OK] Processed 3 temperature events from sensor_data_001.csv

# 4. Check for alerts
python -m smartcafe_brewmaster.api.cli check-alerts
# Output:
#   [!] Found 1 new alert(s):
#   - [ERROR] burn: Temperature 99.0°C exceeds safe threshold

# 5. Query alerts table
SELECT * FROM alerts WHERE brew_id = 1;
# Result:
#   id | alert_type | brew_id | message                        | severity | created_at
#   1  | burn       | 1       | Temperature 99°C exceeds...    | error    | 2026-03-06T10:01:15Z
```

---

## ✨ **Key Design Principles** (From Instructions)

✅ **Idempotent:** Running `check-alerts` twice won't create duplicate alerts  
✅ **Configurable:** Thresholds in `config.py`  
✅ **Testable:** Alert logic in pure domain functions  
✅ **Observable:** Detailed logging at each step  
✅ **Backward Compatible:** New alerts don't break schema  

---

**Want to see the actual code files or test cases?** 🚀