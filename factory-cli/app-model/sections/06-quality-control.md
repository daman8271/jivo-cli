---
title: "Quality Control — Jivo Mart app-model"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: reference
tags: [jivogpt, factory-cli, quality-control]
---

# Quality Control — Jivo Mart app-model

> **Provenance — imported 2026-07-19; source snapshot 2026-06-30.** This note came from the JIVO_MART-only `daman8271/jivo-factory-intel` baseline. For the current three-company study and the live-verified 2026-07-19 state, use [[docs/factory/FACTORY_MAP|FACTORY_MAP]] and [[CLI/factory-cli/README|the current CLI guide]].
> Last updated: 2026-06-30. Data verified against live factory.jivo.in/api/v1 (Company-Code: JIVO_MART).

---

## 1. Purpose — what this section is for in the factory

The Quality Control (QC) section is the gating layer between inbound material receipt and warehouse acceptance/GRPO posting. Its two primary jobs are:

1. **Inbound material inspection** — every item delivered by a vendor at the gate generates an *arrival slip* in QC. A chemist physically inspects the material against defined parameters and records a pass/fail decision; a QA Manager then reviews and ratifies or overrides. Only after a QC-accepted decision does the gate entry become eligible for GRPO posting in SAP.

2. **Production QC** — inspection of finished or in-process goods against production runs and sessions. This path links to the Production Execution module's lines/runs/sessions and includes a line-clearance step before production starts.

QC is therefore a mandatory checkpoint in two flows:
- Gate-in → **QC (Arrival Slips)** → GRPO → Warehouse
- Production planning → **QC (Line Clearance + Production QC)** → Production Execution

For Jivo Mart currently, only the inbound material (arrival slips) path has live data. Production QC, line clearance, and the master configuration tables are enabled in the app but not yet used.

---

## 2. Page tree

```
/qc                                           QC home dashboard (inspection counts summary)
├── /qc/pending                               Pending inspection list (all items needing action)
├── /qc/approvals                             QAM approval queue (awaiting-qam decision)
│
├── /qc/arrival-slips                         Inbound material arrival slips list
│   ├── /qc/arrival-slips/approvals           Arrival-slip inspection approvals queue
│   ├── /qc/arrival-slips/inspections/:inspectionId
│   │                                         Inspection detail for a specific arrival slip
│   └── /qc/arrival-slips/inspections/:slipId/new
│                                             Create a new inspection against an arrival slip
│
├── /qc/inspections/:inspectionId             Inspection detail (general, by inspection ID)
└── /qc/inspections/:slipId/new              New inspection (general entry point)
│
├── /qc/customer-returns                      Customer return QC list
│   └── /qc/customer-returns/:returnId        Individual customer return QC detail
│
├── /qc/line-clearance                        Production line clearance checks
│
├── /qc/production                            Production QC list (all runs/sessions)
│   ├── /qc/production/approvals              Production QC approval queue
│   ├── /qc/production/runs/:runId            QC detail for a production run
│   └── /qc/production/sessions/:sessionId   QC detail for a production session
│
└── /qc/master                               Master configuration
    ├── /qc/master/material-types            Material type definitions
    ├── /qc/master/parameters                QC parameter library
    └── /qc/master/print-documents           Print document templates (COA, QC reports)
```

---

## 3. Per-page detail

### 3.1 `/qc` — QC Home / Dashboard

**Purpose:** Landing page showing a summary count of all inspections by status so QC staff can see their workload at a glance.

**API endpoint:** `GET /quality-control/inspections/counts/`

**Key fields returned:**
| Field | Value (live Jivo Mart) |
|---|---|
| `not_started` | 8 |
| `draft` | 0 |
| `awaiting_chemist` | 0 |
| `awaiting_qam` | 0 |
| `completed` | 0 |
| `rejected` | 0 |
| `hold` | 0 |
| `actionable` | 8 |

Also likely calls `GET /quality-control/production-qc/counts/` for the production QC summary:
| Field | Value (live Jivo Mart) |
|---|---|
| `draft` | 0 |
| `submitted` | 0 |
| `approved` | 0 |
| `rejected` | 0 |

**Sample (live, verified 2026-06-30):**
```json
{
  "not_started": 8,
  "draft": 0,
  "awaiting_chemist": 0,
  "awaiting_qam": 0,
  "completed": 0,
  "rejected": 0,
  "hold": 0,
  "actionable": 8
}
```
All 8 actionable inspection items are in NOT_STARTED state — material has arrived and been submitted to QC, but no inspection has been initiated yet.

---

### 3.2 `/qc/pending` — Pending Inspection List

**Purpose:** Shows all inspection items that are in any "pending" stage — i.e., any state that is not completed/rejected/return-to-vendor. This is the primary worklist for a QC chemist.

**API endpoint:** `GET /quality-control/inspections/pending/`

**Key fields per row:**
- `arrival_slip_id` — links to the arrival slip record
- `inspection_id` — null if inspection not yet started
- `entry_no` — gate entry number (e.g. `GE-2026-8750`)
- `report_no` / `internal_lot_no` — assigned during inspection
- `po_item_code` — SAP material/item code
- `item_name` — descriptive name of the material
- `party_name` — vendor/supplier name
- `billing_qty` / `billing_uom` — quantity received per vendor invoice
- `workflow_status` — `NOT_STARTED` | `DRAFT` | `AWAITING_CHEMIST` | `AWAITING_QAM` | `COMPLETED` | `REJECTED` | `HOLD`
- `qc_stage` — current stage in the inspection workflow
- `chemist_decision` — `{decision, label, by, decided_at, remarks}`
- `manager_decision` — `{decision, label, by, decided_at, remarks}`
- `qc_decision` — final decision (null until completed)
- `factory_head_decision` — escalation path decision
- `material_type_name` — material classification (null = not configured)
- `rejected_qc_return_entry_id` / `rejected_qc_return_entry_no` — gate return cross-reference if rejected

**Live Jivo Mart records (8 total, all NOT_STARTED):**

| arrival_slip_id | entry_no | item_name | party_name | billing_qty | billing_uom |
|---|---|---|---|---|---|
| 589 | GE-2026-8750 | CARTON 5 LTR + 1 LTR 1 PCS | CVS PACKAGING PRIVATE LIMITED | 195.000 | PCS |
| 588 | GE-2026-8750 | CARTON 5 LTR HDPE 1 PCS THERMO | CVS PACKAGING PRIVATE LIMITED | 637.000 | PCS |
| 553 | GE-2026-0118 | CARTON 5 LTR + 1 LTR 1 PCS | CVS PACKAGING PRIVATE LIMITED | 1,425.000 | PCS |
| 535 | GE-2026-2604 | POLY BAG | S.N. INDUSTRIES | 275.300 | KGS |
| 534 | GE-2026-2604 | POLY BAG | S.N. INDUSTRIES | 158.800 | KGS |
| 529 | GE-2026-2430 | THERMOCOL SET 5 LTR HDPE FULL | RS ENTERPRISES | 924.000 | PCS |
| 525 | GE-2026-2379 | CARTON 1 LTR OLIVE 3 PCS | CVS PACKAGING PRIVATE LIMITED | 2,200.000 | PCS |
| 524 | GE-2026-2379 | CARTON 5 LTR + 1 LTR 1 PCS | CVS PACKAGING PRIVATE LIMITED | 125.000 | PCS |

All 8 items are packaging materials (PM-coded items, not raw oils), from 3 vendors: CVS Packaging Private Limited, S.N. Industries, RS Enterprises. All are dated May 2026 and stuck in NOT_STARTED — no inspection has been started despite the slips being submitted weeks ago.

---

### 3.3 `/qc/arrival-slips` — Arrival Slips List

**Purpose:** Lists all arrival slips (one per PO line item delivered in a gate entry) that have been submitted to QC. This is the record of *what material arrived* with documentary evidence. Each slip is associated with a gate entry (entry_no) and a PO receipt.

**API endpoint:** `GET /quality-control/arrival-slips/`

**Key fields per arrival slip:**
- `id` — slip ID (same as `arrival_slip_id` in inspections)
- `po_item_receipt` — links to PO item receipt record
- `po_item_code` — SAP material code (PM-prefix = packaging material)
- `item_name` — material description
- `po_receipt_id` — parent PO receipt group
- `vehicle_entry_id` — links to gate-core vehicle entry
- `entry_no` — gate entry number (GE-YYYY-XXXX format)
- `particulars` — free-text description
- `arrival_datetime` — when vehicle arrived at gate
- `weighing_required` — whether weighbridge check needed (all = true for Jivo Mart)
- `party_name` — vendor name
- `billing_qty` / `billing_uom` — invoiced quantity and unit
- `in_time_to_qa` — when slip was submitted to QC queue
- `truck_no_as_per_bill` — vehicle number on invoice
- `commercial_invoice_no` — vendor invoice number
- `eway_bill_no` / `bilty_no` — logistics documents
- `has_certificate_of_analysis` — whether COA document was uploaded
- `has_certificate_of_quantity` — whether COQ was uploaded (all false for Jivo Mart)
- `status` — `SUBMITTED` (all Jivo Mart slips)
- `submitted_by_name` — QC staff who submitted
- `remarks` — free text, e.g. "COA NOT AVAILABLE SO DO NOT REJECTED AND GATE RETURN ARRIVAL"
- `attachments` — list of uploaded files with `attachment_type` (CERTIFICATE_OF_ANALYSIS etc.)

**Sample record (live, slip ID 589, verified 2026-06-30):**
```json
{
  "id": 589,
  "po_item_code": "PM0000087",
  "item_name": "CARTON 5 LTR + 1 LTR 1 PCS",
  "entry_no": "GE-2026-8750",
  "vehicle_entry_id": 466,
  "arrival_datetime": "2026-05-19T07:50:00+05:30",
  "in_time_to_qa": "2026-05-19T13:23:03.586086+05:30",
  "party_name": "CVS PACKAGING PRIVATE LIMITED",
  "billing_qty": "195.000",
  "billing_uom": "PCS",
  "truck_no_as_per_bill": "DL01LW6036",
  "commercial_invoice_no": "Cvs/386/26-27",
  "has_certificate_of_analysis": true,
  "has_certificate_of_quantity": false,
  "status": "SUBMITTED",
  "submitted_by_name": "Jasmeet Singh",
  "attachments": [
    {
      "id": 506,
      "file": "https://factory.jivo.in/media/arrival_slip_attachments/IMG20260519124000.jpg",
      "attachment_type": "CERTIFICATE_OF_ANALYSIS"
    }
  ]
}
```

Note the elapsed time: vehicle arrived at 07:50, slip was submitted to QC at 13:23 — ~5.5 hours after gate entry. All 8 slips have a COA attachment but none have a COQ. Submitters are Jasmeet Singh (slip 589) and Arvind (all others).

---

### 3.4 `/qc/arrival-slips/inspections/:inspectionId` — Arrival Slip Inspection Detail

**Purpose:** Shows the full inspection record for a particular arrival slip — parameter readings, chemist decision, QA manager review, and disposition. This is where a chemist opens the inspection form and enters test results.

**API endpoint:** `GET /quality-control/inspections/:inspectionId/` (by inspection ID, not slip ID)

**Note:** For Jivo Mart, all 8 arrival slips have `inspection_id: null` — no inspection has been started on any of them. The endpoint `/quality-control/inspections/589/` returns `{"detail":"No RawMaterialInspection matches the given query."}` because the ID is the inspection's own ID, not the arrival slip ID. Inspection records are created only when the chemist initiates the process.

**Expected fields when an inspection exists:** report_no, internal_lot_no, workflow_status, test parameters (name/spec/actual/result per parameter), chemist_decision (decision/remarks/decided_at), manager_decision, factory_head_decision, final_status, effective_final_status.

---

### 3.5 `/qc/arrival-slips/inspections/:slipId/new` — Create New Inspection

**Purpose:** Form (likely multi-step) for a chemist to begin a QC inspection against an arrival slip. The slip ID in the URL identifies which material is being inspected.

**API interaction:** POST to create the inspection record (likely `POST /quality-control/inspections/` with `arrival_slip_id` body). The form would display slip details (item name, vendor, quantity), allow entering test parameters, and capture the chemist's pass/fail decision.

**Jivo Mart status:** Not yet exercised — 0 inspections created to date.

---

### 3.6 `/qc/approvals` and `/qc/arrival-slips/approvals` — QAM Approval Queue

**Purpose:** Shows inspections where chemist has completed testing and submitted their finding, now awaiting QA Manager review (`awaiting_qam` stage). Manager either approves, rejects, or sends back to chemist.

**API endpoint:** `GET /quality-control/inspections/awaiting-qam/`

**Live Jivo Mart:** 0 records — no inspection has progressed to awaiting-qam stage.

Also may show `GET /quality-control/inspections/awaiting-chemist/`: 0 records.

---

### 3.7 `/qc/customer-returns` and `/qc/customer-returns/:returnId` — Customer Returns

**Purpose:** QC inspection of goods returned by customers (as opposed to vendor returns). Covers the scenario where distributed product is returned and needs re-inspection before being accepted back into inventory.

**API endpoint:** The URL `/quality-control/customer-returns/` returns HTTP 404 — this endpoint does not exist in the current API version. This is a UI-level route that likely calls a different API path, or the feature is planned/not yet enabled for Jivo Mart.

**Jivo Mart status:** Not configured / no data. Endpoint 404s.

---

### 3.8 `/qc/line-clearance` — Line Clearance

**Purpose:** Pre-production checklist that QC staff must complete before a production line can start running. Verifies cleanliness, previous batch removal, labeling accuracy, etc.

**API endpoint:** `GET /production-execution/line-clearance/` (the QC line clearance page reads from the production-execution module's line-clearance resource)

**Live Jivo Mart:** 0 records — production lines are not configured (`/production-execution/lines/` = empty, `/production-execution/line-configs/` = empty). Line clearance cannot be performed until production lines are set up.

---

### 3.9 `/qc/production` — Production QC List

**Purpose:** Lists all production QC inspections — in-process and finished goods checks taken at points during a production run or session.

**API endpoint:** `GET /quality-control/production-qc/`

**Live Jivo Mart:** 0 records. Counts: `{draft: 0, submitted: 0, approved: 0, rejected: 0}`.

Also references production sessions and runs from `/production-execution/runs/` and `/production-execution/sessions/` (both 0 records for Jivo Mart).

---

### 3.10 `/qc/production/approvals` — Production QC Approvals

**Purpose:** Approval queue for production QC checks — where a QA manager reviews a submitted production inspection before marking it approved or rejected.

**API endpoint:** `GET /quality-control/production-qc/approvals/` — returns `[]` for Jivo Mart.

---

### 3.11 `/qc/production/runs/:runId` and `/qc/production/sessions/:sessionId`

**Purpose:** QC detail view tied to a specific production run or session from the Production Execution module. Allows recording mid-run or end-of-run quality checks.

**Jivo Mart status:** No production runs or sessions exist (`/production-execution/runs/` = empty), so these pages have no data.

---

### 3.12 `/qc/master/material-types` — Material Type Master

**Purpose:** Defines categories of materials (e.g., packaging, raw oil, additives) that map to different QC parameter sets. Used to automatically load the right inspection parameters when a chemist starts an inspection.

**API endpoint:** `GET /quality-control/material-types/`

**Live Jivo Mart:** 0 records — not configured. Because material types are empty, the `material_type_name` field in all inspection records is `null`.

---

### 3.13 `/qc/master/parameters` — QC Parameters Library

**Purpose:** Defines the specific test parameters for each material type — e.g., moisture content, density, viscosity, colour index — along with the acceptable specification range and UOM. Chemists enter actual measured values against these specs.

**API endpoint:** The URL `/quality-control/parameters/` returns HTTP 404. The endpoint does not exist at that path; parameters may be nested under material types or accessed differently.

**Jivo Mart status:** Not configured / endpoint not found.

---

### 3.14 `/qc/master/print-documents` — Print Document Templates

**Purpose:** Configures the printable QC report templates — e.g., the QC certificate, the COA format, the inspection report. These are printed and attached to shipments or stored in records.

**API endpoint:** `GET /quality-control/print-documents/`

**Live Jivo Mart:** 0 records — no print templates configured.

---

## 4. Workflows (multi-step flows + statuses)

### 4.1 Inbound Material Inspection Workflow (Arrival Slips)

This is the primary active workflow for Jivo Mart.

```
GATE-IN (Gate section)
    │  Gate entry created for inbound vehicle;
    │  PO receipt items checked and submitted
    ▼
ARRIVAL SLIP CREATED
    │  One slip per PO line item in the gate entry
    │  QC staff uploads COA photograph
    │  Slip status: SUBMITTED
    │  Inspection status: NOT_STARTED
    ▼
INSPECTION INITIATED (chemist opens /arrival-slips/inspections/:slipId/new)
    │  Inspection record created: workflow_status → DRAFT
    │  Chemist enters: report_no, internal_lot_no, material_type
    │  Chemist records test parameter readings
    ▼
CHEMIST SUBMITS DECISION
    │  workflow_status → AWAITING_CHEMIST (or the chemist IS the submitter,
    │  and their decision triggers AWAITING_QAM)
    │  chemist_decision: { decision: PASS/FAIL, remarks, decided_at }
    ▼
QA MANAGER REVIEW (/qc/approvals or /qc/arrival-slips/approvals)
    │  workflow_status: AWAITING_QAM
    │  manager_decision: { decision: APPROVE/REJECT/HOLD, remarks, decided_at }
    ▼
FINAL OUTCOMES:
    ├── COMPLETED (pass) → qc_decision = ACCEPTED
    │       → GRPO entry becomes is_ready_for_grpo: true
    │       → Material eligible for GRPO posting in SAP
    │       → Warehouse receives material
    │
    ├── REJECTED → qc_decision = REJECTED
    │       → rejected_qc_return_entry_id populated
    │       → Gate-core: rejected-qc-return entry created (gate-core/rejected-qc-returns)
    │       → Material returned to vendor via gate exit
    │
    ├── RETURN_TO_VENDOR → material sent back without full rejection process
    │       → Appears in /quality-control/inspections/return-to-vendor/
    │
    └── HOLD → qc_decision on hold, pending further investigation
```

**Status values observed in API:**
- `workflow_status`: `NOT_STARTED`, `DRAFT`, `AWAITING_CHEMIST`, `AWAITING_QAM`, `COMPLETED`, `REJECTED`, `HOLD`
- `qc_stage`: mirrors workflow_status
- `final_status` / `effective_final_status`: null until decision
- `chemist_decision.label`: "Pending" (pre-decision)
- `manager_decision.label`: "Pending" (pre-decision)

### 4.2 Production QC Workflow

```
PRODUCTION RUN/SESSION STARTED (Production Execution section)
    │
    ▼
LINE CLEARANCE (/qc/line-clearance)
    │  QC checks the line before production begins
    │  Linked to production-execution/line-clearance
    ▼
PRODUCTION QC DURING RUN (/qc/production/runs/:runId)
    │  production-qc record created: status → DRAFT
    │  QC inspector records findings
    ▼
SUBMITTED → APPROVED / REJECTED
    │  Appears in /qc/production/approvals if SUBMITTED
    │
    └── APPROVED → batch cleared for packaging/dispatch
        REJECTED → batch put on hold / scrapped
```

**Status values (from production-qc counts schema):** `DRAFT`, `SUBMITTED`, `APPROVED`, `REJECTED`

**Jivo Mart status:** This entire flow is currently unused — 0 records in all production-qc endpoints.

---

## 5. Cross-section connections

### 5.1 Gate-Core → QC (Arrival Slips)
When a gate entry's PO receipt items are submitted in the Gate section, the system automatically creates QC arrival slips (`quality-control/arrival-slips/`). The `vehicle_entry_id` on every slip links back to the gate-core vehicle entry. The `entry_no` (e.g. `GE-2026-8750`) is shared between gate-core and QC.

The gate-core's `vehicle_entry_id: 466` (entry GE-2026-8750) has 2 QC arrival slips (IDs 588 and 589). Confirmed via cross-checking: gate arrival for that vehicle appears in `/grpo/all-entries/` with `status: QC_PENDING, phase: QC, is_ready_for_grpo: false`.

### 5.2 QC → GRPO
GRPO entries in `/grpo/all-entries/` are blocked at `phase: QC` while any arrival slip inspection remains pending. All 5 gate entries visible in GRPO are in `QC_PENDING` status. Once QC marks all items in a gate entry as accepted, `is_ready_for_grpo` flips to `true` and the GRPO user can post the goods receipt to SAP.

GRPO summary confirms: `qc_accepted_qty: "0.000"` — not a single unit has passed QC yet for Jivo Mart.

### 5.3 QC (Rejected) → Gate-Core (Rejected QC Returns)
When an inspection is rejected, the system creates a `rejected-qc-return` entry in gate-core (`/gate-core/rejected-qc-returns/`). This entry tracks the return vehicle movement out of the factory for rejected material. The inspection record carries `rejected_qc_return_entry_id` and `rejected_qc_return_entry_no` for this linkage. Currently 0 rejected-qc-returns for Jivo Mart.

### 5.4 QC (Production) → Production Execution
The `/qc/production/runs/:runId` and `/qc/production/sessions/:sessionId` pages consume data from `/production-execution/runs/` and likely sessions. The `/qc/line-clearance` page consumes `/production-execution/line-clearance/`. All of these are currently empty for Jivo Mart because production lines have not been configured.

### 5.5 QC Master → Gate-Core (Vendor Management)
The material types and QC parameters masters define what gets inspected; vendor PO codes come from SAP via `/quality-control/sap-items/` (0 records for Jivo Mart). The lack of material types explains why `material_type_name` is `null` on all 8 live inspection rows.

---

## 6. Data presence for Jivo Mart (which pages have live data vs empty, with counts)

| Endpoint | Count | Status |
|---|---|---|
| `/quality-control/arrival-slips/` | **8** | LIVE — packaging materials (PM items) from 3 vendors |
| `/quality-control/inspections/` | **8** | LIVE — all in NOT_STARTED, no inspection started |
| `/quality-control/inspections/actionable/` | **8** | LIVE — same 8 rows |
| `/quality-control/inspections/pending/` | **8** | LIVE — same 8 rows |
| `/quality-control/inspections/counts/` | 1 object | LIVE — `{not_started:8, actionable:8, all_else:0}` |
| `/quality-control/inspections/draft/` | 0 | Empty |
| `/quality-control/inspections/awaiting-chemist/` | 0 | Empty |
| `/quality-control/inspections/awaiting-qam/` | 0 | Empty |
| `/quality-control/inspections/completed/` | 0 | Empty |
| `/quality-control/inspections/rejected/` | 0 | Empty |
| `/quality-control/inspections/return-to-vendor/` | 0 | Empty |
| `/quality-control/material-types/` | 0 | Not configured |
| `/quality-control/print-documents/` | 0 | Not configured |
| `/quality-control/production-qc/` | 0 | Not used — production not configured |
| `/quality-control/production-qc/counts/` | 1 object | LIVE but all zeros |
| `/quality-control/production-qc/pending/` | 0 | Empty |
| `/quality-control/sap-items/` | 0 | Not configured |
| `/quality-control/customer-returns/` | 404 | Endpoint not found |
| `/quality-control/parameters/` | 404 | Endpoint not found |
| `/quality-control/line-clearance/` | 404 | Endpoint not found (uses production-execution/line-clearance = 0) |
| `/quality-control/approvals/` | 404 | Endpoint not found (approval via inspection sub-status) |
| `/quality-control/production-qc/approvals/` | 0 | Empty list |

**Key observation:** Jivo Mart has 8 packaging material arrivals stuck in QC limbo since May 2026. They were submitted by gate staff (Arvind and Jasmeet Singh) with COA photos but no chemist has initiated inspections. As a result, 5 GRPO gate entries are also blocked at `QC_PENDING` phase with `qc_accepted_qty: "0.000"` — no inbound material has cleared QC for GRPO posting. The production QC and master configuration sub-sections are entirely unconfigured.

---

## Reference — UI routes (from bundle)
- `/qc`
- `/qc/approvals`
- `/qc/arrival-slips`
- `/qc/arrival-slips/approvals`
- `/qc/arrival-slips/inspections/:inspectionId`
- `/qc/arrival-slips/inspections/:slipId/new`
- `/qc/customer-returns`
- `/qc/customer-returns/:returnId`
- `/qc/inspections/:inspectionId`
- `/qc/inspections/:slipId/new`
- `/qc/line-clearance`
- `/qc/master/material-types`
- `/qc/master/parameters`
- `/qc/master/print-documents`
- `/qc/pending`
- `/qc/production`
- `/qc/production/approvals`
- `/qc/production/runs/:runId`
- `/qc/production/sessions/:sessionId`

## Reference — captured API endpoints + record counts (this section)
- `/quality-control/arrival-slips/` -> 8 (list)
- `/quality-control/inspections/` -> 8 (list)
- `/quality-control/inspections/actionable/` -> 8 (list)
- `/quality-control/inspections/awaiting-chemist/` -> 0 (list)
- `/quality-control/inspections/awaiting-qam/` -> 0 (list)
- `/quality-control/inspections/completed/` -> 0 (list)
- `/quality-control/inspections/counts/` -> 1 (object)
- `/quality-control/inspections/draft/` -> 0 (list)
- `/quality-control/inspections/pending/` -> 8 (list)
- `/quality-control/inspections/rejected/` -> 0 (list)
- `/quality-control/inspections/return-to-vendor/` -> 0 (list)
- `/quality-control/material-types/` -> 0 (list)
- `/quality-control/print-documents/` -> 0 (list)
- `/quality-control/production-qc/` -> 0 (list)
- `/quality-control/production-qc/counts/` -> 1 (object)
- `/quality-control/production-qc/pending/` -> 0 (list)
- `/quality-control/sap-items/` -> 0 (list)

Linked: [[docs/factory/FACTORY_MAP|FACTORY_MAP]] · [[docs/FACTORY_CLI_PLAN|FACTORY_CLI_PLAN]] · [[docs/READ_ONLY_LAW|READ_ONLY_LAW]]
