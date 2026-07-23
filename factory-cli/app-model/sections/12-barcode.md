---
title: "Barcode — Jivo Mart app-model"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: reference
tags: [jivogpt, factory-cli, barcode]
---

# Barcode — Jivo Mart app-model

> **Provenance — imported 2026-07-19; source snapshot 2026-06-30.** This note came from the JIVO_MART-only `daman8271/jivo-factory-intel` baseline. For the current three-company study and the live-verified 2026-07-19 state, use [[docs/factory/FACTORY_MAP|FACTORY_MAP]] and [[CLI/factory-cli/README|the current CLI guide]].
> Last documented: 2026-06-30. Jivo Mart (JIVO_MART) only.

## 1. Purpose — what this section is for in the factory

The Barcode section is the core **finished-goods track-and-trace and outbound dispatch** system for Jivo Mart's factory. Every carton that comes off the production line gets a barcode label. From that moment until the box ships to a customer, this section records where it is and what happened to it.

Specifically, the section handles:

- **Box lifecycle** — generating, printing, and tracking carton-level barcodes (`BOX-...`) from production through warehouse stock to dispatch.
- **Pallet lifecycle** — grouping boxes onto pallet barcodes (`PLT-...`) for efficient warehouse movement and dispatch.
- **Sales dispatch** — scan-to-ship workflow tied to SAP AR invoices (sales bills); operators scan boxes/pallets on the loading dock to verify every line is fulfilled before the truck leaves.
- **Intercompany transfers** — boxes manufactured by Jivo Oil (`JIVO_OIL`) are transferred to Jivo Mart's inventory via barcode scan; boxes can also be returned.
- **Repack and dismantle** — partial-carton repack (when damaged boxes need consolidation) and box dismantle operations.
- **Print management** — label reprints and bulk printing via a TSC DA310 label printer.
- **Traceability** — full audit trail of every movement event (CREATE → PALLETIZE → DISPATCH, or CREATE → TRANSFER_COMPLETED etc.) per barcode, and cross-company trace.

As of 2026-06-30 the section has **27,206 box barcodes** and **583 pallet barcodes** in the system, with **1,017 intercompany transfers** completed and **57 dispatch sessions** open/completed against SAP invoices.

---

## 2. Page tree

```
/barcode                          — Section landing / summary dashboard

/barcode/boxes                    — Box inventory
  /barcode/boxes/                 — Paginated list of all boxes with filters (status, warehouse, item, date)
  /barcode/boxes/:boxId           — Box detail: full movement history, pallet link, dispatch session link
  /barcode/boxes/generate/        — Generate new box barcodes from a production run / item + batch entry

/barcode/pallets                  — Pallet inventory
  /barcode/pallets/               — Paginated list of all pallets (box count, item, status, warehouse)
  /barcode/pallets/:palletId      — Pallet detail: list of all boxes on the pallet, dispatch info
  /barcode/pallets/create/        — Create a new pallet barcode manually

/barcode/generate                 — Generate barcodes (entry point, likely redirects to boxes/generate)
/barcode/print-history            — Print history alias (redirects to /barcode/print/history/)
/barcode/print/history/           — History of all label prints: label type, print type, printer, operator
/barcode/print/bulk/              — Bulk label printing: select multiple boxes/pallets, send to printer

/barcode/scan                     — Scan interface alias
/barcode/scan/                    — Barcode scan entry point (used for ad-hoc scans)
/barcode/scan/history/            — Full audit log of every scan event (15,031 records); shows scan_type,
                                    barcode, result (SUCCESS / NOT_FOUND), operator, device

/barcode/dispatch                 — Dispatch management home
  /barcode/dispatch/bills/lookup/ — POST-only: look up a SAP AR invoice by bill number to create a session
  /barcode/dispatch/sessions/     — All dispatch sessions (tabbed view)
    /barcode/dispatch/sessions/active/      — Sessions in ACTIVE status (currently being scanned)
    /barcode/dispatch/sessions/closed/      — Manually closed sessions (0 in Jivo Mart; feature exists)
    /barcode/dispatch/sessions/completed/   — Fully scanned and dispatched sessions
    /barcode/dispatch/sessions/from-bill/   — Create / look up a session by SAP bill number (GET param)
  /barcode/dispatch/settings/     — Dispatch configuration (single global settings object)
  /barcode/dispatch/reports       — Reports dashboard alias
    /barcode/dispatch/reports/              — Session-level report (57 rows; one row per session)
    /barcode/dispatch/reports/boxes/        — Box-level dispatch report (1,000 rows, hard-capped)
    /barcode/dispatch/reports/pallets/      — Pallet-level dispatch report (583 rows)
    /barcode/dispatch/reports/rejected-scans/ — All rejected scan events with reason codes (962 rows)
  /barcode/dispatch/summary/:sessionId      — Per-session summary: lines, scan progress, scanned_units

/barcode/intercompany             — Intercompany transfer management
  /barcode/intercompany/dashboard/  — Summary dashboard: today's activity + cumulative routes + recent transfers
  /barcode/intercompany/transfers/  — Paginated list of all IC transfers (1,017 completed)
  /barcode/intercompany/:transferId — Transfer detail: lines, barcode list, status, notes
  /barcode/intercompany/scan/       — POST-only scan input: submit a barcode to a pending IC transfer
  /barcode/intercompany/trace/      — Trace a barcode across companies: full cross-company event history

/barcode/box-transfer             — Box transfer (within Jivo Mart, warehouse-to-warehouse)
/barcode/transfer                 — Transfer alias
/barcode/transfers/box/           — POST-only: submit a box-level transfer

/barcode/loose/                   — Loose / partial-qty records (boxes with residual items after repack)
/barcode/repack                   — Repack interface alias
/barcode/repack/                  — Repack operation: create a new consolidated box from partial-qty sources
/barcode/reprint                  — Reprint label interface (scan/enter a barcode, send to printer)
/barcode/dismantle                — Dismantle a box: break a box barcode into individual loose items
/barcode/split                    — Split a box into smaller boxes (distinct from dismantle)
/barcode/move                     — Move boxes/pallets between warehouses or bins
/barcode/traceability             — End-to-end traceability lookup: enter a barcode, see full history
/barcode/items/oitm/              — SAP item master (OITM) for barcode-managed finished-goods items
/barcode/production-release-oil/  — Production oil release (SAP HANA table not yet configured for JIVO_MART)
```

---

## 3. Per-page detail

### 3.1 Box list — `/barcode/boxes/`

**Purpose:** Browse all finished-goods cartons in the barcode system; filter by status, warehouse, item, date of manufacture.

**API endpoint:** `GET /barcode/boxes/` (paginated)

**Key fields:**

| Field | Meaning |
|---|---|
| `box_barcode` | Unique label: `BOX-YYYYMMDD-XX-NNNN` (standard) or `BOX-YYYYMMDD-RP-NNNN` (repack) |
| `item_code` / `item_name` | SAP finished-goods SKU |
| `batch_number` | Production batch (e.g. `L1  001035`) |
| `qty` | Pieces in this carton |
| `uom` | Unit of measure (`PCS`) |
| `mfg_date` / `exp_date` | Manufacturing and expiry dates |
| `pallet` / `pallet_code` | FK to pallet if palletized |
| `current_warehouse` | e.g. `BH-PF` (Bhiwandi Packed-Finished) or `BH-FGM` |
| `current_bin` | Bin location within warehouse (mostly blank) |
| `status` | `ACTIVE`, `DISPATCHED`, `DISMANTLED` |
| `dispatch_session` | FK to dispatch session if dispatched |
| `production_line` | Empty for normal boxes; `RP` for repack-generated boxes |

**Live sample (2 records):**

```json
{
  "id": 151981,
  "box_barcode": "BOX-20260610-XX-5228",
  "item_code": "FG0000004",
  "item_name": "COLD PRESS 5 LTR 4 PCS",
  "batch_number": "L1  001035",
  "qty": "4.00",
  "uom": "PCS",
  "mfg_date": "2026-06-10",
  "exp_date": "2028-06-09",
  "pallet": 3171,
  "pallet_code": "PLT-20260629-XX-096",
  "current_warehouse": "BH-PF",
  "status": "ACTIVE",
  "dispatch_session": null
}
```

**Data presence:** 27,206 total boxes — 26,604 ACTIVE, 596 DISPATCHED, 4 DISMANTLED. Warehouses: `BH-PF` and `BH-FGM`.

---

### 3.2 Box detail — `/barcode/boxes/:boxId`

**Purpose:** Full detail for one carton: item info, current location, full movement history, and links to any repack or dismantle events.

**API endpoint:** `GET /barcode/boxes/{id}/`

**Key fields (extra vs. list):**

| Field | Meaning |
|---|---|
| `movements[]` | Ordered list of movement events: `CREATE`, `PALLETIZE`, `DISPATCH`, `TRANSFER` etc. Each has `from_warehouse`, `to_warehouse`, `performed_by`, `performed_at` |
| `dismantled_into[]` | List of dismantled sub-records (if box was dismantled) |
| `repacked_from[]` | List of source loose records that were consolidated into this box (if it is a repack box) |
| `production_run` | FK to production run (if generated from production) |

**Movement event types observed:** `CREATE`, `PALLETIZE`, `DISPATCH`.

**Live sample (BOX-20260629-RP-0001):**
```
id: 151918 — box BOX-20260629-RP-0001
item: FG0000227 RICE BRAN OIL 1 LTR 16 PCS
batch: L3  000051, qty: 8 PCS
status: ACTIVE, warehouse: BH-FGM, production_line: RP
movements: [CREATE → BH-FGM]
repacked_from: [{source_box: BOX-20260612-XX-4324, qty: 8}]
```

---

### 3.3 Box generate — `/barcode/boxes/generate/`

**Purpose:** Operator creates new box barcodes for a production batch. Typically triggered after a production run completes. The form takes item code, batch number, manufacture/expiry dates, quantity per box, and box count; the system mints `BOX-YYYYMMDD-XX-NNNN` barcodes in sequence and queues them for printing.

**API endpoint:** `POST /barcode/boxes/` (write operation; not tested read-only).

**Data presence:** Page is functional — boxes are generated daily. The `created_by_name: "Barcode"` entries in the box list indicate system/automated generation from production.

---

### 3.4 Pallet list — `/barcode/pallets/`

**Purpose:** List all pallets (physical wooden pallets holding multiple boxes) in the warehouse system.

**API endpoint:** `GET /barcode/pallets/` (paginated)

**Key fields:**

| Field | Meaning |
|---|---|
| `pallet_id` | Unique label: `PLT-YYYYMMDD-XX-NNN` |
| `item_code` / `item_name` | The item this pallet holds (a pallet holds one SKU) |
| `batch_number` | Batch on the pallet |
| `box_count` | Boxes currently on the pallet |
| `total_boxes` | Total boxes ever assigned |
| `available_boxes` / `dispatched_boxes` | Boxes available vs. dispatched |
| `max_box_count` | Max capacity (0 = unlimited) |
| `total_qty` / `uom` | Total pieces across all boxes |
| `current_warehouse` | e.g. `BH-PF` |
| `status` | `ACTIVE`, `DISPATCHED`, `CLEARED` |
| `dispatch_session` | FK if pallet is linked to a dispatch session |

**Live sample:**
```json
{
  "id": 3122,
  "pallet_id": "PLT-20260629-XX-047",
  "item_code": "FG0000424",
  "item_name": "FIRST PRESSED MUSTARD OIL 1 LTR 20 PCS",
  "batch_number": "L4  006647",
  "box_count": 36,
  "available_boxes": 36,
  "dispatched_boxes": 0,
  "total_qty": "720.00",
  "uom": "PCS",
  "mfg_date": "2026-06-25",
  "exp_date": "2028-06-24",
  "current_warehouse": "BH-PF",
  "status": "ACTIVE"
}
```

**Data presence:** 583 pallets total — 564 ACTIVE, 13 DISPATCHED, 1 CLEARED. All in `BH-PF` (1 in `BH-CRUDE`).

---

### 3.5 Pallet detail — `/barcode/pallets/:palletId`

**Purpose:** Detailed view of a single pallet: all boxes currently on it, dispatch linkage.

**API endpoint:** `GET /barcode/pallets/{id}/`

**Extra fields vs. list:** `boxes[]` — full list of all box records assigned to this pallet (same schema as box list entries).

**Live sample (pallet 3122):** Returns 36 box records for FIRST PRESSED MUSTARD OIL 1 LTR 20 PCS, all ACTIVE, batch L4 006647, each box has 20 PCS.

---

### 3.6 Pallet create — `/barcode/pallets/create/`

**Purpose:** Operator creates a new pallet barcode (mints `PLT-YYYYMMDD-XX-NNN`) before stacking boxes onto it.

**API endpoint:** `POST /barcode/pallets/` (write; not tested read-only).

---

### 3.7 Print history — `/barcode/print/history/`

**Purpose:** Audit trail of every label print event: what was printed, by whom, on which printer, and whether it was an initial print or reprint.

**API endpoint:** `GET /barcode/print/history/` (paginated)

**Key fields:**

| Field | Meaning |
|---|---|
| `label_type` | `BOX` or `PALLET` |
| `reference_code` | The barcode printed (e.g. `BOX-20260629-XX-4004`) |
| `print_type` | `INITIAL` (first print) or `REPRINT` |
| `reprint_reason` | Reason code for reprint (numeric) |
| `printed_by_name` | Operator name |
| `printed_at` | Timestamp |
| `printer_name` | Label printer used (e.g. `TSC DA310`) |

**Live sample:**
```json
{
  "id": 156354,
  "label_type": "BOX",
  "reference_code": "BOX-20260629-XX-4004",
  "print_type": "REPRINT",
  "reprint_reason": "33",
  "printed_by_name": "Jassi",
  "printed_at": "2026-06-29T15:54:02+05:30",
  "printer_name": "TSC DA310"
}
```

**Data presence:** 16 records; all are `BOX` type `REPRINT` on `TSC DA310`. The relatively small count (16) compared to 27,206 boxes suggests initial prints are not all logged here, or pagination is limited in the display window.

---

### 3.8 Scan history — `/barcode/scan/history/`

**Purpose:** Complete audit log of every barcode scan across the system: scan type, barcode raw value, parse result, operator, device (browser UA).

**API endpoint:** `GET /barcode/scan/history/` (paginated)

**Key fields:**

| Field | Meaning |
|---|---|
| `scan_type` | Operation being performed: `SHIP` (dispatch scan), potentially others |
| `barcode_raw` | The raw barcode string scanned |
| `barcode_parsed` | Parsed barcode object `{barcode, entity_type}` |
| `entity_type` | `BOX`, `PALLET`, `UNKNOWN` |
| `scan_result` | `SUCCESS` or `NOT_FOUND` |
| `context_ref_type` | Why the scan happened: `SALES_DISPATCH` |
| `context_ref_id` | FK to the dispatch session |
| `scanned_by_name` | Operator |
| `device_info` | Browser/device user-agent string |
| `scanned_at` | Timestamp |

**Live sample:**
```json
{
  "id": 25211,
  "scan_type": "SHIP",
  "barcode_raw": "BOX-20260624-XX-2331",
  "entity_type": "BOX",
  "scan_result": "SUCCESS",
  "context_ref_type": "SALES_DISPATCH",
  "context_ref_id": 230,
  "scanned_by_name": "Deepak",
  "device_info": "Mozilla/5.0 (Linux; Android 10; K) ... Mobile Safari/537.36",
  "scanned_at": "2026-06-29T20:24:25+05:30"
}
```

**Data presence:** 15,031 records. All observed scan_types are `SHIP`, all context is `SALES_DISPATCH`. Operators use Android mobile devices.

---

### 3.9 Dispatch sessions — `/barcode/dispatch/sessions/`

**Purpose:** Manage the scan-to-ship sessions that verify boxes against SAP sales invoices before dispatch. Each session is linked to one AR invoice (bill_number / sap_doc_num). Tabs: Active, Closed, Completed.

**API endpoint:**
- `GET /barcode/dispatch/sessions/active/` — sessions being scanned right now
- `GET /barcode/dispatch/sessions/completed/` — fully scanned and dispatched
- `GET /barcode/dispatch/sessions/closed/` — manually closed without completing

**Session status lifecycle:** `DRAFT` → `PARTIAL` → `READY_TO_DISPATCH` → `ACTIVE` (scanning) → `COMPLETED` → dispatched; or `CLOSED` (manual close).

**Key session fields:**

| Field | Meaning |
|---|---|
| `bill_number` | SAP AR Invoice number (e.g. `706260331`) |
| `sap_doc_entry` | SAP internal doc entry |
| `delivery_number` | SAP delivery number |
| `customer_code` / `customer_name` | Customer |
| `ship_to_name` | Delivery address |
| `bill_date` | Invoice date |
| `status` | `DRAFT`, `PARTIAL`, `READY_TO_DISPATCH`, `ACTIVE`, `COMPLETED`, `CLOSED`, `CANCELLED` |
| `total_expected_qty` | Total PCS expected per SAP lines |
| `total_scanned_qty` | PCS confirmed by scan so far |
| `pending_qty` | Still to scan |
| `accepted_scan_count` | Accepted barcode scans |
| `rejected_scan_count` | Rejected scans (wrong item, not found, etc.) |
| `pallet_scan_count` | Pallets scanned (one pallet = many boxes) |
| `box_scan_count` | Individual boxes scanned |
| `lines[]` | One line per SAP invoice line: material_code, bill_qty, scanned_qty, status |
| `scanned_units[]` | Every accepted scan unit: box_barcode, item, batch, qty, warehouse, scanned_by |
| `can_dispatch` | Whether the session is ready to dispatch |
| `sap_sync_status` | `NOT_CONFIGURED` for all Jivo Mart sessions (SAP sync disabled) |

**Live sample (completed session 118):**
```
bill: 706260331  customer: R K WORLDINFOCOM PVT LTD  Gurugram
date: 2026-06-15  status: COMPLETED
total_expected_qty: 4220 PCS  total_scanned_qty: 4220 PCS
lines: 1 (COLD PRESS SUNFLOWER 1 LTR 20 PCS, 211 boxes of 20 PCS)
accepted_scan_count: 16 (pallets)  pallet_scan_count: 5  box_scan_count: 211
dispatched_by: Sonu  dispatched_at: 2026-06-17T16:42
```

**Live sample (active session 188):**
```
bill: 706260740  customer: R K WORLDINFOCOM PVT LTD  Haryana
date: 2026-06-25  status: ACTIVE  started_at: 2026-06-26
total_expected_qty: 2000 PCS  total_scanned_qty: 0 PCS  (scanning not yet begun)
lines: 1 (COLD PRESS SUNFLOWER 1 LTR 20 PCS, 100 boxes)
can_scan: true  can_dispatch: false
```

**Data presence (57 sessions total):** DRAFT=19, PARTIAL=24, READY_TO_DISPATCH=11, ACTIVE=1, COMPLETED=2. Closed=0. SAP sync disabled for all (`NOT_CONFIGURED`).

---

### 3.10 Dispatch settings — `/barcode/dispatch/settings/`

**Purpose:** Global configuration for the dispatch scanning workflow.

**API endpoint:** `GET /barcode/dispatch/settings/` (single object)

**Live data:**
```json
{
  "allow_partial_dispatch": true,
  "allow_partial_pallet_dispatch": true,
  "allow_box_dispatch_from_pallet": true,
  "require_sequential_item_scanning": true,
  "require_sap_sync_on_completion": true,
  "allow_manual_close": true,
  "allow_admin_override": false,
  "created_at": "2026-06-01T14:53:07+05:30",
  "updated_at": "2026-06-22T17:17:46+05:30"
}
```

Key implications: sequential item scanning is enforced (one line must be fully scanned before the next); SAP sync is required on completion at configuration level, but SAP sync itself is `NOT_CONFIGURED` in all sessions, meaning dispatch completes without SAP writeback currently.

---

### 3.11 Dispatch reports — `/barcode/dispatch/reports/`

**Purpose:** Flat reporting views for management and audit of dispatch activity.

**Sub-endpoints:**

#### Session report — `/barcode/dispatch/reports/`
57 rows (one per session). Fields: session_id, bill_number, delivery_number, customer, status, created_by, completed_by, started_at, completed_at, total_expected_qty, total_dispatched_qty, pending_qty, expected_boxes, dispatched_boxes, pending_boxes, sap_sync_status.

#### Box report — `/barcode/dispatch/reports/boxes/`
1,000 rows (hard-capped at 1,000). Fields: box_id, box_barcode, material_code, quantity, uom, pallet_barcode, box_status, dispatch_session_id, bill_number, dispatched_time, removed_from_pallet.

**Sample:**
```json
{"box_barcode": "BOX-20260606-XX-2881", "material_code": "FG0000142", "quantity": "16.00", "pallet_barcode": "PLT-20260606-XX-068", "box_status": "ACTIVE", "dispatch_session_id": null, "bill_number": ""}
```

#### Pallet report — `/barcode/dispatch/reports/pallets/`
583 rows. Fields: pallet_id, pallet_barcode, pallet_status, total_boxes, dispatched_boxes, remaining_boxes, dispatch_session_id, bill_number, dispatched_time.

#### Rejected scans report — `/barcode/dispatch/reports/rejected-scans/`
962 rows. Fields: scan_id, barcode, scan_type, rejection_reason (text), rejection_code, bill_number, user, scan_time.

**Sample rejected scan:**
```json
{"barcode": "PLT-20260608-XX-008", "scan_type": "UNKNOWN", "rejection_reason": "Barcode was not found in the barcode system.", "rejection_code": "BARCODE_NOT_FOUND", "bill_number": "606260154", "user": "sonu@jivo.in"}
```

Common rejection_code: `BARCODE_NOT_FOUND` (old or invalid barcodes scanned).

---

### 3.12 Dispatch session summary — `/barcode/dispatch/summary/:sessionId`

**Purpose:** Post-dispatch summary page for a completed session (receipt-style view of what was shipped). Renders the same detail as the session detail endpoint.

**API endpoint:** `GET /barcode/dispatch/sessions/{sessionId}/` (same as session detail).

---

### 3.13 Intercompany dashboard — `/barcode/intercompany/dashboard/`

**Purpose:** Overview of cross-company barcode transfers (e.g. Jivo Oil manufactures boxes, then hands them over to Jivo Mart's inventory via barcode scan).

**API endpoint:** `GET /barcode/intercompany/dashboard/`

**Key fields:**
- `today` — today's summary: transfer_count, barcode_count, carton_count, total_qty
- `routes[]` — cumulative stats per transfer direction
- `recent_transfers[]` — last 10 transfers (full detail)

**Live data (as of 2026-06-30):**

| Route | Transfers | Barcodes | Total Qty |
|---|---|---|---|
| JIVO_OIL → JIVO_MART | 994 | 27,875 | 353,790 PCS |
| JIVO_MART → JIVO_OIL | 19 | 534 | 9,732 PCS |
| JIVO_BEVERAGES → JIVO_MART | 4 | 65 | 780 PCS |

Today (2026-06-30): 0 transfers (snapshot time was after activity ended).

---

### 3.14 Intercompany transfers list — `/barcode/intercompany/transfers/`

**Purpose:** Full paginated list of all intercompany transfer records.

**API endpoint:** `GET /barcode/intercompany/transfers/` (paginated)

**Key fields:**

| Field | Meaning |
|---|---|
| `transfer_number` | Unique ID: `ICBT-YYYYMMDDHHMMSSnnnnnn` |
| `source_company_code` / `destination_company_code` | From/to company |
| `entity_type` | `BOX` or `PALLET` |
| `status` | All observed: `COMPLETED` |
| `total_barcodes` | Number of barcodes in this transfer |
| `total_qty` / `uom` | Total quantity |
| `sap_enabled` | `false` for Jivo Mart (SAP sync not configured) |
| `lines[]` | One record per barcode: box FK, barcode, item_code, item_name, batch, qty, from/to company |
| `reversed_at` | If the transfer was reversed (returned) |
| `device_id` | `web` (browser-based) |
| `created_by_name` | Operator who performed the transfer |

**Live sample:**
```json
{
  "transfer_number": "ICBT-20260629191556184924",
  "source_company_code": "JIVO_OIL",
  "destination_company_code": "JIVO_MART",
  "entity_type": "BOX",
  "status": "COMPLETED",
  "total_barcodes": 7,
  "total_qty": "112.000",
  "uom": "PCS",
  "sap_enabled": false,
  "created_by_name": "Jassi"
}
```

**Data presence:** 1,017 total transfers. From 100-record sample: 100% COMPLETED; entity_type mix: 83% BOX, 17% PALLET; 96% are JIVO_OIL → JIVO_MART, 4% JIVO_MART → JIVO_OIL.

---

### 3.15 Intercompany transfer detail — `/barcode/intercompany/:transferId`

**Purpose:** Full detail of one transfer including all lines and individual barcode records.

**API endpoint:** `GET /barcode/intercompany/transfers/{id}/` (note: the `/barcode/intercompany/1021/` path returned 404; the correct path appears to be via the transfers sub-resource).

---

### 3.16 Intercompany trace — `/barcode/intercompany/trace/`

**Purpose:** Enter a barcode value and see its complete cross-company history: which company manufactured it, all transfer events, current owner company, current location, and dispatch status.

**API endpoint:** `GET /barcode/intercompany/trace/?search={barcode}`

**Live sample (BOX-20260606-XX-2881):**
```json
{
  "barcode": "BOX-20260606-XX-2881",
  "current_company": "JIVO_MART",
  "current_company_name": "Jivo Mart",
  "manufacturing_company": "JIVO_OIL",
  "dispatch_status": "NOT_DISPATCHED",
  "current_location": "BH-PF",
  "history": [
    {"transaction_type": "MANUFACTURED",   "to_company_code": "JIVO_OIL",  "created_at": "2026-06-06T..."},
    {"transaction_type": "SCANNED",        "from": "JIVO_OIL", "to": "JIVO_MART", "created_at": "2026-06-29T..."},
    {"transaction_type": "TRANSFER_COMPLETED", "transfer_number": "ICBT-...", "from": "JIVO_OIL", "to": "JIVO_MART", "created_at": "2026-06-29T..."}
  ]
}
```

---

### 3.17 Loose records — `/barcode/loose/`

**Purpose:** Tracks partial-quantity "loose" carton sources that have been dismantled and are waiting to be repacked. When a box is opened and not all items are used, the remaining items are tracked here until they are consolidated into a new repack box.

**API endpoint:** `GET /barcode/loose/` (paginated)

**Key fields:**

| Field | Meaning |
|---|---|
| `item_code` / `item_name` | The SKU |
| `batch_number` | Batch |
| `qty` | Remaining loose quantity (often 0.00 after repacking) |
| `original_qty` | Original quantity when the loose record was created |
| `source_box` / `source_box_barcode` | The original box that was opened |
| `source_pallet` / `source_pallet_id` | Pallet the source box was on |
| `reason` | `OTHER`, `DAMAGED`, `MANUFACTURING_DEFECT`, etc. |
| `reason_notes` | Free-text notes |
| `status` | `PENDING` (not yet repacked) or `REPACKED` |
| `repacked_into_box` / `repacked_into_barcode` | FK to the new box created after repacking |

**Live data (7 records, all REPACKED):**
```
id=727: FG0000227 RICE BRAN OIL 1 LTR 16 PCS, batch L3 000051
  source: BOX-20260612-XX-4324 (8 PCS loose) → repacked into BOX-20260629-RP-0001
  reason: OTHER, warehouse: BH-PF
```

**Data presence:** 7 records total, all REPACKED (no pending loose items on 2026-06-30). Item is always RICE BRAN OIL 1 LTR 16 PCS, same batch.

---

### 3.18 Repack — `/barcode/repack/`

**Purpose:** Operator creates a new repack box by consolidating one or more loose records. Generates a new `BOX-YYYYMMDD-RP-NNNN` barcode. The repacked box gets a new label and enters inventory.

**API endpoint:** `POST /barcode/loose/` or similar write endpoint (not tested read-only).

---

### 3.19 Items / OITM — `/barcode/items/oitm/`

**Purpose:** SAP item master reference for finished-goods items that are barcode-managed. Used by the barcode system to validate item codes during box generation.

**API endpoint:** `GET /barcode/items/oitm/` (returns up to 100, list not paginated)

**Key fields:** `item_code`, `item_name`, `inventory_uom` (`PCS`), `manage_batch_numbers` (always `true`), `item_group_code` (always 102 = Finished Goods), `is_inventory_item`, `is_sales_item`, `valid_for`, `frozen_for`.

**Sample items:**
```
FG0000001: COLD PRESS 15 LTR
FG0000004: COLD PRESS 5 LTR 4 PCS
FG0000081: COLD PRESS SUNFLOWER 1 LTR 20 PCS
FG0000142: COLD PRESS GROUNDNUT OIL 1 LTR 16 PCS
FG0000227: RICE BRAN OIL 1 LTR 16 PCS
FG0000424: FIRST PRESSED MUSTARD OIL 1 LTR 20 PCS
```

**Data presence:** 100 items (list is capped at 100). All are item_group_code=102 (Finished Goods), all batch-managed, none are serial-managed.

---

### 3.20 Production release oil — `/barcode/production-release-oil/`

**Purpose:** Intended to release production-finished oil records from a SAP HANA table into the barcode system.

**Status for Jivo Mart:** NOT CONFIGURED. Live API returns:
```json
{"error": "(259, 'invalid table name: Could not find table/view PRODUCTION_RELEASE_OIL in schema JIVO_MART_HANADB')"}
```
The underlying HANA table `PRODUCTION_RELEASE_OIL` does not exist in the `JIVO_MART_HANADB` schema. This page is empty/broken for Jivo Mart.

---

### 3.21 Move, Split, Dismantle, Reprint, Traceability, Box-transfer

These are operational action pages (mostly POST-only write endpoints or lookup pages):

- **`/barcode/move`** — Move a box or pallet to a different warehouse/bin. Write operation.
- **`/barcode/split`** — Split one box into two or more boxes with smaller quantities. Write operation.
- **`/barcode/dismantle`** — Dismantle a box barcode (sets status to `DISMANTLED`, qty to 0). Used for damaged or empty cartons. 4 dismantled boxes exist in Jivo Mart.
- **`/barcode/reprint`** — Enter a barcode, select printer, send reprint. Uses `POST /barcode/print/history/`. Printer: TSC DA310.
- **`/barcode/traceability`** — Full traceability lookup: enter any barcode, get its complete history including intercompany trace. No distinct GET endpoint — builds from box/pallet detail + intercompany trace.
- **`/barcode/box-transfer` / `/barcode/transfer` / `/barcode/transfers/box/`** — Transfer boxes between internal warehouses. `/barcode/transfers/box/` is POST-only (GET returns "Method not allowed").
- **`/barcode/print/bulk/`** — Bulk print: select multiple barcodes, batch-print to the TSC printer.

---

## 4. Workflows (multi-step flows + statuses)

### 4.1 Box barcode generation and printing

```
Production run completes (line produces boxes)
  → Operator opens /barcode/boxes/generate/ (or /barcode/generate)
  → Selects item_code (from /barcode/items/oitm/), enters batch, mfg_date, exp_date, qty/box, box_count
  → System mints BOX-YYYYMMDD-XX-NNNN barcodes in sequence
  → Boxes created with status=ACTIVE, warehouse assigned
  → Labels printed to TSC DA310 via /barcode/print/bulk/ or auto-print
  → Print event logged in /barcode/print/history/ (print_type=INITIAL)
```

### 4.2 Palletizing

```
Boxes in warehouse → Operator creates pallet at /barcode/pallets/create/
  → System mints PLT-YYYYMMDD-XX-NNN
  → Operator scans boxes onto pallet (scan at /barcode/scan/)
  → Box.pallet FK updated; Box movement event: PALLETIZE added
  → Pallet box_count increments
  → Pallet status: ACTIVE (has boxes)
  → CLEARED = pallet was used but all boxes removed
```

### 4.3 Sales dispatch session

```
Dispatch team creates session from SAP invoice:
  POST /barcode/dispatch/bills/lookup/ with bill_number
    → Session created, status=DRAFT
    → SAP invoice lines imported (one line per material_code)

  Session goes DRAFT → PARTIAL as some boxes are scanned
    → Operator scans BOX or PLT barcodes at loading dock
    → Each scan: POST to session scan endpoint
    → Accepted scan: box status = DISPATCHED, movement event: DISPATCH
    → Rejected scan: logged to rejected-scans with rejection_code (BARCODE_NOT_FOUND, WRONG_ITEM, etc.)
    → Scan events logged in /barcode/scan/history/ (scan_type=SHIP, context=SALES_DISPATCH)

  PARTIAL → READY_TO_DISPATCH (all lines fulfilled)
    → can_dispatch = true
    → Operator reviews session summary at /barcode/dispatch/summary/{id}

  READY_TO_DISPATCH → COMPLETED (Dispatched by button)
    → dispatched_at and dispatched_by set
    → sap_sync_status would be triggered if configured (currently NOT_CONFIGURED)

  Alternatively: ACTIVE → CLOSED (manual close by operator with close_reason)
```

**Session status distribution (live):** DRAFT=19, PARTIAL=24, READY_TO_DISPATCH=11, ACTIVE=1, COMPLETED=2, CLOSED=0.

### 4.4 Intercompany transfer (JIVO_OIL → JIVO_MART)

```
Jivo Oil manufactures boxes → boxes exist in JIVO_OIL inventory
  → Transfer triggered at /barcode/intercompany/scan/ (JIVO_OIL operator scans boxes)
  → Each scan: POST to IC scan endpoint, validated in JIVO_OIL context
  → IC transfer record created: ICBT-{timestamp}
    → Lines added: one per barcode (item_code, batch, qty, from_company, to_company)
  → Transfer COMPLETED
    → Box ownership updated to JIVO_MART (current_company in trace = JIVO_MART)
    → Intercompany history: MANUFACTURED (JIVO_OIL) → SCANNED → TRANSFER_COMPLETED (JIVO_MART)
    → Visible in /barcode/intercompany/dashboard/ and /barcode/intercompany/transfers/

  Reverse transfer (JIVO_MART → JIVO_OIL): same process, 19 such transfers so far
```

### 4.5 Repack workflow

```
Damaged/partial box identified → Loose record created at /barcode/loose/
  → source_box, remaining_qty, reason recorded; status=PENDING

One or more loose records ready to consolidate:
  → Operator opens /barcode/repack/
  → Selects loose records (same item/batch)
  → System creates new BOX-YYYYMMDD-RP-NNNN barcode
  → New box status=ACTIVE, production_line=RP
  → Loose records: status → REPACKED, repacked_into_box set
  → New box: repacked_from[] lists all source loose records
  → New label printed via /barcode/reprint or /barcode/print/bulk/
```

### 4.6 Label reprint

```
Damaged or lost label → Operator goes to /barcode/reprint
  → Enters barcode or scans it
  → Selects printer (TSC DA310)
  → Submits reprint request
  → Print event logged: label_type=BOX, print_type=REPRINT, reprint_reason={code}, printed_by, printer_name
```

---

## 5. Cross-section connections

| This section | Connects to | How |
|---|---|---|
| **Box generate** | Production (section: Production) | Boxes are created after production runs complete; `production_run` FK in box record links to production run entity |
| **Dispatch sessions** | SAP AR Invoices | Sessions are created from SAP sales bills; `sap_doc_entry`, `sap_doc_num`, `delivery_number` link back to SAP Business One |
| **Dispatch sessions** | Warehouse | Box `current_warehouse` / `current_bin` tracks warehouse location; dispatch moves boxes out of BH-PF to customer |
| **Intercompany transfers** | Jivo Oil (JIVO_OIL company) | Boxes manufactured by Jivo Oil are transferred in; this is the primary stock replenishment route for Jivo Mart (994 transfers, 353,790 PCS received) |
| **Intercompany transfers** | Jivo Beverages (JIVO_BEVERAGES) | 4 transfers, 65 barcodes, 780 PCS received from Beverages |
| **Scan history** | All operations | Every scan from any context (dispatch, IC transfer) is logged here with context_ref_type and context_ref_id |
| **Print history** | Label printing hardware | All TSC DA310 label print events are centralised here |
| **Items/OITM** | SAP item master | Item master is the authoritative source for FG item codes and batch management settings |
| **Barcode boxes** | Gate / GRPO (Inbound) | Potentially: received goods could generate barcodes at gate (not confirmed for Jivo Mart — production-release-oil is the gap) |
| **Traceability** | Cross-section | Pulls from box movements, intercompany trace, and scan history to build a full audit trail |

---

## 6. Data presence for Jivo Mart

| Endpoint | Count | Status |
|---|---|---|
| `/barcode/boxes/` | 27,206 | **LIVE** — Active production. 26,604 ACTIVE, 596 DISPATCHED, 4 DISMANTLED. |
| `/barcode/pallets/` | 583 | **LIVE** — Active. 564 ACTIVE, 13 DISPATCHED, 1 CLEARED. |
| `/barcode/loose/` | 7 | **LIVE** — 7 records, all REPACKED (no pending loose). All RICE BRAN OIL batch L3 000051. |
| `/barcode/print/history/` | 16 | **LIVE** — small active window. All BOX REPRINT on TSC DA310. |
| `/barcode/scan/history/` | 15,031 | **LIVE** — high-volume. All SHIP / SALES_DISPATCH context. |
| `/barcode/dispatch/sessions/active/` | 55 | **LIVE** — 55 sessions in active API endpoint (mix of statuses) |
| `/barcode/dispatch/sessions/completed/` | 2 | **LIVE** — 2 fully completed dispatches |
| `/barcode/dispatch/sessions/closed/` | 0 | EMPTY — no manually closed sessions |
| `/barcode/dispatch/reports/` | 57 | **LIVE** — 57 sessions: DRAFT=19, PARTIAL=24, READY_TO_DISPATCH=11, ACTIVE=1, COMPLETED=2 |
| `/barcode/dispatch/reports/boxes/` | 1,000 | **LIVE** (hard-capped at 1,000; real count higher) |
| `/barcode/dispatch/reports/pallets/` | 583 | **LIVE** |
| `/barcode/dispatch/reports/rejected-scans/` | 962 | **LIVE** — 962 rejected scan events; most reason: BARCODE_NOT_FOUND |
| `/barcode/dispatch/settings/` | 1 | **LIVE** — configured 2026-06-01, updated 2026-06-22 |
| `/barcode/intercompany/dashboard/` | 1 | **LIVE** — 3 routes, 1,017 total transfers |
| `/barcode/intercompany/transfers/` | 1,017 | **LIVE** — all COMPLETED; 96% JIVO_OIL→JIVO_MART |
| `/barcode/items/oitm/` | 100 | **LIVE** (capped at 100) — all FG items, group 102 |
| `/barcode/production-release-oil/` | 0 | **BROKEN** — HANA table `PRODUCTION_RELEASE_OIL` missing in JIVO_MART schema |
| `/barcode/dispatch/bills/lookup/` | — | **POST-only** — GET returns 405 Method Not Allowed |
| `/barcode/transfers/box/` | — | **POST-only** — GET returns 405 Method Not Allowed |
| `/barcode/intercompany/scan/` | — | **POST-only** — GET returns 405 Method Not Allowed |
| `/barcode/boxes/generate/` | — | Write-only UI page (POST); not a GET endpoint |
| `/barcode/pallets/create/` | — | Write-only UI page (POST); not a GET endpoint |

**Summary for Jivo Mart:** The Barcode section is fully operational as the primary track-and-trace layer for finished goods. Box and pallet stock is high-volume and active. Dispatch sessions are heavily used (57 sessions, operators scanning on Android mobile). Intercompany transfers are the main stock intake route (994 transfers from Jivo Oil). The only non-functional piece is `production-release-oil`, which has a missing HANA table. SAP sync on dispatch completion is `NOT_CONFIGURED` — dispatches complete internally without writing back to SAP Business One.

---

## Reference — UI routes (from bundle)
- `/barcode`
- `/barcode/box-transfer`
- `/barcode/boxes`
- `/barcode/boxes/`
- `/barcode/boxes/:boxId`
- `/barcode/boxes/generate/`
- `/barcode/dismantle`
- `/barcode/dispatch`
- `/barcode/dispatch/bills/lookup/`
- `/barcode/dispatch/reports`
- `/barcode/dispatch/reports/`
- `/barcode/dispatch/reports/boxes/`
- `/barcode/dispatch/reports/pallets/`
- `/barcode/dispatch/reports/rejected-scans/`
- `/barcode/dispatch/sessions/`
- `/barcode/dispatch/sessions/active/`
- `/barcode/dispatch/sessions/closed/`
- `/barcode/dispatch/sessions/completed/`
- `/barcode/dispatch/sessions/from-bill/`
- `/barcode/dispatch/settings/`
- `/barcode/dispatch/summary/:sessionId`
- `/barcode/generate`
- `/barcode/intercompany`
- `/barcode/intercompany/:transferId`
- `/barcode/intercompany/dashboard/`
- `/barcode/intercompany/scan/`
- `/barcode/intercompany/trace/`
- `/barcode/intercompany/transfers/`
- `/barcode/items/oitm/`
- `/barcode/loose`
- `/barcode/loose/`
- `/barcode/move`
- `/barcode/pallets`
- `/barcode/pallets/`
- `/barcode/pallets/:palletId`
- `/barcode/pallets/create/`
- `/barcode/print-history`
- `/barcode/print/bulk/`
- `/barcode/print/history/`
- `/barcode/production-release-oil/`
- `/barcode/repack`
- `/barcode/repack/`
- `/barcode/reprint`
- `/barcode/scan`
- `/barcode/scan/`
- `/barcode/scan/history/`
- `/barcode/split`
- `/barcode/traceability`
- `/barcode/transfer`
- `/barcode/transfers/box/`

## Reference — captured API endpoints + record counts (this section)
- `/barcode/boxes/` -> 27206 (paginated_list)
- `/barcode/dispatch/reports/` -> 57 (list)
- `/barcode/dispatch/reports/boxes/` -> 1000 (list, hard-capped)
- `/barcode/dispatch/reports/pallets/` -> 583 (list)
- `/barcode/dispatch/reports/rejected-scans/` -> 962 (list)
- `/barcode/dispatch/sessions/active/` -> 55 (paginated_list)
- `/barcode/dispatch/sessions/closed/` -> 0 (paginated_list)
- `/barcode/dispatch/sessions/completed/` -> 2 (paginated_list)
- `/barcode/dispatch/settings/` -> 1 (object)
- `/barcode/intercompany/dashboard/` -> 1 (object)
- `/barcode/intercompany/transfers/` -> 1017 (paginated_list, live count)
- `/barcode/items/oitm/` -> 100 (list, capped)
- `/barcode/loose/` -> 7 (paginated_list)
- `/barcode/pallets/` -> 583 (paginated_list)
- `/barcode/print/history/` -> 16 (paginated_list)
- `/barcode/scan/history/` -> 15031 (paginated_list)

Linked: [[docs/factory/FACTORY_MAP|FACTORY_MAP]] · [[docs/FACTORY_CLI_PLAN|FACTORY_CLI_PLAN]] · [[docs/READ_ONLY_LAW|READ_ONLY_LAW]]
