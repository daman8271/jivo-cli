---
title: "Warehouse — Jivo Mart app-model"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: reference
tags: [jivogpt, factory-cli, warehouse]
---

# Warehouse — Jivo Mart app-model

> **Provenance — imported 2026-07-19; source snapshot 2026-06-30.** This note came from the JIVO_MART-only `daman8271/jivo-factory-intel` baseline. For the current three-company study and the live-verified 2026-07-19 state, use [[docs/factory/FACTORY_MAP|FACTORY_MAP]] and [[CLI/factory-cli/README|the current CLI guide]].
> Documented: 2026-06-30. All API calls ran live against JIVO_MART (Company-Code: JIVO_MART).

## 1. Purpose — what this section is for in the factory

The Warehouse section is the finished-goods Warehouse Management System (WMS) for JIVO_MART. It gives real-time visibility and operational control over stock across the entire outbound supply chain: from production hand-off at Bhakharpur through regional distribution warehouses (Mayapuri Delhi, Gurugram, Haryana FBF, Karnataka, Punjab) to e-commerce staging.

Specifically this section handles:

1. **WMS dashboard and overview** — consolidated KPIs: items in stock, total on-hand quantity (448,965 PCS / ≈₹9.96 crore at time of capture), breakdown by warehouse and item group.
2. **Per-warehouse stock levels** — item × warehouse grid with on-hand, committed, on-order, available, and stock value against all 31 SAP warehouse codes.
3. **Stock movements audit trail** — every IN/OUT transaction by type (GRPO from production, AR_INVOICE outbound sale, TRANSFER between warehouses).
4. **Batch expiry management** — 300 active production batches tracked for expiry; all currently flagged NO_EXPIRY (no expiry dates populated in SAP yet for JIVO_MART).
5. **Sales order backlog** — 86 open SAP sales orders (300 lines, 88,309 units open) showing which warehouse is committed but not yet dispatched.
6. **Billing reconciliation** — compares goods received from production (GRPO quantities) against SAP AR invoice quantities; highlights items that are unbilled or partially billed.
7. **Inter-warehouse transfer tracking** — SAP inventory transfer documents linking source and destination warehouses (e.g., Bhakharpur FGM → Mayapuri INTRANSIT → Mayapuri FG).
8. **FG Receipts** — registration of finished goods arriving from the production floor into the warehouse (currently not in use for JIVO_MART; list is empty).
9. **BOM Requests** — warehouse requests for raw/packaging materials driven by production BOM (currently not in use for JIVO_MART; list is empty).
10. **Stock check lookup** — a POST utility endpoint allowing any module to query real-time per-warehouse on-hand and available for a given list of item codes.

---

## 2. Page tree (page → subpage → sub-subpage / wizard steps)

```
/warehouse                              Landing — routes to WMS dashboard or section index
│
├── /warehouse/wms/                     WMS module
│   ├── dashboard/                      WMS KPI Dashboard — aggregate snapshot
│   ├── warehouses/                     Warehouse master list (31 SAP warehouses)
│   │   └── summary/                    Per-warehouse stock health summary
│   ├── stock/
│   │   ├── overview/                   Stock overview — item × warehouse grid
│   │   └── movements/                  Stock movement audit log (recent transactions)
│   ├── batches/
│   │   └── expiry/                     Batch stock with expiry status per lot
│   ├── billing/
│   │   └── overview/                   GRPO vs AR Invoice billing reconciliation
│   ├── sales-orders/
│   │   └── backlog/                    Open/unfulfilled sales order lines by warehouse
│   ├── item-groups/                    SAP item group reference list
│   └── transfers/
│       └── overview/                   Inter-warehouse transfer document list
│
├── /warehouse/bom-requests/            BOM material pull requests (EMPTY for JIVO_MART)
│   ├── :requestId                      BOM request detail view
│   └── create/                         Create BOM request wizard (step 1 entry point)
│
├── /warehouse/fg-receipts/             FG receipts registration (EMPTY for JIVO_MART)
│   └── create/                         Create FG receipt wizard (step 1 entry point)
│
└── /warehouse/stock/check/             Stock check — POST-only lookup tool (no list UI)
```

---

## 3. Per-page detail

### 3.1 WMS Dashboard (`/warehouse/wms/dashboard/`)
**Purpose:** Central real-time KPI view for warehouse managers. Shows aggregate inventory health, per-warehouse value distribution, item-group breakdown, top-value SKUs, and the 20 most recent stock movements.

**API:** `GET /warehouse/wms/dashboard/`

**Response shape:**
- `kpis`: aggregate totals
- `stock_by_warehouse[]`: items and value per warehouse (only warehouses with stock)
- `stock_by_group[]`: items and value per item group
- `top_items_by_value[]`: top 10 SKUs by stock value
- `stock_health`: counts of items by health status
- `recent_movements[]`: 20 latest movement events

**Live sample (2026-06-29):**
```json
"kpis": {
  "total_items": 268,
  "total_on_hand": 448965.9,
  "total_value": 99621731.23,
  "low_stock": 0,
  "critical_stock": 0,
  "zero_stock": 0,
  "overstock": 0
}
"stock_by_warehouse": [
  { "warehouse_code": "BH-FGM", "items": 52, "value": 59441180.39 },
  { "warehouse_code": "DL-MP",  "items": 156, "value": 13221334.53 },
  { "warehouse_code": "DL-GR",  "items": 112, "value": 6033646.24 },
  { "warehouse_code": "DL-EC",  "items": 88,  "value": 5377067.94 },
  ...14 warehouses total...
]
"stock_by_group": [
  { "group_name": "FINISHED",          "items": 180, "value": 96361677.35 },
  { "group_name": "PACKAGING MATERIAL","items": 26,  "value": 2777877.00 },
  { "group_name": "TRADING ITEMS",     "items": 19,  "value": 288083.78 },
  { "group_name": "FIXED ASSETS",      "items": 6,   "value": 194093.10 }
]
"top_items_by_value": [
  { "item_code": "FG0000009", "item_name": "EXTRA LIGHT OLIVE 5 LTR TIN 4 PCS",   "quantity": 6147.0,  "value": 9988875.0 },
  { "item_code": "FG0000151", "item_name": "SANO POMACE OLIVE 5 LTR TIN 4 PCS",   "quantity": 6145.0,  "value": 7681250.0 },
  { "item_code": "FG0000011", "item_name": "MUSTARD KACCHI GHANI 5 LTR 4 PCS",   "quantity": 10116.0, "value": 7587000.0 }
]
```

**Key fields:** `total_items`, `total_on_hand`, `total_value`, warehouse-level value breakdown, `recent_movements[].transaction_type` (AR_INVOICE / TRANSFER / GRPO).

---

### 3.2 Warehouse Master (`/warehouse/wms/warehouses/`)
**Purpose:** Reference list of all SAP warehouse codes and names for JIVO_MART. Used as a lookup in filters across stock overview, movements, and transfers.

**API:** `GET /warehouse/wms/warehouses/`

**Response shape:** `{ "warehouses": [ { "code": "...", "name": "..." }, ... ] }`

**Full warehouse list (31 warehouses, live):**

| Code | Name |
|------|------|
| 01 | General Warehouse |
| BH-FG | Bhakharpur Finished Basement |
| BH-FGM | Bhakharpur finished goods (main FG store) |
| BH-FK | Bhakharpur Flipkart Packing |
| BH-GR | Bhakharpur GR (Goods Receipt staging) |
| BH-GRM | Bhakharpur Return Stock |
| BH-INT | Bhakharpur Finished INTRANSIT |
| BH-JM | Bhakharpur Jivo mart (dedicated Jivomart stock) |
| BH-LR | Luhari Jhajjar Finished |
| BH-PF | Bhakharpur Production Finished 1st Floor |
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
| DP-DL | DROPSHIP DELHI |
| DP-HR | DROPSHIP HARYANA |
| DP-PB | DROPSHIP PUNJAB |
| FBF-HR | HARYANA FBF GODOWN |
| GM-HR | GURUGRAM HARYANA |
| KT-FBF | Karnataka Finished New Godown |
| KT-FG | Karnataka Finished |
| PB-FG | Punjab Haryana |
| PB-INT | Punjab INTRANSIT |
| RJ-FG | Rajasthan Finished |
| UP-FG | Uttar Pradesh Finished |

**Note:** "GR" warehouses (BH-GR, DL-GR) are goods-receipt staging zones; "INT" warehouses (BH-INT, DL-INT, PB-INT) are in-transit virtual warehouses used during inter-location stock transfers.

---

### 3.3 Warehouse Summary (`/warehouse/wms/warehouses/summary/`)
**Purpose:** Per-warehouse aggregated stock health — item count, total on-hand quantity, total stock value, and alert counts. Shows only warehouses with active stock (18 of 31).

**API:** `GET /warehouse/wms/warehouses/summary/`

**Response shape:** `{ "warehouses": [ { warehouse_code, warehouse_name, total_items, total_on_hand, total_value, low_stock_count, critical_stock_count, overstock_count, zero_stock_count }, ... ] }`

**Live sample — active warehouses (2026-06-29):**

| Code | Name | Items | On-Hand (PCS) | Value (₹) |
|------|------|-------|--------------|-----------|
| BH-FGM | Bhakharpur finished goods | 71 | 189,308.0 | 5,94,41,180 |
| DL-MP | MAYAPURI FINISHED (MAIN) | 181 | 165,636.8 | 1,32,21,335 |
| DL-GR | Mayapuri GR | 123 | 12,828.0 | 60,33,646 |
| DL-EC | Mayapuri E-Commerce | 94 | 20,022.0 | 53,77,068 |
| DL-FG | MAYAPURI (GODAMWALA) FINISHED | 126 | 26,366.0 | 52,94,355 |
| BH-JM | Bhakharpur Jivo mart | 19 | 13,194.1 | 40,08,339 |
| BH-FK | Bhakharpur Flipkart Packing | 7 | 12,700.0 | 26,19,000 |
| FBF-HR | HARYANA FBF GODOWN | 29 | 3,257.0 | 14,65,798 |
| KT-FG | Karnataka Finished | 9 | 2,142.0 | 10,31,999 |
| BH-GR | Bhakharpur GR | 24 | 2,965.0 | 6,99,333 |
| DL-FA | MAYAPURI FIXED ASSET GODOWN | 6 | 6.0 | 1,94,093 |
| KT-FBF | Karnataka Finished New Godown | 23 | 307.0 | 1,44,131 |
| PB-FG | Punjab Haryana | 6 | 142.0 | 67,700 |
| BH-FG | Bhakharpur Finished Basement | 61 | 92.0 | 23,754 |

**Note:** All alert counts (low_stock_count, critical_stock_count, overstock_count, zero_stock_count) are 0 for all warehouses in the summary view — the thresholds (min_level, max_level) are set to 0 in SAP item master, so no alerts trigger.

---

### 3.4 Stock Overview (`/warehouse/wms/stock/overview/`)
**Purpose:** Granular item × warehouse matrix. Every line is one SAP item code at one warehouse, showing on-hand, committed (open SO), on-order (open PO/production), available (on-hand minus committed), avg price, stock value, and stock status.

**API:** `GET /warehouse/wms/stock/overview/`

**Summary totals:**
- `total_items`: 953 (item × warehouse combinations with non-zero data)
- `total_on_hand`: 448,965.9 PCS
- `total_committed`: 1,422,314.0 PCS (open sales orders reservations)
- `total_available`: −973,348.1 PCS (heavily negative — significant backorder situation)
- `total_value`: ₹9,96,21,731

**Key fields per row:** `item_code`, `item_name`, `item_group`, `uom`, `warehouse_code`, `on_hand`, `committed`, `on_order`, `available`, `avg_price`, `stock_value`, `min_level`, `max_level`, `last_purchase_price`, `stock_status`

**Stock status values observed:** `NORMAL` (on-hand > 0), `ZERO` (on-hand = 0)

**Live sample (2 rows):**
```json
{
  "item_code": "FG0000004", "item_name": "COLD PRESS 5 LTR 4 PCS",
  "item_group": "FINISHED", "uom": "PCS", "warehouse_code": "BH-FG",
  "on_hand": 4.0, "committed": 220.0, "on_order": 240.0, "available": -216.0,
  "avg_price": 850.0, "stock_value": 3400.0, "stock_status": "NORMAL"
},
{
  "item_code": "FG0000005", "item_name": "EXTRA LIGHT OLIVE 1 LTR 16 PCS",
  "item_group": "FINISHED", "uom": "PCS", "warehouse_code": "BH-FG",
  "on_hand": 0.0, "committed": 2400.0, "on_order": 400.0, "available": -2400.0,
  "avg_price": 200.0, "stock_value": 0.0, "stock_status": "ZERO"
}
```

**Note:** Large negative `available` values across many items reflect open sales order commitments exceeding current on-hand stock — a supply-demand gap needing production or transfer to resolve.

---

### 3.5 Stock Movements (`/warehouse/wms/stock/movements/`)
**Purpose:** Chronological audit trail of recent stock IN/OUT events across all warehouses, sourced from SAP documents. This is the "ledger view" behind any stock change.

**API:** `GET /warehouse/wms/stock/movements/` (returns most recent 100 records)

**Key fields:** `date`, `item_code`, `item_name`, `warehouse_code`, `in_qty`, `out_qty`, `quantity`, `direction` (IN/OUT), `transaction_type`, `reference` (SAP doc number as string), `doc_num` (integer SAP doc entry), `created_by` (user ID)

**Transaction types observed:**
- `AR_INVOICE` — outbound: stock exits warehouse on a sales/AR invoice (direction=OUT)
- `TRANSFER` — inter-warehouse: stock moves between warehouses (appears as OUT at source and IN at destination)
- `GRPO` — inbound: Goods Receipt PO, stock enters warehouse from production or purchase (direction=IN)

**Live samples (2026-06-29):**
```json
// AR Invoice outbound
{ "item_code": "FG0000424", "item_name": "FIRST PRESSED MUSTARD OIL 1 LTR 20 PCS",
  "warehouse_code": "DL-FG", "out_qty": 1000.0, "direction": "OUT",
  "transaction_type": "AR_INVOICE", "reference": "706260877", "doc_num": 263417 }

// Transfer receipt (IN leg)
{ "item_code": "FG0000424", "warehouse_code": "DL-FG", "in_qty": 1000.0,
  "direction": "IN", "transaction_type": "TRANSFER", "reference": "626674698" }

// GRPO receipt from production
{ "item_code": "FG0000032", "item_name": "COLD PRESS 1 LTR 20 PCS",
  "warehouse_code": "BH-FGM", "in_qty": 6540.0, "direction": "IN",
  "transaction_type": "GRPO", "reference": "2006264558" }
```

---

### 3.6 Batches / Expiry (`/warehouse/wms/batches/expiry/`)
**Purpose:** Tracks active production batches with their expiry status. Intended to flag expired, critical (near-expiry), or warning-level batches.

**API:** `GET /warehouse/wms/batches/expiry/`

**Summary:**
```json
{
  "batch_count": 300,
  "expired_count": 0,
  "critical_count": 0,
  "warning_count": 0,
  "ok_count": 0,
  "total_quantity": 104593.0
}
```

**Key fields per batch:** `item_code`, `item_name`, `batch_number`, `expiry_date`, `manufacturing_date`, `sap_status`, `warehouse_code`, `quantity`, `days_to_expiry`, `expiry_status`

**Live sample:**
```json
{
  "item_code": "FG0000004", "item_name": "COLD PRESS 5 LTR 4 PCS",
  "batch_number": "121345", "expiry_date": "", "manufacturing_date": "",
  "sap_status": "0", "warehouse_code": "BH-FGM",
  "quantity": 3900.0, "days_to_expiry": null, "expiry_status": "NO_EXPIRY"
}
```

**JIVO_MART state:** All 300 batches have `expiry_status = "NO_EXPIRY"` — expiry_date and manufacturing_date are blank strings in SAP. No batches are flagged as expired, critical, or even OK (since no dates are set). The batch tracking feature exists but expiry data is not yet populated.

---

### 3.7 Item Groups (`/warehouse/wms/item-groups/`)
**Purpose:** Reference list of SAP item groups. Used as a filter dimension across stock and billing pages.

**API:** `GET /warehouse/wms/item-groups/`

**Live data (9 groups):**

| Code | Name |
|------|------|
| 101 | CONSUMABLES |
| 102 | FINISHED |
| 110 | FIXED ASSETS |
| 103 | FLAV/PRESTV/INGRDNT |
| 104 | LAB INVENTORY |
| 105 | PACKAGING MATERIAL |
| 106 | RAW MATERIAL |
| 109 | SALES BOM |
| 107 | TRADING ITEMS |

**Context:** Group 102 (FINISHED) dominates stock value; groups 105 and 106 are the procurement/inbound side. Group 107 (TRADING ITEMS) has active stock in the WMS.

---

### 3.8 Billing Overview (`/warehouse/wms/billing/overview/`)
**Purpose:** Reconciliation view between goods received from production (GRPO) and what has been billed on SAP AR invoices. Surfaces unbilled or partially-billed FG stock — quantities produced and received into warehouse but not yet invoiced outbound.

**API:** `GET /warehouse/wms/billing/overview/`

**Summary (live, 2026-06-29):**
```json
{
  "total_received_qty":   8471736.22,
  "total_billed_qty":     8395792.92,
  "total_unbilled_qty":     75943.30,
  "total_received_value": 236,11,16,596.76,
  "total_billed_value":   234,82,88,728.05,
  "total_unbilled_value":    1,28,27,868.71,
  "fully_billed_count": 737,
  "partially_billed_count": 15,
  "unbilled_count": 5
}
```

**757 total items.** Status breakdown: FULLY_BILLED=737, PARTIALLY_BILLED=15, UNBILLED=5.

**Key fields per item:** `item_code`, `item_name`, `warehouse_code`, `received_qty`, `received_value`, `billed_qty`, `billed_value`, `unbilled_qty`, `unbilled_value`, `status` (FULLY_BILLED / PARTIALLY_BILLED / UNBILLED), `first_grpo_date`, `last_grpo_date`

**Live sample (2 items):**
```json
// Partially billed — 15% unbilled
{ "item_code": "FG0000030", "item_name": "MUSTARD KACHI GHANI 1 LTR 20 PCS",
  "warehouse_code": "BH-FGM",
  "received_qty": 199202.0, "billed_qty": 176052.0, "unbilled_qty": 23150.0,
  "unbilled_value": 3472500.0, "status": "PARTIALLY_BILLED" }

// Unbilled — fresh GRPO, no AR invoice yet
{ "item_code": "FG0000424", "item_name": "FIRST PRESSED MUSTARD OIL 1 LTR 20 PCS",
  "warehouse_code": "BH-FGM",
  "received_qty": 5100.0, "billed_qty": 0.0, "unbilled_qty": 5100.0,
  "unbilled_value": 867000.0, "status": "UNBILLED",
  "first_grpo_date": "2026-06-29 00:00:00" }
```

---

### 3.9 Sales Orders Backlog (`/warehouse/wms/sales-orders/backlog/`)
**Purpose:** Shows open/unfulfilled SAP sales order lines — orders placed by customers (or inter-company entities) against JIVO_MART's FG warehouses that have not yet been fully dispatched. Gives warehouse managers a view of pending dispatch obligations per warehouse.

**API:** `GET /warehouse/wms/sales-orders/backlog/`

**Summary (live, 2026-06-29):**
```json
{
  "order_count": 86,
  "line_count": 300,
  "open_quantity": 88309.0,
  "warehouse_count": 10
}
```

**Warehouse-level breakdown:**

| Warehouse | Orders | Lines | Open Qty |
|-----------|--------|-------|----------|
| BH-FG | 20 | 49 | 44,956 |
| GM-HR | 8 | 69 | 18,659 |
| DL-FG | 27 | 105 | 14,933 |
| DL-MP | 15 | 43 | 4,235 |
| BH-JM | 10 | 13 | 1,960 |
| DL-EC | 2 | 6 | 1,600 |
| KT-FG | 2 | 7 | 984 |
| DL-GG | 1 | 2 | 932 |
| KT-FBF | 1 | 4 | 47 |
| FBF-HR | 1 | 2 | 3 |

**Key fields per line:** `doc_entry`, `doc_num`, `doc_date`, `due_date`, `customer_code`, `customer_name`, `line_num`, `item_code`, `item_name`, `warehouse_code`, `ordered_qty`, `open_qty`, `delivered_qty`, `fulfillment_pct`

**Live sample:**
```json
{
  "doc_num": 1725021002, "doc_date": "2025-02-01",
  "customer_code": "CUSTA000827", "customer_name": "JIVO MART PVT LTD - HR",
  "item_code": "FG0000010", "item_name": "MUSTARD KACCHI GHANI 1 LTR 16 PCS",
  "warehouse_code": "DL-FG",
  "ordered_qty": 160.0, "open_qty": 160.0, "delivered_qty": 0.0, "fulfillment_pct": 0.0
}
```

**Note:** Some orders date back to Feb 2025 with 0% fulfillment — these are likely legacy open orders in SAP. The primary customer appearing is "JIVO MART PVT LTD - HR" (inter-company Haryana entity).

---

### 3.10 Transfers Overview (`/warehouse/wms/transfers/overview/`)
**Purpose:** Lists recent SAP inter-warehouse inventory transfer documents. Shows the movement of finished goods between warehouse locations (e.g., factory → distribution hub → local warehouse).

**API:** `GET /warehouse/wms/transfers/overview/`

**Summary (live, 2026-06-29):**
```json
{
  "transfer_count": 14,
  "line_count": 200,
  "total_quantity": 70103.0,
  "route_count": 3
}
```

**Active transfer routes:**

| From → To | Transfers | Lines | Quantity | Description |
|-----------|-----------|-------|----------|-------------|
| BH-FGM → DL-INT | 5 | 80 | 34,513 | Bhakharpur FG → Mayapuri Intransit (dispatch leg) |
| DL-INT → DL-FG | 5 | 80 | 34,513 | Mayapuri Intransit → Mayapuri Finished (arrival leg) |
| DL-MP → DL-EC | 4 | 40 | 1,077 | Mayapuri Main → E-Commerce warehouse |

**Key fields per transfer line:** `doc_entry`, `doc_num`, `doc_date`, `header_from_warehouse`, `header_to_warehouse`, `comments`, `line_num`, `item_code`, `item_name`, `quantity`, `from_warehouse`, `to_warehouse`

**Live sample (1 line):**
```json
{
  "doc_num": 626674698, "doc_date": "2026-06-29",
  "header_from_warehouse": "DL-INT", "header_to_warehouse": "DL-FG",
  "comments": "Based On Inventory Transfers 626674697.",
  "item_code": "FG0000424", "item_name": "FIRST PRESSED MUSTARD OIL 1 LTR 20 PCS",
  "quantity": 1000.0, "from_warehouse": "DL-INT", "to_warehouse": "DL-FG"
}
```

**Note:** Transfer documents come in chained pairs (626674697 → 626674698): the first is BH-FGM→DL-INT and the second is DL-INT→DL-FG, representing a two-leg inter-city transfer of the same batch.

---

### 3.11 Stock Check (`/warehouse/stock/check/`)
**Purpose:** Point-in-time multi-SKU stock lookup. Accepts a POST payload with an `item_codes` array and returns per-item, per-warehouse on-hand and available. Not a UI list page — it functions as an embedded lookup used by other sections (e.g., dispatch planning, order confirmation).

**API:** `POST /warehouse/stock/check/` with `{ "item_codes": ["FG0000004", ...] }`

**Key fields per item returned:** `ItemCode`, `ItemName`, `total_on_hand`, `total_available`, `warehouses[]` with `WhsCode`, `OnHand`, `Available` per warehouse

**Live sample (FG0000004):**
```json
{
  "ItemCode": "FG0000004", "ItemName": "COLD PRESS 5 LTR 4 PCS",
  "total_on_hand": 6299.0, "total_available": -5015.0,
  "warehouses": [
    { "WhsCode": "BH-FG",  "OnHand": 4.0,    "Available": -216.0 },
    { "WhsCode": "BH-FGM", "OnHand": 6203.0, "Available": -4771.0 },
    ...all 31 warehouses listed...
  ]
}
```

---

### 3.12 BOM Requests (`/warehouse/bom-requests/`)
**Purpose:** Warehouse staff raise BOM material pull requests to signal that raw or packaging materials are needed from stores to satisfy a production BOM. The create wizard (`/warehouse/bom-requests/create/`) steps through selecting the production order / BOM, specifying required quantities, and submitting the request. Detail view at `/warehouse/bom-requests/:requestId` shows request status and fulfilment.

**API:** `GET /warehouse/bom-requests/`

**JIVO_MART state:** Empty — no BOM requests have been created. This feature is present in the app but not yet in use for JIVO_MART.

---

### 3.13 FG Receipts (`/warehouse/fg-receipts/`)
**Purpose:** Registers the physical receipt of finished goods from the production floor into the warehouse. When a production run completes and packaged goods move from the production area to the FG warehouse, a warehouse operator creates an FG receipt here. The create wizard (`/warehouse/fg-receipts/create/`) would step through selecting the production batch, confirming quantities, and posting the warehouse receipt.

**API:** `GET /warehouse/fg-receipts/`

**JIVO_MART state:** Empty — no FG receipts have been created via this module. Production output is currently tracked through the GRPO path (visible in stock movements as `transaction_type: GRPO`).

---

## 4. Workflows (multi-step flows + statuses)

### 4.1 Finished Goods Inbound (Production → Warehouse)
```
Production completes a batch
    ↓
[FG Receipt OR GRPO posted in SAP]  ← currently via GRPO path for JIVO_MART
    ↓
Stock appears in BH-FGM (Bhakharpur FGM) or BH-PF (Production 1st Floor) warehouse
    ↓
Batch created in SAP (expiry tracking via /batches/expiry/)
    ↓
Billing status: UNBILLED → PARTIALLY_BILLED → FULLY_BILLED
   (tracked on /billing/overview/ as AR Invoices are raised against the GRPO qty)
```

### 4.2 Inter-City Stock Transfer (Factory → Distribution Hub → Local)
```
Warehouse manager initiates SAP Inventory Transfer: BH-FGM → DL-INT
    ↓
Vehicle loaded; SAP doc e.g. 626674697 (BH-FGM OUT)
    ↓
Stock moves to BH-INT / DL-INT (in-transit virtual warehouse)
    ↓
Vehicle arrives at destination; SAP doc e.g. 626674698 (DL-INT IN, DL-FG OUT)
    ↓
Stock available in DL-FG / DL-MP for local dispatch
```
Visible in `/wms/transfers/overview/` as chained document pairs, and in `/wms/stock/movements/` as paired TRANSFER IN + OUT lines with the same reference doc_num.

### 4.3 Outbound Sales Dispatch
```
SAP Sales Order created (visible on /sales-orders/backlog/ as open line)
    ↓
Warehouse picks stock; quantity becomes "committed" in /stock/overview/
    ↓
AR Invoice / Delivery raised in SAP (triggers stock movement: transaction_type=AR_INVOICE, direction=OUT)
    ↓
Fulfilled quantity removed from backlog; fulfillment_pct increases toward 100%
    ↓
Billing status on /billing/overview/ updates toward FULLY_BILLED
```

### 4.4 BOM Material Request (not yet active for JIVO_MART)
```
Production planner identifies BOM material gap
    ↓
Warehouse raises BOM request via /warehouse/bom-requests/create/ wizard
    ↓
BOM request in "pending" state; stores team fulfils the pull
    ↓
Request marked fulfilled; material consumed in production
```

### 4.5 E-Commerce Warehouse Replenishment
```
DL-MP (Mayapuri Main) identified as source
    ↓
SAP transfer doc created: DL-MP → DL-EC (E-Commerce warehouse)
    ↓
Visible in /transfers/overview/ under route DL-MP → DL-EC
    ↓
DL-EC stock increases; available against open e-commerce SO lines
```

---

## 5. Cross-section connections

| This section | Connects to | Via |
|---|---|---|
| `/warehouse/wms/stock/movements/` GRPO entries | **QC & GRPO section** (`/grpo/`) | Same SAP GRPO doc_num; GRPOs posted after QC approval flow into warehouse stock |
| `/warehouse/wms/stock/movements/` AR_INVOICE entries | **Gate / Dispatch** (`/gate-core/sales-dispatch/`) | AR Invoice doc_num = SAP invoice; same invoice linked to SalesDispatch gate-out entry_no |
| `/warehouse/wms/sales-orders/backlog/` customer_code | **Dispatch Plans** (`/dispatch-plans/`) | SAP SO → DispatchPlan → gate-out sequence; backlog lines represent un-dispatched POs |
| `/warehouse/wms/billing/overview/` | **GRPO section** + **Dispatch** | billing reconciles GRPO receipt qty vs SAP AR invoice qty; bridges inbound (GRPO) and outbound (AR Invoice) |
| `/warehouse/wms/transfers/overview/` from/to warehouses | **Gate core BST entries** (`/gate-core/bst-outs/`) | BST (Branch Stock Transfer) gate entries are the physical movement that triggers an inventory transfer doc |
| `/warehouse/bom-requests/` | **Production / Manufacturing** section | BOM request originates from production schedule; pulls from raw-material/packaging warehouses |
| `/warehouse/fg-receipts/` | **Production / Manufacturing** section | FG receipt is the production-to-warehouse handoff; parallel path to GRPO |
| `/warehouse/wms/batches/expiry/` batch_number | **Barcode / Traceability** (`/barcode/boxes/`, `/barcode/pallets/`) | BarcodeBox.batch_number and Pallet.batch_number are the same batch IDs; warehouse physical location tracked by current_warehouse + current_bin on each box/pallet |
| `/warehouse/stock/check/` item_codes | **Barcode / Dispatch sessions** | Stock check is invoked during dispatch session creation to confirm available stock before committing to an outbound shipment |

---

## 6. Data presence for Jivo Mart (which pages have live data vs empty, with counts)

| Page / Endpoint | Status | Live Count |
|---|---|---|
| `/warehouse/wms/dashboard/` | **LIVE** | 268 items, ₹9.96 crore total value, 14 warehouses with stock |
| `/warehouse/wms/warehouses/` | **LIVE** | 31 warehouse codes |
| `/warehouse/wms/warehouses/summary/` | **LIVE** | 18 warehouses with active stock |
| `/warehouse/wms/stock/overview/` | **LIVE** | 953 item × warehouse rows; total on-hand 448,965 PCS |
| `/warehouse/wms/stock/movements/` | **LIVE** | 100 records (most recent); types: AR_INVOICE, TRANSFER, GRPO |
| `/warehouse/wms/batches/expiry/` | **LIVE (feature inactive)** | 300 batches, 104,593 units; all expiry_status = NO_EXPIRY (dates not set in SAP) |
| `/warehouse/wms/item-groups/` | **LIVE** | 9 SAP item groups |
| `/warehouse/wms/billing/overview/` | **LIVE** | 757 items; 737 fully billed, 15 partially billed, 5 unbilled; ₹1.28 crore unbilled |
| `/warehouse/wms/sales-orders/backlog/` | **LIVE** | 86 open orders, 300 lines, 88,309 open qty across 10 warehouses |
| `/warehouse/wms/transfers/overview/` | **LIVE** | 14 transfer documents, 200 lines, 70,103 units; 3 active routes |
| `/warehouse/stock/check/` | **LIVE (POST only)** | No list; returns live per-warehouse data on demand for any item_codes[] |
| `/warehouse/bom-requests/` | **EMPTY** | 0 records — feature not yet used for JIVO_MART |
| `/warehouse/fg-receipts/` | **EMPTY** | 0 records — FG receipt flow replaced by direct GRPO posting |

**Top warehouses by stock value (2026-06-29):**
1. BH-FGM — Bhakharpur finished goods: ₹5.94 crore (189,308 PCS)
2. DL-MP — Mayapuri Finished Main: ₹1.32 crore (165,637 PCS)
3. DL-GR — Mayapuri GR: ₹60.3 lakh (12,828 PCS)
4. DL-EC — Mayapuri E-Commerce: ₹53.8 lakh (20,022 PCS)
5. DL-FG — Mayapuri Godamwala: ₹52.9 lakh (26,366 PCS)

---
## Reference — UI routes (from bundle)
- `/warehouse`
- `/warehouse/bom-requests`
- `/warehouse/bom-requests/`
- `/warehouse/bom-requests/:requestId`
- `/warehouse/bom-requests/create/`
- `/warehouse/fg-receipts`
- `/warehouse/fg-receipts/`
- `/warehouse/fg-receipts/create/`
- `/warehouse/stock/check/`
- `/warehouse/wms/batches/expiry/`
- `/warehouse/wms/billing/overview/`
- `/warehouse/wms/dashboard/`
- `/warehouse/wms/item-groups/`
- `/warehouse/wms/sales-orders/backlog/`
- `/warehouse/wms/stock/movements/`
- `/warehouse/wms/stock/overview/`
- `/warehouse/wms/transfers/overview/`
- `/warehouse/wms/warehouses/`
- `/warehouse/wms/warehouses/summary/`

## Reference — captured API endpoints + record counts (this section)
- `/warehouse/bom-requests/` -> 0 (list, EMPTY for JIVO_MART)
- `/warehouse/fg-receipts/` -> 0 (list, EMPTY for JIVO_MART)
- `/warehouse/stock/check/` -> POST-only; no GET list
- `/warehouse/wms/batches/expiry/` -> 1 object (summary + 300 batches, all NO_EXPIRY)
- `/warehouse/wms/billing/overview/` -> 1 object (summary + 757 items)
- `/warehouse/wms/dashboard/` -> 1 object (KPIs + top items + recent movements)
- `/warehouse/wms/item-groups/` -> 1 object (9 item groups)
- `/warehouse/wms/sales-orders/backlog/` -> 1 object (summary + 300 open SO lines)
- `/warehouse/wms/stock/movements/` -> 1 object (100 recent movements)
- `/warehouse/wms/stock/overview/` -> 1 object (summary + 953 item×warehouse rows)
- `/warehouse/wms/transfers/overview/` -> 1 object (summary + 200 transfer lines)
- `/warehouse/wms/warehouses/` -> 1 object (31 warehouse codes)
- `/warehouse/wms/warehouses/summary/` -> 1 object (18 active warehouses with metrics)

Linked: [[docs/factory/FACTORY_MAP|FACTORY_MAP]] · [[docs/FACTORY_CLI_PLAN|FACTORY_CLI_PLAN]] · [[docs/READ_ONLY_LAW|READ_ONLY_LAW]]
