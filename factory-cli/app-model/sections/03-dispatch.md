---
title: "Dispatch — Jivo Mart app-model"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: reference
tags: [jivogpt, factory-cli, dispatch]
---

# Dispatch — Jivo Mart app-model

> **Provenance — imported 2026-07-19; source snapshot 2026-06-30.** This note came from the JIVO_MART-only `daman8271/jivo-factory-intel` baseline. For the current three-company study and the live-verified 2026-07-19 state, use [[docs/factory/FACTORY_MAP|FACTORY_MAP]] and [[CLI/factory-cli/README|the current CLI guide]].
> Last updated: 2026-06-30. Jivo Mart (JIVO_MART) only. All API samples verified live.

---

## 1. Purpose — what this section is for in the factory

The **Dispatch** section is the outbound-freight control centre for Jivo Mart. It owns three distinct but sequential concerns:

1. **Vehicle Linking & Pipeline visibility** — maps an empty vehicle (already gate-in'd) to a specific SAP sales invoice, assigning transporter/driver details, creating the DispatchPlan that then advances through a 10-stage kanban (BOOKED → DISPATCHED).
2. **Docking & Gatepass** — orchestrates the physical truck-loading event at the dispatch dock: barcode-scanning boxes onto the vehicle, attaching vehicle photos, recording weighment, generating and printing the gatepass, and committing the print to close the gate-out record (DOCK-prefixed SalesDispatch entry).
3. **Post-dispatch accounting** — after the truck departs, two financial sub-flows settle the freight cost in SAP:
   - **Bilty-GRPO**: records the consignment note (bilty) details and posts a SAP service Goods-Receipt PO (GRPO) for freight under each invoice.
   - **Transporter Invoice**: bundles multiple dispatches under one AP invoice to the transporter and posts it to SAP accounts payable.

Every truck dispatch from the factory must pass through all three stages in order.

---

## 2. Page tree

```
/dispatch                                   ← Dispatch section home / overview
│
├── /dispatch-plans/pipeline/               ← Kanban: 10-stage dispatch plan progress board
│
├── /dispatch-plans/bills/                  ← Bills list: SAP invoices pending vehicle assignment
│                                             (requires date_from + date_to query params)
│
├── /dispatch/plans                         ← Dispatch plans list view (tabular alternative to pipeline)
│
├── /dispatch/vehicle-linking               ← Assign vehicle/driver/transporter to a dispatch plan
│
├── /dispatch/docking                       ← Docking session list & status overview
│   ├── /dispatch/docking/:entryId          ← Individual docking entry detail (DOCK-YYYYMMDD-####)
│   │   └── /dispatch/docking/:entryId/reprint  ← Reprint gatepass for a completed entry
│   ├── /dispatch/docking/new               ← New docking session wizard (step 1: select plan)
│   │   ├── /dispatch/docking/new/barcode-scan  ← Step 2: scan carton/pallet barcodes
│   │   ├── /dispatch/docking/new/attachments   ← Step 3: attach vehicle/load photos
│   │   ├── /dispatch/docking/new/weighment     ← Step 4: record gross/tare weighment
│   │   └── /dispatch/docking/new/gatepass      ← Step 5: generate & print gatepass
│   ├── /dispatch/docking/reprint           ← Search & reprint gatepass (lookup by entry)
│   └── /dispatch/docking/reports           ← Docking reports & summary counts
│
├── /dispatch/open-bilties                  ← Dispatched plans whose bilty number is not yet recorded
│   └── /dispatch/open-bilties/             ← (same, canonical URL)
│
├── /dispatch/bilty-grpo                    ← Bilty-GRPO section landing
│   ├── /dispatch/bilty-grpo/pending        ← Queue of dispatched plans needing bilty & GRPO posting
│   │   └── /dispatch/bilty-grpo/pending/   ← (canonical)
│   ├── /dispatch/bilty-grpo/preview/:dispatchPlanId  ← Bilty detail & GRPO form for one plan
│   ├── /dispatch/bilty-grpo/post/          ← POST-only: submit bilty + GRPO to SAP
│   ├── /dispatch/bilty-grpo/options/       ← Reference data: branches, tax codes, GL accounts
│   ├── /dispatch/bilty-grpo/history        ← Completed bilty-GRPO postings list
│   │   └── /dispatch/bilty-grpo/history/:postingId  ← Individual posting detail
│
└── /dispatch/transporter-invoices          ← Transporter invoice section landing
    ├── /dispatch/transporter-invoices/pending     ← Plans ready for transporter AP invoice
    ├── /dispatch/transporter-invoices/preview/    ← Preview transporter invoice before submit
    ├── /dispatch/transporter-invoices/submit/     ← POST-only: submit AP invoice to SAP
    ├── /dispatch/transporter-invoices/post-ap-invoice/  ← Alternate post form
    ├── /dispatch/transporter-invoices/history     ← Posted transporter invoices list
    │   └── /dispatch/transporter-invoices/history/:postingId  ← Individual posting detail
```

---

## 3. Per-page detail

### 3.1 `/dispatch-plans/pipeline/` — Dispatch Pipeline Kanban

**Purpose:** Real-time kanban board showing all active dispatch plans across 10 lifecycle stages. Managers use this to spot bottlenecks (plans stuck at DOCKED, PHOTO_ATTACHED, etc.).

**API:** `GET /api/v1/dispatch-plans/pipeline/`
**Response shape:** `{ columns: [{stage, label, count}], cards: [{...DispatchPlanPipelineCard}] }`

**Key fields per card:**
- `plan_id` — DispatchPlan integer PK (same as `dispatch_plan_id` in other endpoints)
- `stage` / `stage_label` — current pipeline stage
- `stage_at` — timestamp of last stage transition
- `sap_doc_num` / `invoice_number` — SAP invoice number (e.g. `706260665`)
- `vehicle_no` / `vehicle_id` — truck registration
- `transporter_name` / `driver_name` / `driver_mobile_no`
- `dispatch_date` / `place_of_supply` (state code) / `customer_name`
- `empty_gate_in_entry_no` — EVGI-series gate-in that brought the vehicle in
- `gate_out_id` / `gate_out_entry_no` — DOCK-series gate-out once the truck left
- `gate_out_vehicle_entry_id` — DOCKV-series vehicle-entry session FK

**Live sample (2026-06-30):**
```json
{
  "plan_id": 690,
  "stage": "DISPATCHED",
  "stage_label": "Dispatched",
  "stage_at": "2026-06-29T20:58:48.032351+05:30",
  "sap_doc_num": "706260665",
  "vehicle_no": "HR69E9959",
  "transporter_name": "Jivo Wellness",
  "dispatch_date": "2026-06-29",
  "place_of_supply": "HR",
  "customer_name": "R K WORLDINFOCOM PVT LTD",
  "empty_gate_in_entry_no": "EVGI-20260629-0018",
  "gate_out_entry_no": "DOCK-20260629-0022",
  "gate_out_status": "DISPATCHED",
  "gate_out_vehicle_entry_id": 1254
}
```

**Current counts (live):**
| Stage | Count |
|---|---|
| BOOKED | 0 |
| EMPTY_IN | 0 |
| READY_TO_DOCK | 0 |
| DOCKED | 0 |
| PHOTO_ATTACHED | 0 |
| READY_FOR_GATEPASS | 0 |
| GATEPASS_PRINTED | 0 |
| PRINT_COMMITTED | 0 |
| **DISPATCHED** | **19** |
| REJECTED | 0 |
| **Total cards** | **19** |

All 19 active plan cards are in DISPATCHED state — no plans are in-flight at the moment of sampling (2026-06-30). Plans cycle through earlier stages rapidly on dispatch days.

---

### 3.2 `/dispatch-plans/bills/` — Bills Pending Assignment

**Purpose:** Tabular list of SAP sales invoices that have been booked into a DispatchPlan but whose vehicle/driver details may still be PENDING assignment. Operators use this to locate invoices for a given date range and assign or confirm vehicles before dispatch.

**API:** `GET /api/v1/dispatch-plans/bills/?date_from=YYYY-MM-DD&date_to=YYYY-MM-DD`
Both query params are **required**; the endpoint returns `{"detail":"Invalid query parameters.","errors":{"date_from":["This field is required."],"date_to":["This field is required."]}}` without them.

**Response shape:** `{ data: [{...SalesDispatchDocument with embedded plan object}] }`

**Key fields:**
- `doc_entry` / `doc_num` — SAP invoice entry/number
- `card_code` / `card_name` — customer code/name
- `doc_total` — invoice total amount (₹)
- `branch_id` / `branch_name` / `state` — dispatching branch
- `ship_to_address`, `city`, `bp_gstin` — delivery address / GST details
- `total_quantity`, `total_litres`, `total_weight`, `warehouses`, `item_summary` — item breakdown
- `plan.id` — linked DispatchPlan ID
- `plan.booking_status` — `PENDING` (vehicle not yet assigned) or `BOOKED` (vehicle confirmed)
- `plan.pipeline_status.stage` — current kanban stage
- `plan.dispatch_date`, `plan.priority` — scheduled dispatch date and priority

**Live sample (2026-06-29, last 7 days):**
```json
{
  "doc_num": "706260877",
  "doc_date": "2026-06-29",
  "card_name": "R K WORLDINFOCOM PVT LTD",
  "doc_total": 199500.0,
  "branch_name": "DELHI",
  "state": "HR",
  "city": "GURUGRAM",
  "total_litres": 1000.0,
  "item_summary": "FG0000424 - FIRST PRESSED MUSTARD OIL 1 LTR 20 PCS",
  "plan": {
    "id": 742,
    "booking_status": "PENDING",
    "dispatch_date": "2026-06-30",
    "priority": "HIGH",
    "pipeline_status": { "stage": "BOOKED", "stage_label": "Booked" },
    "vehicle_no": "",
    "transporter_name": "",
    "remarks": "01/07/2026 08:30 AM IST"
  }
}
```

**Data presence:** Live data returned when date params are provided. 2 records seen in the last 7 days, both with `booking_status: PENDING` (vehicles not yet assigned).

---

### 3.3 `/dispatch/vehicle-linking` — Vehicle Linking

**Purpose:** Form page where planners assign vehicle, driver, and transporter to a dispatch plan. Once completed, `plan.booking_status` transitions from `PENDING` to `BOOKED` and the plan advances to `EMPTY_IN` or beyond on the pipeline.

**API:** This page reads from `/dispatch-plans/bills/` (the bills list) and uses a POST/PATCH to update the DispatchPlan with `vehicle_id`, `transporter_id`, `driver_id`. No dedicated GET endpoint discovered — the page fetches plans from the bills list filtered to those needing vehicle assignment.

**Key fields set via this page:** `vehicle_no`, `transporter_name`, `transporter_gstin`, `driver_name`, `driver_mobile_no`, `driver_license_no`, `bilty_no`, `dispatch_date`.

---

### 3.4 `/dispatch/docking` and sub-routes — Docking Sessions

**Purpose:** The docking section is the physical loading-bay control module. When an empty vehicle parks at the dispatch dock, an operator creates a new "docking entry" (a SalesDispatch, DOCK-prefixed) via the wizard, scans all carton/pallet barcodes, attaches photos, records weighment, and then generates and prints the gatepass that lets the truck exit.

**API backend:** `GET /api/v1/gate-core/sales-dispatch/` (list), `GET /api/v1/gate-core/sales-dispatch/reports/` (summary counts). The `/dispatch/docking/*` UI routes consume the `gate-core/sales-dispatch` API family, not a `/dispatch/docking/` REST resource (which returns 404).

**Docking list key fields (SalesDispatch):**
- `entry_no` — DOCK-YYYYMMDD-NNNN identifier
- `vehicle_entry_no` — DOCKV- vehicle entry session FK
- `vehicle_entry_status` — `IN_PROGRESS` (loading) or `COMPLETED` (departed)
- `arrival_status` — `LOADING` (inside) or `DEPARTED` (gate-out complete)
- `dispatch_plan` — linked DispatchPlan id
- `vehicle_no`, `transporter_name`, `driver_name`
- `document_count`, `document_numbers` — SAP invoice numbers on this truck
- `document_type` — `INVOICE`
- `gatepass_print_locked` — boolean; true if gatepass is locked by admin
- `gatepass_lock_reason`
- `warehouses`, `item_summary` — FG item codes and names loaded
- `total_litres`, `total_weight`

**Live sample (DOCK-20260629-0022):**
```json
{
  "entry_no": "DOCK-20260629-0022",
  "vehicle_entry_no": "DOCKV-20260629-0022",
  "vehicle_entry_status": "COMPLETED",
  "arrival_status": "DEPARTED",
  "dispatch_plan": 690,
  "vehicle_no": "HR69E9959",
  "transporter_name": "Jivo Wellness",
  "driver_name": "Gurpreet 9872987038",
  "customer_name": "R K WORLDINFOCOM PVT LTD",
  "document_count": 2,
  "document_numbers": ["706260665", "706260666"],
  "item_summary": "FG0000143 - COLD PRESS GROUNDNUT OIL 5 LTR 4 PCS, FG0000032 - COLD PRESS 1 LTR 20 PCS, ...",
  "warehouses": "DL-FG",
  "gatepass_print_locked": false
}
```

**Docking summary counts (live, 2026-06-30):**
```json
{
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
```

**Wizard sub-pages (`/dispatch/docking/new/*`):**

| Step | Route | Purpose |
|---|---|---|
| 1 | `/dispatch/docking/new` | Select dispatch plan / SAP invoice; look up vehicle & driver |
| 2 | `/dispatch/docking/new/barcode-scan` | Scan BOX- and PLT- barcodes to verify loaded cartons against the invoice; integrated with barcode/DispatchSession |
| 3 | `/dispatch/docking/new/attachments` | Attach photos of loaded vehicle (required before gatepass) |
| 4 | `/dispatch/docking/new/weighment` | Enter gross weight, tare weight, weighbridge slip number |
| 5 | `/dispatch/docking/new/gatepass` | Generate, preview and print the physical gatepass PDF |

**Gatepass reprint:** `/dispatch/docking/reprint` (search by entry) and `/dispatch/docking/:entryId/reprint` (direct). These use the `gate-core/sales-dispatch/:id/` endpoint.

**Partial-scan and skip-scan exceptions** (supervisor approval required):
- `/api/v1/docking-admin/partial-scan-requests/` — 21 records active
- `/api/v1/docking-admin/scan-skip-requests/` — 12 records active

**Sample partial-scan request:**
```json
{
  "entry_no": "DOCK-20260629-0022",
  "vehicle_no": "HR69E9959",
  "customer_name": "R K WORLDINFOCOM PVT LTD",
  "scanned_boxes": 4,
  "expected_boxes": 0,
  "reason": "half box scanned old & half new",
  "status": "APPROVED",
  "requested_by_name": "Raaj",
  "reviewed_by_name": "Bhupinder Singh"
}
```

**Docking reports page (`/dispatch/docking/reports`):** Reads from `gate-core/sales-dispatch/reports/` and shows the summary count table above plus lists of trucks in each status bucket.

---

### 3.5 `/dispatch/open-bilties/` — Open Bilties

**Purpose:** Shows dispatch plans that have completed the gate-out (DISPATCHED) but whose bilty (consignment note) number has not yet been recorded. Used by the operations team to chase up missing bilty details from the transporter.

**API:** `GET /api/v1/dispatch/open-bilties/`

**Data presence:** **Empty** (0 records) as of 2026-06-30. This means all recently dispatched plans either already have bilty numbers recorded or are being tracked via the bilty-grpo/pending queue.

---

### 3.6 `/dispatch/bilty-grpo/pending/` — Bilty-GRPO Pending Queue

**Purpose:** Lists all dispatched plans that are ready for the bilty-GRPO accounting step — the freight consignment note has been received from the transporter, and the operator needs to enter the bilty number, freight amount, and post a SAP service GRPO to record the freight cost.

**API:** `GET /api/v1/dispatch/bilty-grpo/pending/`

**Key fields:**
- `dispatch_plan_id` — DispatchPlan PK
- `sap_invoice_doc_num` — SAP invoice number (e.g. `706260628`)
- `booking_status` — always `BOOKED` in this queue
- `dispatch_date`, `vehicle_no`, `driver_name`
- `transporter_name`, `transporter_gstin`
- `linked_vehicle_entry_id` / `linked_vehicle_entry_no` — EVGI- gate-in reference
- `source_state` — 2-letter state code for source branch
- `bilty_no` — consignment note number (empty string = not yet entered)
- `bilty_date`, `freight`, `total_freight` — null until filled
- `invoice_count` — number of SAP invoices in this dispatch plan

**Live sample (plan 619):**
```json
{
  "dispatch_plan_id": 619,
  "sap_invoice_doc_num": "706260628",
  "booking_status": "BOOKED",
  "dispatch_date": "2026-06-26",
  "vehicle_no": "DL01LAD1397",
  "driver_name": "Arun 9667679734",
  "transporter_name": "PICK & SHIP",
  "transporter_gstin": "09AAQCP4145A1ZF",
  "linked_vehicle_entry_no": "EVGI-20260627-0014",
  "source_state": "KT",
  "bilty_no": "",
  "bilty_date": null,
  "freight": null,
  "total_freight": null,
  "invoice_count": 1
}
```

**Data presence:** 6 live records. All have `bilty_no: ""` — awaiting bilty entry from transporter.

---

### 3.7 `/dispatch/bilty-grpo/preview/:dispatchPlanId` — Bilty-GRPO Preview / Form

**Purpose:** Detailed view for a single dispatch plan in the bilty-GRPO pending queue. Shows invoice lines, item summary, pre-populated defaults for the GRPO form, and the form fields for the operator to fill.

**API:** `GET /api/v1/dispatch/bilty-grpo/preview/{dispatch_plan_id}/`

**Key fields returned (beyond what pending includes):**
- `is_ready_for_grpo` — boolean
- `default_amount`, `default_service_description`, `default_place_of_supply`
- `default_effective_month`, `default_budget_delivery_point`
- `default_product_variety`, `default_product_dimension`
- `default_total_litres`, `default_sub_account`
- `invoice_number`, `eway_bill`, `invoice_weight`, `invoice_amount`
- `source_city`, `item_summary`
- `invoice_lines[]` — one line per invoice, with `customer_name`, `source_state`, `source_city`, `service_description`, `product_variety`, `total_litres`, `invoice_weight`, `invoice_amount`, `freight_amount`
- `grpo_status` — null if not yet posted; SAP doc num once posted
- `bilty_attachment`, `bilty_attachment_name`

**Live sample (plan 619):**
```json
{
  "dispatch_plan_id": 619,
  "sap_invoice_doc_num": "706260628",
  "is_ready_for_grpo": true,
  "default_place_of_supply": "KT",
  "default_effective_month": "2026-06",
  "default_product_variety": "Oil",
  "default_product_dimension": "OLIVE",
  "default_total_litres": "1646.000",
  "invoice_amount": "525540.00",
  "invoice_weight": "1810.990",
  "source_city": "KOLAR TALUK",
  "item_summary": "FG0000227 - RICE BRAN 1L 16 PCS, FG0000151 - SANO POMACE OLIVE 5 LTR TIN 4 PCS, ...",
  "grpo_status": null,
  "invoice_lines": [{
    "customer_name": "R K WORLDINFOCOM PVT LTD",
    "source_state": "KT",
    "source_city": "KOLAR TALUK",
    "service_description": "Oil",
    "product_variety": "Oil",
    "product_dimension": "OLIVE",
    "total_litres": "1646.000",
    "invoice_weight": "1810.990",
    "invoice_amount": "525540.00",
    "freight_amount": "0.00"
  }]
}
```

---

### 3.8 `/dispatch/bilty-grpo/options/` — Bilty-GRPO Reference Data

**Purpose:** Configuration object loaded by the bilty-GRPO form to populate branch dropdowns, tax code selectors, and GL account pickers.

**API:** `GET /api/v1/dispatch/bilty-grpo/options/`
**Response shape:** `{ branches: [...], tax_codes: [...], gl_accounts: [...] }`

**Contents:**
- `branches`: 8 branches (DELHI, HARYANA, PUNJAB, RAJASTHAN, KARNATAKA, UTTAR PRADESH, DELHI ISD, JIVO IT) with `branch_id`, `branch_name`, `state`
- `tax_codes`: 24 tax codes covering CGST+SGST combinations at 0%, 5%, 12%, 18%, 28%, 40%, plus IGST variants and RCM codes
- `gl_accounts`: 992 SAP general ledger accounts with `account_code` (e.g. `1101001`) and `account_name`

---

### 3.9 `/dispatch/bilty-grpo/history/` — Bilty-GRPO History

**Purpose:** Lists all DispatchPlans for which a bilty-GRPO has already been posted to SAP.

**API:** `GET /api/v1/dispatch/bilty-grpo/history/`

**Data presence:** **Empty** (0 records). No bilty-GRPOs have been posted yet for Jivo Mart as of 2026-06-30.

---

### 3.10 `/dispatch/transporter-invoices/pending` and related

**Purpose:** After one or more dispatches are recorded with bilty numbers, the transporter presents a consolidated invoice covering multiple trips. This sub-section lets operators bundle plans, preview the AP invoice, and post it to SAP.

**API endpoints:**
- `GET /api/v1/dispatch/transporter-invoices/pending/` — **404 Not Found** (endpoint does not exist; page may use a different API or is unimplemented)
- `POST /api/v1/dispatch/transporter-invoices/preview/` — POST-only (shows 405 on GET)
- `POST /api/v1/dispatch/transporter-invoices/submit/` — POST-only
- `POST /api/v1/dispatch/transporter-invoices/post-ap-invoice/` — POST-only

**Data presence:** History endpoint returns **empty** (0 records). No transporter invoices have been posted yet for Jivo Mart. The pending endpoint returns 404.

---

## 4. Workflows

### 4.1 Full Dispatch Lifecycle (end-to-end)

```
SAP creates AR invoice
       │
       ▼
[BOOKED] DispatchPlan created — SAP invoice + vehicle/driver/transporter assigned
       │     API: POST to /dispatch-plans/ (from bills list / vehicle-linking page)
       │     plan.booking_status: PENDING → BOOKED
       ▼
[EMPTY_IN] Empty vehicle physically enters factory gate
       │     Gate module: EmptyVehicleGateIn created (EVGI-YYYYMMDD-NNNN)
       │     empty_gate_in_entry_no set on pipeline card
       ▼
[READY_TO_DOCK] Vehicle proceeds to dispatch dock
       │
       ▼
[DOCKED] Docking session created (SalesDispatch, DOCK-YYYYMMDD-NNNN)
       │     via /dispatch/docking/new wizard
       │     VehicleEntry (DOCKV-) created; vehicle_entry_status: IN_PROGRESS
       ▼
[PHOTO_ATTACHED] Photos of loaded vehicle attached
       │     via /dispatch/docking/new/attachments step
       ▼
[READY_FOR_GATEPASS] All barcodes scanned, weighment recorded
       │     /dispatch/docking/new/barcode-scan → verifies all FG boxes
       │     /dispatch/docking/new/weighment → kanta_weight recorded
       ▼
[GATEPASS_PRINTED] Gatepass PDF generated and printed
       │     /dispatch/docking/new/gatepass
       ▼
[PRINT_COMMITTED] Gatepass print confirmed/committed by supervisor
       ▼
[DISPATCHED] Vehicle departs; gate-out committed
       │     arrival_status: LOADING → DEPARTED
       │     vehicle_entry_status: IN_PROGRESS → COMPLETED
       │
       ├──► GRPO Service flow (parallel, handled in GRPO section):
       │     GRPOServiceEntry record appears in /grpo/service/pending/
       │
       ▼
[BILTY-GRPO step] Transporter provides consignment note (bilty)
       │     /dispatch/bilty-grpo/pending/ → preview → post
       │     bilty_no, bilty_date, freight entered; SAP service GRPO posted
       │
       ▼
[TRANSPORTER INVOICE step] Transporter submits consolidated invoice
       │     /dispatch/transporter-invoices/pending → preview → submit
       │     SAP AP Invoice posted to accounts payable
       ▼
COMPLETE
```

### 4.2 Docking New Entry Wizard (5 steps)

| Step | Route | Action | Outcome |
|---|---|---|---|
| 1 | `/dispatch/docking/new` | Select dispatch plan, confirm vehicle/driver | DispatchPlan linked; VehicleEntry (DOCKV-) opened |
| 2 | `/dispatch/docking/new/barcode-scan` | Scan BOX- and PLT- barcodes; partial/skip exceptions need supervisor approval | DispatchSession updated; ScanHistory records created |
| 3 | `/dispatch/docking/new/attachments` | Upload photos of loaded truck | Photo attached; stage advances to PHOTO_ATTACHED |
| 4 | `/dispatch/docking/new/weighment` | Enter gross weight, tare weight from weighbridge | `kanta_weight` recorded on DispatchPlan |
| 5 | `/dispatch/docking/new/gatepass` | Preview gatepass PDF and print | Stage advances GATEPASS_PRINTED → PRINT_COMMITTED |

### 4.3 Scan Exception Sub-workflow (during step 2)

When not all boxes can be scanned (damaged barcodes, legacy unlabelled boxes):
- **Partial scan request**: operator requests approval for partially scanned box count; supervisor (e.g. Bhupinder Singh) approves/rejects with notes. Tracked in `/docking-admin/partial-scan-requests/` (21 records observed; all APPROVED).
- **Scan skip request**: operator requests to skip scanning entirely for a dispatch; supervisor review. Tracked in `/docking-admin/scan-skip-requests/` (12 records observed).

Both request types reference a SalesDispatch FK and show `dispatch_status: DISPATCHED` once the truck has left.

### 4.4 Bilty-GRPO Posting Workflow

```
DISPATCHED plan appears in /dispatch/bilty-grpo/pending/
       │
       ▼
Operator opens preview for plan → /dispatch/bilty-grpo/preview/:planId
       │  (sees: invoice details, item summary, default service description, total litres)
       ▼
Operator fills: bilty_no, bilty_date, freight amount, SAP-side fields
       │  (source_state, effective_month, product_variety, SAP GL account, tax code)
       ▼
POST /dispatch/bilty-grpo/post/ → SAP service GRPO created
       │
       ▼
Plan disappears from pending; appears in /dispatch/bilty-grpo/history/
```

**Statuses observed in pending queue:** `bilty_no: ""` (not yet provided by transporter) — all 6 pending plans are waiting for the transporter to send the bilty.

### 4.5 Pipeline Stage Transitions

The 10 stages map to physical events:

| Stage | Physical event | Key record created |
|---|---|---|
| `BOOKED` | SAP invoice auto-booked; plan created | DispatchPlan |
| `EMPTY_IN` | Empty truck enters factory gate | EmptyVehicleGateIn (EVGI-) |
| `READY_TO_DOCK` | Gate officer clears truck to dock | (status flag on VehicleEntry) |
| `DOCKED` | Truck parked at dispatch bay | SalesDispatch (DOCK-) + VehicleEntry (DOCKV-) |
| `PHOTO_ATTACHED` | Load photos uploaded | (attachment on SalesDispatch) |
| `READY_FOR_GATEPASS` | Scanning + weighment complete | kanta_weight on DispatchPlan |
| `GATEPASS_PRINTED` | Gatepass PDF sent to printer | gatepass_printed_at on Arrival |
| `PRINT_COMMITTED` | Print acknowledged by security | gatepass_committed_at on Arrival |
| `DISPATCHED` | Truck departs; gate-out committed | arrival_status: DEPARTED |
| `REJECTED` | Plan cancelled | cancel_reason on SalesDispatch |

---

## 5. Cross-section connections

| This section | → | Other section | Via |
|---|---|---|---|
| Dispatch Pipeline (DispatchPlan) | ← | Gate (fleet-and-gate) | EmptyVehicleGateIn (EVGI-) creates `empty_gate_in_entry_no` on pipeline card; SalesDispatch (DOCK-) sets `gate_out_id` |
| Docking barcode scan | ← | Barcode (barcode-traceability) | `/dispatch/docking/new/barcode-scan` creates a DispatchSession (`barcode/dispatch/sessions/`) keyed to the SAP invoice `bill_number`; BOX- and PLT- barcodes are resolved from BarcodeBox/Pallet master |
| DispatchPlan (post-dispatch) | → | GRPO (quality-and-grpo) | Each dispatched plan generates a GRPOServiceEntry in `/grpo/service/pending/` (6 live records = 6 bilty-grpo-pending); the GRPO section handles the SAP posting |
| SalesDispatch | → | Gate Arrival | `arrival_status: DEPARTED` is set on the shared Arrival record (ARV-) once all companies on a truck have completed their gate-outs; one Arrival can carry multiple companies' SalesDispatch records (e.g. `arrival_company_count: 3` seen) |
| Bilty-GRPO | → | SAP (external) | POST to `/dispatch/bilty-grpo/post/` triggers SAP service GRPO document creation for freight cost |
| Transporter Invoice | → | SAP (external) | POST to `/dispatch/transporter-invoices/submit/` triggers SAP AP Invoice in accounts payable |
| DispatchPlan | ← | SAP (external) | `sap_invoice_doc_entry` / `sap_invoice_doc_num` are the originating SAP AR invoice numbers; bills list pulls live SAP invoices ready for dispatch |

**Key data bridges:**
- `DispatchPlan.plan_id` = `DispatchPlanPipelineCard.plan_id` = `SalesDispatch.dispatch_plan` = `GRPOServiceEntry.dispatch_plan_id` — the single integer key linking pipeline, docking, and accounting
- `SalesDispatch.entry_no` (DOCK-) bridges to PartialScanRequest and ScanSkipRequest via `sales_dispatch` FK
- `DispatchPlan.linked_vehicle_entry_id` (EVGI-) bridges back to the gate module's EmptyVehicleGateIn

---

## 6. Data presence for Jivo Mart

| Endpoint | Live count | Status |
|---|---|---|
| `/dispatch-plans/pipeline/` | 19 cards (all DISPATCHED) | **LIVE** |
| `/dispatch-plans/bills/?date_from=&date_to=` | 2+ per week | **LIVE** (date params required) |
| `/dispatch/bilty-grpo/pending/` | **6** plans awaiting bilty | **LIVE** |
| `/dispatch/bilty-grpo/preview/:id/` | Per-plan detail | **LIVE** |
| `/dispatch/bilty-grpo/options/` | 8 branches, 24 tax codes, 992 GL accounts | **LIVE** (config) |
| `/dispatch/bilty-grpo/history/` | 0 | **EMPTY** — no bilty-GRPOs posted yet |
| `/dispatch/open-bilties/` | 0 | **EMPTY** — all dispatched plans accounted for |
| `/dispatch/transporter-invoices/history/` | 0 | **EMPTY** — no AP invoices posted yet |
| `/dispatch/transporter-invoices/pending/` | 404 | **NOT FOUND** — endpoint does not exist |
| `/gate-core/sales-dispatch/` (docking data) | **38** total | **LIVE**: 35 DISPATCHED, 3 waiting inside, 2 missing photo, 2 gatepass pending, 1 ready |
| `/gate-core/sales-dispatch/reports/` | 38 summary | **LIVE** |
| `/docking-admin/partial-scan-requests/` | **21** | **LIVE** (all APPROVED) |
| `/docking-admin/scan-skip-requests/` | **12** | **LIVE** |

**Summary:** The upstream stages (vehicle linking, docking wizard, barcode scanning, gatepass) are heavily used — 38 docking entries and 21 partial-scan approvals reflect active daily dispatch operations. The downstream accounting stages (bilty-GRPO, transporter invoices) are not yet posted for Jivo Mart: 6 plans are queued in bilty-grpo/pending and 0 have reached the history stage. This suggests the bilty/freight accounting workflow is either new (not yet operationally active) or handled out-of-band and the history data lives in a separate posting that hasn't yet been completed.

---

## Reference — UI routes (from bundle)
- `/dispatch`
- `/dispatch-plans/bills/`
- `/dispatch-plans/pipeline/`
- `/dispatch/bilty-grpo`
- `/dispatch/bilty-grpo/history`
- `/dispatch/bilty-grpo/history/`
- `/dispatch/bilty-grpo/history/:postingId`
- `/dispatch/bilty-grpo/options/`
- `/dispatch/bilty-grpo/pending`
- `/dispatch/bilty-grpo/pending/`
- `/dispatch/bilty-grpo/post/`
- `/dispatch/bilty-grpo/preview/:dispatchPlanId`
- `/dispatch/docking`
- `/dispatch/docking/:entryId`
- `/dispatch/docking/:entryId/reprint`
- `/dispatch/docking/new`
- `/dispatch/docking/new/attachments`
- `/dispatch/docking/new/barcode-scan`
- `/dispatch/docking/new/gatepass`
- `/dispatch/docking/new/weighment`
- `/dispatch/docking/reports`
- `/dispatch/docking/reprint`
- `/dispatch/open-bilties`
- `/dispatch/open-bilties/`
- `/dispatch/plans`
- `/dispatch/transporter-invoices`
- `/dispatch/transporter-invoices/history`
- `/dispatch/transporter-invoices/history/`
- `/dispatch/transporter-invoices/history/:postingId`
- `/dispatch/transporter-invoices/pending`
- `/dispatch/transporter-invoices/post-ap-invoice/`
- `/dispatch/transporter-invoices/preview/`
- `/dispatch/transporter-invoices/submit/`
- `/dispatch/vehicle-linking`

## Reference — captured API endpoints + record counts (this section)
- `/dispatch-plans/pipeline/` -> 1 object (19 cards, all DISPATCHED stage)
- `/dispatch-plans/bills/?date_from=&date_to=` -> live data (2+ per week; date params required)
- `/dispatch/bilty-grpo/history/` -> 0 (list)
- `/dispatch/bilty-grpo/options/` -> 1 object (8 branches, 24 tax codes, 992 GL accounts)
- `/dispatch/bilty-grpo/pending/` -> 6 (list)
- `/dispatch/bilty-grpo/preview/:id/` -> 1 object (per-plan detail with invoice lines)
- `/dispatch/bilty-grpo/post/` -> POST only (not GET)
- `/dispatch/open-bilties/` -> 0 (list)
- `/dispatch/transporter-invoices/history/` -> 0 (list)
- `/dispatch/transporter-invoices/pending/` -> 404 Not Found
- `/dispatch/transporter-invoices/preview/` -> POST only
- `/dispatch/transporter-invoices/submit/` -> POST only
- `/gate-core/sales-dispatch/` -> 38 (docking/SalesDispatch records, backend for /dispatch/docking/* UI)
- `/gate-core/sales-dispatch/reports/` -> 1 object (counts: total=38, dispatched=35, waiting_inside=3)
- `/docking-admin/partial-scan-requests/` -> 21 (scan exception approvals)
- `/docking-admin/scan-skip-requests/` -> 12 (scan skip approvals)

Linked: [[docs/factory/FACTORY_MAP|FACTORY_MAP]] · [[docs/FACTORY_CLI_PLAN|FACTORY_CLI_PLAN]] · [[docs/READ_ONLY_LAW|READ_ONLY_LAW]]
