---
title: "Production — Jivo Mart app-model"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: reference
tags: [jivogpt, factory-cli, production]
---

# Production — Jivo Mart app-model

> **Provenance — imported 2026-07-19; source snapshot 2026-06-30.** This note came from the JIVO_MART-only `daman8271/jivo-factory-intel` baseline. For the current three-company study and the live-verified 2026-07-19 state, use [[docs/factory/FACTORY_MAP|FACTORY_MAP]] and [[CLI/factory-cli/README|the current CLI guide]].
> Last updated: 2026-06-30. Verified against live JIVO_MART API.

## 1. Purpose — what this section is for in the factory

The Production section is a **Manufacturing Execution System (MES)** module that covers the full lifecycle of factory floor production at Jivo Mart. It splits into two cooperating sub-modules:

- **Production Planning** (`/production/planning`): Manages SAP production orders — creation, editing, bulk import, and component-level shortfall tracking. A production plan is the bridge between a sales/demand signal and a shop-floor work order.
- **Production Execution** (`/production/execution`): Drives actual factory runs on named production lines. Operators start runs, log breakdowns and resource usage (electricity, water, gas), perform QC checks, record waste, and execute line-clearance procedures before changing SKUs. The system computes OEE (Overall Equipment Effectiveness) per run and reports on cost-per-unit, downtime causes, and plan achievement.

Together the two sub-modules answer the core factory questions:
- What should be produced, when, and is raw material available? (Planning)
- What was produced, at what efficiency, with what waste and breakdowns? (Execution)

An additional read-only cross-system report — **Production Movement** — tracks SAP-level finished-goods inventory entries (GRPO receipts, transfers, AR invoices) regardless of whether MES run data exists. This is the only endpoint in this section that currently has live transactional data for Jivo Mart.

**Current status for Jivo Mart**: The module is architecturally complete but not yet operationally configured. No production lines, machines, runs, breakdowns, or waste entries have been created. All execution analytics return zero. The Production Movement report and the SAP plan-dashboard are populated.

---

## 2. Page tree (pages → subpages → wizard steps / sub-subpages)

```
/production
├── /production/planning                         Production Planning hub
│   ├── /production/planning/create              Create new production plan (wizard)
│   ├── /production/planning/bulk-import         Bulk-import plans from CSV / SAP
│   ├── /production/planning/:planId             Plan detail view — SAP order + components + shortfall
│   └── /production/planning/:planId/edit        Edit an existing plan
│
└── /production/execution                        Execution dashboard (OEE summary, active runs)
    ├── /production/execution/start-run          Start a new production run (line + SKU + order selection)
    ├── /production/execution/runs/:runId        Run detail hub
    │   ├── /production/execution/runs/:runId/qc          In-run QC check entry
    │   ├── /production/execution/runs/:runId/resources   Resource consumption logging
    │   ├── /production/execution/runs/:runId/yield       Yield / output recording
    │   └── /production/execution/runs/:runId/breakdowns  Breakdowns during this run
    ├── /production/execution/line-management    Production line master configuration
    ├── /production/execution/line-clearance     Line clearance list
    │   ├── /production/execution/line-clearance/create         New line clearance entry
    │   └── /production/execution/line-clearance/:clearanceId   Clearance detail / checklist form
    ├── /production/execution/machine-checklists Machine checklist execution list
    ├── /production/execution/master-data        Master data (lines, machines, breakdown categories,
    │                                            checklist templates)
    ├── /production/execution/breakdowns         Global breakdown log (all lines, all runs)
    ├── /production/execution/waste              Waste log (all lines, all runs)
    └── /production/execution/reports            Reports hub
        ├── /production/execution/reports/daily                    Daily production report
        ├── /production/execution/reports/monthly-summary          Monthly summary (all KPIs by month)
        ├── /production/execution/reports/cost-analysis            Cost analysis (per-run, per-line)
        ├── /production/execution/reports/oee-trend                OEE trend chart over time
        ├── /production/execution/reports/downtime-pareto          Downtime pareto (by cause, by machine)
        ├── /production/execution/reports/plan-vs-production       Plan vs actual achievement
        ├── /production/execution/reports/procurement-vs-planned   Procurement vs planned materials
        ├── /production/execution/reports/resource-consumption     Resource consumption (electricity,
        │                                                          water, gas, compressed air)
        └── /production/execution/reports/waste-trend              Waste trend (by material, by reason)
```

---

## 3. Per-page detail

### 3.1 Production Planning hub — `/production/planning`

**Purpose**: Lists all SAP production orders for Jivo Mart with status, due date, planned vs. completed quantity, component availability, and shortfall flags. Entry point for creating or importing new plans.

**API endpoints**:
- `GET /sap/plan-dashboard/summary/` — flat list of production orders with shortfall summary
- `GET /sap/plan-dashboard/details/` — same orders with full component breakdown
- `GET /sap/plan-dashboard/procurement/` — components with shortfall that require purchasing action

**Key fields** (production order row):
`prod_order_num`, `sku_code`, `sku_name`, `planned_qty`, `completed_qty`, `status` (`released` / `completed` / `closed`), `due_date`, `post_date`, `priority`, `warehouse`, `total_components`, `components_with_shortfall`, `total_remaining_component_qty`

**Live sample** (verified 2026-06-30):
```json
{
  "prod_order_entry": 39,
  "prod_order_num": 825926501,
  "sku_code": "FG0000326",
  "sku_name": "SANO POMACE 1+1 LTR",
  "planned_qty": 160.0,
  "completed_qty": 160.0,
  "status": "released",
  "due_date": "2025-08-19",
  "post_date": "2025-08-19",
  "priority": 100,
  "warehouse": "DL-MP",
  "total_components": 1,
  "components_with_shortfall": 0,
  "total_remaining_component_qty": 0.0
}
```
**Data presence**: 1 SAP production order (FG0000326 SANO POMACE 1+1 LTR, 160 units, DL-MP warehouse, fully completed). The `/production-planning/` API path does not exist; the planning UI is backed entirely by `/sap/plan-dashboard/` endpoints.

---

### 3.2 Create production plan — `/production/planning/create`

**Purpose**: Form/wizard to create a new production plan, selecting a SAP item (FG SKU), setting quantity, due date, warehouse, and priority.

**API endpoints**:
- `GET /production-execution/sap/items/` — item master for SKU selection (193 FG/RM items in cached data; currently returns `[]` live — not yet configured)
- `POST /production-execution/sap/orders/` (write, not exposed to CLI)

**Jivo Mart status**: Not yet configured. sap/items returns empty from live API.

---

### 3.3 Bulk import — `/production/planning/bulk-import`

**Purpose**: Upload a CSV or connect directly to SAP to batch-import production orders into the planning module.

**API endpoint**: Write-side not exposed; reads from `/production-execution/sap/orders/` and `/production-execution/sap/items/`.

**Jivo Mart status**: Unused — sap/orders returns `[]`.

---

### 3.4 Plan detail — `/production/planning/:planId`

**Purpose**: Shows a single SAP production order in detail: the FG SKU being produced, quantity, status, and a component breakdown table showing each raw-material/sub-assembly required, its planned qty, issued qty, remaining qty, stock on hand, committed, on order, net available, and shortfall.

**API endpoint**: `GET /sap/plan-dashboard/details/`

**Key component fields**:
`component_code`, `component_name`, `component_planned_qty`, `component_issued_qty`, `component_remaining_qty`, `stock_on_hand`, `stock_committed`, `stock_on_order`, `net_available`, `shortfall_qty`, `stock_status` (`sufficient` / `shortfall`)

**Live sample** (component row under order 825926501):
```json
{
  "component_line": 0,
  "component_code": "FG0000150",
  "component_name": "SANO POMACE OLIVE 1 LTR 16 PCS",
  "component_planned_qty": 320.0,
  "component_issued_qty": 320.0,
  "component_remaining_qty": 0.0,
  "component_warehouse": "DL-MP",
  "base_qty": 2.0,
  "stock_on_hand": 12720.0,
  "stock_committed": 11768.0,
  "stock_on_order": 25866.0,
  "net_available": 952.0,
  "shortfall_qty": 0.0,
  "stock_status": "sufficient"
}
```

---

### 3.5 Execution Dashboard — `/production/execution`

**Purpose**: Live overview of the production floor — active runs, line status, OEE summary cards, and recent activity. Operator entry point for starting new runs.

**API endpoints**:
- `GET /production-execution/reports/analytics/` — summary object: `total_runs`, `total_production`, `total_running_minutes`, `total_breakdown_minutes`, `availability_percent`
- `GET /production-execution/runs/` — list of active/recent runs
- `GET /production-execution/lines/` — configured production lines

**Live sample** (analytics summary, verified 2026-06-30):
```json
{
  "total_runs": 0,
  "total_production": 0,
  "total_running_minutes": 0,
  "total_breakdown_minutes": 0,
  "availability_percent": 0
}
```
**Jivo Mart status**: All zero — no runs, lines, or machines configured.

---

### 3.6 Start Run — `/production/execution/start-run`

**Purpose**: Wizard to start a new production run on a named line, linking it to a SAP production order (from sap/orders), selecting the output FG item, and setting planned quantity and shift details.

**API endpoints**:
- `GET /production-execution/lines/` — line picker (empty)
- `GET /production-execution/sap/orders/` — open production orders (empty)
- `GET /production-execution/sap/items/` — item master (empty)
- `POST /production-execution/runs/` (write)

**Jivo Mart status**: Not usable — no lines or orders configured.

---

### 3.7 Run Detail — `/production/execution/runs/:runId`

**Purpose**: Live cockpit for a single active run. Shows run number, line, SKU, shift operator, start time, current OEE components (availability / performance / quality), cumulative output, and tabbed sub-sections.

**API endpoint**: `GET /production-execution/runs/{runId}/`

**Sub-tabs** (each with its own endpoint):

#### 3.7a QC tab — `/production/execution/runs/:runId/qc`
In-process quality checks logged during the run. Linked to `quality-control/production-qc` (also empty for Jivo Mart — see QC section).

#### 3.7b Resources tab — `/production/execution/runs/:runId/resources`
Resource consumption per run: electricity (kWh), water (kL), gas (m³), compressed air (m³), labour hours, machine hours. Used to compute cost/unit in cost-analysis reports.

#### 3.7c Yield tab — `/production/execution/runs/:runId/yield`
Final yield recording: planned output vs actual output, yield %, scrap/waste quantity.

#### 3.7d Breakdowns tab — `/production/execution/runs/:runId/breakdowns`
Machine breakdowns that occurred during the run, each with a breakdown category, machine, start/end time, and resolution notes.

**Jivo Mart status**: `/production-execution/runs/` returns `[]` — no run records exist.

---

### 3.8 Line Management — `/production/execution/line-management`

**Purpose**: Admin page to configure production lines — name, default speed (units/hour), shifts, assigned machines, and line-level resource cost rates.

**API endpoints**:
- `GET /production-execution/lines/` — returns `[]` for Jivo Mart
- `GET /production-execution/line-configs/` — returns `[]` for Jivo Mart
- `GET /production-execution/machines/` — returns `[]` for Jivo Mart

**Jivo Mart status**: No lines, line configs, or machines configured.

---

### 3.9 Line Clearance — `/production/execution/line-clearance`

**Purpose**: Regulatory-grade checklist that must be completed before a production line changes from one product/batch to another, preventing cross-contamination. Each clearance record links to a line, a checklist template, and a responsible operator.

**API endpoints**:
- `GET /production-execution/line-clearance/` — list of clearance records (empty)
- `GET /production-execution/reports/line-clearance/` — clearance report (empty)
- `GET /production-execution/checklist-templates/` — checklist template master (empty)

**Line clearance status values** (inferred from entity model): `PENDING`, `IN_PROGRESS`, `AWAITING_APPROVAL`, `APPROVED`, `REJECTED`

**Jivo Mart status**: No clearance records or checklist templates configured.

---

### 3.10 Machine Checklists — `/production/execution/machine-checklists`

**Purpose**: Pre-startup/post-shutdown checklists tied to individual machines. Operators confirm each item (oil levels, guard positions, safety lockouts) before a run starts.

**API endpoint**: `GET /production-execution/machine-checklists/` — returns `[]`

**Key fields** (inferred): checklist_template_id, machine_id, run_id, checked_by, completed_at, pass/fail per item.

**Jivo Mart status**: Empty — no machines or checklist templates configured.

---

### 3.11 Master Data — `/production/execution/master-data`

**Purpose**: Admin setup pages for all MES reference data: production lines, machines, breakdown categories, and checklist templates. This is where an operator configures the system before any runs can start.

**API endpoints**:
- `GET /production-execution/lines/` — `[]`
- `GET /production-execution/machines/` — `[]`
- `GET /production-execution/breakdown-categories/` — `[]`
- `GET /production-execution/checklist-templates/` — `[]`

**Jivo Mart status**: All empty. The entire MES execution module is awaiting initial setup of these master records.

---

### 3.12 Breakdowns — `/production/execution/breakdowns`

**Purpose**: Global list of all machine/line breakdown events across all runs, filterable by date, line, machine, and breakdown category. Used for MTBF/MTTR analysis.

**API endpoint**: `GET /production-execution/breakdown-categories/` (category master, empty) + individual breakdown records from runs.

**Key breakdown fields** (inferred from report schema): `machine`, `line`, `breakdown_category`, `start_time`, `end_time`, `duration_minutes`, `resolved_by`, `root_cause`, `action_taken`

**Jivo Mart status**: Empty.

---

### 3.13 Waste — `/production/execution/waste`

**Purpose**: Waste log of all material rejected or lost during production — excess oil, packaging failures, line rejects. Each entry links to a run, a material, a waste reason, and may require QA approval before the batch is confirmed.

**API endpoint**: `GET /production-execution/waste/` — returns `[]`

**Waste analytics structure** (from `/production-execution/reports/analytics/waste/`):
```json
{
  "by_material": [],
  "by_approval_status": [],
  "total_waste_logs": 0
}
```

**Jivo Mart status**: Empty.

---

### 3.14 Reports Hub — `/production/execution/reports`

All reports are backed by analytics endpoints under `/production-execution/reports/analytics/`. All return zero/empty data for Jivo Mart because there are no production runs to aggregate. The endpoints and their schemas are confirmed via live API calls.

#### 3.14a Daily Report — `/production/execution/reports/daily`
**Purpose**: Day-level production summary per line and SKU.
**API endpoint**: `/production-execution/reports/daily/` — returns HTTP 404 (not yet implemented as a distinct endpoint; daily data is derived from the runs list).

#### 3.14b Monthly Summary — `/production/execution/reports/monthly-summary`
**Purpose**: Year-at-a-glance table with 12 monthly rows showing total runs, production volume, average OEE, total cost, cost/unit, waste, and resource costs (electricity, water, gas, compressed air, labour, machine, overhead).
**API endpoint**: `GET /production-execution/reports/analytics/monthly-summary/`

**Schema** (year=2026, all months return zero):
```json
{
  "year": 2026,
  "months": [
    {
      "month": 1, "month_name": "January",
      "total_runs": 0, "total_production": 0.0, "avg_oee": 0,
      "total_cost": 0.0, "cost_per_unit": 0, "total_waste": 0,
      "electricity_cost": 0.0, "water_cost": 0.0, "gas_cost": 0.0,
      "compressed_air_cost": 0.0, "labour_cost": 0.0,
      "machine_cost": 0.0, "overhead_cost": 0.0,
      "total_breakdown_minutes": 0.0
    }
    ... (12 months total)
  ]
}
```

#### 3.14c Cost Analysis — `/production/execution/reports/cost-analysis`
**Purpose**: Per-run and per-line cost breakdown, cost distribution chart, and trend over time.
**API endpoint**: `GET /production-execution/reports/analytics/cost-analysis/`

**Schema**:
```json
{
  "per_run": [], "trend": [], "by_line": [],
  "cost_distribution": {},
  "summary": {
    "total_cost": 0, "avg_per_unit": 0,
    "total_production": 0, "run_count": 0
  }
}
```

#### 3.14d OEE Trend — `/production/execution/reports/oee-trend`
**Purpose**: OEE over time by line, including breakdown by availability / performance / quality components.
**API endpoint**: `GET /production-execution/reports/analytics/oee-trend/`

**Schema**:
```json
{
  "trend": [], "by_line": [], "per_run": [],
  "summary": {
    "total_runs": 0, "avg_oee": 0, "group_by": "daily"
  }
}
```

Also: `GET /production-execution/reports/analytics/oee/` — simpler summary object with `total_runs`, `total_production`, `total_running_minutes`, `total_breakdown_minutes`, `availability_percent`, `per_run_oee: []`.

#### 3.14e Downtime Pareto — `/production/execution/reports/downtime-pareto`
**Purpose**: Pareto chart of breakdown causes. Shows which failure categories account for most downtime. Also displays per-machine breakdown totals and MTBF/MTTR.
**API endpoint**: `GET /production-execution/reports/analytics/downtime-pareto/`

**Schema**:
```json
{
  "pareto": [], "by_machine": [], "trend": [],
  "summary": {
    "total_breakdowns": 0, "total_breakdown_minutes": 0.0,
    "total_running_minutes": 0.0,
    "mtbf_minutes": 0, "mttr_minutes": 0
  }
}
```
Also: `GET /production-execution/reports/analytics/downtime/` — flat breakdown list: `{"breakdowns": [], "total_count": 0, "total_minutes": 0}`.

#### 3.14f Plan vs Production — `/production/execution/reports/plan-vs-production`
**Purpose**: Table comparing each production order's planned qty vs actual qty, with achievement % per SKU.
**API endpoint**: `GET /production-execution/reports/analytics/plan-vs-production/`

**Schema**:
```json
{
  "items": [],
  "summary": {
    "total_orders": 0, "avg_achievement_pct": 0,
    "total_planned": 0, "total_actual": 0
  }
}
```

#### 3.14g Procurement vs Planned — `/production/execution/reports/procurement-vs-planned`
**Purpose**: Compares raw material procurement against the planned production schedule — shows whether materials arrived on time to support the plan.
**API endpoint**: `/production-execution/reports/procurement-vs-planned/` — returns HTTP 404 (not yet implemented as a distinct endpoint).

#### 3.14h Resource Consumption — `/production/execution/reports/resource-consumption`
**Purpose**: Daily resource usage (electricity, water, gas, compressed air) aggregated across all lines, with cost per case (production unit).
**API endpoint**: `GET /production-execution/reports/analytics/resource-consumption/`

**Schema**:
```json
{
  "daily_data": [],
  "summary": {
    "total_days": 0, "total_production": 0,
    "grand_total_cost": 0, "avg_cost_per_case": 0
  }
}
```

#### 3.14i Waste Trend — `/production/execution/reports/waste-trend`
**Purpose**: Waste over time broken down by material and rejection reason, with approval-rate tracking (approved vs unreviewed waste).
**API endpoint**: `GET /production-execution/reports/analytics/waste-trend/`

**Schema**:
```json
{
  "by_material": [], "by_reason": [], "trend": [],
  "by_approval_status": [],
  "summary": {
    "total_waste_qty": 0, "total_waste_logs": 0,
    "unique_materials": 0, "approval_rate": 0
  }
}
```

---

### 3.15 Production Movement Report (standalone cross-section report)

**Purpose**: Inventory-level view of all finished-goods stock movements (inward receipts, outward invoices, warehouse transfers) tracked in SAP. This is **not** an MES run report — it mirrors SAP document postings and is the only production-adjacent endpoint with live transactional data for Jivo Mart.

**API endpoints**:
- `GET /production-execution/reports/production-movement/` — movement rows (supports filters: `date_from`, `date_to`, `warehouse`, `direction`, `transaction_type`, `production_only`)
- `GET /production-execution/reports/production-movement/filter-options/` — warehouse and transaction type reference data

**Filter options** (live, verified 2026-06-30):
```
Warehouses:
  BH-FGM  — Bhakharpur finished goods
  BH-FK   — Bhakharpur Flipkart Packing
  DL-MP   — MAYAPURI FINISHED (MAIN)

Transaction types:
  13 = AR Invoice, 14 = AR Credit, 15 = Delivery, 16 = Return,
  18 = AP Invoice, 19 = AP Credit, 20 = GRPO, 21 = Return to Vendor,
  59 = Goods Receipt, 60 = Goods Issue, 67 = Transfer, 202 = Production Order
```

**Live sample row** (GRPO inward, 2026-06-29):
```json
{
  "date": "2026-06-29T00:00:00",
  "item_code": "FG0000032",
  "item_name": "COLD PRESS 1 LTR 20 PCS",
  "item_group": "FINISHED",
  "warehouse": "BH-FGM",
  "warehouse_name": "Bhakharpur finished goods",
  "in_qty": 6540.0,
  "out_qty": 0.0,
  "quantity": 6540.0,
  "direction": "IN",
  "transaction_value": 1111800.0,
  "transaction_type": 20,
  "transaction_label": "GRPO",
  "reference": "2006264558",
  "doc_num": "263345",
  "created_by": "13091"
}
```

**Live summary** (date_from=2026-01-01, date_to=2026-06-30, verified 2026-06-30):
```
Total entries:    500 (limited by max 500 records per query)
Inward entries:    88
Outward entries:  412
Opening qty:   103,302 units
Total IN qty:  213,115 units  (88 GRPO entries, 43 unique docs = 191,552 + 21,533 transfers in)
Total OUT qty: 173,268 units
Net qty:        39,847 units
Closing qty:   367,645 units
Total value: ₹98,471,610
Net value:   ₹10,808,309

By transaction type:
  GRPO       (type 20): 43 entries, 191,552 in,      0 out, ₹48,844,036
  Transfer   (type 67): 260 entries, 21,533 in, 110,229 out, ₹36,397,152
  AR Invoice (type 13): 25 entries,       0 in,  62,471 out, ₹13,037,848
  Delivery   (type 15): 164 entries,     18 in,     568 out,    ₹185,876
  Return     (type 16): 8 entries,       12 in,       0 out,      ₹6,698

By warehouse:
  BH-FGM (Bhakharpur FG):     241 entries, 204,462 in, 165,372 out, ₹92,095,381
  DL-MP  (Mayapuri Finished): 258 entries,   7,953 in,   7,896 out,  ₹6,257,229
  BH-FK  (Bhakharpur FK):       1 entry,       700 in,       0 out,    ₹119,000
```

---

## 4. Workflows (multi-step flows + statuses)

### 4.1 Production Planning Workflow

```
SAP creates Production Order
        ↓
Plan visible in /production/planning list
  [status: released]
        ↓
Component availability checked (sap/plan-dashboard/details)
  → If shortfall: components flagged, procurement action raised
  → If sufficient: plan ready to execute
        ↓
Operator creates Run in /production/execution/start-run
  (links run to plan via SAP order number)
        ↓
[status: completed — when planned_qty = completed_qty]
```

**SAP production order statuses observed**: `released`, `completed`, `closed`

### 4.2 Production Run Lifecycle (MES execution — not yet active for Jivo Mart)

```
start-run page
  → Select line + SAP order + FG item + planned qty
        ↓
Run created [status: PENDING / PLANNED]
        ↓
Operator starts run [status: IN_PROGRESS]
  ├── Log breakdowns → [BREAKDOWN → RESUMED]
  ├── Log resources (electricity, water, gas, air, labour)
  ├── Log QC checks (linked to quality-control/production-qc)
  └── Log waste entries (pending QA approval)
        ↓
Run completed [status: COMPLETED]
  → Yield recorded (actual output vs planned)
        ↓
OEE calculated: availability × performance × quality
Cost allocated: resources → cost/unit
```

### 4.3 Line Clearance Workflow (MES — not yet active)

```
Line finishes a batch (run completed)
        ↓
Line clearance created [status: PENDING]
  → Operator works through checklist template items
  → Each item marked PASS / FAIL with notes
        ↓
All items checked [status: IN_PROGRESS → AWAITING_APPROVAL]
        ↓
Supervisor reviews
  → Approved: [status: APPROVED] → Line cleared for next product
  → Rejected: [status: REJECTED] → Must re-do clearance
        ↓
Next run can start on that line
```

### 4.4 Waste Approval Workflow (MES — not yet active)

```
Operator logs waste during run
  → Waste entry created [approval_status: PENDING]
        ↓
QA reviewer assesses (approves or rejects recorded quantity)
  → [approval_status: APPROVED / REJECTED]
        ↓
Approved waste included in waste-trend analytics
```

---

## 5. Cross-section connections

| This section | Links to | How |
|---|---|---|
| Production Planning | SAP / Procurement | SAP production order (prod_order_num) links to raw material POs; component shortfall flags trigger procurement action |
| Production Planning | Warehouse (WMS) | component_warehouse + warehouse field on order; component stock_on_hand read from SAP warehouse master |
| Production Run | QC (quality-control) | Runs link to `quality-control/production-qc` for in-process quality checks during execution |
| Production Run | Barcode/Traceability | Finished goods boxes printed during or after a run (BarcodeBox.production_line field references the line name) |
| Production Run → Yield | Warehouse / FG Receipts | When a run completes, the FG quantity is receipted into warehouse (`/warehouse/fg-receipts/`) and a GRPO document is posted in SAP |
| Production Movement report | Warehouse (WMS) | Reads the same SAP FG movement postings that the WMS tracks; three shared warehouses (BH-FGM, DL-MP, BH-FK) |
| Production Movement report | Dispatch | AR Invoice and Delivery outward movements represent goods dispatched to customers (same SAP doc_num seen in dispatch section) |
| Breakdown Categories | Maintenance | Machine breakdowns recorded here overlap with the Maintenance module's work-order system (machine_id is shared) |
| Line Clearance | QC | Line clearance can trigger a QC inspection of the cleaned line before the next batch starts |

---

## 6. Data presence for Jivo Mart (which pages have live data vs empty)

### Has live data

| Endpoint | Count / Notes |
|---|---|
| `/sap/plan-dashboard/summary/` | 1 production order (FG0000326 SANO POMACE 1+1 LTR, 160 units, completed, DL-MP) |
| `/sap/plan-dashboard/details/` | Same 1 order with full component tree (1 component: FG0000150, fully issued) |
| `/sap/plan-dashboard/procurement/` | 0 shortage items (the single order has no shortfall) |
| `/production-execution/reports/production-movement/` | 500 entries for 2026-01-01→2026-06-30 (limited by 500-row cap); ₹98.47M total value across 3 warehouses |
| `/production-execution/reports/production-movement/filter-options/` | 3 warehouses, 12 transaction types |
| `/production-execution/reports/analytics/monthly-summary/` | Returns structured object (12 months) but all zeros — schema confirmed |
| All other `/production-execution/reports/analytics/*` | Return valid JSON schema objects but all zeros/empty arrays — confirmed endpoints exist |

### Empty for Jivo Mart (not yet configured)

| Endpoint | Count | Reason |
|---|---|---|
| `/production-execution/lines/` | 0 | No production lines registered |
| `/production-execution/machines/` | 0 | No machines registered |
| `/production-execution/line-configs/` | 0 | No line configuration done |
| `/production-execution/runs/` | 0 | No production runs ever started |
| `/production-execution/breakdown-categories/` | 0 | No breakdown categories defined |
| `/production-execution/checklist-templates/` | 0 | No checklist templates created |
| `/production-execution/machine-checklists/` | 0 | No machine checklist executions |
| `/production-execution/line-clearance/` | 0 | No line clearance records |
| `/production-execution/waste/` | 0 | No waste entries |
| `/production-execution/sap/orders/` | 0 (live) | SAP orders not being pulled/linked into MES |
| `/production-execution/sap/items/` | 0 (live) | Item master not configured in MES; 193-item catalog exists in cached state |
| `/production-execution/costs/analytics/` | 0 | No cost records (no runs) |
| `/production-execution/reports/line-clearance/` | 0 | No clearance records |
| `/quality-control/production-qc/` | 0 | No in-process QC entries |

### Note on sap/items discrepancy
The raw captured file `/root/jivo-factory-intel/raw/production-execution__sap__items.json` contains 193 FG/RM items (captured from local cache in a prior sync). The live API returns `[]`. This suggests the item master was configured at some point during setup/testing but has since been cleared or the live endpoint has stricter filters. The 193 items catalog (FG, RM, SL, SC prefixes) represents the full production SKU universe for Jivo Mart.

---

## Reference — UI routes (from bundle)
- `/production`
- `/production/execution`
- `/production/execution/breakdowns`
- `/production/execution/line-clearance`
- `/production/execution/line-clearance/:clearanceId`
- `/production/execution/line-clearance/create`
- `/production/execution/line-management`
- `/production/execution/machine-checklists`
- `/production/execution/master-data`
- `/production/execution/reports`
- `/production/execution/reports/cost-analysis`
- `/production/execution/reports/daily`
- `/production/execution/reports/downtime-pareto`
- `/production/execution/reports/monthly-summary`
- `/production/execution/reports/oee-trend`
- `/production/execution/reports/plan-vs-production`
- `/production/execution/reports/procurement-vs-planned`
- `/production/execution/reports/resource-consumption`
- `/production/execution/reports/waste-trend`
- `/production/execution/runs/:runId`
- `/production/execution/runs/:runId/breakdowns`
- `/production/execution/runs/:runId/qc`
- `/production/execution/runs/:runId/resources`
- `/production/execution/runs/:runId/yield`
- `/production/execution/start-run`
- `/production/execution/waste`
- `/production/planning`
- `/production/planning/:planId`
- `/production/planning/:planId/edit`
- `/production/planning/bulk-import`
- `/production/planning/create`

## Reference — captured API endpoints + record counts (this section)
- `/production-execution/breakdown-categories/` -> 0 (list) — no breakdown categories defined
- `/production-execution/checklist-templates/` -> 0 (list) — no checklist templates
- `/production-execution/costs/analytics/` -> 0 (list) — no run costs
- `/production-execution/line-clearance/` -> 0 (list) — no clearance records
- `/production-execution/line-configs/` -> 0 (list) — no line configs
- `/production-execution/lines/` -> 0 (list) — no lines configured
- `/production-execution/machine-checklists/` -> 0 (list) — no checklist executions
- `/production-execution/machines/` -> 0 (list) — no machines registered
- `/production-execution/reports/analytics/` -> 1 (object) — schema present, all zeros
- `/production-execution/reports/analytics/cost-analysis/` -> 1 (object) — schema present, all zeros
- `/production-execution/reports/analytics/downtime-pareto/` -> 1 (object) — schema present, all zeros
- `/production-execution/reports/analytics/downtime/` -> 1 (object) — schema present, all zeros
- `/production-execution/reports/analytics/monthly-summary/` -> 1 (object) — 12-month array, all zeros
- `/production-execution/reports/analytics/oee-trend/` -> 1 (object) — schema present, all zeros
- `/production-execution/reports/analytics/oee/` -> 1 (object) — schema present, all zeros
- `/production-execution/reports/analytics/plan-vs-production/` -> 1 (object) — schema present, all zeros
- `/production-execution/reports/analytics/resource-consumption/` -> 1 (object) — schema present, all zeros
- `/production-execution/reports/analytics/waste-trend/` -> 1 (object) — schema present, all zeros
- `/production-execution/reports/analytics/waste/` -> 1 (object) — schema present, all zeros
- `/production-execution/reports/line-clearance/` -> 0 (list) — no records
- `/production-execution/reports/production-movement/` -> 1 (object) — LIVE DATA: 500 entries, ₹98.47M value
- `/production-execution/reports/production-movement/filter-options/` -> 1 (object) — LIVE: 3 warehouses, 12 tx types
- `/production-execution/runs/` -> 0 (list) — no production runs
- `/production-execution/sap/items/` -> 0 live / 193 cached (list) — item master not synced
- `/production-execution/sap/orders/` -> 0 (list) — SAP orders not linked to MES
- `/production-execution/waste/` -> 0 (list) — no waste logs
- `/sap/plan-dashboard/summary/` -> 1 object, 1 order — LIVE DATA
- `/sap/plan-dashboard/details/` -> 1 object, 1 order with components — LIVE DATA
- `/sap/plan-dashboard/procurement/` -> 1 object, 0 shortfall items — LIVE DATA

Linked: [[docs/factory/FACTORY_MAP|FACTORY_MAP]] · [[docs/FACTORY_CLI_PLAN|FACTORY_CLI_PLAN]] · [[docs/READ_ONLY_LAW|READ_ONLY_LAW]]
