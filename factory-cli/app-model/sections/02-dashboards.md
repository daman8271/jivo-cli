---
title: "Dashboards — Jivo Mart app-model"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: reference
tags: [jivogpt, factory-cli, dashboards]
---

# Dashboards — Jivo Mart app-model

> **Provenance — imported 2026-07-19; source snapshot 2026-06-30.** This note came from the JIVO_MART-only `daman8271/jivo-factory-intel` baseline. For the current three-company study and the live-verified 2026-07-19 state, use [[docs/factory/FACTORY_MAP|FACTORY_MAP]] and [[CLI/factory-cli/README|the current CLI guide]].
> STATUS: COMPLETE (documented 2026-06-30). Jivo Mart (JIVO_MART) only.

## 1. Purpose — what this section is for in the factory

The Dashboards section is the cross-cutting intelligence layer of the Jivo Mart factory app. It aggregates data from every other module (gate, QC, warehouse, production, dispatch) into purpose-built read-only views that operations and planning teams use to monitor the factory's health in real time.

There are eight distinct dashboard pages covering:
- **Stock visibility** — current on-hand quantities and health ratios across all warehouses, and historical point-in-time snapshots
- **Inventory age** — how long finished goods have sat in warehouses (ageing by SKU × warehouse), driving FIFO discipline and write-off risk decisions
- **Non-moving raw materials** — PM/RM items that have had zero or near-zero consumption over a configurable threshold period
- **SAP production plan** — live SAP production orders vs. component availability (shortfall detection)
- **Sales planning vs. requirement** — SAP HANA stored-procedure-driven gap analysis of forecast vs. procurement requirement (NOTE: not operative for JIVO_MART; only configured for JIVO_OIL and JIVO_BEVERAGES)
- **Production movement** — day-level stock movements (in/out) across finished goods and raw material warehouses
- **Dispatch pipeline** — real-time status of all outbound dispatches in flight (truck-in → loading → gatepass → departed)
- **Dispatch plans** — kanban board of all dispatch bookings through their full 10-stage pipeline

---

## 2. Page tree

```
/dashboards                                  Root (landing / aggregated overview)
├── /dashboards/dispatch-pipeline            Dispatch Pipeline Monitor (trucks in yard by status)
├── /dashboards/dispatch-plans               Dispatch Plans Kanban (10-stage pipeline board)
├── /dashboards/inventory-age                Inventory Age Dashboard
│   ├── /dashboards/inventory-age/filter-options/  Filter options loader (item groups, sub-groups, varieties, warehouses)
│   └── /dashboards/inventory-age/report/   Aged inventory report (FG by SKU × warehouse)
├── /dashboards/non-moving                   Non-Moving Raw Materials Dashboard (item-group filter)
├── /dashboards/production-movement          Production Movement Report (daily inventory in/out)
├── /dashboards/sales-planning-requirement   Sales Planning vs. Requirement Dashboard
│   ├── /dashboards/sales-planning-requirement/status/    Refresh job status (latest/last_success timestamps)
│   ├── /dashboards/sales-planning-requirement/refresh/   Trigger a manual refresh (POST-only)
│   ├── /dashboards/sales-planning-requirement/report/    Gap-analysis rows + summary
│   └── /dashboards/sales-planning-requirement/analysis/  Procedure metadata & Postgres schema
├── /dashboards/sap-plan                     SAP Production Plan Dashboard (component shortfall view)
├── /dashboards/stock-levels                 Alias/entry for stock level views
├── /dashboards/stock/                       Live Stock Levels (all items × warehouses, paginated)
└── /dashboards/stock/as-of/                Historical Stock Snapshot (SAP OINM reconstruction, requires ?as_of_date=)
```

---

## 3. Per-page detail

### 3.1 /dashboards — Root / landing

**Purpose:** Entry point for the Dashboards section. Acts as a navigation hub; the `/api/v1/dashboards/` path itself returns a 404 (no dedicated summary API). Individual sub-dashboards each hit their own API endpoints.

**API:** None at root level. Each child page loads independently.

---

### 3.2 /dashboards/dispatch-pipeline — Dispatch Pipeline Monitor

**Purpose:** Real-time wall-board view of all outbound dispatch sessions currently active at the factory gate. Shows exactly which trucks are inside the yard, which are awaiting a photo, which need a gatepass, and how many have departed — enabling gate security and dispatch supervisors to manage loading queues.

**API endpoint:** `GET /api/v1/gate-core/sales-dispatch/reports/`

**Key fields returned:**
- `counts.total` — total dispatches in current session window
- `counts.waiting_inside` — trucks still physically in the yard
- `counts.missing_photo` — dispatches without a truck photo (required before gatepass)
- `counts.gatepass_pending` — dispatches where gatepass not yet printed
- `counts.printed_not_committed` — gatepass printed but not committed (lock step)
- `counts.ready_for_dispatch` — all checks done, awaiting physical departure
- `counts.dispatched` — departed
- `counts.rejected_cancelled` — cancelled dispatches
- `counts.truck_with_photo` — how many trucks have photos attached
- `waiting_inside[]` — array of detailed dispatch records for trucks currently in yard, each with: `entry_no` (DOCK-series), `vehicle_entry_no` (DOCKV-series), customer name, invoice numbers (`sap_doc_num`), item summary, route, weight totals

**Live sample (Jivo Mart, 2026-06-29):**
```json
{
  "counts": {
    "total": 38,
    "waiting_inside": 3,
    "missing_photo": 2,
    "gatepass_pending": 2,
    "printed_not_committed": 0,
    "ready_for_dispatch": 1,
    "dispatched": 35,
    "rejected_cancelled": 0,
    "truck_with_photo": 36
  }
}
```
Sample waiting_inside record (DOCK-20260622-0010):
- Vehicle: DOCKV-20260622-0010, customer: BAGRRYS INDIA PRIVATE LIMITED
- Invoice: SAP doc 606260149, item: FG0000053 (COLD PRESS SUNFLOWER 5 LTR 4 PCS), 154 PCS, ₹1.31L
- Dispatch date: 2026-06-19, warehouse: BH-FGM

---

### 3.3 /dashboards/dispatch-plans — Dispatch Plans Kanban Board

**Purpose:** A kanban-style board showing every dispatch booking and its pipeline stage, from initial booking through to physical departure. Gives the logistics team a comprehensive view of all planned shipments simultaneously.

**API endpoint:** `GET /api/v1/dispatch-plans/pipeline/`

**Pipeline stages (in order):**
1. `BOOKED` — Invoice booked, dispatch plan created
2. `EMPTY_IN` — Empty truck entered gate (EVGI event recorded)
3. `READY_TO_DOCK` — Truck assigned to a docking slot
4. `DOCKED` — Truck docked and loading in progress
5. `PHOTO_ATTACHED` — Loaded-truck photo captured
6. `READY_FOR_GATEPASS` — QC/weight checks done, ready for gatepass
7. `GATEPASS_PRINTED` — Gatepass document printed
8. `PRINT_COMMITTED` — Gatepass committed (locked)
9. `DISPATCHED` — Truck departed gate
10. `REJECTED` — Dispatch cancelled/rejected

**Key fields per plan card:** `plan_id`, `stage`, `stage_label`, `sap_invoice_doc_num` (SAP invoice number), `invoice_number`, `vehicle_no`, `transporter_name`, `driver_name`, `customer_name`, `dispatch_date`, `place_of_supply`, `gate_out_entry_no` (DOCK-series), `empty_gate_in_entry_no` (EVGI-series), `gate_out_status`

**Live data (Jivo Mart):** 19 dispatch plans, all in DISPATCHED stage at time of capture. This means the kanban board renders only one occupied column for JIVO_MART — all active plans have already completed the full pipeline.

---

### 3.4 /dashboards/inventory-age — Inventory Age Dashboard

**Purpose:** Shows how long finished-goods (and select other item groups) stock has been sitting in each warehouse. Enables FIFO management, identifies slow-moving or at-risk stock before expiry, and feeds provisioning decisions. The age is calculated from `effective_date` (the date the stock entered SAP) to today.

This page has two sub-routes: a filter-options loader and the paginated report itself.

#### 3.4.1 /dashboards/inventory-age/filter-options/

**API endpoint:** `GET /api/v1/dashboards/inventory-age/filter-options/`

Returns reference data to populate the dashboard's filter dropdowns:

| Filter dimension | Values (count) |
|---|---|
| `item_groups` | 9 groups (CONSUMABLES 101, FINISHED 102, FIXED ASSETS 110, FLAV/PRESTV/INGRDNT 103, LAB INVENTORY 104, PACKAGING MATERIAL 105, RAW MATERIAL 106, SALES BOM 109, TRADING ITEMS 107) |
| `sub_groups` | 35 product sub-categories (CANOLA, OLIVE, MUSTARD, GHEE, SUNFLOWER, COCONUT, COFFEE, TEA, HONEY, RICE BRAN, GROUNDNUT, SESAME, SEEDS, etc.) |
| `varieties` | 75 variety/SKU labels (COLD PRESS, EXTRA LIGHT, POMACE, EXTRA VIRGIN, MUSTARD KACCHI GHANI, MUSTARD PAKKI GHANI, DESI GHEE, RICE BRAN, SUNFLOWER, BLENDED, GROUNDNUT, HONEY, etc.) |
| `warehouses` | 14 warehouses: BH-FG, BH-FGM, BH-FK, BH-GR, BH-JM, DL-EC, DL-FA, DL-FG, DL-GR, DL-MP, FBF-HR, KT-FBF, KT-FG, PB-FG |

#### 3.4.2 /dashboards/inventory-age/report/

**API endpoint:** `GET /api/v1/dashboards/inventory-age/report/`

Query params: `?warehouse=`, `?item_group=`, `?variety=`, `?sub_group=` (all optional filters); paginated.

**Key fields per row:**
| Field | Meaning |
|---|---|
| `item_code` | SAP item code (FG-prefix for finished goods) |
| `item_name` | Full product description |
| `is_litre` | Whether quantity unit represents litres |
| `item_group` | SAP item group name |
| `variety` | Product variety (e.g. COLD PRESS, POMACE, EXTRA LIGHT) |
| `sku` | Package size (e.g. 1 LTR, 5 LTR) |
| `sub_group` | Sub-category (e.g. CANOLA, OLIVE, MUSTARD) |
| `warehouse` | SAP warehouse code where stock sits |
| `on_hand` | Current quantity in stock |
| `litres` | Equivalent litres (same as on_hand when is_litre=true) |
| `in_stock_value` | Current stock value in ₹ |
| `calc_price` | Calculated price per unit in ₹ |
| `effective_date` | Date stock entered SAP (age reference date) |
| `days_age` | Days since effective_date (= age of this stock lot) |

**Live data totals (Jivo Mart, all warehouses, no filter):**
- 602 FG item-warehouse rows
- Total quantity: 448,965.9 units/litres
- Total value: ₹1,01,05,351 (~₹10.1 crore)
- 14 warehouses

**Sample records:**
```
FG0000004 COLD PRESS 5 LTR 4 PCS | BH-GR | on_hand=34, litres=34,
  value=₹15,300, calc_price=₹450, effective_date=2024-09-07, days_age=661

FG0000005 EXTRA LIGHT OLIVE 1 LTR 16 PCS | BH-FK | on_hand=2000, litres=2000,
  value=₹7,37,926, calc_price=₹368.96, effective_date=2024-09-07, days_age=661

FG0000009 EXTRA LIGHT OLIVE 5 LTR TIN 4 PCS | BH-GR | on_hand=3, litres=3,
  value=₹5,536, calc_price=₹1,845, effective_date=2024-09-07, days_age=661
```

Note: All items sampled show `effective_date=2024-09-07` and `days_age=661`, suggesting the effective date is pinned to the date the system was initialized/seeded — not dynamically updated per batch. This is a data quality concern.

---

### 3.5 /dashboards/non-moving — Non-Moving Raw Materials Dashboard

**Purpose:** Identifies raw materials and packaging materials that have not been consumed within a configurable number of days. Helps procurement and warehouse teams flag obsolete or excess RM stock.

**API endpoints:**
- Filter/reference: `GET /api/v1/non-moving-rm/item-groups/` — returns available item groups for filtering
- Report: `GET /api/v1/non-moving-rm/` — returns the non-moving items report (requires filter params to return data)

**Item groups available for filter (from `/non-moving-rm/item-groups/`):**
10 groups returned: CONSUMABLES (101), CONSUMABLES WITH INVENTORY (114), FA CONSUMABLES (112), FINISHED (102), FIXED ASSETS (110), LABORATORY APPARATUS (111), PACKAGING MATERIAL (105), RAW MATERIAL (106), SALES BOM (109), TRADING ITEMS (107)

**Key fields (from `/dashboards/stock/` which shares the schema):**
| Field | Meaning |
|---|---|
| `item_code` | SAP item code (PM-prefix for packaging, RM-prefix for raw material) |
| `item_name` | Item description |
| `warehouse` | Warehouse holding the stock |
| `on_hand` | Current quantity |
| `min_stock` | Minimum stock benchmark |
| `uom` | Unit of measure (PCS, KGS, etc.) |
| `stock_status` | health classification (none/healthy/low/critical) |
| `health_ratio` | ratio of on_hand to min_stock |
| `movement_status` | slow / normal / fast (based on consumption frequency) |
| `last_consumption_date` | Date of last SAP goods issue |
| `days_since_last_consumption` | Days with no consumption |
| `warehouse_count` | Number of warehouses holding this item |
| `has_warning` | Boolean flag for items that breach non-moving thresholds |

**Live data note:** The bare `/non-moving-rm/` endpoint returned no results when called without filters. With `?item_group_code=106` (RAW MATERIAL) it also returned empty. The filter-options endpoint returned item groups successfully. This is a report that likely requires a `days_threshold` query parameter (e.g. `?days_threshold=90`) or a selected item group to return non-empty results for JIVO_MART.

---

### 3.6 /dashboards/production-movement — Production Movement Report

**Purpose:** Shows daily stock movements (IN and OUT) for finished goods warehouses, tied to production events and dispatch transactions. Allows production supervisors to reconcile what was produced, issued to dispatch, and transferred during a date range.

**API endpoints:**
- Report: `GET /api/v1/production-execution/reports/production-movement/`
- Filter options: `GET /api/v1/production-execution/reports/production-movement/filter-options/`

**Query params:** `?date_from=YYYY-MM-DD&date_to=YYYY-MM-DD` (default = today), `?warehouse=` (filter to a specific warehouse), `?direction=in|out|all` (default=all), `?production_only=true|false` (default=true, filters to production-related transactions only)

**Filter options (from `/production-execution/reports/production-movement/filter-options/`):**
- Warehouses: BH-FGM (Bhakharpur finished goods), BH-FK (Bhakharpur Flipkart Packing), DL-MP (MAYAPURI FINISHED MAIN)
- Transaction types: 13 (AR Invoice), 14 (AR Credit), 15 (Delivery), 16 (Return), 18 (AP Invoice), 19 (AP Credit), 20 (GRPO), 21 (Return to Vendor), 59 (Goods Receipt), 60 (Goods Issue), 67 (Transfer), and others

**Key fields per movement row:**
| Field | Meaning |
|---|---|
| `date` | Transaction date (ISO timestamp) |
| `item_code` | SAP item code |
| `item_name` | Item description |
| `item_group` | Item group (FINISHED, RAW MATERIAL, etc.) |
| `warehouse` | SAP warehouse code |
| `warehouse_name` | Human-readable warehouse name |
| `in_qty` | Quantity entering warehouse |
| `out_qty` | Quantity leaving warehouse |
| `quantity` | Net transaction quantity |
| `direction` | IN or OUT |
| `transaction_value` | ₹ value (negative for OUT) |
| `abs_value` | Absolute value in ₹ |
| `transaction_type` | SAP transaction type code |
| `transaction_label` | Human label (AR Invoice, GRPO, Goods Issue, etc.) |
| `reference` | SAP document number (invoice/PO/transfer ref) |
| `doc_num` | Internal doc number |
| `created_by` | SAP user ID who created the transaction |

**Summary fields (in response root):**
- `summary.opening_qty`, `total_in_qty`, `total_out_qty`, `net_qty`, `closing_qty`
- `summary.total_value`, `net_value`
- `warehouse_summary[]` — per-warehouse breakdown
- `movement_type_summary[]` — per-transaction-type totals

**Live sample (Jivo Mart, 2026-06-29, all warehouses):**
```
date: 2026-06-29 | FG0000005 EXTRA LIGHT OLIVE 1 LTR 16 PCS | BH-FGM | OUT 48 PCS
  transaction_type=13 (AR Invoice), reference=606260192, value=-₹15,600

date: 2026-06-29 | FG0000142 COLD PRESS GROUNDNUT OIL 1 LTR 16 PCS | BH-FGM | OUT 672 PCS
  transaction_type=13 (AR Invoice), reference=606260192, value=-₹1,14,240
```

**Summary at capture (2026-06-29, production_only=true):**
- opening_qty: 367,644.8 units
- total_in_qty: 0.0, total_out_qty: 0.0 (no production-tagged transactions today)
- closing_qty: 367,644.8

Note: `production_only=true` by default means only SAP Goods Receipt (type 59) and Goods Issue (type 60) transactions appear. With `?production_only=false&date_from=2026-06-01&date_to=2026-06-30`, AR Invoice dispatch transactions (type 13) are visible.

---

### 3.7 /dashboards/sales-planning-requirement — Sales Planning vs. Requirement

**Purpose:** A monthly planning dashboard that compares the sales forecast (from SAP) with actual procurement requirements, factoring in current stock and open POs. Designed to surface net shortages so procurement can act. It is driven by a SAP HANA stored procedure (`SALES PLANNING VS REQUIREMENT_WEEKLY`) that must be manually refreshed.

**IMPORTANT: This dashboard is NOT operative for JIVO_MART.** The analysis endpoint explicitly lists `supported_companies: ["JIVO_BEVERAGES", "JIVO_OIL"]`. JIVO_MART is not in the supported list. All report data is empty (0 items, all summary fields = 0) and the status shows `latest=null, last_success=null`.

**API endpoints:**

#### 3.7.1 /dashboards/sales-planning-requirement/status/

`GET /api/v1/dashboards/sales-planning-requirement/status/`

Returns the timestamp of the most recent refresh attempt:
```json
{ "latest": null, "last_success": null }
```
Both null for JIVO_MART (never run).

#### 3.7.2 /dashboards/sales-planning-requirement/refresh/

`POST /api/v1/dashboards/sales-planning-requirement/refresh/`

Triggers a manual refresh of the SAP procedure. GET is not allowed (405).

#### 3.7.3 /dashboards/sales-planning-requirement/report/

`GET /api/v1/dashboards/sales-planning-requirement/report/`

Returns paginated planning gap rows:
**Key fields per row (schema from analysis):**
| Field | Meaning |
|---|---|
| `item_code` | SAP item code |
| `item_name` | Item description |
| `planning_month` | Planning cycle name |
| `forecast_name` | SAP forecast/plan name |
| `planned_qty` | Forecasted sales/production quantity |
| `base_required_qty` | BOM-derived raw requirement |
| `min_stock` | Safety stock floor |
| `stock_in_hand` | Current SAP stock |
| `required_qty` | Final gap after stock consideration |
| `open_po_qty` | Open PO quantity covering the requirement |
| `net_shortage_qty` | Remaining uncovered shortage |
| `report_execution_at` | SAP procedure run timestamp |

**Summary fields:** `total_items`, `total_planned_qty`, `total_base_required_qty`, `total_required_qty`, `total_min_stock`, `total_stock_in_hand`, `total_open_po_qty`, `total_net_shortage_qty`, `shortage_items`, `po_covered_items`, `open_po_coverage_percent`

**Live data for JIVO_MART:** `data: [], summary: all zeros` — not populated.

#### 3.7.4 /dashboards/sales-planning-requirement/analysis/

`GET /api/v1/dashboards/sales-planning-requirement/analysis/`

Returns procedure metadata and Postgres table schema:
```json
{
  "procedure_name": "SALES PLANNING VS REQUIREMENT_WEEKLY",
  "company_code": "JIVO_MART",
  "supported_companies": ["JIVO_BEVERAGES", "JIVO_OIL"],
  "procedure_output": [],
  "scheduler": {
    "frequency": "Monthly",
    "command": "python manage.py run_sales_planning_requirement_scheduler",
    "default_cron": { "day": 1, "hour": 2, "minute": 30 }
  }
}
```

---

### 3.8 /dashboards/sap-plan — SAP Production Plan Dashboard

**Purpose:** Shows open SAP production orders and their component-level status, highlighting any component shortfalls that would prevent completion. This is the production planning team's quick check on whether materials are available to execute the current production schedule.

**API endpoints:**
- `GET /api/v1/sap/plan-dashboard/summary/` — production order summary (one row per order)
- `GET /api/v1/sap/plan-dashboard/details/` — same orders with full component breakdown per order
- `GET /api/v1/sap/plan-dashboard/procurement/` — only orders where components have a shortfall

**Key fields — production order:**
| Field | Meaning |
|---|---|
| `prod_order_entry` | SAP production order entry (internal id) |
| `prod_order_num` | SAP production order number |
| `sku_code` | FG item code being produced |
| `sku_name` | FG item name |
| `planned_qty` | Target production quantity |
| `completed_qty` | Quantity already completed/issued |
| `status` | SAP order status (released, etc.) |
| `due_date` | Production target date |
| `post_date` | Posting date |
| `priority` | Order priority |
| `warehouse` | Target warehouse |
| `total_components` | Number of BOM component lines |
| `components_with_shortfall` | How many components have insufficient stock |
| `total_remaining_component_qty` | Remaining unissued component quantity |

**Key fields — component (details endpoint only):**
| Field | Meaning |
|---|---|
| `component_code` | Component item code |
| `component_name` | Component description |
| `component_planned_qty` | Required component quantity |
| `component_issued_qty` | Already issued to production |
| `component_remaining_qty` | Still needed |
| `stock_on_hand` | SAP inventory on hand |
| `stock_committed` | Already committed to other orders |
| `stock_on_order` | Open PO quantity |
| `net_available` | on_hand − committed |
| `shortfall_qty` | Max(0, remaining − net_available) |
| `stock_status` | sufficient / shortage |
| `vendor_lead_time` | Vendor lead time in days |
| `default_vendor` | Default vendor name |

**Live data (Jivo Mart):**
- **Summary:** 1 production order — prod_order_num=825926501, FG0000326 "SANO POMACE 1+1 LTR", planned=160, completed=160, status=released, due_date=2025-08-19, warehouse=DL-MP, 0 components with shortfall
- **Details:** 1 component — FG0000150 "SANO POMACE OLIVE 1 LTR 16 PCS", planned_qty=320, issued=320, remaining=0, stock_on_hand=12,720, net_available=952, shortfall=0, stock_status=sufficient
- **Procurement (shortfall view):** Empty — no components currently in shortage

Note: The production order (due date 2025-08-19) is a historical completed order still visible in the SAP plan view. The component (FG0000150) being used as a BOM input for another FG (FG0000326 SANO POMACE 1+1 LTR COMBO) is an unusual case of a finished good becoming a component in a higher-order BOM (a sales combo/kit assembly).

---

### 3.9 /dashboards/stock-levels — Stock Levels (entry page)

**Purpose:** Navigation entry point / alias for the stock level views. Renders the same stock data as `/dashboards/stock/` but may show the summary/filter UI before the paginated table loads.

**API:** Same as `/dashboards/stock/` below.

---

### 3.10 /dashboards/stock/ — Live Stock Levels Dashboard

**Purpose:** Comprehensive per-item per-warehouse stock health dashboard covering all 33 JIVO_MART warehouses and all item types. For each item-warehouse combination, shows current on-hand quantity, minimum stock benchmark, and a health classification (healthy/low/critical/none). Also tracks movement velocity (slow/normal/fast) and when each item last had a consumption event.

**API endpoint:** `GET /api/v1/dashboards/stock/`

Query params: `?item_group=` (filter by item group name e.g. FINISHED), `?warehouse=`, `?stock_status=`, `?movement_status=`; paginated with `?page=` and `?page_size=`.

**Key fields per row:**
| Field | Meaning |
|---|---|
| `item_code` | SAP item code (FG/PM/RM prefix) |
| `item_name` | Item description |
| `warehouse` | SAP warehouse code |
| `on_hand` | Current quantity on hand |
| `min_stock` | Minimum stock level (benchmark) |
| `uom` | Unit of measure (PCS, KGS, LTR, etc.) |
| `stock_status` | `none` (no benchmark set), `healthy` (on_hand ≥ min_stock), `low` (0 < on_hand < min_stock), `critical` (on_hand = 0 and min_stock > 0) |
| `health_ratio` | on_hand / min_stock (0 if min_stock = 0) |
| `movement_status` | `slow` (rarely consumed), `normal`, or `fast` (high turnover) |
| `last_consumption_date` | Date of last SAP goods issue against this item |
| `days_since_last_consumption` | Integer days since last goods issue (null if never consumed) |
| `warehouse_count` | How many warehouses hold this item |
| `has_warning` | True if the item breaches any warning threshold |

**Meta (response root):**
- `total_items` — total item-warehouse rows matching filter
- `healthy_count`, `low_stock_count`, `critical_stock_count` — aggregate status counts
- `warehouses[]` — list of all warehouse codes in scope

**Live data (Jivo Mart, no filter, 2026-06-29):**
- **43,575** item-warehouse rows across **33 warehouses**
- `healthy_count: 0`, `low_stock_count: 0`, `critical_stock_count: 0`
- All rows show `stock_status: "none"` and `health_ratio: 0.0` because `min_stock` is universally 0 (no minimum stock benchmarks have been configured in the system for any item)
- All sampled rows show `movement_status: "slow"` (no recent consumption events)

Warehouses covered: 01, BH-DRP, BH-FG, BH-FGM, BH-FK, BH-GR, BH-GRM, BH-INT, BH-JM, BH-LR, BH-PF, BH-PP, DL-EC, DL-FA, DL-FG, DL-GG, DL-GR, DL-INT, DL-ISD, DL-IT, DL-MP, DL-OT, DP-DL, DP-HR, DP-PB, FBF-HR, GM-HR, KT-FBF, KT-FG, PB-FG, PB-INT, RJ-FG, UP-FG

---

### 3.11 /dashboards/stock/as-of/ — Historical Stock Snapshot

**Purpose:** Reconstructs what the stock position looked like at any past date, using SAP OINM (inventory movement) history. Useful for audits, month-end closes, and reconciliations where the current live stock is not sufficient.

**API endpoint:** `GET /api/v1/dashboards/stock/as-of/?as_of_date=YYYY-MM-DD`

Required parameter: `as_of_date` (returns a 400 error if omitted).

**Key fields:** Same schema as `/dashboards/stock/` above (item_code, item_name, warehouse, on_hand, min_stock, uom, stock_status, health_ratio, movement_status, last_consumption_date, days_since_last_consumption, warehouse_count, has_warning).

**Meta additional field:**
- `as_of_date` — the requested date
- `reconstruction_note` — "On-hand and movement age are reconstructed from SAP OINM. Benchmark and item master fields are current SAP values."

**Live data (Jivo Mart, as_of_date=2026-06-30):**
- **43,575** rows (same item-warehouse count as live endpoint)
- All min_stock = 0, same status classification issues as live endpoint
- total_pages: 14,525 (at page_size=3)

---

## 4. Workflows (multi-step flows + statuses)

### 4.1 Dispatch Pipeline workflow

The dispatch pipeline page tracks trucks through the full outbound flow visible in the gate and docking modules:

```
SAP Invoice Created
  → BOOKED (dispatch plan created in system)
  → EMPTY_IN (truck enters gate empty: EVGI-series entry)
  → READY_TO_DOCK (truck assigned to loading dock)
  → DOCKED (loading in progress: DOCKV-series vehicle entry)
  → PHOTO_ATTACHED (truck + load photo taken and uploaded)
  → READY_FOR_GATEPASS (supervisor sign-off, scan validation complete)
  → GATEPASS_PRINTED (DOCK-series gatepass document printed)
  → PRINT_COMMITTED (gatepass committed/locked — irreversible)
  → DISPATCHED (truck physically departed gate: gate-out logged)
  ↘ REJECTED (at any stage prior to commitment)
```

This pipeline is visible in the Dispatch Plans page (`/dispatch-plans/pipeline/`) as a kanban board and in the Dispatch Pipeline page (`/gate-core/sales-dispatch/reports/`) as a status summary with truck lists.

### 4.2 Sales Planning Requirement refresh workflow

```
Manual trigger (POST /dashboards/sales-planning-requirement/refresh/)
  OR Monthly cron (1st of month, 02:30)
    → Django calls SAP HANA stored procedure SALES PLANNING VS REQUIREMENT_WEEKLY
    → Procedure returns planning rows for supported companies (JIVO_OIL, JIVO_BEVERAGES)
    → App replaces rows in postgres table for that company inside a transaction
    → Status endpoint updated: latest = run time, last_success = if no error
```

Note: This workflow does not execute for JIVO_MART (not a supported company in the procedure).

### 4.3 Inventory Age — age calculation

Age is static from `effective_date` in SAP (the date the batch was first received/produced). It is not a rolling "days-in-current-location" metric — once `effective_date` is set, `days_age` grows continuously. All current JIVO_MART records show effective_date=2024-09-07 (system initialization date), making `days_age` uniform (~661 days) and not meaningful for FIFO management until SAP batch data is maintained properly.

---

## 5. Cross-section connections

| Dashboard | Links to / consumes from |
|---|---|
| Dispatch Pipeline | Gate module: SalesDispatch (DOCK-series), VehicleEntry (DOCKV-series), EmptyVehicleGateIn (EVGI-series), Arrival (ARV-series). DispatchPlan for booking context. |
| Dispatch Plans | DispatchPlan entity (covers booking → dispatch). Links to Gate (EVGI gate-in, DOCK gate-out), Barcode (scan completion before gatepass), GRPO Service (bilty/freight). |
| Inventory Age | SAP FG warehouse stock (OITM + OINM). Cross-references Barcode boxes (item_code = FG-prefix), Warehouse WMS (warehouse codes). |
| Non-Moving RM | SAP RM/PM item master. Cross-references Procurement (PO/GRPOs bring RM in), Production (goods issues consume RM out). |
| Production Movement | Production Execution module: uses SAP OINM movements. Transaction types include GRPO (RM in), AR Invoice (FG dispatch), Goods Issue (RM to production), Goods Receipt (FG from production). |
| Sales Planning Req. | SAP HANA procedure output. Cross-references PO data (open_po_qty). Only active for JIVO_OIL and JIVO_BEVERAGES. |
| SAP Plan | SAP production orders (via OINM). Component codes link to OITM item master; component warehouses link to Warehouse WMS. |
| Stock Levels | SAP OITM + OINM. Same warehouse codes as WMS module. Item codes span all item groups (FG, PM, RM, etc.). min_stock field would link to SAP item benchmarks if configured. |
| Stock As-Of | SAP OINM (inventory movement history). Reconstruction of any historical date. |

---

## 6. Data presence for Jivo Mart — which pages have live data vs empty

| Dashboard page | API endpoint(s) | Live data? | Count / detail |
|---|---|---|---|
| Dispatch Pipeline | `/gate-core/sales-dispatch/reports/` | **YES** | 38 dispatches: 35 departed, 3 waiting in yard, 36 with photos |
| Dispatch Plans | `/dispatch-plans/pipeline/` | **YES** | 19 plans, all in DISPATCHED stage (pipeline fully shifted) |
| Inventory Age — filter options | `/dashboards/inventory-age/filter-options/` | **YES** | 9 item groups, 35 sub_groups, 75 varieties, 14 warehouses |
| Inventory Age — report | `/dashboards/inventory-age/report/` | **YES** | 602 FG rows, ₹10.1 crore total, 14 warehouses; but days_age all ~661 (static effective_date, see note) |
| Non-Moving RM — item groups | `/non-moving-rm/item-groups/` | **YES** | 10 item groups returned |
| Non-Moving RM — report | `/non-moving-rm/` | **EMPTY** (needs filter params) | No data returned without `?item_group_code=` or `?days_threshold=` |
| Production Movement | `/production-execution/reports/production-movement/` | **YES (with date filter)** | Live AR Invoice movements on 2026-06-29; defaults to production_only=true (today = empty). opening_qty=367,644.8 |
| Sales Planning — status | `/dashboards/sales-planning-requirement/status/` | **EMPTY (not configured)** | latest=null, last_success=null; JIVO_MART not a supported company |
| Sales Planning — report | `/dashboards/sales-planning-requirement/report/` | **EMPTY (not configured)** | data=[], all summary totals=0 |
| Sales Planning — analysis | `/dashboards/sales-planning-requirement/analysis/` | **YES (metadata only)** | Procedure name, schema, scheduler config returned; supported_companies does NOT include JIVO_MART |
| SAP Plan — summary | `/sap/plan-dashboard/summary/` | **YES (sparse)** | 1 production order (825926501, FG0000326, completed, due 2025-08-19) |
| SAP Plan — details | `/sap/plan-dashboard/details/` | **YES (sparse)** | Same 1 order, 1 component (FG0000150, fully issued, 0 shortfall) |
| SAP Plan — procurement | `/sap/plan-dashboard/procurement/` | **EMPTY** | No components with shortfall |
| Stock Levels | `/dashboards/stock/` | **YES** | 43,575 item-warehouse rows, 33 warehouses; ALL stock_status="none" (min_stock never set) |
| Stock As-Of | `/dashboards/stock/as-of/?as_of_date=` | **YES** | 43,575 rows reconstructed from SAP OINM; requires date param |

### Summary of configuration gaps

1. **Sales Planning vs. Requirement** — fully unsupported for JIVO_MART. The SAP HANA procedure only runs for JIVO_OIL and JIVO_BEVERAGES. The page will show empty data for JIVO_MART permanently unless the procedure is extended.

2. **Stock health classifications** — all 43,575 items show `stock_status="none"` because `min_stock=0` for every item. This makes the healthy/low/critical counts meaningless. No minimum stock benchmarks have been configured.

3. **Inventory age** — all items share `effective_date=2024-09-07` (system initialization seed date), making `days_age` a uniform ~661 days and not useful for actual FIFO/age management. Per-batch effective dates need to be maintained in SAP.

4. **Non-moving RM** — the report endpoint requires explicit filter parameters to return results. A bare call returns nothing. The UI presumably supplies default filters on load.

5. **Production movement** — defaults to `production_only=true`, which shows only Goods Receipt (59) and Goods Issue (60) transactions. For JIVO_MART's current production data (all production module records empty), this gives 0 rows for today unless you widen to include AR Invoices.

---

## Reference — UI routes (from bundle)
- `/dashboards`
- `/dashboards/dispatch-pipeline`
- `/dashboards/dispatch-plans`
- `/dashboards/inventory-age`
- `/dashboards/inventory-age/filter-options/`
- `/dashboards/inventory-age/report/`
- `/dashboards/non-moving`
- `/dashboards/production-movement`
- `/dashboards/sales-planning-requirement`
- `/dashboards/sales-planning-requirement/analysis/`
- `/dashboards/sales-planning-requirement/refresh/`
- `/dashboards/sales-planning-requirement/report/`
- `/dashboards/sales-planning-requirement/status/`
- `/dashboards/sap-plan`
- `/dashboards/stock-levels`
- `/dashboards/stock/`
- `/dashboards/stock/as-of/`

## Reference — captured API endpoints + record counts (this section)
- `/dashboards/inventory-age/filter-options/` -> 1 object (9 item groups, 35 sub-groups, 75 varieties, 14 warehouses)
- `/dashboards/inventory-age/report/` -> 602 FG rows, ₹10.1 crore total value, 14 warehouses
- `/dashboards/sales-planning-requirement/analysis/` -> 1 object (procedure metadata; JIVO_MART not supported)
- `/dashboards/sales-planning-requirement/report/` -> 0 rows (JIVO_MART not supported)
- `/dashboards/sales-planning-requirement/status/` -> 1 object (latest=null, last_success=null)
- `/dashboards/stock/` -> 43,575 item-warehouse rows, 33 warehouses
- `/dashboards/stock/as-of/` -> 43,575 rows (requires ?as_of_date=)
- `/non-moving-rm/item-groups/` -> 10 item groups
- `/non-moving-rm/` -> empty without filter params
- `/sap/plan-dashboard/summary/` -> 1 production order (825926501 / FG0000326)
- `/sap/plan-dashboard/details/` -> 1 order, 1 component (FG0000150, no shortfall)
- `/sap/plan-dashboard/procurement/` -> 0 components with shortfall
- `/gate-core/sales-dispatch/reports/` -> counts object (38 total, 35 dispatched, 3 waiting)
- `/dispatch-plans/pipeline/` -> 19 plans, all DISPATCHED stage
- `/production-execution/reports/production-movement/` -> live movements (requires date params for non-empty data)
- `/production-execution/reports/production-movement/filter-options/` -> 3 warehouses, 12+ transaction types

Linked: [[docs/factory/FACTORY_MAP|FACTORY_MAP]] · [[docs/FACTORY_CLI_PLAN|FACTORY_CLI_PLAN]] · [[docs/READ_ONLY_LAW|READ_ONLY_LAW]]
