---
title: "GRPO — Jivo Mart app-model"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: reference
tags: [jivogpt, factory-cli, grpo]
---

# GRPO — Jivo Mart app-model

> **Provenance — imported 2026-07-19; source snapshot 2026-06-30.** This note came from the JIVO_MART-only `daman8271/jivo-factory-intel` baseline. For the current three-company study and the live-verified 2026-07-19 state, use [[docs/factory/FACTORY_MAP|FACTORY_MAP]] and [[CLI/factory-cli/README|the current CLI guide]].
> STATUS: COMPLETE. Jivo Mart (JIVO_MART) only. Documented 2026-06-30.

## 1. Purpose — what this section is for in the factory

GRPO (Goods Receipt Purchase Order) is the SAP document-posting module for all inbound and service receipts at Jivo Mart's factory. It sits at the end of two distinct pipeline chains and is responsible for officially accepting goods or services into SAP, updating inventory and accounts payable.

**Material GRPO** — the inbound raw material / packaging material chain:  
A vehicle carrying supplier goods arrives at the factory gate, is logged as a gate entry (GE-series), its materials undergo QC inspection, and — once QC approves — the accounts team posts a GRPO to SAP against the original Purchase Order. Only after GRPO posting are the items formally received into SAP inventory (warehouse BH-JM for Jivo Mart). The items involved are packaging materials (PM-prefixed SAP item codes: cartons, poly bags, thermocol sets, etc.).

**Service GRPO** — the outbound freight/transport chain:  
After a customer dispatch is completed and the truck has departed, the logistics team enters the bilty (lorry receipt) details against the dispatch plan. Once the bilty and freight details are captured, the accounts team posts a Service GRPO to SAP against the SAP sales invoice. This records the transport service expense in the books and closes the freight liability against the dispatcher.

Neither flow involves raw oil or finished-goods inventory creation — the material GRPO is exclusively for packaging material receipt, and the service GRPO is for freight service recognition.

---

## 2. Page tree

```
/grpo
├── [Root]  →  redirects to /grpo/all-entries (or summary tab)
│
├── /grpo/summary/                      Dashboard: pending/posted/failed counts
│
├── MATERIAL GRPO SUB-SECTION
│   The UI presents this as a "Material" tab. All backend API calls go to /grpo/* (no
│   /grpo/material/ prefix at the API level — those routes return 404; the "material"
│   is a frontend-only namespace in the route tree).
│
├── /grpo/all-entries  (/grpo/material/all-entries)
│       All gate entries regardless of QC/posting status — full audit view
│
├── /grpo/pending  (/grpo/material/pending)
│       Gate entries where QC has approved all items (is_ready_for_grpo = true);
│       ready to post to SAP as a GRPO — the actionable queue for accounts team
│
├── /grpo/preview/:vehicleEntryId  (/grpo/material/preview/:vehicleEntryId)
│       Pre-posting review form for a specific gate entry: shows PO details,
│       item lines, unit prices, tax codes, warehouse, GL accounts, and
│       QC-accepted quantities before the user submits to SAP
│
├── /grpo/post/
│       POST action endpoint — submits the GRPO to SAP (no GET; write-only action)
│
├── /grpo/history  (/grpo/material/history)
│       All successfully posted material GRPOs (completed receipts); SAP doc numbers visible
│
├── /grpo/history/:postingId  (/grpo/material/history/:postingId)
│       Detail view of a single posted GRPO — shows SAP GRPO doc number, total amount,
│       item-level receipt confirmation, and posting timestamps
│
└── SERVICE GRPO SUB-SECTION
    │
    ├── /grpo/service
    │       Root of service GRPO — redirects to /grpo/service/pending
    │
    ├── /grpo/service/options/
    │       Reference/config data for the service GRPO form: SAP branches list,
    │       GST tax codes, and GL accounts (not a list of records; a config object)
    │
    ├── /grpo/service/pending  (/grpo/service/pending/)
    │       Dispatch plans that have completed outbound dispatch and have bilty details
    │       entered; awaiting service GRPO posting to SAP
    │
    ├── /grpo/service/preview/:dispatchPlanId
    │       Full detail review form for a service GRPO: shows invoice details, item
    │       summary, freight amount, tax code defaults, source state, effective month,
    │       product variety/dimension, total litres, and per-invoice breakdown lines;
    │       user completes form fields before posting
    │
    ├── /grpo/service/post/
    │       POST action endpoint for service GRPO submission (no GET; write-only)
    │
    ├── /grpo/service/history  (/grpo/service/history/)
    │       All posted service GRPOs (completed freight receipts)
    │
    └── /grpo/service/history/:postingId
            Detail view of a posted service GRPO — shows SAP doc number, amount,
            transporter, bilty, and item lines
```

---

## 3. Per-page detail

### 3.1 `/grpo/summary/` — Dashboard summary tile

**Purpose:** Single aggregate object showing the current GRPO pipeline health across both material and service flows.

**API endpoint:** `GET /grpo/summary/` → returns a single object (not a list).

**Key fields:**

| Field | Meaning |
|---|---|
| `pending_entry_count` | Gate entries where QC has approved but GRPO not yet posted |
| `pending_po_count` | Number of PO receipts pending posting |
| `qc_accepted_qty` | Total quantity accepted by QC across all pending entries |
| `qc_rejected_qty` | Total quantity rejected by QC |
| `posting_pending_count` | Entries queued for posting (ready but not submitted) |
| `posted_count` | Successfully posted GRPOs |
| `failed_count` | GRPO posting attempts that failed at SAP |
| `partially_posted_count` | Entries with some PO receipts posted and some pending |

**Live Jivo Mart sample (as of 2026-06-30):**
```json
{
  "pending_entry_count": 0,
  "pending_po_count": 0,
  "qc_accepted_qty": "0.000",
  "qc_rejected_qty": "0.000",
  "posting_pending_count": 0,
  "posted_count": 0,
  "failed_count": 0,
  "partially_posted_count": 0
}
```
All counts are zero — confirming no material GRPOs have been posted in Jivo Mart yet. All visible entries are stuck in QC_PENDING (QC inspections not completed).

---

### 3.2 `/grpo/all-entries/` — All material entries

**Purpose:** Complete list of gate entries that are in the GRPO pipeline, regardless of QC status or posting status. This is the full audit trail view.

**API endpoint:** `GET /grpo/all-entries/` → returns a flat list of GRPOEntry objects.

**Key fields per entry:**

| Field | Meaning |
|---|---|
| `vehicle_entry_id` | FK to VehicleEntry (the gate session ID) |
| `entry_no` | Gate entry number (GE-YYYY-NNNN format) |
| `status` | Pipeline status: `QC_PENDING`, `QC_APPROVED`, `POSTING_PENDING`, `POSTED`, `PARTIALLY_POSTED`, `FAILED` |
| `status_label` | Human-readable status |
| `phase` | Current pipeline phase: `QC` (QC not done), `GRPO` (QC done, ready to post) |
| `is_ready_for_grpo` | Boolean — true when all items have QC decisions |
| `is_fully_posted` | Boolean — true when all PO receipts have been posted to SAP |
| `entry_time` | Timestamp when the gate entry was created |
| `total_po_count` / `posted_po_count` / `pending_po_count` | PO receipt breakdown counts |
| `suppliers[]` | List of suppliers with `supplier_code`, `supplier_name`, `po_count` |
| `po_numbers[]` | SAP PO numbers being received |
| `po_receipts[]` | Nested per-PO breakdown with item lines |

**Per-PO-receipt item fields:**

| Field | Meaning |
|---|---|
| `po_item_receipt_id` | FK to POItemReceipt |
| `item_code` | SAP item code (PM-prefix = packaging material) |
| `item_name` | Item description |
| `received_qty` | Quantity brought by the truck |
| `accepted_qty` | Quantity passed by QC (0.000 if QC not done) |
| `rejected_qty` | Quantity rejected by QC |
| `uom` | Unit of measure (PCS, KGS) |
| `qc_status` | `INSPECTION_PENDING`, `APPROVED`, `REJECTED` |

**Live Jivo Mart sample — 2 of 5 entries:**

Entry 1: Gate entry GE-2026-8750 (vehicle_entry_id: 466, entered 2026-05-19)
- Supplier: CVS PACKAGING PRIVATE LIMITED (VENDA000277)
- PO: 426224589
- Items: PM0000497 "CARTON 5 LTR HDPE 1 PCS THERMO" (637 PCS received), PM0000087 "CARTON 5 LTR + 1 LTR 1 PCS" (195 PCS received)
- Status: QC_PENDING; accepted_qty = 0 on all items

Entry 2: Gate entry GE-2026-0118 (vehicle_entry_id: 442, entered 2026-05-05)
- Supplier: CVS PACKAGING PRIVATE LIMITED (VENDA000277)
- PO: 426224589
- Items: PM0000087 "CARTON 5 LTR + 1 LTR 1 PCS" (1,425 PCS received)
- Status: QC_PENDING; accepted_qty = 0

All 5 entries are the same supplier group CVS PACKAGING or S.N. INDUSTRIES / RS ENTERPRISES; items are cartons, poly bags, and thermocol packaging. No entry has progressed past QC_PENDING.

---

### 3.3 `/grpo/pending/` — Material GRPO posting queue

**Purpose:** Filtered view of gate entries where QC is fully completed and the entry is ready for SAP GRPO posting. This is the accounts-team work queue.

**API endpoint:** `GET /grpo/pending/` → list. Filters all-entries to `is_ready_for_grpo = true`.

**Live Jivo Mart:** Returns `[]` (empty list). No entry has completed QC yet, so there is nothing in the posting queue. This matches the summary showing 0 for `pending_entry_count`.

---

### 3.4 `/grpo/preview/:vehicleEntryId` — Pre-posting GRPO review form

**Purpose:** Expanded detail view of a gate entry for the accounts team to review before posting to SAP. Shows SAP PO details (sap_doc_entry, branch_id), per-item unit prices, tax codes, warehouse codes, and GL account codes. Also shows whether the current QC state makes the entry ready for posting (`is_ready_for_grpo`).

**API endpoint:** `GET /grpo/preview/{vehicle_entry_id}/` → list of per-PO-receipt preview objects for that gate entry.

**Additional fields vs all-entries:**

| Field | Meaning |
|---|---|
| `po_date` | Date the PO was raised |
| `sap_doc_entry` | SAP internal PO document entry ID |
| `branch_id` | SAP branch for posting |
| `vendor_ref` / `invoice_no` / `invoice_date` / `challan_no` | Supplier invoice details |
| `items[].ordered_qty` | Original PO quantity (vs received_qty) |
| `items[].unit_price` | SAP unit price for the item |
| `items[].tax_code` | GST tax code (e.g., `CG+SG@5` = CGST+SGST at 5%) |
| `items[].warehouse_code` | SAP destination warehouse (e.g., `BH-JM` = Bhakharpur Jivo Mart) |
| `items[].gl_account` | SAP GL account code (e.g., `1103005` = PACKAGING MATERIALS OIL) |
| `items[].arrival_slip_id` | FK to ArrivalSlip that triggered QC |
| `items[].inspection_id` | FK to Inspection record (null if QC not started) |
| `items[].inspection_report_no` | QC report number (empty if QC pending) |
| `grpo_status` / `sap_doc_num` / `total_amount` | Populated after posting; null before |

**Live Jivo Mart sample — vehicle_entry_id 466:**
```json
{
  "vehicle_entry_id": 466,
  "entry_no": "GE-2026-8750",
  "entry_status": "QC_PENDING",
  "is_ready_for_grpo": false,
  "po_receipt_id": 425,
  "po_number": "426224589",
  "supplier_code": "VENDA000277",
  "supplier_name": "CVS PACKAGING PRIVATE LIMITED",
  "po_date": "2026-04-29",
  "sap_doc_entry": 5041,
  "branch_id": 2,
  "items": [
    {
      "po_item_receipt_id": 614,
      "item_code": "PM0000497",
      "item_name": "CARTON 5 LTR HDPE 1 PCS THERMO",
      "ordered_qty": "1200.000",
      "received_qty": "637.000",
      "accepted_qty": "0.000",
      "unit_price": "27.000000",
      "tax_code": "CG+SG@5",
      "warehouse_code": "BH-JM",
      "gl_account": "1103005",
      "qc_status": "INSPECTION_PENDING",
      "inspection_id": null
    }
  ],
  "grpo_status": null,
  "sap_doc_num": null,
  "total_amount": null
}
```
Confirms: warehouse BH-JM (Bhakharpur – Jivo Mart), GL account 1103005 (PACKAGING MATERIALS OIL), tax code CG+SG@5, SAP PO doc_entry 5041, branch 2 (HARYANA). The `is_ready_for_grpo: false` and null SAP doc fields confirm no posting has occurred.

---

### 3.5 `/grpo/post/` — Material GRPO post action

**Purpose:** Write endpoint that submits a GRPO document to SAP. Sends the accepted quantities from the QC-approved gate entry as an official goods receipt in SAP, updating inventory and creating an accounts-payable entry for the supplier.

**API endpoint:** `POST /grpo/post/` — not GETable (returns "Method GET not allowed"). Accepts the `vehicle_entry_id` and optionally per-item overrides.

**Data requirements:** The form from the preview page is submitted with supplier invoice details, final accepted quantities, and the unit prices / tax codes / warehouse / GL account already pre-filled from the PO (user can override).

---

### 3.6 `/grpo/history/` and `/grpo/history/:postingId` — Posted material GRPOs

**Purpose:** Record of all successfully posted material GRPOs. The list view shows posting status and SAP doc numbers; the detail view shows item-level receipt confirmation.

**API endpoint:** `GET /grpo/history/` → list; `GET /grpo/history/{postingId}/` → single record.

**Expected key fields (inferred from preview schema and SAP posting patterns):**

| Field | Meaning |
|---|---|
| `sap_doc_num` | SAP GRPO document number (assigned at posting time) |
| `sap_doc_entry` | SAP internal doc entry ID |
| `total_amount` | Total posted amount in INR |
| `grpo_status` | `POSTED`, `FAILED`, `PARTIALLY_POSTED` |
| `posted_at` | Timestamp of posting |
| `items[].accepted_qty` | Final quantity received per item |
| `items[].unit_price` | Price at which goods were received |

**Live Jivo Mart:** Both `GET /grpo/history/` and `GET /grpo/history/{id}/` return `[]` / empty. No material GRPO has ever been posted in Jivo Mart. This is consistent with all entries being in QC_PENDING (QC must complete before posting can occur).

---

### 3.7 `/grpo/service/pending/` — Service GRPO posting queue

**Purpose:** List of outbound dispatch plans that have been dispatched and linked to a bilty (or have had bilty-ready status set), awaiting the accounts team to post a service GRPO (freight receipt) to SAP.

**API endpoint:** `GET /grpo/service/pending/` → list of GRPOServiceEntry objects.

**Key fields:**

| Field | Meaning |
|---|---|
| `dispatch_plan_id` | FK to DispatchPlan |
| `sap_invoice_doc_entry` / `sap_invoice_doc_num` | The originating SAP sales invoice (e.g., `706260628`) |
| `booking_status` | Dispatch booking status (all are `BOOKED` in current data) |
| `dispatch_date` | Date goods were dispatched |
| `vehicle_no` | Truck registration number |
| `driver_name` | Driver name and mobile |
| `transporter_name` / `transporter_gstin` | Transport company details |
| `linked_vehicle_entry_id` / `linked_vehicle_entry_no` | Gate entry for this dispatch (EVGI-series) |
| `source_state` | State code of dispatch origin (for GST determination: `KT`, `WB`, `HR`, `HP`) |
| `bilty_no` / `bilty_date` | Lorry receipt number and date (empty = not yet filled) |
| `freight` / `total_freight` | Per-invoice and total freight amount |
| `invoice_count` | Number of SAP invoices grouped in this dispatch plan |
| `created_at` / `updated_at` | Creation and last-update timestamps |

**Live Jivo Mart sample — 2 of 6 entries:**

Entry 1 (dispatch_plan_id 619):
- SAP invoice: 706260628 (sap_invoice_doc_entry: 35198)
- Dispatch date: 2026-06-26 · Transporter: PICK & SHIP (GSTIN: 09AAQCP4145A1ZF)
- Vehicle: DL01LAD1397 · Driver: Arun 9667679734
- Linked gate entry: EVGI-20260627-0014 · Source state: KT (Karnataka)
- Bilty: not filled (empty string); freight: null

Entry 2 (dispatch_plan_id 452):
- SAP invoice: 706260501 (sap_invoice_doc_entry: 34988)
- Dispatch date: 2026-06-20 · Transporter: JIVO WELLNESS PVT LTD (intercompany)
- Vehicle: HR69F9627 · Driver: Milkha singh
- Linked gate entry: EVGI-20260624-0025 · Source state: HR (Haryana)
- Bilty: "NA" · Bilty date: 2026-06-24 · Freight: ₹0.25 (intercompany token amount)
- invoice_count: 3 (three invoices bundled in one dispatch plan)

All 6 entries have `booking_status: BOOKED` — dispatched but service GRPO not yet posted.

---

### 3.8 `/grpo/service/preview/:dispatchPlanId` — Service GRPO pre-posting form

**Purpose:** Expanded detail for a service GRPO before posting. Adds the full invoice item summary, source city, customer details, product variety/dimension (for SAP categorization), total litres, invoice weight, invoice amount, and per-invoice breakdown lines. The user fills in the freight amount, bilty details, tax code, GL account, and SAC (Service Accounting Code) before submitting.

**API endpoint:** `GET /grpo/service/preview/{dispatchPlanId}/` → single object.

**Additional fields vs service-pending:**

| Field | Meaning |
|---|---|
| `is_ready_for_grpo` | Boolean (true in preview = vehicle gate-out confirmed, ready to post) |
| `default_amount` | Pre-filled freight amount (can be overridden) |
| `default_service_description` | Default service description for SAP (e.g., `"Oil"`) |
| `default_place_of_supply` | GST place of supply (state code) |
| `default_effective_month` | Month for which the service is being receipted (e.g., `"2026-06"`) |
| `default_budget_delivery_point` | SAP delivery point label (e.g., `"Del Bkhp"`) |
| `default_sac_entry` / `default_sac_code` | SAP Service Accounting Code for freight |
| `default_product_variety` / `default_product_dimension` | Product classification (e.g., Oil / OLIVE) |
| `default_total_litres` | Total litres dispatched (for freight rate calculation) |
| `default_sub_account` | SAP sub-account type (e.g., `"SALES"`) |
| `invoice_number` | Primary SAP invoice number |
| `eway_bill` | E-way bill number for the shipment |
| `invoice_weight` | Total shipment weight (kg) |
| `invoice_amount` | Total SAP invoice value (INR) |
| `source_city` | Origin city (e.g., `"KOLAR TALUK"`) |
| `item_summary` | Pipe-separated list of FG item codes + descriptions |
| `bilty_attachment` / `bilty_attachment_name` | Bilty document upload |
| `grpo_status` / `sap_doc_num` / `total_amount` | Null before posting |
| `invoice_lines[]` | Per-invoice breakdown (customer, total litres, freight, invoice amount) |

**Live Jivo Mart sample — dispatch_plan_id 619:**
```json
{
  "dispatch_plan_id": 619,
  "sap_invoice_doc_num": "706260628",
  "is_ready_for_grpo": true,
  "default_amount": "0.00",
  "default_service_description": "Oil",
  "default_place_of_supply": "KT",
  "default_effective_month": "2026-06",
  "default_total_litres": "1646.000",
  "default_product_variety": "Oil",
  "default_product_dimension": "OLIVE",
  "invoice_amount": "525540.00",
  "invoice_weight": "1810.990",
  "source_city": "KOLAR TALUK",
  "item_summary": "FG0000227 - RICE BRAN 1L 16 PCS, FG0000151 - SANO POMACE OLIVE 5 LTR TIN 4 PCS, ...",
  "grpo_status": null,
  "sap_doc_num": null,
  "invoice_lines": [
    {
      "customer_code": "CUSTA000048",
      "customer_name": "R K WORLDINFOCOM PVT LTD",
      "source_state": "KT",
      "source_city": "KOLAR TALUK",
      "total_litres": "1646.000",
      "invoice_amount": "525540.00",
      "freight_amount": "0.00"
    }
  ]
}
```

This dispatch to Karnataka (R K WORLDINFOCOM PVT LTD) contains 1,646 litres of oil products (Olive oils, Mustard, Soyabean, etc.) worth ₹5,25,540 — the freight service GRPO will record the transport cost against this invoice.

---

### 3.9 `/grpo/service/post/` — Service GRPO post action

**Purpose:** Write endpoint that submits the service GRPO to SAP. Accepts the `dispatch_plan_id`, freight amount, bilty details, tax code, SAC code, GL account, and product details.

**API endpoint:** `POST /grpo/service/post/` — not GETable (returns "Method GET not allowed").

---

### 3.10 `/grpo/service/history/` and `/grpo/service/history/:postingId` — Posted service GRPOs

**Purpose:** Record of all posted service GRPOs (completed freight receipts).

**API endpoint:** `GET /grpo/service/history/` → list; `GET /grpo/service/history/{postingId}/` → detail.

**Live Jivo Mart:** Returns `[]`. No service GRPO has been posted yet.

---

### 3.11 `/grpo/service/options/` — Reference data for service GRPO form

**Purpose:** Config/reference object providing lookup lists needed to fill the service GRPO form. Not a paginated entity list — returns a single composite object with three collections.

**API endpoint:** `GET /grpo/service/options/` → single object.

**Collections:**

**branches** (8 records) — SAP branches for Jivo Mart:

| branch_id | branch_name | state |
|---|---|---|
| 1 | DELHI | DL |
| 2 | HARYANA | HR |
| 3 | PUNJAB | PB |
| 4 | RAJASTHAN | RJ |
| 5 | KARNATAKA | KT |
| 6 | UTTAR PRADESH | UP |
| 7 | DELHI ISD | DL |
| 8 | JIVO IT | DL |

**tax_codes** (24 records) — GST tax codes for service GRPO:
Covers CGST+SGST (intra-state) and IGST (inter-state) at 0%, 5%, 12%, 18%, 28%, 40%, plus RCM variants (Reverse Charge Mechanism) and exempt. Examples: `CG+SG@18` = CGST+SGST@18%, `IGST@5` = IGST@5%, `RCGSG@18` = RCM CGST+SGST@18%.

**gl_accounts** (400+ records) — Full SAP chart of accounts. Includes:
- Sundry Debtors by channel (GT, E-COM, MT, HORECA, etc.)
- Intercompany accounts: JIVO MART PVT. LTD. by state (Delhi 1102008, Haryana 1102009, Punjab 1102010, Karnataka 1102011, Rajasthan 1102012, UP 1102013)
- Stock accounts: Packaging Materials Oil (1103005), Finished Goods Oil (1103001), etc.
- Bank accounts (HDFC, ICICI, Indian Bank)
- GST ledgers (Input/Output IGST/CGST/SGST at each rate)
- Creditor accounts, employee salary payable, provisions
- Asset accounts (P&M, furniture, vehicles, buildings)

---

## 4. Workflows

### 4.1 Material GRPO workflow (inbound packaging materials)

```
[Gate Section]
Supplier truck arrives at factory
↓
Gate entry created (GE-YYYY-NNNN, VehicleEntry record)
Gate staff create ArrivalSlip per PO line item
↓
[QC Section]
QC inspection triggered for each ArrivalSlip
  → Chemist samples and tests material
  → Chemist enters lab results and makes decision
  → QAM (Quality Assurance Manager) reviews and approves/rejects
  → factory_head_decision (if required)
  Inspection workflow_status: NOT_STARTED → DRAFT → AWAITING_CHEMIST
                               → AWAITING_QAM → COMPLETED / REJECTED
↓
QC decision on each item:
  - APPROVED: accepted_qty updated, qc_status = APPROVED
  - REJECTED: rejected_qty updated, material returned to vendor
↓
When ALL items in the gate entry are decided:
  → is_ready_for_grpo = true, phase shifts from QC to GRPO
  → Entry appears in /grpo/pending/
↓
[GRPO Section — Accounts Team]
Accounts team opens /grpo/pending/ queue
  → Selects gate entry → /grpo/preview/:vehicleEntryId
  → Reviews PO details, QC quantities, unit prices, tax codes, GL accounts
  → Enters supplier invoice no, invoice date, challan no (if any)
  → Submits via /grpo/post/ (POST action)
↓
SAP GRPO posted:
  → SAP assigns grpo_status = POSTED, sap_doc_num (GRPO doc number), total_amount
  → Inventory in warehouse BH-JM updated (packaging materials received)
  → Accounts payable created for supplier
  → Entry moves from /grpo/pending/ to /grpo/history/
  → Summary counters: posted_count++
↓
(If posting fails): grpo_status = FAILED → failed_count++; stays in queue for retry
(If partial): grpo_status = PARTIALLY_POSTED → partially_posted_count++; pending PO receipts remain
```

**Status sequence:** `QC_PENDING` → `QC_APPROVED` (is_ready_for_grpo=true) → `POSTING_PENDING` → `POSTED` / `PARTIALLY_POSTED` / `FAILED`

**Phase sequence:** `QC` → `GRPO`

---

### 4.2 Service GRPO workflow (outbound freight)

```
[Dispatch Section]
Dispatch plan created (sap_invoice_doc_num, vehicle, driver, transporter)
↓
[Gate Section]
Empty vehicle gate-in (EVGI-series entry)
Vehicle loaded and dispatched (gate out, DOCK-series)
↓
[Dispatch / Bilty]
Bilty (lorry receipt) received from transporter
Dispatch team enters bilty_no, bilty_date, freight amount
  → Dispatch plan booking_status stays BOOKED
  → linked_vehicle_entry confirmed
↓
[Service GRPO Section — Accounts Team]
Accounts team opens /grpo/service/pending/ queue
  → All dispatch plans with bilty captured appear here
  → Selects a plan → /grpo/service/preview/:dispatchPlanId
  → Reviews: invoice details, product variety/dimension, total litres,
    source state, effective month, freight amount, SAC code, tax code
  → Confirms or overrides default values
  → Uploads bilty attachment (optional)
  → Submits via /grpo/service/post/ (POST action)
↓
SAP Service GRPO posted:
  → SAP assigns sap_doc_num, grpo_status = POSTED, total_amount
  → Freight expense recognized in books
  → Entry moves to /grpo/service/history/
```

---

## 5. Cross-section connections

| This section | Links to | Via |
|---|---|---|
| GRPO Material | Gate Core / QC | `vehicle_entry_id` (GE-series gate entry) → VehicleEntry |
| GRPO Material | Quality Control | `arrival_slip_id` (per PO line) → ArrivalSlip; `inspection_id` → Inspection |
| GRPO Material | Procurement / PO | `po_receipt_id` → POReceipt; `po_number` → Purchase Order in SAP; `sap_doc_entry` = SAP PO doc |
| GRPO Material | Vendor master | `supplier_code` (VENDA-prefixed) → Vendor |
| GRPO Material | Warehouse (WMS) | `warehouse_code` = `BH-JM` → SAP warehouse; inventory is booked here on GRPO posting |
| GRPO Material | SAP (accounting) | `gl_account` (1103005 etc.) → GL account; posting creates SAP GRPO document (`sap_doc_num`) |
| GRPO Service | Dispatch | `dispatch_plan_id` → DispatchPlan; `sap_invoice_doc_entry` → SAP sales invoice |
| GRPO Service | Gate Core | `linked_vehicle_entry_id` (EVGI-series) → VehicleEntry (the outbound gate exit) |
| GRPO Service | Dispatch (Bilty GRPO) | The `/dispatch/bilty-grpo/pending/` queue is essentially the same DispatchPlan set visible in `/grpo/service/pending/` — both show dispatch plans awaiting bilty/service GRPO posting. The Dispatch section (`/dispatch/bilty-grpo/*`) provides this same functionality from the dispatcher's perspective, while the GRPO section provides it from the accounts team's perspective. Same 6 records observed in both. |
| GRPO Service | SAP (accounting) | GL accounts and tax codes from `/grpo/service/options/`; posting creates SAP service GRPO doc |
| GRPO Service | Vendor / Transporter | `transporter_name` + `transporter_gstin` identify the transport vendor |
| GRPO (both) | SAP plan dashboard | The SAP plan dashboard (`/sap/plan-dashboard/`) shows procurement and posting status; GRPO completions feed this dashboard |

**Pipeline position:**
```
Gate (arrival) → QC (inspection) → GRPO (material receipt into SAP) → Warehouse (inventory)
                                                                              ↕
Dispatch (bilty) → GRPO Service (freight recognition in SAP) → Accounts (AP)
```

---

## 6. Data presence for Jivo Mart

### 6.1 Material GRPO

| Endpoint | Count | Status |
|---|---|---|
| `/grpo/all-entries/` | **5 records** | LIVE — all 5 in QC_PENDING phase |
| `/grpo/pending/` | **0 records** | EMPTY — no entries have passed QC yet |
| `/grpo/preview/:vehicleEntryId` | **Data present** | LIVE — preview works for any of the 5 entries (verified: VE 466) |
| `/grpo/history/` | **0 records** | EMPTY — no material GRPO has ever been posted |
| `/grpo/summary/` | **0 across all counters** | LIVE but all zeroes |

**Material GRPO bottleneck:** All 5 gate entries (vehicle_entry_ids 424, 429, 434, 442, 466) are blocked at QC_PENDING. QC inspections for these entries have never been started (inspection_id = null on all items). The oldest entry dates from 2026-05-02 — over 7 weeks stuck in QC. The items are exclusively packaging materials (cartons, poly bags, thermocol) from 3 suppliers.

**Suppliers in pipeline:**
- CVS PACKAGING PRIVATE LIMITED (VENDA000277) — 3 gate entries, PO 426224589, items PM0000087 / PM0000234 / PM0000497
- S.N. INDUSTRIES (VENDA000996) — 1 gate entry, PO 526224503, item PM0000535 (poly bags)
- RS ENTERPRISES (VENDA000937) — 1 gate entry, PO 426224599, item PM0000404 (thermocol sets)

**Warehouse target:** BH-JM (Bhakharpur – Jivo Mart) for all entries. Branch 2 (Haryana). GL account 1103005 (PACKAGING MATERIALS OIL).

### 6.2 Service GRPO

| Endpoint | Count | Status |
|---|---|---|
| `/grpo/service/pending/` | **6 records** | LIVE — 6 dispatch plans awaiting service GRPO |
| `/grpo/service/preview/:dispatchPlanId` | **Data present** | LIVE — verified for dispatch plan 619 |
| `/grpo/service/history/` | **0 records** | EMPTY — no service GRPO has been posted |
| `/grpo/service/options/` | **8 branches, 24 tax codes, 400+ GL accounts** | LIVE config data |

**Service GRPO pending breakdown (6 dispatch plans):**

| dispatch_plan_id | SAP Invoice | Dispatch Date | Transporter | Source State | Bilty Status |
|---|---|---|---|---|---|
| 619 | 706260628 | 2026-06-26 | PICK & SHIP | KT (Karnataka) | Not filled |
| 620 | 706260627 | 2026-06-26 | PICK & SHIP | WB (West Bengal) | Not filled |
| 623 | 706260625 | 2026-06-26 | PICK & SHIP | KT (Karnataka) | Not filled |
| 622 | 706260620 | 2026-06-26 | PICK & SHIP | KT (Karnataka) | Not filled |
| 452 | 706260501 | 2026-06-20 | JIVO WELLNESS PVT LTD | HR (Haryana) | bilty_no="NA", freight=₹0.25 |
| 431 | 606260149 | 2026-06-19 | PICK & SHIP | HP (Himachal Pradesh) | Not filled |

The 4 Karnataka dispatches (619, 622, 623 on 2026-06-26) share the same vehicle DL01LAD1397 / driver Arun / gate entry EVGI-20260627-0014 (one vehicle, multiple invoices). Dispatch plan 452 is an intercompany transfer (transporter = JIVO WELLNESS PVT LTD, freight = ₹0.25 token).

**Observation:** 4 of 6 service GRPO entries have no bilty filled at all (bilty_no = ""). The is_ready_for_grpo flag is true for at least entry 619 (confirmed from preview), suggesting the flag is set based on gate exit rather than bilty entry. The accounts team needs to fill in bilty and freight details before posting to SAP.

---

## Reference — UI routes (from bundle)
- `/grpo`
- `/grpo/all-entries`
- `/grpo/all-entries/`
- `/grpo/history`
- `/grpo/history/`
- `/grpo/history/:postingId`
- `/grpo/material`
- `/grpo/material/all-entries`
- `/grpo/material/history`
- `/grpo/material/history/:postingId`
- `/grpo/material/pending`
- `/grpo/material/preview/:vehicleEntryId`
- `/grpo/pending`
- `/grpo/pending/`
- `/grpo/post/`
- `/grpo/preview`
- `/grpo/preview/:vehicleEntryId`
- `/grpo/service`
- `/grpo/service/history`
- `/grpo/service/history/`
- `/grpo/service/history/:postingId`
- `/grpo/service/options/`
- `/grpo/service/pending`
- `/grpo/service/pending/`
- `/grpo/service/post/`
- `/grpo/service/preview/:dispatchPlanId`
- `/grpo/summary/`

**Note on `/grpo/material/*` routes:** These are frontend-only UI routes. The `/grpo/material/` prefix does not exist at the API level — `GET /grpo/material/all-entries/` returns HTTP 404. The frontend uses these paths to namespace the Material GRPO sub-section within the router, but all API calls go to the corresponding `/grpo/` base paths.

## Reference — captured API endpoints + record counts (this section)
- `/grpo/all-entries/` → 5 (list) — all in QC_PENDING
- `/grpo/history/` → 0 (list) — no posted material GRPOs
- `/grpo/pending/` → 0 (list) — no entries passed QC
- `/grpo/service/history/` → 0 (list) — no posted service GRPOs
- `/grpo/service/options/` → 1 (object) — 8 branches, 24 tax codes, 400+ GL accounts
- `/grpo/service/pending/` → 6 (list) — all BOOKED, bilty pending on 4 of 6
- `/grpo/summary/` → 1 (object) — all counters zero

Linked: [[docs/factory/FACTORY_MAP|FACTORY_MAP]] · [[docs/FACTORY_CLI_PLAN|FACTORY_CLI_PLAN]] · [[docs/READ_ONLY_LAW|READ_ONLY_LAW]]
