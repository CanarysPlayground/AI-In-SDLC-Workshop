# SmartCafé BrewMaster – Complete Guide

## 🚀 How to Run This Code

### **Step 1: Setup Environment**
```bash
cd c:\Users\kavyashrias\AI-In-SDLC-Workshop

# Create virtual environment
python -m venv venv

# Activate it
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### **Step 2: Initialize Database**
```bash
python -m smartcafe_brewmaster.api.cli init-db
```

### **Step 3: Run Commands**
```bash

#Check what is there in the inventory
python -m smartcafe_brewmaster.api.cli inventory-list

#if already existing then insert another item

# # Add inventory Use a unique SKU each time (any one insertion)
python -m smartcafe_brewmaster.api.cli inventory-add "BEAN-001" "Ethiopian Beans" 500 grams 100

python -m smartcafe_brewmaster.api.cli inventory-add "BEAN-002" "Ethiopian Beans" 500 grams 100

python -m smartcafe_brewmaster.api.cli inventory-add "BEAN-003" "Kenyan Beans" 400 grams 80

python -m smartcafe_brewmaster.api.cli inventory-add "BEAN-004" "Colombian Beans" 600 grams 120

# Schedule a brew
python -m smartcafe_brewmaster.api.cli schedule-brew "Espresso" 92.5 3

# Check alerts
python -m smartcafe_brewmaster.api.cli check-alerts

# Generate reports
python -m smartcafe_brewmaster.api.cli report

# Process IoT sensor data
python -m smartcafe_brewmaster.api.cli ingest
```

### **Step 4: Run Tests**
```bash
pytest tests/ -v
```

---

## 📚 Application Explained Simply

### **What is SmartCafé BrewMaster?**
A system that manages a coffee machine's operations automatically. It tracks inventory, schedules brews, monitors temperature sensors, detects problems (burnt coffee, over-brewing), and generates reports.

---

### **File Structure & What Each Does**

```
smartcafe_brewmaster/
│
├── 📄 config.py
│   └── Central settings (temperature limits, thresholds, file paths)
│
├── 📁 domain/
│   ├── models.py → Pure data classes (Inventory, Brew, Alert, Temperature)
│   └── logic.py  → Smart algorithms (Burn detector, Over-brew detector)
│
├── 📁 adapters/
│   └── db.py     → SQLite database with CRUD operations
│
├── 📁 services/
│   ├── inventory.py      → Add/update/list coffee beans & supplies
│   ├── brew.py           → Schedule & track brewing sessions
│   ├── alerts.py         → Monitor & deduplicate alerts
│   ├── iot_ingestion.py  → Read temperature sensor CSV files
│   └── reports.py        → Generate CSV reports
│
├── 📁 api/
│   └── cli.py            → Command-line interface (all user commands)
│
├── 📁 sql/
│   └── schema.sql        → Database structure
│
├── 📁 tests/
│   └── *_test.py         → Unit & integration tests
│
├── 📁 data/
│   └── iot_dropbox/      → Folder where sensor data files are dropped
│
└── 📁 reports/
    └── *.csv             → Generated daily reports
```

---

### **How Data Flows Through the System**

```
1. IoT SENSORS
   ↓ (CSV files dropped in /data/iot_dropbox/)
   
2. IOT_INGESTION_SERVICE
   ├─ Reads CSV: sensor_id, observed_at, temp_c
   ├─ Validates data
   └─ Writes to database
   
3. DATABASE (SQLite)
   ├─ Stores: temperature events, brews, alerts, inventory
   
4. ALERT SERVICE
   ├─ Monitors: Is temperature too high? (BURN)
   ├─ Checks: Did brewing take too long? (OVER-BREW)
   └─ Creates alerts
   
5. REPORT SERVICE
   └─ Generates CSV files: inventory, brews, alerts
   
6. CLI (User Interface)
   └─ All commands go here
```

---

## 🖥️ **API Only vs UI**

### **Currently: API Only (CLI)**
- ✅ **Command-line interface** for developers/scripts
- ✅ Can be called from automation tools, bash scripts, or other programs
- ❌ **No web UI** (no browser interface yet)
- ❌ **No REST API** (no HTTP endpoints yet)

**Example:**
```bash
# This is how you interact with the system
python -m smartcafe_brewmaster.api.cli inventory-add "BEAN-001" "Coffee" 500 grams 100
```

---

## 💻 **Tech Stack**

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Language** | Python 3.9+ | Core application |
| **Database** | SQLite | Persistent storage |
| **Data Format** | CSV | IoT sensor files |
| **CLI Framework** | Click | Command-line interface |
| **Testing** | pytest | Unit & integration tests |
| **Logging** | Python logging | Debug & monitoring |
| **Data Models** | dataclasses | Type-safe objects |

**Why this stack?**
- ✅ **Lightweight** (no heavy framework)
- ✅ **Easy to extend** (modular design)
- ✅ **Perfect for MVP** (fast to build)
- ✅ **Ready for scale** (can add REST API, web UI, ML later)

---

## 🚀 **Future Improvements**

### **Phase 2: Add a Web UI**
```python
# Add Flask or FastAPI REST endpoints
POST /api/inventory
GET /api/brews
GET /api/alerts
# Then build React/Vue frontend
```

### **Phase 3: ML & Intelligence**
- 📊 **Usage predictions**: "You'll need more beans in 3 days"
- 🤖 **Anomaly detection**: Detect machines getting old/worn
- 🌟 **Flavor recommendations**: "This bean works best at 93°C"

### **Phase 4: Advanced Features**
- 📱 **Mobile app** (notifications about alerts)
- 🔌 **Real IoT devices** (not just CSV files)
- 📈 **Historical analytics** (trends & patterns)
- 🔐 **User authentication** (multiple operators)
- ☁️ **Cloud sync** (backup & multi-location)

### **Phase 5: Operations**
- 🐳 **Docker containerization**
- ☁️ **Deploy to AWS/Azure**
- 📊 **Prometheus metrics** (monitoring)
- 🔄 **Automated backups**

---

## 📋 **Quick Feature Checklist**

| Feature | Status |
|---------|--------|
| ✅ Inventory tracking | **Done** |
| ✅ Brew scheduling | **Done** |
| ✅ Temperature monitoring | **Done** |
| ✅ Burn detection | **Done** |
| ✅ Over-brew detection | **Done** |
| ✅ CSV reports | **Done** |
| ✅ CLI interface | **Done** |
| ❌ Web UI | **Future** |
| ❌ REST API | **Future** |
| ❌ ML predictions | **Future** |
| ❌ Mobile app | **Future** |

---

## 🎯 **What to Build Next**

If you want to extend this immediately, I recommend:

1. **Add REST API** (15 min)
   ```bash
   pip install fastapi uvicorn
   # Create api/rest.py with GET/POST endpoints
   ```

2. **Add Web Dashboard** (2-3 hours)
   ```bash
   # Use Streamlit (easiest) or Flask + HTML
   # Show real-time alerts & inventory
   ```

3. **Add Email Alerts** (30 min)
   ```bash
   pip install smtplib
   # Send alert emails when burn detected
   ```

Would you like me to **build any of these improvements**? 🚀