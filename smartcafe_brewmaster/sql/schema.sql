-- SmartCafé BrewMaster Database Schema
-- SQLite schema for MVP
-- This schema is a contract and must not be changed destructively

CREATE TABLE IF NOT EXISTS inventory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_sku TEXT UNIQUE NOT NULL,
    item_name TEXT NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 0,
    unit TEXT NOT NULL,
    reorder_level INTEGER NOT NULL DEFAULT 0,
    updated_at TEXT NOT NULL  -- ISO8601 UTC
);

CREATE TABLE IF NOT EXISTS brew_schedule (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recipe_name TEXT NOT NULL,
    start_time TEXT NOT NULL,  -- ISO8601 UTC
    target_temp_c REAL NOT NULL,
    duration_min INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'scheduled',  -- scheduled|brewing|done|canceled
    created_at TEXT NOT NULL  -- ISO8601 UTC
);

CREATE TABLE IF NOT EXISTS temperature_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sensor_id TEXT NOT NULL,
    brew_id INTEGER,
    observed_at TEXT NOT NULL,  -- ISO8601 UTC
    temp_c REAL NOT NULL,
    raw_file TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alert_type TEXT NOT NULL,  -- burn|overbrew|system
    brew_id INTEGER,
    message TEXT NOT NULL,
    severity TEXT NOT NULL,  -- info|warn|error
    created_at TEXT NOT NULL  -- ISO8601 UTC
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_inventory_sku ON inventory(item_sku);
CREATE INDEX IF NOT EXISTS idx_brew_schedule_status ON brew_schedule(status);
CREATE INDEX IF NOT EXISTS idx_brew_schedule_start_time ON brew_schedule(start_time);
CREATE INDEX IF NOT EXISTS idx_temperature_events_observed_at ON temperature_events(observed_at);
CREATE INDEX IF NOT EXISTS idx_temperature_events_sensor_id ON temperature_events(sensor_id);
CREATE INDEX IF NOT EXISTS idx_temperature_events_brew_id ON temperature_events(brew_id);
CREATE INDEX IF NOT EXISTS idx_alerts_brew_id ON alerts(brew_id);
CREATE INDEX IF NOT EXISTS idx_alerts_created_at ON alerts(created_at);
CREATE INDEX IF NOT EXISTS idx_alerts_alert_type ON alerts(alert_type);
