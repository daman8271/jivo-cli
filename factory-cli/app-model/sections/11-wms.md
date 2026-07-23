---
title: "WMS — Jivo Mart app-model"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: reference
tags: [jivogpt, factory-cli, wms]
---

# WMS — Jivo Mart app-model

> **Provenance — imported 2026-07-19; source snapshot 2026-06-30.** This note came from the JIVO_MART-only `daman8271/jivo-factory-intel` baseline. For the current three-company study and the live-verified 2026-07-19 state, use [[docs/factory/FACTORY_MAP|FACTORY_MAP]] and [[CLI/factory-cli/README|the current CLI guide]].
> STATUS: COMPLETE. Documented 2026-06-30. Jivo Mart (JIVO_MART) only.

## 1. Purpose — what this section is for in the factory

The WMS (Warehouse Management System) section is the **finished-goods inventory control tower** for Jivo Mart. It provides a single pane of glass over all 31 warehouses—from the Bhakharpur factory floor to regional distribution points across Delhi, Haryana, Karnataka, Punjab, Rajasthan, and Uttar Pradesh.

Core functions:
- **Real-time stock visibility** — on-hand, committed, and available quantities per SKU per warehouse, with health indicators (low/critical/zero/overstock).
- **Batch / expiry monitoring** — tracks every SAP batch number with its expiry status across all warehouse locations.
- **Inter-warehouse transfer management** — records and tracks SAP inventory transfer documents as goods move between factory, transit, and regional warehouses.
- **Sales order backlog** — surfaces all open (unfulfilled) SAP sales order lines so warehouse staff can prioritise dispatch.
- **GRPO billing reconciliation** — reconciles production goods-receipts (GRPO) against billing to surface unbilled stock (i.e., goods received but not yet invoiced to the receiving entity).
- **Stock movement ledger** — a chronological log of every inbound (GRPO), outbound (AR_INVOICE), and transfer movement with SAP document reference.

The WMS section does **not** handle gate entries, barcode scanning, or dispatch session creation — those belong to the Gate, Barcode, and Dispatch sections respectively. WMS is the stock-level layer that sits on top of SAP inventory data.

---

## 2. Page tree

```
/wms                          ← WMS home — KPI dashboard
├── /wms/warehouses           ← Warehouse directory + per-warehouse stock summary
├── /wms/stock                ← Stock overview (per-SKU, per-warehouse) + movement ledger
│   └── (sub-view)            ← Stock movements (ledger of individual transactions)
├── /wms/batches              ← Batch expiry tracker (all active batches, expiry status)
├── /wms/orders               ← Sales order backlog (open unfulfilled SAP sales orders)
├── /wms/billing              ← GRPO billing overview (received-vs-billed reconciliation)
└── /wms/transfers            ← Inter-warehouse transfer overview (active SAP transfers)
```

### Page descriptions

| Route | What it does |
|---|---|
| `/wms` | Dashboard landing: headline KPIs (total items, on-hand quantity, total value, health counts), stock breakdown by warehouse and item group, top 10 items by value, and the 20 most recent stock movements. |
| `/wms/warehouses` | List of all configured warehouses with per-warehouse summary (item count, on-hand qty, stock value, alert counts). Allows drill-down to a single warehouse's stock profile. |
| `/wms/stock` | Paginated table of all SKU-warehouse combinations (953 lines for Jivo Mart) with on-hand, committed, on-order, available qty, avg price, stock value, and stock status. Filters by warehouse, item group, status. |
| `/wms/stock` (movements sub-view) | Chronological ledger of all inventory movements: each line shows date, item, warehouse, in_qty / out_qty, direction (IN/OUT), transaction_type (GRPO / TRANSFER / AR_INVOICE), SAP reference number, and doc_num. |
| `/wms/batches` | Table of all active SAP batch numbers (300 visible) with item, warehouse, quantity, manufacturing date, expiry date, days_to_expiry, and expiry_status (NO_EXPIRY / OK / WARNING / CRITICAL / EXPIRED). Summary KPIs at top. |
| `/wms/orders` | Sales order backlog: summary (total orders, lines, open qty, warehouse count), breakdown by warehouse, and full line-by-line list. Each line: SAP doc_entry/doc_num, doc_date, due_date, customer, item, warehouse, ordered_qty, open_qty, delivered_qty, fulfillment_pct. |
| `/wms/billing` | GRPO-to-billing reconciliation: summary (total received/billed/unbilled qty and value, counts by billing status), then per-item detail rows. Each row: item, warehouse, received_qty/value, billed_qty/value, unbilled_qty/value, status (FULLY_BILLED / PARTIALLY_BILLED / UNBILLED), first and last GRPO date. |
| `/wms/transfers` | Overview of recent SAP inventory transfer documents: summary (transfer count, line count, total qty, route count), route-level aggregates (from/to warehouse, count, lines, qty), and full line-by-line transfer list. |

---

## 3. Per-page detail

### 3.1 `/wms` — Dashboard

**Purpose:** Executive-level KPI landing page for finished-goods inventory health.

**API endpoint:** `GET /warehouse/wms/dashboard/`

**Key fields returned:**
- `kpis`: total_items, total_on_hand, total_value, low_stock, critical_stock, zero_stock, overstock
- `stock_by_warehouse[]`: warehouse_code, items, value
- `stock_by_group[]`: group_name, items, value
- `top_items_by_value[]`: item_code, item_name, quantity, value
- `stock_health`: normal, low, critical, zero, overstock (counts)
- `recent_movements[]`: date, item_code, item_name, warehouse, in_qty, out_qty, direction, quantity

**Live sample (Jivo Mart, pulled 2026-06-30):**
```
KPIs:
  total_items:    268 distinct SKUs
  total_on_hand:  448,965.9 units
  total_value:    ₹9,96,21,731.23 (~₹9.96 crore)
  low_stock:      0
  critical_stock: 0
  zero_stock:     0
  overstock:      0
  stock_health.normal: 268 (all items classified normal)

Top 3 warehouses by value:
  BH-FGM  (Bhakharpur finished goods):     52 items, ₹5,94,41,180
  DL-MP   (Mayapuri Finished Main):       156 items, ₹1,32,21,334
  DL-GR   (Mayapuri GR):                 112 items,   ₹60,33,646

Stock by item group:
  FINISHED:           180 items, ₹9,63,61,677 (dominant — 96.7% of value)
  PACKAGING MATERIAL:  26 items,  ₹27,77,877
  TRADING ITEMS:       19 items,   ₹2,88,083
  FIXED ASSETS:         6 items,   ₹1,94,093

Top 3 items by value:
  FG0000009  EXTRA LIGHT OLIVE 5 LTR TIN 4 PCS        6,147 units  ₹99,88,875
  FG0000151  SANO POMACE OLIVE 5 LTR TIN 4 PCS        6,145 units  ₹76,81,250
  FG0000011  MUSTARD KACCHI GHANI 5 LTR 4 PCS        10,116 units  ₹75,87,000

Most recent movement (2026-06-29):
  FG0000424  FIRST PRESSED MUSTARD OIL 1 LTR 20 PCS  DL-FG  OUT 1,000 units
```

---

### 3.2 `/wms/warehouses` — Warehouse Directory + Summary

**Purpose:** Lists all 31 configured SAP warehouses and shows which ones have active stock.

**API endpoints:**
- `GET /warehouse/wms/warehouses/` — full warehouse master list (31 warehouses, name + code)
- `GET /warehouse/wms/warehouses/summary/` — per-warehouse stock summary (18 warehouses have non-zero on-hand)

**Key fields from warehouses/**
- `warehouses[]`: code, name

**Key fields from warehouses/summary/**
- `warehouses[]`: warehouse_code, warehouse_name, total_items, total_on_hand, total_value, low_stock_count, critical_stock_count, overstock_count, zero_stock_count

**Live sample — full warehouse list (31 total, Jivo Mart, 2026-06-30):**

*Bhakharpur (factory site):*
| Code | Name |
|------|------|
| BH-FG | Bhakharpur Finished Basement |
| BH-FGM | Bhakharpur finished goods |
| BH-FK | Bhakharpur Flipkart Packing |
| BH-GR | Bhakharpur GR |
| BH-GRM | Bhakharpur Return Stock |
| BH-INT | Bhakharpur Finished INTRANSIT |
| BH-JM | Bhakharpur Jivo mart |
| BH-LR | Luhari Jhajjar Finished |
| BH-PF | Bhakharpur Production Finished 1st Floor |

*Delhi/Mayapuri (distribution hub):*
| Code | Name |
|------|------|
| DL-EC | Mayapuri E-Commerce |
| DL-FA | MAYAPURI FIXED ASSET GODOWN |
| DL-FG | MAYAPURI (GODAMWALA) FINISHED |
| DL-GG | DELHI MAYAPURI VIRTUAL GODOWN |
| DL-GR | Mayapuri GR |
| DL-INT | MAYAPURI FINISHED INTRANSIT |
| DL-ISD | DELHI ISD |
| DL-IT | DELHI JIVO IT |
| DL-MP | MAYAPURI FINISHED (MAIN) |
| DL-OT | PARAM |

*Regional & drop-ship:*
| Code | Name |
|------|------|
| DP-DL / DP-HR / DP-PB | Dropship Delhi / Haryana / Punjab |
| FBF-HR | HARYANA FBF GODOWN |
| GM-HR | GURUGRAM HARYANA |
| KT-FBF / KT-FG | Karnataka Finished New Godown / Karnataka Finished |
| PB-FG / PB-INT | Punjab Haryana / Punjab INTRANSIT |
| RJ-FG | Rajasthan Finished |
| UP-FG | Uttar Pradesh Finished |

**Live sample — warehouse summary (top 6 by on-hand value):**
```
BH-FGM  Bhakharpur finished goods:   71 items  189,308 units  ₹5,94,41,180
DL-MP   Mayapuri Finished (Main):   181 items  165,636 units  ₹1,32,21,334
DL-GR   Mayapuri GR:                123 items   12,828 units    ₹60,33,646
DL-FG   Mayapuri (Godamwala):       126 items   26,366 units    ₹52,94,355
DL-EC   Mayapuri E-Commerce:         94 items   20,022 units    ₹53,77,067
BH-JM   Bhakharpur Jivo mart:        19 items   13,194 units    ₹40,08,339
```

Zero-stock warehouses (items configured but no current on-hand): BH-PF, DL-GG, DL-INT, GM-HR (these are staging or virtual warehouses that zero out after transfers complete).

---

### 3.3 `/wms/stock` — Stock Overview

**Purpose:** Per-SKU, per-warehouse inventory snapshot showing the full supply/demand picture (on-hand vs committed vs on-order vs available).

**API endpoint:** `GET /warehouse/wms/stock/overview/` (paginated, 953 total SKU-warehouse lines, 50 per page)

**Key fields:**
- `summary`: total_items, total_on_hand, total_committed, total_available, total_value
- `items[]`: item_code, item_name, item_group, uom, warehouse_code, on_hand, committed, on_order, available, avg_price, stock_value, min_level, max_level, last_purchase_price, stock_status (NORMAL / ZERO)

**Live sample (first page, BH-FG warehouse, 2026-06-30):**
```
Summary: 953 lines, on-hand 448,965.9, committed 1,422,314, available -973,348.1, value ₹9.96cr

FG0000004  COLD PRESS 5 LTR 4 PCS         BH-FG  on_hand:4   committed:220   on_order:240  available:-216  NORMAL
FG0000005  EXTRA LIGHT OLIVE 1 LTR 16 PCS BH-FG  on_hand:0   committed:2400  on_order:400  available:-2400 ZERO
FG0000011  MUSTARD KACCHI GHANI 5 LTR 4PCS BH-FG on_hand:0   committed:5191  on_order:0    available:-5191 ZERO
FG0000142  COLD PRESS GROUNDNUT OIL 1L 16PCS BH-FG on_hand:0 committed:20940 on_order:20400 avail:-20940   ZERO
```

**Notable pattern:** The overall available quantity is deeply negative (-973,348 units). Almost every warehouse-SKU line at BH-FG shows ZERO on-hand with large committed quantities. This means Jivo Mart's entire stock of finished goods committed to sales orders exceeds its physical on-hand. The company relies on daily production (incoming GRPOs) to service ongoing commitments.

---

### 3.4 `/wms/stock` (movements sub-view) — Stock Movement Ledger

**Purpose:** Chronological audit log of every inventory movement in SAP: production receipts (GRPO), inter-warehouse transfers (TRANSFER), and sales outflows (AR_INVOICE).

**API endpoint:** `GET /warehouse/wms/stock/movements/`

**Key fields:**
- `movements[]`: date, item_code, item_name, warehouse_code, in_qty, out_qty, quantity, direction (IN/OUT), transaction_type, reference (SAP doc number string), doc_num (SAP internal), created_by (user id)

**Transaction types observed:**
| Type | Meaning |
|------|---------|
| GRPO | Goods Receipt Purchase Order — production batch arrives into a warehouse (IN movement) |
| TRANSFER | Inter-warehouse transfer (paired IN and OUT across two warehouse lines) |
| AR_INVOICE | Outbound sales invoice — goods leave a warehouse to a customer (OUT movement) |

**Live sample (2026-06-29 movements, 2026-06-30 pull):**
```
GRPO inbound (ref 2006264558) into BH-FGM:
  FG0000032  COLD PRESS 1 LTR 20 PCS         IN  6,540 units
  FG0000005  EXTRA LIGHT OLIVE 1 LTR 16 PCS  IN  7,160 units
  FG0000393  COLD PRESS GROUNDNUT 200MLS 70PCS IN 7,840 units
  FG0000030  MUSTARD KACHI GHANI 1 LTR 20 PCS IN 11,150 units

TRANSFER (BH-FGM → DL-INT, ref 626674697):
  FG0000030  MUSTARD KACHI GHANI 1 LTR 20 PCS  OUT BH-FGM  4,240 units  doc 263356
                                                 IN  DL-INT  4,240 units  doc 263357

AR_INVOICE outbound from BH-FGM (ref 606260192):
  FG0000030  MUSTARD KACHI GHANI 1 LTR 20 PCS  OUT  6,780 units  doc 263377
  FG0000142  COLD PRESS GROUNDNUT OIL 1 LTR     OUT 15,008 units  doc 263341
```

SAP doc_num values in the 263,000 range observed for 2026-06-29, indicating high transaction volume.

---

### 3.5 `/wms/batches` — Batch Expiry Tracker

**Purpose:** Monitors SAP batch numbers across all warehouses to surface batches approaching expiry (edible oils require FSSAI date tracking).

**API endpoint:** `GET /warehouse/wms/batches/expiry/`

**Key fields:**
- `summary`: batch_count, expired_count, critical_count, warning_count, ok_count, total_quantity
- `batches[]`: item_code, item_name, batch_number, expiry_date, manufacturing_date, sap_status, warehouse_code, quantity, days_to_expiry, expiry_status

**Expiry statuses:** NO_EXPIRY, OK, WARNING, CRITICAL, EXPIRED

**Live sample (2026-06-30):**
```
Summary:
  batch_count:    300 (sampled)
  expired_count:  0
  critical_count: 0
  warning_count:  0
  ok_count:       0
  total_quantity: 104,593 units

Sample records:
  FG0000004  COLD PRESS 5 LTR 4 PCS    batch 123213456  BH-FGM  20 units   expiry_status: NO_EXPIRY  expiry_date: ""
  FG0000004  COLD PRESS 5 LTR 4 PCS    batch 121345     BH-FGM  3,900 units expiry_status: NO_EXPIRY  expiry_date: ""
  FG0000005  EXTRA LIGHT OLIVE 1L 16PCS batch 20250207MJ414  FBF-HR  972 units  expiry_status: NO_EXPIRY expiry_date: ""
  FG0000009  EXTRA LIGHT OLIVE 5L TIN   batch 123154     BH-FGM  2,288 units expiry_status: NO_EXPIRY
```

**Important data quality observation:** All 300 sampled batches have `expiry_date: ""` and `manufacturing_date: ""` with `days_to_expiry: null` and `expiry_status: "NO_EXPIRY"`. Batch numbers themselves appear inconsistent — some follow a dated format (e.g. `20250207MJ401` = 7 Feb 2025, suffix MJ401) while many are arbitrary numeric strings (e.g. `123213456`, `5155`, `421564`). The system infrastructure for expiry tracking is in place but expiry dates have not been consistently populated in SAP for Jivo Mart's batches. The "ok_count: 0" despite batch_count: 300 confirms no date is populated at all.

---

### 3.6 `/wms/orders` — Sales Order Backlog

**Purpose:** Surfaces all open SAP sales order lines (lines that have not been fully delivered) to help warehouse staff understand what needs to be picked and shipped.

**API endpoint:** `GET /warehouse/wms/sales-orders/backlog/`

**Key fields:**
- `summary`: order_count, line_count, open_quantity, warehouse_count
- `warehouses[]`: warehouse_code, order_count, line_count, open_quantity
- `lines[]`: doc_entry, doc_num, doc_date, due_date, customer_code, customer_name, line_num, item_code, item_name, warehouse_code, ordered_qty, open_qty, delivered_qty, fulfillment_pct

**Live sample (2026-06-30):**
```
Summary:
  order_count:    86 open sales orders
  line_count:     300 open lines
  open_quantity:  88,309 units unfulfilled
  warehouse_count: 10

Backlog by warehouse:
  BH-FG   20 orders, 49 lines, 44,956 open units
  GM-HR    8 orders, 69 lines, 18,659 open units
  DL-FG   27 orders, 105 lines, 14,933 open units
  DL-MP   15 orders, 43 lines,  4,235 open units
  BH-JM   10 orders, 13 lines,  1,960 open units
  DL-EC    2 orders,  6 lines,  1,600 open units
  KT-FG    2 orders,  7 lines,    984 open units
  ...

Oldest open order (doc_num 1725021002, date 2025-02-01):
  customer: JIVO MART PVT LTD - HR  (CUSTA000827)
  FG0000010  MUSTARD KACCHI GHANI 1 LTR 16 PCS  DL-FG  ordered 160, open 160, delivered 0  (0% fulfilled)
  FG0000011  MUSTARD KACCHI GHANI 5 LTR 4 PCS   DL-FG  ordered 4, open 4, delivered 0

Large partially-fulfilled order (doc_num 1725031237, date 2025-03-15):
  JIVO MART PVT LTD - DL (CUSTA000874)
  FG0000032  COLD PRESS 1 LTR 20 PCS  GM-HR  ordered 2075, open 16, delivered 2059  (99.2% fulfilled)
  FG0000028  POMACE OLIVE 1 LTR 16PCS GM-HR  ordered 1037, open 314, delivered 723  (69.7% fulfilled)
```

**Customer codes observed in backlog:**
- CUSTA000827 = JIVO MART PVT LTD - HR (Haryana)
- CUSTA000874 = JIVO MART PVT LTD - DL (Delhi)
- CUSTA000876 = JIVO MART PVT LTD - KR (Karnataka)
- CUSTA000001 = JIVO WELLNESS PVT LTD

**Note:** The backlog contains orders dating back to Feb 2025 (16+ months). Many have 0% fulfillment. This appears to be accumulated historical backlog from the order management system, not purely current open demand.

---

### 3.7 `/wms/billing` — GRPO Billing Overview

**Purpose:** Reconciles production goods-receipts (GRPOs — when finished goods arrive from the factory into the warehouse) against the billing documents. Surfaces items that have been physically received but not yet invoiced.

**API endpoint:** `GET /warehouse/wms/billing/overview/`

**Key fields:**
- `summary`: total_received_qty, total_billed_qty, total_unbilled_qty, total_received_value, total_billed_value, total_unbilled_value, fully_billed_count, partially_billed_count, unbilled_count
- `items[]`: item_code, item_name, warehouse_code, received_qty, received_value, billed_qty, billed_value, unbilled_qty, unbilled_value, status, first_grpo_date, last_grpo_date

**Live sample (2026-06-30):**
```
Summary (cumulative all-time):
  total_received_qty:    8,471,736.22 units
  total_billed_qty:      8,395,792.92 units
  total_unbilled_qty:       75,943.30 units (0.9% of received)
  total_received_value:  ₹2,36,11,16,596.76 (~₹236.11 crore)
  total_billed_value:    ₹2,34,82,88,728.05
  total_unbilled_value:    ₹1,28,27,869     (~₹1.28 crore)
  fully_billed_count:    737 items (fully reconciled)
  partially_billed_count: 15 items
  unbilled_count:          5 items (received but zero billing)

Top partially billed items (BH-FGM warehouse):
  FG0000030  MUSTARD KACHI GHANI 1L 20PCS   received 199,202  billed 176,052  unbilled 23,150  (₹34.73L)  GRPO range: 2026-04-24 → 2026-06-29
  FG0000081  COLD PRESS SUNFLOWER 1L 20PCS  received  84,865  billed  70,465  unbilled 14,400  (₹21.60L)
  FG0000393  COLD PRESS GROUNDNUT 200ML 70PCS received 105,920 billed 98,080  unbilled  7,840  (₹2.67L)
  FG0000005  EXTRA LIGHT OLIVE 1L 16PCS     received  69,484  billed  62,324  unbilled  7,160  (₹23.27L)
  FG0000032  COLD PRESS 1L 20PCS            received  68,884  billed  62,344  unbilled  6,540  (₹11.12L)

Unbilled item:
  FG0000424  FIRST PRESSED MUSTARD OIL 1L 20PCS  received 5,100  billed 0  unbilled 5,100 (₹8.67L)  UNBILLED
```

---

### 3.8 `/wms/transfers` — Inter-warehouse Transfers Overview

**Purpose:** Shows active SAP inventory transfer documents — movements of finished goods between warehouses (e.g. factory to distribution centre, main godown to e-commerce cell).

**API endpoint:** `GET /warehouse/wms/transfers/overview/`

**Key fields:**
- `summary`: transfer_count, line_count, total_quantity, route_count
- `routes[]`: from_warehouse, to_warehouse, transfer_count, line_count, quantity
- `transfers[]`: doc_entry, doc_num, doc_date, header_from_warehouse, header_to_warehouse, comments, line_num, item_code, item_name, quantity, from_warehouse, to_warehouse

**Live sample (2026-06-30):**
```
Summary (recent window):
  transfer_count: 14 SAP transfer docs
  line_count:     200 item lines
  total_quantity: 70,103 units in motion
  route_count:    3 active routes

Routes:
  BH-FGM → DL-INT  5 docs, 80 lines, 34,513 units  (factory to transit)
  DL-INT → DL-FG   5 docs, 80 lines, 34,513 units  (transit to Mayapuri finished)
  DL-MP  → DL-EC   4 docs, 40 lines,  1,077 units  (main to e-commerce cell)

Sample transfer (doc_num 626674697, BH-FGM → DL-INT, 2026-06-29):
  FG0000030  MUSTARD KACHI GHANI 1L 20PCS    4,240 units
  FG0000081  COLD PRESS SUNFLOWER 1L 20PCS   3,660 units  (via doc 626674695)
  FG0000424  FIRST PRESSED MUSTARD OIL 1L    1,000 units
  FG0000011  MUSTARD KACCHI GHANI 5L 4PCS    1,000 units (separate doc 626674693)
  (15 SKUs total per transfer document)

Linked transfer (doc_num 626674698, DL-INT → DL-FG, same day):
  comment: "Based On Inventory Transfers 626674697."  ← references the outbound leg
  Same 15 SKUs, same quantities — completing the two-leg relay
```

**Note:** The transit pattern is a **two-leg relay** through DL-INT (MAYAPURI FINISHED INTRANSIT). SAP creates paired documents: one OUT from BH-FGM to DL-INT, then a second IN from DL-INT to DL-FG. The leg-2 document's `comments` field references the leg-1 doc number. This keeps DL-INT at zero balance once both legs post.

---

## 4. Workflows (multi-step flows + statuses)

### 4.1 Production → Stock Flow
```
[Production / Factory output]
    ↓ GRPO document posted in SAP
[BH-FGM: Bhakharpur finished goods warehouse]  ← stock arrives, billing/overview tracks unbilled
    ↓ SAP inventory transfer request created
[DL-INT: Mayapuri INTRANSIT]  ← doc_num 626674xxx "BH-FGM → DL-INT"
    ↓ SAP second-leg transfer document (comments ref first leg)
[DL-FG: Mayapuri (Godamwala) Finished]  ← stock available for dispatch from Delhi
    ↓ AR Invoice raised (customer sale)
[BarcodeBox.dispatch_session → SalesDispatch]  ← exit via Gate/Barcode section
```

### 4.2 E-Commerce Replenishment
```
[DL-MP: Mayapuri Finished Main]
    ↓ SAP inventory transfer (based on transfer request 626678xxx)
[DL-EC: Mayapuri E-Commerce]  ← picks to fulfil e-commerce orders
```

### 4.3 Billing Reconciliation Lifecycle
```
GRPO posted → item appears in billing/overview as UNBILLED
    ↓ billing document raised in SAP
Item transitions to PARTIALLY_BILLED (if qty partially invoiced) or FULLY_BILLED
```
**Statuses:** UNBILLED → PARTIALLY_BILLED → FULLY_BILLED

### 4.4 Batch Expiry Monitoring
```
Batch created in SAP (batch number assigned at production or goods receipt)
    ↓
Appears in /warehouse/wms/batches/expiry/ with expiry_status
Status values: NO_EXPIRY (date not populated) | OK | WARNING | CRITICAL | EXPIRED
```
Current state for Jivo Mart: all 300 visible batches show NO_EXPIRY — expiry dates are not populated.

### 4.5 Sales Order Fulfilment
```
SAP Sales Order created (doc_num 17xxxxx or 17xxxxxx series)
    ↓ line appears in backlog with fulfillment_pct = 0 and open_qty = ordered_qty
        ↓ delivery posted (AR_INVOICE / delivery note in SAP)
open_qty decreases, fulfillment_pct increases
    ↓ when open_qty = 0, line drops from backlog
```

---

## 5. Cross-section connections

| WMS connects to | How |
|---|---|
| **Barcode (dispatch)** | BarcodeBox.current_warehouse and BarcodeBox.current_bin reference the same warehouse codes tracked in WMS (e.g. DL-FG, BH-FGM). A dispatch session's AR_INVOICE movement appears as an OUT in the WMS movements ledger. |
| **Gate (SalesDispatch)** | Gate section's SalesDispatch.warehouses field references WMS warehouse codes. When a truck is loaded and gate-out occurs, the associated AR_INVOICE posts OUT movements in WMS stock. |
| **GRPO / Procurement** | GRPOEntry (quality-and-grpo section) when posted creates the GRPO transaction_type movement in WMS movements ledger. The billing/overview endpoint directly tracks GRPO receipts vs invoices. |
| **Production** | Production GRPOs (finished goods from production runs) arrive into BH-FGM and appear in WMS as GRPO IN movements. The WMS billing overview tracks these against invoicing. |
| **SAP item master** | item_code fields (FG-prefixed) across all WMS endpoints bridge to the SAP OITM item master exposed via `/barcode/items/oitm/`. |
| **Transfer requests** | The DL-MP → DL-EC transfers reference "Inventory Transfer Request" doc numbers (626678xxx) in comments — these originate from a transfer-request workflow (not directly visible in this section's API but tracked in SAP). |

---

## 6. Data presence for Jivo Mart (which pages have live data vs empty)

| Endpoint | Kind | Records (count) | Status |
|---|---|---|---|
| `/warehouse/wms/dashboard/` | object | 1 | LIVE — fully populated, 268 items, ₹9.96cr |
| `/warehouse/wms/warehouses/` | object | 1 | LIVE — 31 warehouses listed |
| `/warehouse/wms/warehouses/summary/` | object | 1 | LIVE — 18 warehouses with non-zero stock |
| `/warehouse/wms/stock/overview/` | paginated object | 953 lines (20 pages) | LIVE — extensive |
| `/warehouse/wms/stock/movements/` | object | 100+ movements (recent) | LIVE — active daily |
| `/warehouse/wms/batches/expiry/` | object | 300 batches | LIVE count, but NO expiry dates populated — data quality issue |
| `/warehouse/wms/billing/overview/` | object | 757 items total (737 fully billed + 15 partial + 5 unbilled) | LIVE — ₹236cr cumulative |
| `/warehouse/wms/sales-orders/backlog/` | object | 86 orders / 300 lines | LIVE — but contains historical stale orders back to Feb 2025 |
| `/warehouse/wms/transfers/overview/` | object | 14 transfers, 200 lines | LIVE — active daily transfers |
| `/warehouse/wms/item-groups/` | object | 9 item groups | LIVE — reference data |

**Summary of coverage:**
- All 10 WMS API endpoints return live data for Jivo Mart.
- Stock, movements, billing, transfers are fully active (daily transactions observed).
- Batch expiry monitoring is structurally present but **expiry/manufacturing dates are blank** for all 300 visible batches — the expiry alerting feature is not operational for Jivo Mart.
- Sales order backlog contains genuine open orders but also a significant tail of historical orders (Feb 2025 – present) with 0% fulfilment that appear to be unclosed or carry-over orders rather than current unmet demand.

---

## Reference — UI routes (from bundle)
- `/wms`
- `/wms/batches`
- `/wms/billing`
- `/wms/orders`
- `/wms/stock`
- `/wms/transfers`
- `/wms/warehouses`

## Reference — captured API endpoints + record counts (this section)
- `/warehouse/wms/batches/expiry/` -> 1 (object) — 300 batches, 104,593 units, all NO_EXPIRY
- `/warehouse/wms/billing/overview/` -> 1 (object) — 757 items; ₹236cr received, ₹1.28cr unbilled
- `/warehouse/wms/dashboard/` -> 1 (object) — 268 SKUs, 448,965 units, ₹9.96cr
- `/warehouse/wms/item-groups/` -> 1 (object) — 9 groups (CONSUMABLES, FINISHED, FIXED ASSETS, FLAV/PRESTV/INGRDNT, LAB INVENTORY, PACKAGING MATERIAL, RAW MATERIAL, SALES BOM, TRADING ITEMS)
- `/warehouse/wms/sales-orders/backlog/` -> 1 (object) — 86 orders, 300 lines, 88,309 open units
- `/warehouse/wms/stock/movements/` -> 1 (object) — rolling window, 100+ lines per pull; types: GRPO / TRANSFER / AR_INVOICE
- `/warehouse/wms/stock/overview/` -> 1 (object) — 953 SKU-warehouse lines; total available -973,348 (heavily committed)
- `/warehouse/wms/transfers/overview/` -> 1 (object) — 14 docs, 200 lines, 70,103 units; 3 routes active
- `/warehouse/wms/warehouses/` -> 1 (object) — 31 warehouses
- `/warehouse/wms/warehouses/summary/` -> 1 (object) — 18 warehouses with active stock

Linked: [[docs/factory/FACTORY_MAP|FACTORY_MAP]] · [[docs/FACTORY_CLI_PLAN|FACTORY_CLI_PLAN]] · [[docs/READ_ONLY_LAW|READ_ONLY_LAW]]
