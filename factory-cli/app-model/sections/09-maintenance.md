---
title: "Maintenance — Jivo Mart app-model"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: reference
tags: [jivogpt, factory-cli, maintenance]
---

# Maintenance — Jivo Mart app-model

> **Provenance — imported 2026-07-19; source snapshot 2026-06-30.** This note came from the JIVO_MART-only `daman8271/jivo-factory-intel` baseline. For the current three-company study and the live-verified 2026-07-19 state, use [[docs/factory/FACTORY_MAP|FACTORY_MAP]] and [[CLI/factory-cli/README|the current CLI guide]].
> COMPLETED: Jivo Mart (JIVO_MART) only. All API calls verified 2026-06-30.

## 1. Purpose — what this section is for in the factory

The Maintenance module is a full-featured Computerized Maintenance Management System (CMMS) embedded inside the Jivo factory app. Its purpose is to:

- **Register and track every physical asset** on the factory floor in a hierarchy (Plant → Area → Line → Machine → Component → Utility), with documents (manuals, AMC agreements, warranties, calibration records, service reports) and photos attached.
- **Issue and manage work orders** across all maintenance types: breakdown repair, general maintenance, preventive maintenance, inspection, calibration, AMC/vendor visits, and projects/improvements. Work orders track status from draft through to closure, record production impact (no impact / reduced performance / production stoppage / safety risk), and carry before/after photos.
- **Run a Preventive Maintenance (PM) programme**: define PM plans (per asset, per frequency), auto-generate due work orders from those plans, execute them via checklists (checkbox / pass-fail / number / text inputs), and track PM compliance.
- **Manage spare parts inventory**: maintain a spare parts catalogue (with spare categories), track stock levels, raise spare requests from work orders, record inward/outward/consume/return stock movements, and alert when stock falls below minimum.
- **Schedule and track vendor AMC/service visits** for equipment covered by Annual Maintenance Contracts or warranty.
- **Generate reports** (daily and monthly) covering work order completion rate, breakdown count, production downtime, average MTTR (mean time to repair), average MTBF (mean time between failures), PM compliance %, and spare consumption cost.
- **Provide a real-time dashboard** summarising all of the above, plus an alert centre for critical events.
- **Support mobile scan workflows**: operators scan asset or spare QR codes on the shop floor to pull up asset/work-order information instantly, and mark work-order status updates via scan.

For JIVO_MART as of 2026-06-30, the module is fully built and configured on the API side (all status enums, hierarchy levels, and option lists are live) but **no master data has been entered yet** — no assets, no spares, no PM plans, no work orders. The module is production-ready but awaits onboarding.

---

## 2. Page tree

```
/maintenance                              — Module root / splash
│
├── /maintenance/dashboard/               — Live dashboard: KPI cards + activity feeds
├── /maintenance/alerts/                  — Alert centre: active critical alerts
├── /maintenance/automation               — Frontend-only automation rules page
│                                           (no backing API endpoint — /automation path
│                                           returns HTTP 404 at the API level)
│
├── /maintenance/masters                  — Master data hub (nav to sub-pages)
│   ├── /maintenance/asset-categories/   — Asset category management list + add
│   ├── /maintenance/asset-departments/  — Asset department management list + add
│   └── /maintenance/asset-locations/    — Asset location management list + add
│
├── /maintenance/assets                   — Asset register list view
│   ├── /maintenance/assets/             — Asset list with filters (status, dept, category, line)
│   │   └── [CREATE FORM]               — New asset wizard (inline on this page)
│   ├── /maintenance/assets/:assetId     — Asset detail page
│   │   ├── Overview / info tab         — Nameplate data, status, hierarchy, AMC/warranty
│   │   ├── Documents tab               — Linked asset documents
│   │   ├── Photos tab                  — Asset photos
│   │   ├── Work Orders tab             — Work orders for this asset
│   │   └── PM Plans tab                — Preventive maintenance plans for this asset
│   ├── /maintenance/asset-documents/   — All asset documents (cross-asset list)
│   ├── /maintenance/asset-photos/      — All asset photos (cross-asset list)
│   └── /maintenance/options/           — Configuration options reference (enum lookups,
│                                          user list, category/location/dept dropdowns)
│
├── /maintenance/pm                       — Preventive Maintenance hub
│   ├── /maintenance/pm-plans/           — PM plan list (one plan per asset per frequency)
│   │   └── /maintenance/pm-plans/generate-due/  — POST action: generates due work orders
│   │                                              from all active PM plans
│   ├── /maintenance/pm-checklist-items/ — PM checklist item templates
│   └── /maintenance/pm-executions/     — PM execution log (one per work order, per plan run)
│
├── /maintenance/work-orders             — Work order pipeline / kanban
│   ├── /maintenance/work-orders/       — Work order list with filters (status, type, priority, dept)
│   │   └── [CREATE FORM]              — New work order form
│   ├── /maintenance/work-orders/:workOrderId — Work order detail
│   │   ├── Info tab                   — Type, asset, priority, impact, description
│   │   ├── Assignment tab             — Technician assigned, estimated time
│   │   ├── Spare Requests tab         — Spares requested for this WO
│   │   ├── Photos tab                 — Before/after/general photos
│   │   └── Timeline tab               — Status history log
│   └── /maintenance/work-order-photos/ — All work-order photos (cross-WO list)
│
├── /maintenance/spares                   — Spare parts inventory hub
│   ├── /maintenance/spares/            — Spare parts catalogue list with filters
│   ├── /maintenance/spares/low-stock/  — Spares below minimum stock threshold
│   ├── /maintenance/spares/stock/      — Individual spare stock detail (by code/ID)
│   ├── /maintenance/spare-categories/  — Spare category management list + add
│   ├── /maintenance/spare-movements/   — Spare stock movement log (all inward/issue/consume/return/adjust)
│   └── /maintenance/spare-requests/   — Spare requests raised from work orders
│
├── /maintenance/vendor-visits/          — AMC / vendor service visit list + scheduling
│
├── /maintenance/reports                  — Reports hub
│   └── /maintenance/reports/           — Maintenance reports (daily / monthly toggle)
│
└── /maintenance/scan                     — Mobile scan entry points
    ├── /maintenance/scan/lookup/        — GET: look up an asset or spare by QR/barcode code
    └── /maintenance/scan/work-order/   — POST: update work-order status via scan
```

---

## 3. Per-page detail

### 3.1 Dashboard (`/maintenance/dashboard/`)

**Purpose:** Real-time KPI hub for the maintenance manager. Aggregates data across all sub-modules into one view.

**API endpoint:** `GET /maintenance/dashboard/`
**Supports filters:** `?department=`, `?line=`, `?priority=`, `?date_from=`, `?date_to=`

**Data sections returned (from live API call, 2026-06-30):**

| Section | Fields | Description |
|---|---|---|
| `assets` | total, active, inactive, by_status{}, breakdown, under_pm, under_repair | Asset status breakdown counts |
| `masters` | categories, locations, departments | Master data record counts |
| `work_orders` | total, open, assigned, in_progress, completed, waiting_spare, waiting_vendor, critical, breakdowns, by_status{} | Work order pipeline counts |
| `breakdowns` | open, critical, in_progress, stoppage | Breakdown-specific counts |
| `pm` | open, due_today, overdue, completed_due, due_total, compliance_percent | PM plan execution KPIs |
| `today_tasks` | total, overdue, high_priority, items[] | Today's pending maintenance tasks |
| `production_downtime` | total_minutes, active_breakdowns, impacted_runs, stoppage_work_orders | Production impact metrics |
| `spares` | total, critical, low_stock, below_minimum, critical_shortage | Spare parts stock health |
| `spare_risk` | low_stock, below_minimum, critical_shortage, shortage_qty, items[] | Specific at-risk spares list |
| `vendor_amc` | due_visits, overdue_visits, amc_due, amc_overdue, warranty_due, warranty_expired, visits[], amc_assets[] | Vendor AMC and warranty status |
| `open_breakdowns` | [] | Active breakdown work orders (abbreviated cards) |
| `pm_due_work_orders` | [] | PM work orders due today/overdue (abbreviated cards) |
| `recent_assets` | [] | Recently added/modified assets |
| `recent_work_orders` | [] | Recently created work orders |
| `low_stock_spares` | [] | Items below minimum stock level |

**Live sample (Jivo Mart, 2026-06-30):**
```json
{
  "assets": {"total": 0, "active": 0, "breakdown": 0, "under_pm": 0},
  "masters": {"categories": 0, "locations": 0, "departments": 0},
  "work_orders": {"total": 0, "open": 0, "completed": 0, "critical": 0},
  "pm": {"open": 0, "due_today": 0, "overdue": 0, "compliance_percent": null},
  "production_downtime": {"total_minutes": 0, "active_breakdowns": 0, "impacted_runs": 0},
  "spares": {"total": 0, "low_stock": 0, "critical_shortage": 0}
}
```
All counters are zero — the module is not yet populated for Jivo Mart.

---

### 3.2 Alert Centre (`/maintenance/alerts/`)

**Purpose:** Shows time-stamped alerts for critical events (e.g. overdue breakdown, spare stock critical, PM overdue). Used as a notification inbox for maintenance supervisors.

**API endpoint:** `GET /maintenance/alerts/`

**Key fields:** `generated_at`, `total` (count), `counts` (dict of alert type → count), `alerts[]` (list of alert objects).

**Live sample (2026-06-30):**
```json
{
  "generated_at": "2026-06-30 01:18",
  "counts": {},
  "total": 0,
  "alerts": []
}
```
No alerts generated — expected since no assets or work orders exist.

---

### 3.3 Masters (`/maintenance/masters`, `/maintenance/asset-categories/`, `/maintenance/asset-departments/`, `/maintenance/asset-locations/`)

**Purpose:** Pre-requisite configuration that must be set up before assets can be registered. Masters define the classification taxonomy for the asset register.

| Page | API endpoint | Purpose |
|---|---|---|
| Asset categories | `GET /maintenance/asset-categories/` | Type of asset (e.g. "Filling Machine", "Boiler", "Conveyor") |
| Asset departments | `GET /maintenance/asset-departments/` | Owning department (e.g. "Production", "Utilities", "Engineering") |
| Asset locations | `GET /maintenance/asset-locations/` | Physical location in the plant (e.g. "Line 1", "Boiler Room", "Warehouse") |

**Key fields (inferred from options and endpoint naming):** `id`, `name`, and for locations: `parent` (supports nested hierarchy).

**Live data for Jivo Mart:** All three endpoints return empty `[]`. No categories, departments, or locations have been defined yet. The `options` endpoint confirms this: `"categories": [], "locations": [], "departments": []`.

---

### 3.4 Asset Register (`/maintenance/assets/`, `/maintenance/assets/:assetId`)

**Purpose:** The central register of all physical assets at the factory. Each asset is a node in the 6-level physical hierarchy (Plant → Area → Line → Machine → Component → Utility). Tracks nameplate data, operational status, AMC/warranty cover, and links to work orders, PM plans, documents, and photos.

**API endpoints:**
- `GET /maintenance/assets/` — paginated list with filters: `?status=`, `?department=`, `?category=`, `?line=`, `?search=`
- `GET /maintenance/assets/:assetId` — single asset detail
- `GET /maintenance/asset-documents/` — all documents across all assets
- `GET /maintenance/asset-photos/` — all photos across all assets

**Asset statuses** (from `/maintenance/options/`):

| Value | Label |
|---|---|
| RUNNING | Running |
| IDLE | Idle |
| BREAKDOWN | Breakdown |
| UNDER_PM | Under PM |
| UNDER_REPAIR | Under Repair |
| RETIRED | Retired |

**Hierarchy levels** (from `/maintenance/options/`):

| Value | Label |
|---|---|
| PLANT | Plant |
| AREA | Area |
| LINE | Line |
| MACHINE | Machine |
| COMPONENT | Component |
| UTILITY | Utility |

**Asset document types** (from `/maintenance/options/`):

| Value | Label |
|---|---|
| MANUAL | Manual |
| WARRANTY | Warranty |
| AMC | AMC |
| SERVICE_REPORT | Service Report |
| CALIBRATION | Calibration |
| OTHER | Other |

**Expected key fields (from API error messages and options schema):** `id`, `code` (asset code / QR-scannable), `name`, `hierarchy_level`, `parent_asset`, `category`, `department`, `location`, `status`, `make`, `model`, `serial_no`, `purchase_date`, `installation_date`, `amc_start_date`, `amc_end_date`, `warranty_expiry`, `description`.

**Live data for Jivo Mart:** `GET /maintenance/assets/` returns `[]`. `GET /maintenance/assets/1/` returns `{"detail": "No Asset matches the given query."}`. No assets registered.

---

### 3.5 Options (`/maintenance/options/`)

**Purpose:** Returns all enumeration lists and reference data used to populate dropdowns in work order, PM plan, spare, and asset forms. Also returns the live factory user list (for assignment) and linked production machines. This is not a user-facing page but is loaded on form open.

**API endpoint:** `GET /maintenance/options/`

**Complete enum groups returned:**

| Field | Values |
|---|---|
| `statuses` | RUNNING, IDLE, BREAKDOWN, UNDER_PM, UNDER_REPAIR, RETIRED |
| `priorities` | NORMAL, HIGH, CRITICAL |
| `pm_frequencies` | DAILY, WEEKLY, MONTHLY, QUARTERLY, HALF_YEARLY, YEARLY |
| `pm_execution_statuses` | PENDING, IN_PROGRESS, COMPLETED, SKIPPED, OVERDUE |
| `checklist_input_types` | CHECKBOX, PASS_FAIL, NUMBER, TEXT |
| `hierarchy_levels` | PLANT, AREA, LINE, MACHINE, COMPONENT, UTILITY |
| `document_types` | MANUAL, WARRANTY, AMC, SERVICE_REPORT, CALIBRATION, OTHER |
| `work_types` | COMPLAINT, BREAKDOWN, GENERAL, PREVENTIVE, INSPECTION, CALIBRATION, AMC_VENDOR, PROJECT |
| `work_statuses` | DRAFT, OPEN, ASSIGNED, IN_PROGRESS, WAITING_SPARE, WAITING_VENDOR, ON_HOLD, COMPLETED, APPROVED, CLOSED |
| `work_impacts` | NO_IMPACT, DEGRADED, STOPPAGE, SAFETY_RISK |
| `work_photo_types` | BEFORE, AFTER, GENERAL |
| `spare_request_statuses` | REQUESTED, PARTIALLY_ISSUED, ISSUED, PARTIALLY_CONSUMED, CLOSED, CANCELLED |
| `spare_movement_types` | RECEIPT, ISSUE, CONSUME, RETURN, ADJUSTMENT |
| `gate_qc_statuses` | NOT_REQUIRED, PENDING, ACCEPTED, REJECTED, WAIVED |
| `gate_receipt_statuses` | NOT_RECEIVED, RECEIVED, BLOCKED |
| `vendor_visit_statuses` | PLANNED, IN_PROGRESS, COMPLETED, CANCELLED |

**User list (live, 43 active factory users):** Includes EP-prefixed codes (full-time employees) and JWPL-prefixed codes (Jivo workers/plant laborers). Sample users:

| id | full_name | employee_code |
|---|---|---|
| 11 | Arvind | JWPL2783 |
| 19 | Bhupinder Singh | EP000 |
| 28 | Amit Pal Singh | EP1235 |
| 38 | Deepak | DEEPAK |
| 44 | Harpreet Singh | EP123 |

**Also returns (currently empty):** `categories: []`, `locations: []`, `departments: []`, `spare_categories: []`, `production_machines: []`.

---

### 3.6 PM Plans (`/maintenance/pm-plans/`, `/maintenance/pm-executions/`, `/maintenance/pm-checklist-items/`)

**Purpose:** Preventive Maintenance planning. A PM plan ties an asset to a maintenance frequency and a checklist; the system auto-generates due work orders on schedule.

**API endpoints:**
- `GET /maintenance/pm-plans/` — list all PM plans (filterable by asset, frequency)
- `POST /maintenance/pm-plans/generate-due/` — trigger generation of due work orders from plans (action endpoint; GET not allowed)
- `GET /maintenance/pm-executions/` — log of all executed (or pending) PM plan runs
- `GET /maintenance/pm-checklist-items/` — checklist item templates attached to PM plans

**PM frequencies:** DAILY, WEEKLY, MONTHLY, QUARTERLY, HALF_YEARLY, YEARLY

**PM execution statuses:** PENDING, IN_PROGRESS, COMPLETED, SKIPPED, OVERDUE

**Checklist input types:** CHECKBOX, PASS_FAIL, NUMBER, TEXT (e.g. "Check oil level" = PASS_FAIL; "Temperature reading" = NUMBER)

**Expected key fields for a PM Plan:** `id`, `asset`, `frequency`, `last_executed_at`, `next_due_at`, `checklist_items[]` (each: question text, input_type, is_mandatory).

**Live data for Jivo Mart:** All three endpoints return `[]`. The `generate-due/` endpoint is a POST-only action (returns 405 on GET). No PM plans configured.

---

### 3.7 Work Orders (`/maintenance/work-orders/`, `/maintenance/work-orders/:workOrderId`)

**Purpose:** The core operational record of the Maintenance module. A work order is raised whenever maintenance activity is needed — manually (breakdown complaint, scheduled PM, project) or auto-generated from a PM plan. It tracks the complete lifecycle from draft to closure.

**API endpoints:**
- `GET /maintenance/work-orders/` — paginated list; filters: `?status=`, `?work_type=`, `?priority=`, `?asset=`, `?department=`, `?date_from=`, `?date_to=`, `?search=`
- `GET /maintenance/work-orders/:workOrderId` — full detail record
- `GET /maintenance/work-order-photos/` — all photos across all work orders

**Work order types:**

| Value | Label |
|---|---|
| COMPLAINT | Complaint |
| BREAKDOWN | Breakdown |
| GENERAL | General Maintenance |
| PREVENTIVE | Preventive Maintenance |
| INSPECTION | Inspection |
| CALIBRATION | Calibration |
| AMC_VENDOR | AMC / Vendor Visit |
| PROJECT | Project / Improvement |

**Work order statuses:**

| Value | Label | Description |
|---|---|---|
| DRAFT | Draft | Not yet submitted |
| OPEN | Open | Submitted, awaiting assignment |
| ASSIGNED | Assigned | Technician assigned, not started |
| IN_PROGRESS | In Progress | Work underway |
| WAITING_SPARE | Waiting Spare | Blocked on spare parts |
| WAITING_VENDOR | Waiting Vendor | Blocked on vendor/AMC visit |
| ON_HOLD | On Hold | Manually paused |
| COMPLETED | Completed | Work done, awaiting approval |
| APPROVED | Approved | Supervisor approved completion |
| CLOSED | Closed | Fully closed out |

**Production impact levels:**

| Value | Label |
|---|---|
| NO_IMPACT | No Production Impact |
| DEGRADED | Reduced Performance |
| STOPPAGE | Production Stoppage |
| SAFETY_RISK | Safety Risk |

**Photo types:** BEFORE (before repair), AFTER (after repair), GENERAL

**Expected key fields for a Work Order:** `id`, `work_order_no`, `work_type`, `status`, `priority` (NORMAL/HIGH/CRITICAL), `asset` (FK), `department`, `description`, `production_impact`, `assigned_to` (User FK), `estimated_minutes`, `actual_minutes`, `started_at`, `completed_at`, `closed_at`, `spare_requests[]`, `photos[]`, `status_history[]`.

**Live data for Jivo Mart:** `GET /maintenance/work-orders/` returns `[]` for all status filters (DRAFT through CLOSED). `GET /maintenance/work-orders/1/` returns `{"detail": "No MaintenanceWorkOrder matches the given query."}`. No work orders exist.

---

### 3.8 Spare Parts (`/maintenance/spares/`, `/maintenance/spare-categories/`, `/maintenance/spare-movements/`, `/maintenance/spare-requests/`)

**Purpose:** Manages the maintenance storeroom — tracks which spare parts are held, their minimum stock levels, and all inward/outward movements. Spare requests are linked to specific work orders, so consumption is traceable to the maintenance job.

**API endpoints:**
- `GET /maintenance/spares/` — spare parts catalogue list (filterable by category, low-stock)
- `GET /maintenance/spares/low-stock/` — spares where current stock ≤ minimum level
- `GET /maintenance/spares/stock/` — stock detail for one spare (requires `?code=` param; returns 404 if spare not found)
- `GET /maintenance/spare-categories/` — spare part category list (e.g. "Bearings", "Belts", "Seals")
- `GET /maintenance/spare-movements/` — full movement log (RECEIPT / ISSUE / CONSUME / RETURN / ADJUSTMENT)
- `GET /maintenance/spare-requests/` — requests raised from work orders

**Spare movement types:**

| Value | Label | Triggered by |
|---|---|---|
| RECEIPT | Receipt from Gate | Spare received at factory gate (links to Gate/QC section) |
| ISSUE | Issue to Work Order | Spare taken from store for a WO |
| CONSUME | Consume on Work Order | Spare actually consumed during repair |
| RETURN | Return Unused Spare | Unused spare returned to store |
| ADJUSTMENT | Stock Adjustment | Manual correction |

**Spare request statuses:** REQUESTED → PARTIALLY_ISSUED → ISSUED → PARTIALLY_CONSUMED → CLOSED (or CANCELLED)

**Gate integration fields** (on spare receipt): `gate_qc_status` (NOT_REQUIRED / PENDING / ACCEPTED / REJECTED / WAIVED), `gate_receipt_status` (NOT_RECEIVED / RECEIVED / BLOCKED) — the spare's inward gate receipt and QC inspection flows through the same gate/QC pipeline used for raw materials.

**Expected key fields for a Spare:** `id`, `code` (QR-scannable), `name`, `category`, `unit`, `current_stock`, `minimum_stock`, `location` (bin/rack in storeroom), `unit_cost`, `supplier`.

**Live data for Jivo Mart:** All spare endpoints return `[]`. `GET /maintenance/spares/stock/` without a valid code returns `{"detail": "Spare was not found for the selected code."}`. `GET /maintenance/spare-categories/` returns `[]`. The options endpoint confirms `spare_categories: []`. No spare parts configured.

---

### 3.9 Vendor Visits (`/maintenance/vendor-visits/`)

**Purpose:** Schedules and tracks visits from external service vendors — for AMC (Annual Maintenance Contract) servicing, warranty repairs, or one-off technical visits. Linked to specific assets.

**API endpoint:** `GET /maintenance/vendor-visits/`

**Vendor visit statuses:** PLANNED, IN_PROGRESS, COMPLETED, CANCELLED

**Expected key fields:** `id`, `visit_no`, `asset` (FK), `vendor_name`, `visit_type` (AMC / WARRANTY / GENERAL), `planned_date`, `actual_date`, `status`, `technician_name`, `observations`, `next_visit_date`.

**Live data for Jivo Mart:** Returns `[]`. The dashboard's `vendor_amc` section also shows all zeros: `{due_visits: 0, overdue_visits: 0, amc_due: 0, amc_overdue: 0, warranty_due: 0, warranty_expired: 0, visits: [], amc_assets: []}`.

---

### 3.10 Reports (`/maintenance/reports/`)

**Purpose:** Generates daily or monthly maintenance reports summarising work order performance, breakdown metrics, PM compliance, spare consumption costs, and MTTR/MTBF.

**API endpoint:** `GET /maintenance/reports/`
**Parameters:** `?report_type=daily|monthly`, `?date_from=`, `?date_to=`, `?department=`, `?asset=`, `?line=`, `?priority=`

**Key summary metrics:**

| Field | Description |
|---|---|
| `total_work_orders` | All WOs in period |
| `completed_work_orders` | Completed in period |
| `open_work_orders` | Still open |
| `breakdowns` | Breakdown-type WOs |
| `completion_percent` | Completion rate |
| `production_downtime_minutes` | Total production stoppage minutes |
| `average_repair_minutes` | Mean time to repair (MTTR proxy) |
| `average_mttr_minutes` | MTTR (minutes) |
| `average_mtbf_days` | MTBF (days between breakdowns) |
| `spare_consumed_cost` | Total cost of spares consumed |
| `pm_due` | PM work orders due in period |
| `pm_completed` | PM work orders completed |
| `pm_compliance_percent` | PM completion rate |
| `vendor_visits` | Vendor visits completed |
| `rows[]` | Per-asset breakdown detail rows |

**Live sample (monthly, 2026-01-01 to 2026-06-30):**
```json
{
  "report_type": "monthly",
  "title": "Monthly maintenance report",
  "generated_at": "2026-06-30 03:29",
  "summary": {
    "total_work_orders": 0,
    "completed_work_orders": 0,
    "breakdowns": 0,
    "completion_percent": 0,
    "production_downtime_minutes": 0,
    "average_repair_minutes": null,
    "average_mttr_minutes": null,
    "average_mtbf_days": null,
    "spare_consumed_cost": "0.00",
    "pm_due": 0,
    "pm_completed": 0,
    "pm_compliance_percent": null,
    "vendor_visits": 0
  },
  "rows": []
}
```
All zeros and nulls — module not in use yet.

---

### 3.11 Scan Endpoints (`/maintenance/scan/lookup/`, `/maintenance/scan/work-order/`)

**Purpose:** Mobile-first endpoints for factory floor workers to interact with maintenance via handheld QR scanners or phones.

**Scan lookup** (`GET /maintenance/scan/lookup/?q=<code>`): Resolves a scanned QR code to either a maintenance asset or a spare part. Returns `{"found": true/false, "code": "...", "detail": "..."}` and, if found, the asset or spare record.

**Scan work-order** (`POST /maintenance/scan/work-order/`): Allows a technician to scan a work-order QR code and submit a status update (e.g. mark IN_PROGRESS, mark COMPLETED) from the shop floor without using the web UI. GET is not allowed on this endpoint.

**Live sample from lookup (2026-06-30):**
```json
{"found": false, "code": "", "detail": "No maintenance asset or spare matched this code."}
```

---

### 3.12 Automation page (`/maintenance/automation`)

**Purpose (inferred from UI route):** Configuration of automated rules — e.g. auto-raise a work order when an asset goes into BREAKDOWN status, auto-generate a spare request when stock falls below minimum, or auto-schedule a PM when due. This is a frontend-only configuration page.

**API status:** The path `https://factory.jivo.in/api/v1/maintenance/automation/` returns HTTP 404. No backing API endpoint exists at this path as of 2026-06-30. The automation logic may be handled server-side via the `pm-plans/generate-due/` action and other hooks, with this page serving as a UI configuration panel that writes to other endpoints.

---

## 4. Workflows (multi-step flows + statuses)

### 4.1 Work Order lifecycle

```
[Trigger] ──────────────────────────────────────────────────────────────────
  Manual complaint / breakdown report           → status: DRAFT
  Auto-generated from PM plan                   → status: OPEN (skips DRAFT)
  Inspection, calibration, project              → status: DRAFT
                                                              │
                                                         Submit WO
                                                              │
                                                           OPEN
                                                              │
                                                     Assign technician
                                                              │
                                                          ASSIGNED
                                                              │
                                                       Start work
                                                              │
                                                         IN_PROGRESS
                                                        /          \
                                               Need spare         Need vendor
                                                   │                   │
                                            WAITING_SPARE      WAITING_VENDOR
                                                   │                   │
                                          Spare issued       Vendor arrives
                                                   └─────┬─────┘
                                                         │
                                                    Work done
                                                         │
                                                     COMPLETED
                                                         │
                                               Supervisor reviews
                                                         │
                                                     APPROVED ─── (rejected → IN_PROGRESS)
                                                         │
                                                       CLOSED
                                              (or ON_HOLD at any stage)
```

**Photos** are attached at any point (BEFORE / AFTER / GENERAL types). **Spare requests** are raised during IN_PROGRESS and fulfilled via the spare-requests → spare-movements pipeline.

### 4.2 Preventive Maintenance cycle

```
Configure PM Plan:
  Asset + Frequency (DAILY/WEEKLY/MONTHLY/QUARTERLY/HALF_YEARLY/YEARLY)
  + Checklist items (CHECKBOX / PASS_FAIL / NUMBER / TEXT)
                    │
          POST /pm-plans/generate-due/    ← triggered manually or via cron
                    │
         Creates Work Orders (type=PREVENTIVE, status=OPEN)
                    │
         Technician executes: IN_PROGRESS
                    │
         Fills in PM checklist (pm-executions record created)
         pm_execution_status: PENDING → IN_PROGRESS → COMPLETED (or SKIPPED/OVERDUE)
                    │
         Work Order: COMPLETED → APPROVED → CLOSED
                    │
         PM plan's last_executed_at updated, next_due_at recalculated
```

PM compliance % = completed_due / due_total × 100 (tracked in dashboard and reports).

### 4.3 Spare parts inward flow (gate linkage)

```
Spare ordered from vendor
         │
Gate Entry (via Gate/QC section, entry_type = spare)
         │
gate_receipt_status: NOT_RECEIVED → RECEIVED
gate_qc_status:      NOT_REQUIRED / PENDING → ACCEPTED / REJECTED / WAIVED
         │
Spare Movement: type=RECEIPT → current_stock increases
         │
Spare available in store
```

### 4.4 Spare request / issue flow (from work order)

```
Work Order raises Spare Request (status=REQUESTED)
         │
Storekeeper checks stock
         │ (if sufficient)
Issue spare → Spare Movement: type=ISSUE
Spare Request status → ISSUED (or PARTIALLY_ISSUED)
         │
Technician uses spare during repair
         │
Consume record → Spare Movement: type=CONSUME
Spare Request status → CLOSED
         │ (if leftover)
Return unused → Spare Movement: type=RETURN → stock re-credited
```

### 4.5 Vendor AMC / visit flow

```
Asset has AMC contract (amc_end_date, warranty_expiry on Asset)
         │
Dashboard alerts: amc_due / amc_overdue / warranty_expired
         │
Schedule vendor visit → Vendor Visit record (status=PLANNED)
         │
Work Order type=AMC_VENDOR raised (status=WAITING_VENDOR)
         │
Vendor arrives → Vendor Visit: IN_PROGRESS
                 Work Order: IN_PROGRESS
         │
Service completed → Vendor Visit: COMPLETED
                    Work Order: COMPLETED → APPROVED → CLOSED
```

---

## 5. Cross-section connections

| Connection | How it links |
|---|---|
| **Gate / Spare inwards** | Spare parts received at the factory gate flow through the same gate entry pipeline used for raw materials. The spare record carries `gate_qc_status` and `gate_receipt_status` fields that match statuses in the Gate/QC section. |
| **Production Execution** | The dashboard's `production_downtime` section aggregates from production run data (`impacted_runs`, `stoppage_work_orders`). When a work order has `work_impact=STOPPAGE`, it is counted against the production schedule. The options endpoint links to `production_machines[]` (empty for Jivo Mart), which would reference machines defined in the Production Execution section. |
| **QC / QC-approved gate entries** | Spares entering via the gate go through `gate_qc_status` checks (PENDING → ACCEPTED/REJECTED/WAIVED), mirroring the inbound raw-material QC workflow. |
| **Scan / Barcode infrastructure** | The `scan/lookup/` endpoint uses the same QR-code scanning infrastructure as the Barcode Traceability section. Assets and spares are assigned scannable codes; the lookup resolves them in the same way box/pallet barcodes are resolved in the barcode domain. |
| **User/HR master** | The options endpoint returns the live factory user list (43 users) for technician assignment. These are the same users used across all other sections (gate security, QC chemist, warehouse staff, etc.). |
| **Vendor master** | Vendor visits and AMC documents reference vendor names/contact; these are likely the same vendors in the Procurement domain's vendor master (212 vendors in `/po/vendors/`). |

---

## 6. Data presence for Jivo Mart (live counts as of 2026-06-30)

| Endpoint | Kind | Count | Status |
|---|---|---|---|
| `/maintenance/dashboard/` | object | 1 (all-zero KPIs) | Live but empty data |
| `/maintenance/alerts/` | object | 0 alerts | Live but empty |
| `/maintenance/options/` | object | 1 (full enum + 43 users) | **Has live data** |
| `/maintenance/reports/` | object | 1 (all-zero metrics) | Live but empty data |
| `/maintenance/assets/` | list | 0 | Empty — no assets onboarded |
| `/maintenance/asset-categories/` | list | 0 | Empty — no masters configured |
| `/maintenance/asset-departments/` | list | 0 | Empty — no masters configured |
| `/maintenance/asset-locations/` | list | 0 | Empty — no masters configured |
| `/maintenance/asset-documents/` | list | 0 | Empty |
| `/maintenance/asset-photos/` | list | 0 | Empty |
| `/maintenance/work-orders/` | list | 0 | Empty — no work orders raised |
| `/maintenance/work-order-photos/` | list | 0 | Empty |
| `/maintenance/pm-plans/` | list | 0 | Empty — no PM plans configured |
| `/maintenance/pm-executions/` | list | 0 | Empty |
| `/maintenance/pm-checklist-items/` | list | 0 | Empty |
| `/maintenance/spares/` | list | 0 | Empty — no spare parts registered |
| `/maintenance/spares/low-stock/` | list | 0 | Empty |
| `/maintenance/spare-categories/` | list | 0 | Empty |
| `/maintenance/spare-movements/` | list | 0 | Empty |
| `/maintenance/spare-requests/` | list | 0 | Empty |
| `/maintenance/vendor-visits/` | list | 0 | Empty — no vendor visits |

**Summary:** 3 of 21 maintenance API endpoints return meaningful data — the dashboard (showing all-zero KPIs), the alerts object (zero alerts), and the options endpoint (full enum schema + 43 factory user records). The remaining 18 endpoints all return empty results.

The maintenance module for Jivo Mart is **fully built and schema-complete** (all enums, status machines, and hierarchy levels are configured at the system level) but **entirely un-populated**. No assets have been registered, no masters (categories, locations, departments) have been set up, no PM plans, no work orders, and no spare parts catalogue has been entered. The module is awaiting its initial onboarding/data-entry phase.

---

## Reference — UI routes (from bundle)
- `/maintenance`
- `/maintenance/alerts/`
- `/maintenance/asset-categories/`
- `/maintenance/asset-departments/`
- `/maintenance/asset-documents/`
- `/maintenance/asset-locations/`
- `/maintenance/asset-photos/`
- `/maintenance/assets`
- `/maintenance/assets/`
- `/maintenance/assets/:assetId`
- `/maintenance/automation`
- `/maintenance/dashboard/`
- `/maintenance/masters`
- `/maintenance/options/`
- `/maintenance/pm`
- `/maintenance/pm-checklist-items/`
- `/maintenance/pm-executions/`
- `/maintenance/pm-plans/`
- `/maintenance/pm-plans/generate-due/`
- `/maintenance/reports`
- `/maintenance/reports/`
- `/maintenance/scan/lookup/`
- `/maintenance/scan/work-order/`
- `/maintenance/spare-categories/`
- `/maintenance/spare-movements/`
- `/maintenance/spare-requests/`
- `/maintenance/spares`
- `/maintenance/spares/`
- `/maintenance/spares/low-stock/`
- `/maintenance/spares/stock/`
- `/maintenance/vendor-visits/`
- `/maintenance/work-order-photos/`
- `/maintenance/work-orders`
- `/maintenance/work-orders/`
- `/maintenance/work-orders/:workOrderId`

## Reference — captured API endpoints + record counts (this section)
- `/maintenance/alerts/` -> 1 (object, 0 alerts inside)
- `/maintenance/asset-categories/` -> 0 (list)
- `/maintenance/asset-departments/` -> 0 (list)
- `/maintenance/asset-documents/` -> 0 (list)
- `/maintenance/asset-locations/` -> 0 (list)
- `/maintenance/asset-photos/` -> 0 (list)
- `/maintenance/assets/` -> 0 (list)
- `/maintenance/dashboard/` -> 1 (object, all-zero KPIs)
- `/maintenance/options/` -> 1 (object: full enums + 43 users + empty masters)
- `/maintenance/pm-checklist-items/` -> 0 (list)
- `/maintenance/pm-executions/` -> 0 (list)
- `/maintenance/pm-plans/` -> 0 (list)
- `/maintenance/reports/` -> 1 (object, all-zero metrics)
- `/maintenance/spare-categories/` -> 0 (list)
- `/maintenance/spare-movements/` -> 0 (list)
- `/maintenance/spare-requests/` -> 0 (list)
- `/maintenance/spares/` -> 0 (list)
- `/maintenance/spares/low-stock/` -> 0 (list)
- `/maintenance/vendor-visits/` -> 0 (list)
- `/maintenance/work-order-photos/` -> 0 (list)
- `/maintenance/work-orders/` -> 0 (list)

Linked: [[docs/factory/FACTORY_MAP|FACTORY_MAP]] · [[docs/FACTORY_CLI_PLAN|FACTORY_CLI_PLAN]] · [[docs/READ_ONLY_LAW|READ_ONLY_LAW]]
