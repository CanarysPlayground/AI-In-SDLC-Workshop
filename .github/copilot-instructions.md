# SmartCafé BrewMaster – Copilot Custom Instructions

These instructions tell GitHub Copilot how to generate code, tests, and docs for the **SmartCafé BrewMaster** application.  
We’re building a greenfield MVP **now**, with a plan to **enhance later** without breaking core behaviors.

Copilot MUST follow the sections below.

---

## 1) Project Mission & Scope

**Build first, extend safely later.**  
Initial MVP includes:

- **Inventory tracking**
- **Brew scheduling**
- **IoT temperature sensor ingestion (drop-folder)**
- **Burn/over‑brew alerts**
- **Static reports (CSV)**

Later enhancements (do NOT implement yet, but keep the design extensible for):

- Usage & refill predictions
- Anomaly intelligence
- Flavor recommendations
- Maintenance guidance

---

## 2) Architecture Guardrails (Brownfield-friendly from Day 1)

- Treat the MVP’s **public interfaces, database schema, and file formats as contracts** for future compatibility.
- **Do not** rewrite core modules once established; add new features via **extension points** (adapters, services, or sidecars).
- Keep IoT ingestion **file-based drop-folder** as the canonical interface.
- Separate **domain logic** from **IO/adapters** to make testing and future ML plug-in easy.

**Recommended initial structure**

``

## 3) Data Contracts (SQLite) — Define Once, Don’t Break

The **SQLite schema is fixed** once created. Copilot MUST NOT change columns/types in later work.  
All evolutions must use **new tables** or **views**—never destructive changes.

**Initial schema (minimal & pragmatic):**

- `inventory`  
  - `id` (INTEGER PK AUTOINCREMENT)  
  - `item_sku` (TEXT UNIQUE NOT NULL)  
  - `item_name` (TEXT NOT NULL)  
  - `quantity` (INTEGER NOT NULL DEFAULT 0)  
  - `unit` (TEXT NOT NULL)                # e.g., grams, ml, units
  - `reorder_level` (INTEGER NOT NULL DEFAULT 0)
  - `updated_at` (TEXT ISO8601)

- `brew_schedule`  
  - `id` (INTEGER PK AUTOINCREMENT)  
  - `recipe_name` (TEXT NOT NULL)  
  - `start_time` (TEXT ISO8601 NOT NULL)  
  - `target_temp_c` (REAL NOT NULL)  
  - `duration_min` (INTEGER NOT NULL)  
  - `status` (TEXT NOT NULL DEFAULT 'scheduled')  # scheduled|brewing|done|canceled
  - `created_at` (TEXT ISO8601)

- `temperature_events`  
  - `id` (INTEGER PK AUTOINCREMENT)  
  - `sensor_id` (TEXT NOT NULL)  
  - `brew_id` (INTEGER NULL)              # optional association
  - `observed_at` (TEXT ISO8601 NOT NULL)  
  - `temp_c` (REAL NOT NULL)  
  - `raw_file` (TEXT NOT NULL)            # filename ingested

- `alerts`  
  - `id` (INTEGER PK AUTOINCREMENT)  
  - `alert_type` (TEXT NOT NULL)          # burn|overbrew|system
  - `brew_id` (INTEGER NULL)
  - `message` (TEXT NOT NULL)
  - `severity` (TEXT NOT NULL)            # info|warn|error
  - `created_at` (TEXT ISO8601)

**Rules:**
- Use **UTC ISO8601** timestamps everywhere.
- Use **foreign keys** only if needed; otherwise keep loose coupling (ids only).
- Add **indexes** on frequent filters (e.g., `temperature_events(observed_at)`, `brew_schedule(status)`).

---

## 4) IoT Ingestion Contract (Drop-Folder)

- Copilot MUST implement a **watcher** that reads new files from `/data/iot_dropbox`.
- File format (MVP): **CSV** with headers: `sensor_id,observed_at,temp_c`  
  - `observed_at` is ISO8601 UTC.
- On successful parse, write each row into `temperature_events` and move the file to `/data/iot_dropbox/processed/` (or `/failed/` with error log).
- The folder path is **configurable**, but the ingestion method **must remain drop-folder based**.

---

## 5) Alerts Logic (Burn / Over‑Brew)

- **Burn alert**: temp exceeds a safe threshold (default 98°C) for > N seconds while a brew is active.
- **Over-brew alert**: brew active beyond scheduled `duration_min` + grace (default 10%) **or** temperature stays above serving band after brew completion.
- Thresholds are **configurable** via `config.py` (but defaults must be safe).
- Alerts must be **idempotent** for the same condition window—avoid duplicate spam.

---

## 6) Reports (CSV)

- Generate **static CSV** reports to `/reports`:
  - `inventory_snapshot_YYYYMMDD.csv`
  - `brew_runs_YYYYMMDD.csv` (start, end, avg/max temp, over-brew flag)
  - `alerts_YYYYMMDD.csv`
- Reports must be reproducible (pure reads), and NEVER mutate data.

---

## 7) General Coding Standards (Python)

- Follow **PEP 8**.
- Use **descriptive variable and function names**.
- Include **docstrings** for all functions and classes (Google or NumPy style).
- Type hints for public functions.
- Prefer **pure functions** in `/domain`.
- Avoid global state; use constructor or function injection.
- Log with structured context (adapter-level logger).

---

## 8) Testing Standards

- **Unit tests** for domain logic and services.
- **Integration tests** for DB adapters and ingestion flow (temp dirs/files).
- Use **pytest**; aim for meaningful coverage of critical paths.
- Use **mocks/stubs** for time (`time_provider`) and filesystem where appropriate.
- Test **idempotency** for ingestion and alerts.
- New features MUST include unit tests.

---

## 9) Copilot Generation Rules (What to Prefer / Avoid)

**Prefer**
- Small, single-responsibility modules.
- Dependency-injected adapters (pass `db`, `clock`, `logger`, `paths`).
- Explicit data models (dataclasses or pydantic if already in deps).
- Configuration via `config.py` (env‑overrides ok).
- Safe migrations: **append-only** changes to schema via new SQL script files.

**Avoid**
- Changing established table schemas or meaning of columns.
- Embedding file paths or secrets inline; use config.
- Tight coupling between domain and IO classes.
- Long functions (> 40–50 lines) without clear structure.

---

## 10) Developer Experience & Commands

- Provide a **CLI** entry (in `/api/cli.py`) for:
  - `init-db` – run `sql/schema.sql`
  - `ingest` – process `/data/iot_dropbox`
  - `report` – emit today’s CSVs
  - `schedule` – add/list/update schedules
- Add `README.md` snippets showing example usage.
- Add `Makefile` (optional): `setup`, `test`, `run`.

---

## 11) Observability

- Use adapter-level logging: ingestion start/end, files processed, rows inserted, alerts emitted.
- Include correlation fields (file name, brew_id, sensor_id) in logs.
- Errors should be actionable with clear messages and next steps.

---

## 12) Security & Operations

- Fail closed on malformed input (send file to `/failed` + log).
- Don’t execute arbitrary code from ingestion files.
- Handle partial failures (one bad row shouldn’t drop entire file unless configured).
- Respect least privilege for file operations.

---

## 13) Backward Compatibility Promise

Once the MVP ships:
- **Do not** change:
  - IoT file headers/semantics
  - SQLite schema (no destructive edits)
  - Report filenames/columns
- Future intelligence (predictions/recommendations) must be **adjacent modules** reading current DB and emitting new tables or files—not breaking existing ones.

---

## 14) Commit & PR Hygiene (recommended)

- Conventional commits: `feat:`, `fix:`, `chore:`, `docs:`, `test:`, `refactor:`.
- PRs must include:
  - Summary, scope, risks
  - Any schema changes (new files only)
  - Tests included

---

## 15) Quick Start Epics for Copilot

- **Epic A: Inventory**
  - CRUD services, validation, reorder calculations, snapshot CSV.

- **Epic B: Brew Scheduling**
  - Create/list/update timelines, status transitions, time-based checks.

- **Epic C: IoT Ingestion**
  - Watch folder, parse CSV, insert events, processed/failed routing, logs.

- **Epic D: Alerts**
  - Burn/over‑brew detectors, de-duplication, persisted alerts.

- **Epic E: Reports**
  - Inventory snapshot, brew runs summary, alerts export.

---

## 16) Summary for Copilot

**Goal:** Build a clean MVP that is safe to evolve.  
**Never break:** SQLite schema, IoT drop-folder contract, report formats.  
**Always:** Keep core logic pure, add-on features modular, and code well‑tested and documented.
