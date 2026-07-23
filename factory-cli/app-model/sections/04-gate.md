---
title: "Gate — Jivo Mart app-model"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: reference
tags: [jivogpt, factory-cli, gate]
---

# Gate — Jivo Mart app-model

> **Provenance — imported 2026-07-19; source snapshot 2026-06-30.** This note came from the JIVO_MART-only `daman8271/jivo-factory-intel` baseline. For the current three-company study and the live-verified 2026-07-19 state, use [[docs/factory/FACTORY_MAP|FACTORY_MAP]] and [[CLI/factory-cli/README|the current CLI guide]].
> STATUS: COMPLETE. Jivo Mart (JIVO_MART) only. Last updated: 2026-06-30.

---

## 1. Purpose — what this section is for in the factory

The Gate section is the physical security and logistics control point for the Jivo Mart factory. Every vehicle, person, or material that enters or leaves the factory premises is tracked here. The section serves five broad functions:

1. **Vehicle arrival registration** — a cross-company weighbridge log (ARV-prefix entries) capturing tare weight, driver, and security officer when any truck first arrives at the gate.
2. **Outbound finished-goods dispatch** — the primary production-to-delivery gate control, tracking DOCK-prefix gate-out entries linked to SAP sales invoices, with barcode scanning, truck photo, weighment, gatepass printing, and final vehicle dispatch.
3. **Inbound material gate-in** — raw materials, daily needs, construction goods, fixed assets, job-work, maintenance items, and repair parts entering the factory; each category has its own multi-step wizard and dedicated entry type.
4. **BST and empty vehicle management** — branch stock transfers (inter-warehouse moves) and tracking empty vehicles that enter to be loaded.
5. **Person access control** — visitor and contractor-labour gate entries with check-in/check-out status, backed by a master register of visitors (149) and labours (3).

---

## 2. Page tree

```
/gate                                    Gate dashboard (hub)
├── /gate/new                            New gate entry — type selector wizard
│
├── /gate/arrivals                       Arrivals log — weighbridge view (all companies, ARV-prefix)
│   └── /gate/arrivals/:arrivalId/gatepass  Print/view the vehicle arrival gatepass
│
├── /gate/raw-materials                  Raw material truck gate-in (GE-prefix)
│   ├── /gate/raw-materials/all              All RM gate entries list
│   ├── /gate/raw-materials/new              New RM gate entry wizard
│   │   ├── .../step2                        Items & quantities (PO lines)
│   │   ├── .../step3                        Weighment / weighbridge data
│   │   ├── .../step4                        Supplier / document details
│   │   ├── .../attachments                  Upload CoA, CoQ, other docs
│   │   └── .../review                       Review & submit
│   └── /gate/raw-materials/edit/:entryId    Edit existing RM gate entry
│       ├── .../step1  .../step2  .../step3  .../step4
│       ├── .../attachments
│       └── .../review
│
├── /gate/daily-needs                    Daily-needs gate-in (food/canteen items)
│   ├── /gate/daily-needs/all               All daily-needs entries list
│   ├── /gate/daily-needs/new               New entry wizard
│   │   ├── .../step2  .../attachments  .../review
│   └── /gate/daily-needs/edit/:entryId     Edit existing daily-needs entry
│       ├── .../step1  .../step2  .../attachments  .../review
│
├── /gate/construction                   Construction material gate-in
│   ├── /gate/construction/all
│   ├── /gate/construction/new
│   │   └── .../step2  .../attachments  .../review
│   └── /gate/construction/edit/:entryId
│       └── .../step1  .../step2  .../attachments  .../review
│
├── /gate/fixed-assets                   Fixed-assets gate-in (machinery, furniture, etc.)
│   ├── /gate/fixed-assets/all
│   ├── /gate/fixed-assets/new
│   │   └── .../step2  .../attachments  .../review
│   └── /gate/fixed-assets/edit/:entryId
│       └── .../step1  .../step2  .../attachments  .../review
│
├── /gate/maintenance                    Maintenance material gate-in
│   ├── /gate/maintenance/all
│   ├── /gate/maintenance/new
│   │   └── .../step2  .../attachments  .../review
│   └── /gate/maintenance/edit/:entryId
│       └── .../step1  .../step2  .../attachments  .../review
│
├── /gate/job-work                       Job-work material gate-in (outsourced processing)
│   └── /gate/job-work/new
│       └── .../step2  .../attachments  .../review
│
├── /gate/bst-in                         BST (Branch Stock Transfer) inbound
│   └── /gate/bst-in/new
│       └── .../step1  .../attachments  .../review
│
├── /gate/bst-out                        BST outbound
│   └── /gate/bst-out/new
│       └── .../step2  .../weighment  .../gatepass  .../attachments  .../review
│
├── /gate/bst-return                     BST return (goods sent back)
│   └── /gate/bst-return/new
│       └── .../step1  .../attachments  .../review
│
├── /gate/empty-vehicle-in               Empty vehicle gate-in (EVGI-prefix)
│   └── /gate/empty-vehicle-in/new
│       └── .../weighment  .../attachments  .../review
│
├── /gate/empty-vehicle-out              Empty vehicle gate-out (EVGO-prefix)
│   ├── /gate/empty-vehicle-out/:entryId     View specific gate-out entry
│   └── /gate/empty-vehicle-out/new
│       └── .../weighment
│
├── /gate/sales-dispatch                 Sales dispatch gate-out (DOCK-prefix, FG outbound)
│   ├── /gate/sales-dispatch/:entryId        View specific dispatch entry
│   ├── /gate/sales-dispatch/barcode-reports Barcode scan reports for dispatch
│   └── /gate/sales-dispatch/new
│       ├── .../barcode-scan                 Scan FG boxes/pallets
│       ├── .../weighment                    Truck weighment (tare → gross → net)
│       ├── .../gatepass                     Print gatepass (QR-coded)
│       └── .../attachments                  Upload truck photo + other docs
│
├── /gate/rejected-materials             Rejected materials gate-out (vendor return)
│   └── /gate/rejected-materials/new
│       └── .../items  .../weighment
│
├── /gate/rejected-qc-return             QC-rejected material return to vendor
│   └── /gate/rejected-qc-return/new
│       └── .../items  .../weighment
│
├── /gate/customer-return                Customer returns gate-in
│   ├── /gate/customer-return/:entryId       View specific return
│   └── /gate/customer-return/new
│       └── .../attachments
│
├── /gate/repair-movement                Repair movement tracker
│
├── /gate/repair-parts-in                Repair parts gate-in
│   ├── /gate/repair-parts-in/:entryId
│   └── /gate/repair-parts-in/new
│
├── /gate/repair-parts-out               Repair parts gate-out
│   ├── /gate/repair-parts-out/:entryId
│   └── /gate/repair-parts-out/new
│
├── /gate/visitor-labour                 Visitor & labour gate management
│   ├── /gate/visitor-labour/all             All gate entry log
│   ├── /gate/visitor-labour/inside          Currently inside the factory
│   ├── /gate/visitor-labour/contractors     Contractors master list
│   ├── /gate/visitor-labour/contractor/:id/labours  Contractor's registered labours
│   ├── /gate/visitor-labour/labours         All labours master list
│   ├── /gate/visitor-labour/visitors        All visitors master list
│   ├── /gate/visitor-labour/entry/:entryId  Single entry detail
│   └── /gate/visitor-labour/new             New visitor/labour entry
│
└── /gate/labour                         Labour verification station
    └── /gate/labour/verify              Verify labour identity at gate
```

---

## 3. Per-page detail

### 3.1 Gate Dashboard (`/gate`)

**Purpose:** Hub page listing all gate entry types and their current status counts.  
**API:** `/gate-core/sales-dispatch/reports/` (dispatch counts), plus other module lists.  
**Live sample — sales-dispatch report counts:**
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

---

### 3.2 Arrivals (`/gate/arrivals`)

**Purpose:** Cross-company weighbridge log. Every vehicle that arrives at the Jivo complex is registered here by the security officer. The arrival record captures the tare weight and bridges the vehicle to all subsequent gate-in and gate-out entries across JIVO_MART, JIVO_OIL, and JIVO_BEVERAGES.

**API:** `GET /gate-core/arrivals/` — returns a flat array, no pagination.

**Key fields:** `arrival_no` (ARV-prefix), `vehicle_no`, `driver_name`, `gate_in_date`, `in_time`, `tare_weight`, `security_name`, `status` (LOADING / DEPARTED), `gate_out_date`, `out_time`, `departed_at`, `gatepass_no`, `gate_ins[]` (embedded EmptyVehicleGateIn refs), `gate_outs[]` (embedded SalesDispatch refs).

**Real sample (JIVO_MART entry, 2026-06-29):**
```json
{
  "id": 113,
  "arrival_no": "ARV-20260629-0018",
  "vehicle_no": "DL01MB2623",
  "driver_name": "Jaivind 9582295755",
  "gate_in_date": "2026-06-29",
  "in_time": "16:50:00",
  "tare_weight": "5660.000",
  "security_name": "Sachin",
  "status": "DEPARTED",
  "gate_out_date": "2026-06-29",
  "out_time": "19:48:04",
  "gatepass_no": null,
  "gate_ins": [
    { "entry_no": "EVGI-20260629-0019", "company_code": "JIVO_MART", "cover_count": 1 }
  ],
  "gate_outs": [
    { "entry_no": "DOCK-20260629-0017", "company_code": "JIVO_MART",
      "status": "DISPATCHED", "gatepass_no": "DCK/JIVO_MART/2026-27/000033",
      "sap_doc_num": "606260185" }
  ]
}
```

**Data presence:** 117 arrivals total (all companies). JIVO_MART is involved in 24 arrivals (as gate-in or gate-out participant). Statuses: 16 LOADING, 101 DEPARTED.

**Note:** The arrivals list is shared — the Company-Code: JIVO_MART header does NOT filter to only Jivo Mart vehicles. All three companies' truck movements are visible.

---

### 3.3 Arrival Gatepass (`/gate/arrivals/:arrivalId/gatepass`)

**Purpose:** Displays or prints the vehicle-level gatepass for a multi-company arrival (e.g. a single truck that loaded for both JIVO_MART and JIVO_OIL). The ARV-prefixed gatepass (`ARV/2026-27/000003`) is distinct from the company-specific DOCK gatepass.

**API:** The gatepass data is embedded in the arrival record. There is no separate `/gate-core/arrivals/:id/gatepass/` endpoint (returns 404). The gatepass fields on the arrival are `gatepass_no`, `gatepass_printed_at`, `gatepass_committed_at`.

**Live sample:** From ARV-20260629-0022: `gatepass_no = "ARV/2026-27/000003"`, `gatepass_printed_at = "2026-06-29T20:55:25"`, `gatepass_committed_at = null` (still LOADING, not yet departed).

---

### 3.4 Raw Materials Gate-In (`/gate/raw-materials`)

**Purpose:** Registers inbound trucks delivering raw materials (oils, packaging, etc.) against open purchase orders. Each truck arrival creates a GE-prefix entry that acts as the root for QC inspection and GRPO (goods receipt) posting.

**API:**
- Gate entries list: exposed via `GET /grpo/all-entries/` (GE-prefix entries, e.g. GE-2026-8750)
- QC arrival slips: `GET /quality-control/arrival-slips/` (one slip per PO line item received)
- GRPO posting: `POST /grpo/post/` (write, not documented here)

**Entry number format:** `GE-YYYY-NNNN` (e.g. GE-2026-8750)

**Key fields on GRPOEntry:** `vehicle_entry_id`, `entry_no` (GE-prefix), `status` (QC_PENDING / GRPO_PENDING / COMPLETED), `phase` (QC / GRPO), `entry_time`, `suppliers[]`, `po_numbers[]`, `po_receipts[]` (each with items showing `item_code`, `received_qty`, `accepted_qty`, `rejected_qty`).

**Wizard steps:**
- **Step 2** — Select PO and line items; enter received quantities
- **Step 3** — Weighment (weighbridge gross/tare/net)
- **Step 4** — Supplier document details (invoice no, e-way bill, bilty, CoA/CoQ)
- **Attachments** — Upload commercial invoice, CoA, CoQ images
- **Review** — Final check before submission

**Real sample (from GRPO all-entries, 2026-05-19):**
```json
{
  "entry_no": "GE-2026-8750",
  "status": "QC_PENDING",
  "phase": "QC",
  "entry_time": "2026-05-19T13:18:09",
  "suppliers": [{ "supplier_code": "VENDA000277", "supplier_name": "CVS PACKAGING PRIVATE LIMITED" }],
  "po_numbers": ["426224589"],
  "po_receipts": [{
    "items": [
      { "item_code": "PM0000087", "item_name": "CARTON 5 LTR + 1 LTR 1 PCS",
        "received_qty": "195.000", "accepted_qty": "0.000", "qc_status": "INSPECTION_PENDING" },
      { "item_code": "PM0000497", "item_name": "CARTON 5 LTR HDPE 1 PCS THERMO",
        "received_qty": "637.000", "accepted_qty": "0.000", "qc_status": "INSPECTION_PENDING" }
    ]
  }]
}
```

**Data presence:** 5 GE entries visible in GRPO all-entries, all in QC_PENDING phase (packaging materials from CVS Packaging and others, May 2026). History and GRPO-pending views are empty — no completed GRPO postings visible.

---

### 3.5 Daily Needs Gate-In (`/gate/daily-needs`)

**Purpose:** Tracks inbound goods that satisfy daily factory operational needs — primarily food/canteen supplies. A category-based gate entry (not PO-linked).

**API:**
- Categories: `GET /daily-needs-gatein/gate-entries/daily-need/categories/` → 1 record: `{ "id": 2, "category_name": "Food" }`
- Gate entries list: no standalone endpoint found (returns 404 for `/daily-needs-gatein/gate-entries/`). The entries are likely stored internally and accessed through the UI only.

**Wizard steps:** step2 (items & quantities by category), attachments, review.

**Data presence:** Only the "Food" category is configured. No gate entry records returned via API.

---

### 3.6 Construction / Fixed Assets / Maintenance Gate-In

**Purpose:** These three pages share an identical structure for inbound material gate-ins:
- **Construction** — building materials, civil works supplies
- **Fixed Assets** — machinery, furniture, equipment
- **Maintenance** — spare parts, maintenance consumables

Each has an "all" list, new entry wizard (step2 + attachments + review), and edit flow.

**API:** No dedicated `/gate-core/construction/`, `/gate-core/fixed-assets/`, or `/gate-core/maintenance/` endpoints exist (all return 404). These entry types likely use the same underlying gate-entry model as daily-needs but with different category classification.

**Data presence:** No records returned via any attempted API path. Not yet configured or used for Jivo Mart.

---

### 3.7 Job Work Gate-In (`/gate/job-work`)

**Purpose:** Tracks inbound goods returning from job-work (outsourced processing). Material sent out for processing returns through this entry type. Linked to SAP GRPOs and production orders.

**API:**
- `GET /gate-core/job-work/` → 0 records
- `GET /gate-core/job-work/sap-grpos/` → 0 records (eligible SAP GRPOs to link)
- `GET /gate-core/job-work/sap-production-orders/` → 0 records (eligible production orders)

**Data presence:** All three job-work endpoints are empty. Not yet used for Jivo Mart.

---

### 3.8 BST In / Out / Return (`/gate/bst-in`, `/gate/bst-out`, `/gate/bst-return`)

**Purpose:** Branch Stock Transfer — formal gate entries for inventory movements between Jivo Mart warehouses (or between companies). A BST-in records stock arriving at this location; BST-out records stock departing; BST-return records stock sent back.

**API:**
- `GET /gate-core/bst-ins/` → 0 records; `GET /gate-core/bst-ins/eligible-outs/` → 0
- `GET /gate-core/bst-outs/` → 0 records; `GET /gate-core/bst-returns/` → 0
- `GET /gate-core/bst-outs/sap-transfers/` → **50 SAP inventory transfer documents** (open, status "O")

**Real sample — SAP transfer document (eligible for BST-out linking):**
```json
{
  "doc_entry": 3168,
  "doc_num": "626674698",
  "doc_date": "2026-06-29",
  "doc_status": "O",
  "from_warehouse": "DL-INT",
  "to_warehouse": "DL-FG",
  "branch_id": 1,
  "line_count": 15,
  "total_quantity": 7734.0
}
```

**Data presence:** 50 SAP transfer documents exist as source documents (eligible to attach to BST-out entries), but zero BST gate entries have been created. The BST flow is configured in SAP but no gate-level BST entries have been raised for Jivo Mart.

---

### 3.9 Empty Vehicle Gate-In (`/gate/empty-vehicle-in`)

**Purpose:** Registers an empty truck that arrives at the factory specifically to be loaded for outbound dispatch. Creates an EVGI-prefix entry that is retired when the vehicle completes its dispatch gate-out. For JIVO_MART, all EVGI entries have reason = DISPATCH.

**API:** `GET /gate-core/empty-vehicle-ins/` — 36 records.

**Key fields:** `entry_no` (EVGI-prefix), `company_code`, `vehicle_number`, `vehicle_type`, `transporter_name`, `driver_name`, `driver_mobile`, `reason` (DISPATCH / BST / REPAIR_MOVEMENT / JOB_WORK / OTHER), `gate_in_date`, `in_time`, `document_reference`, `pipeline_status` (stage + module_status), `bst_gate_out_id`.

**Real sample (JIVO_MART, 2026-06-29):**
```json
{
  "entry_no": "EVGI-20260629-0019",
  "company_code": "JIVO_MART",
  "vehicle_number": "DL01MB2623",
  "vehicle_type": "Truck",
  "transporter_name": "Arnav Transport Service",
  "driver_name": "Jaivind 9582295755",
  "reason": "DISPATCH",
  "reason_display": "Dispatch",
  "gate_in_date": "2026-06-29",
  "in_time": "16:50:00",
  "document_reference": "Dispatch 606260185",
  "document_notes": "Weight: 9097.250 kg",
  "pipeline_status": {
    "stage": "DISPATCHED",
    "stage_label": "Dispatched",
    "module": "sales dispatch out",
    "module_status": "dispatched"
  }
}
```

**5 reasons supported:** BST, DISPATCH, REPAIR_MOVEMENT, JOB_WORK, OTHER.

**Data presence:** 36 EVGI entries for Jivo Mart; all have reason=DISPATCH. 0 eligible for new gate-in (no trucks currently waiting to be assigned). 43 entries are eligible for empty-vehicle-out (vehicles inside that haven't formally exited through the empty-out flow).

---

### 3.10 Empty Vehicle Gate-Out (`/gate/empty-vehicle-out`)

**Purpose:** Formally records a vehicle leaving empty (without a load), either because it was refused or the purpose was concluded without a dispatch. Most loaded vehicles exit via the Sales Dispatch gate-out instead.

**API:** `GET /gate-core/empty-vehicle-outs/` → 1 record; `GET /gate-core/empty-vehicle-outs/eligible-entries/` → 43 eligible vehicles.

**Real sample (only EVGO record for Jivo Mart):**
```json
{
  "entry_no": "EVGO-20260621-0003",
  "vehicle_entry_no": "EVGI-20260620-0001",
  "vehicle_number": "DL01MA6176",
  "driver_name": "raju",
  "gate_out_date": "2026-06-21",
  "out_time": "19:25:54",
  "status": "COMPLETED",
  "remarks": "Bulk empty-out of pending-at-dock trucks (no load)."
}
```

**Data presence:** 1 EVGO record. 43 vehicles are eligible for empty-out (inside the factory without completed dispatch). The low EVGO count confirms most vehicles exit via the Sales Dispatch flow, not the empty-out flow.

---

### 3.11 Sales Dispatch Gate-Out (`/gate/sales-dispatch`)

**Purpose:** The primary outbound finished-goods gate-out module. Each DOCK-prefix entry tracks a single vehicle loading and dispatching one or more SAP sales invoices. The full workflow spans barcode scanning, truck photo, weighment, and gatepass printing before the security officer marks the vehicle as dispatched.

**API:**
- `GET /gate-core/sales-dispatch/` — 38 records (DOCK-prefix)
- `GET /gate-core/sales-dispatch/documents/` — 200 SAP invoices awaiting dispatch
- `GET /gate-core/sales-dispatch/lock/` — singleton lock status (`is_locked: false`)
- `GET /gate-core/sales-dispatch/reports/` — summary counts
- `GET /gate-core/sales-dispatch/pending-bookings/` — 0 records

**Key fields:** `entry_no` (DOCK-prefix), `vehicle_entry_no` (DOCKV-prefix docking session), `dispatch_date`, `vehicle_no`, `transporter_name`, `driver_name`, `documents[]` (SAP invoice objects with `sap_doc_num`, `customer_name`, `item_summary`), `gatepass_no` (DCK/JIVO_MART/2026-27/XXXXXX), `qr_payload`, `truck_photo`, `gross_weight`, `tare_weight`, `net_weight`, `status` (DOCKED / PRINT_COMMITTED / DISPATCHED), `printed_at`, `dispatched_at`, `items[]` (line-level FG items).

**Wizard sub-pages:**
- **barcode-scan** — scan pallet/box barcodes to verify loaded SKUs
- **weighment** — enter gross weight from weighbridge (tare from arrival); calculates net weight
- **gatepass** — system generates QR-coded gatepass with entry_no, sap_doc_nums, vehicle, random_code
- **attachments** — upload truck photo (GPS-tagged), bilty, e-way bill

**Real sample (DOCK-20260629-0022, status DISPATCHED):**
```json
{
  "entry_no": "DOCK-20260629-0022",
  "vehicle_no": "HR69E9959",
  "transporter_name": "Jivo Wellness",
  "dispatch_date": "2026-06-29",
  "customer_name": "R K WORLDINFOCOM PVT LTD",
  "sap_doc_num": "706260665, 706260666",
  "sap_doc_total": "206102.00",
  "gatepass_no": "DCK/JIVO_MART/2026-27/000036",
  "gross_weight": 3140.0, "tare_weight": 2190.0, "net_weight": 950.0,
  "status": "DISPATCHED",
  "dispatched_at": "2026-06-29T20:58:48",
  "item_summary": "FG0000143 - COLD PRESS GROUNDNUT OIL 5 LTR 4 PCS, FG0000032 - COLD PRESS 1 LTR 20 PCS, ..."
}
```

**Gatepass number format:** `DCK/JIVO_MART/2026-27/XXXXXX`

**Data presence:** 38 DOCK entries — 35 DISPATCHED, 2 DOCKED (truck inside, loading), 1 PRINT_COMMITTED (gatepass printed, awaiting security release). 200 SAP invoices are available as source documents for new dispatches.

**Lock:** Sales dispatch lock is OFF (`is_locked: false`). When locked, no new DOCK entries can be created.

---

### 3.12 Barcode Reports (`/gate/sales-dispatch/barcode-reports`)

**Purpose:** Reporting page showing barcode scan details for dispatches — scanned vs expected boxes/pallets per invoice, rejected scans, partial dispatch approvals.

**API:** Uses the barcode dispatch reports module:
- `GET /barcode/dispatch/reports/` — per-session summary
- `GET /barcode/dispatch/reports/boxes/` — box-level detail
- `GET /barcode/dispatch/reports/rejected-scans/` — rejected scan log

**Data presence:** Live data — 57 dispatch sessions, 1000+ box records, 962 rejected scans in the barcode module.

---

### 3.13 Rejected Materials Gate-Out (`/gate/rejected-materials`)

**Purpose:** Gate entry for returning rejected/substandard materials to the vendor. Captures the items being returned, weighment, and generates a rejection note.

**API:** No standalone endpoint found (all `/gate-core/rejected-materials/` paths return 404). Not yet implemented server-side, or uses a shared model.

**Data presence:** Not configured/used for Jivo Mart.

---

### 3.14 Rejected QC Return (`/gate/rejected-qc-return`)

**Purpose:** Formal gate-out for materials that failed QC inspection and are being returned to the vendor. Linked to the QC inspection decision (chemist/QAM) and the GRPO module.

**API:** `GET /gate-core/rejected-qc-returns/` → 0 records.

**Data presence:** 0 rejected QC returns recorded. The wizard exists (items + weighment steps) but no entries have been raised.

---

### 3.15 Customer Returns (`/gate/customer-return`)

**Purpose:** Gate-in for finished goods returned by customers. Captures the return reference and attachments.

**API:** No standalone endpoint found (returns 404 for all `/gate-core/customer-returns/` attempts). Not yet implemented server-side.

**Data presence:** Not configured/used for Jivo Mart.

---

### 3.16 Repair Parts In / Out / Repair Movement

**Purpose:**
- **Repair Parts In** — records spare parts and equipment entering for repairs
- **Repair Parts Out** — records repaired equipment/parts leaving after service
- **Repair Movement** — tracks assets moving within the plant for repair purposes

**API:** No server-side endpoints found (all `/gate-core/repair-parts-ins/`, `/gate-core/repair-parts-outs/`, `/gate-core/repair-movements/` return 404).

**Data presence:** Not yet implemented or used for Jivo Mart.

---

### 3.17 Visitor & Labour Management (`/gate/visitor-labour`)

**Purpose:** Access control for non-vehicle persons — company visitors, clients, contractors and their labours. Security logs gate-in and gate-out times, captures purpose of visit, and maintains a master register.

**API:**
- `GET /person-gatein/person-types/` → 2 types: `visitor`, `labour`
- `GET /person-gatein/gates/` → 1 gate: `Front gate` (id=2)
- `GET /person-gatein/visitors/` → 149 registered visitors
- `GET /person-gatein/labours/` → 3 registered labours
- `GET /person-gatein/contractors/` → 2 registered contractors
- `GET /person-gatein/entries/` → 206 gate entries (paginated)

**Entry key fields:** `id`, `person_type` (visitor/labour), `gate_in` (Front gate), `gate_out`, `name_snapshot`, `entry_time`, `actual_entry_time`, `exit_time`, `purpose`, `vehicle_no`, `status` (IN/OUT/CANCELLED), `visitor` (FK to visitor master), `labour` (FK to labour master), `approved_by`, `created_by`.

**Real sample — visitor gate entry (currently IN, 2026-06-29):**
```json
{
  "id": 212,
  "person_type": { "name": "visitor" },
  "gate_in": { "name": "Front gate" },
  "name_snapshot": "Pinu 9953012307",
  "entry_time": "2026-06-29T14:29:47",
  "actual_entry_time": "2026-06-29T14:27:00",
  "exit_time": null,
  "purpose": "Meeting khan",
  "status": "IN",
  "visitor": 152
}
```

**Real sample — visitor master record:**
```json
{
  "id": 5,
  "name": "Ashwani gupta",
  "mobile": "9871794788",
  "company_name": "Sukriti entp",
  "id_proof_type": null,
  "blacklisted": false,
  "created_at": "2026-02-24T14:29:40"
}
```

**Data presence:** 206 entries — 205 visitor-type, 1 labour-type; 2 currently IN, 203 OUT, 1 CANCELLED. 149 visitors and 3 labours in master register. 2 contractors (including one expired: `contract_valid_till: 2026-05-31`).

---

### 3.18 Labour Verify (`/gate/labour/verify`)

**Purpose:** Identity verification station at the gate for contractor labours. The security officer scans or enters a labour ID to confirm the person is registered and their contractor's permit is valid before allowing entry.

**API:** Uses `/person-gatein/labours/` for lookup and `/person-gatein/entries/` to create entry. No dedicated verify endpoint — verification logic is frontend-driven.

---

## 4. Workflows (multi-step flows + statuses)

### 4.1 Sales Dispatch (Finished Goods Outbound) — PRIMARY WORKFLOW

This is the most active gate workflow for Jivo Mart (38 DOCK entries, 35 completed dispatches).

```
[SAP Invoice created] 
    ↓
[Dispatch Plan: BOOKED] — booked in the Dispatch module
    ↓
[Empty Vehicle Gate-In: EVGI created] — truck arrives, weighbridge records tare weight,
                                         security creates EVGI entry (reason=DISPATCH)
    ↓
[ARV (Arrival) created] — cross-company weighbridge log (ARV-prefix gatepass for multi-company truck)
    ↓
[Docking: DOCKV (VehicleEntry) created] — truck docks at loading bay
    ↓
[Sales Dispatch (DOCK) entry created] — DOCKED status; document_type=INVOICE; SAP invoice linked
    ↓
[Barcode Scanning] — warehouse scans pallet/box barcodes against invoice line items
    ↓
[Truck Photo] — uploaded via mobile; GPS-tagged; required before gatepass
    ↓
[Weighment] — gross weight entered; net = gross - tare (from ARV record)
    ↓
[Gatepass Generated] — QR-coded: DCK/JIVO_MART/2026-27/XXXXXX; status → PRINT_COMMITTED
    ↓
[Security Release] — security officer confirms vehicle departure; status → DISPATCHED
    ↓
[Arrival departed] — ARV status → DEPARTED; EVGI retired_at stamped
```

**DOCK statuses:** DOCKED → PRINT_COMMITTED → DISPATCHED (also: REJECTED, CANCELLED)

**Gatepass lock:** A company-level lock (`/gate-core/sales-dispatch/lock/`) can freeze all new dispatches when needed (currently unlocked).

---

### 4.2 Raw Material Gate-In (Inbound)

```
[PO created in SAP] 
    ↓
[Supplier's truck arrives] 
    ↓
[Security creates GE-entry] — GE-YYYY-NNNN assigned; vehicle/driver/supplier recorded
    ↓
[QC: ArrivalSlips created] — one slip per PO line item (billing_qty, billing_uom, truck_no_as_per_bill,
                               commercial_invoice_no, has_certificate_of_analysis)
    ↓
[QC Inspection: Chemist] — physical/chemical parameters tested; draft → awaiting-chemist
    ↓
[QC Decision: QAM] — quality assurance manager approves/rejects; awaiting-qam → completed/rejected
    ↓
[If PASS → GRPO posted] — SAP Goods Receipt PO created; accepted_qty updated; material enters warehouse
[If FAIL → Rejected QC Return] — /gate/rejected-qc-return wizard; vehicle exits empty
```

**GE entry statuses:** QC_PENDING → GRPO_PENDING → COMPLETED (or REJECTED)

---

### 4.3 Visitor / Labour Gate Entry

```
[Person arrives at Front Gate]
    ↓
[Security creates /person-gatein/entries/ record]
    ↓ status = IN
    ↓
[Person exits]
    ↓
[Security records exit_time]
    ↓ status = OUT
```

Statuses: IN → OUT (or CANCELLED if entry is voided)

---

### 4.4 Empty Vehicle Gate-In → Gate-Out (without dispatch)

```
[Empty truck arrives for reason OTHER / REPAIR_MOVEMENT / etc.]
    ↓
[EVGI entry created]
    ↓
[Purpose fulfilled (repair completed, goods collected, etc.)]
    ↓
[Empty Vehicle Gate-Out: EVGO entry created]
    ↓ status = COMPLETED
```

Note: 43 vehicles are currently "eligible" for empty-out (inside the factory), but only 1 EVGO record exists — indicating most vehicles leave via dispatch rather than the empty-out flow.

---

### 4.5 BST (Branch Stock Transfer) — Not Yet Active

```
[SAP inventory transfer document created (50 exist as eligible source docs)]
    ↓
[BST-Out entry: WOULD link SAP transfer doc + record vehicle/weighment/gatepass]
    ↓
[Material leaves factory]
    ↓
[BST-In entry at receiving location]
```

All BST gate entries (bst-ins, bst-outs, bst-returns) are currently 0. The 50 SAP transfer documents exist but no gate-level BST entries have been raised.

---

## 5. Cross-section connections

| Connection | How it flows |
|---|---|
| **Gate → QC** | Raw material gate-in (GE-prefix VehicleEntry) → QC arrival slips created per PO line → QC inspection module |
| **Gate → GRPO** | After QC approval of a GE-entry → GRPO module posts the SAP goods receipt |
| **Gate → Dispatch** | Dispatch Plans (booked invoices) drive EVGI creation → DOCK entries use the DispatchPlan as source |
| **Gate → Barcode/Docking** | DOCK (SalesDispatch) entry links a DOCKV (VehicleEntry docking session) which is used by the Barcode scanning module to verify loaded FG boxes |
| **Gate → Warehouse** | After GRPO is posted, accepted materials enter the warehouse (warehouse module tracks stock). FG dispatches deplete warehouse stock via SAP AR invoice/delivery. |
| **Arrivals ↔ multi-company** | The ARV record is shared across JIVO_OIL, JIVO_MART, JIVO_BEVERAGES — a single truck can have gate_ins and gate_outs for multiple companies under one ARV entry |
| **Rejected QC → Gate** | When QC rejects material, the rejected-qc-return gate entry is created and the inspection.rejected_qc_return_entry_no is set, closing the loop |
| **Barcode Dispatch → Gate** | PartialScanRequests and ScanSkipRequests (docking-admin) reference SalesDispatch (DOCK entries) for gatepass exception approvals |
| **Visitor entries → Notifications** | Gate entry creation may trigger notifications to the host employee (notification module, 135 unread) |

---

## 6. Data presence for Jivo Mart — live counts verified 2026-06-30

| Entity / Page | API endpoint | Count | Has live data? |
|---|---|---|---|
| Vehicle Arrivals (ARV) | `/gate-core/arrivals/` | 117 total (24 with JIVO_MART) | Yes |
| Empty Vehicle Gate-Ins (EVGI) | `/gate-core/empty-vehicle-ins/` | 36 | Yes |
| EVGI Reasons | `/gate-core/empty-vehicle-ins/reasons/` | 5 | Yes (config) |
| Vehicles eligible for EVGO | `/gate-core/empty-vehicle-outs/eligible-entries/` | 43 | Yes |
| Empty Vehicle Gate-Outs (EVGO) | `/gate-core/empty-vehicle-outs/` | 1 | Minimal |
| Sales Dispatch Gate-Out (DOCK) | `/gate-core/sales-dispatch/` | 38 | Yes |
| SAP Invoices ready to dispatch | `/gate-core/sales-dispatch/documents/` | 200 | Yes |
| Dispatch Lock | `/gate-core/sales-dispatch/lock/` | 1 (unlocked) | Yes (config) |
| Dispatch Summary | `/gate-core/sales-dispatch/reports/` | 1 (object) | Yes |
| Dispatch Pending Bookings | `/gate-core/sales-dispatch/pending-bookings/` | 0 | Empty |
| BST SAP Transfer docs | `/gate-core/bst-outs/sap-transfers/` | 50 | Yes (SAP source only) |
| BST Gate-Ins | `/gate-core/bst-ins/` | 0 | **Empty** |
| BST Gate-Outs | `/gate-core/bst-outs/` | 0 | **Empty** |
| BST Returns | `/gate-core/bst-returns/` | 0 | **Empty** |
| Job Work Gate-Ins | `/gate-core/job-work/` | 0 | **Empty** |
| Job Work SAP GRPOs | `/gate-core/job-work/sap-grpos/` | 0 | **Empty** |
| Job Work SAP Prod. Orders | `/gate-core/job-work/sap-production-orders/` | 0 | **Empty** |
| Rejected QC Returns | `/gate-core/rejected-qc-returns/` | 0 | **Empty** |
| Daily Needs Categories | `/daily-needs-gatein/gate-entries/daily-need/categories/` | 1 ("Food") | Yes (config only) |
| Daily Needs Gate Entries | (no standalone endpoint) | n/a | Not found via API |
| Construction Gate Entries | (no standalone endpoint) | n/a | **Not found** |
| Fixed Assets Gate Entries | (no standalone endpoint) | n/a | **Not found** |
| Maintenance Gate Entries | (no standalone endpoint) | n/a | **Not found** |
| Rejected Materials Gate-Out | (no standalone endpoint) | n/a | **Not found** |
| Customer Returns | (no standalone endpoint) | n/a | **Not found** |
| Repair Parts In/Out | (no standalone endpoint) | n/a | **Not found** |
| Person Gate Entries | `/person-gatein/entries/` | 206 | Yes |
| Visitor Master | `/person-gatein/visitors/` | 149 | Yes |
| Labour Master | `/person-gatein/labours/` | 3 | Yes |
| Contractors | `/person-gatein/contractors/` | 2 | Yes |
| Gates (physical) | `/person-gatein/gates/` | 1 (Front gate) | Yes |
| Person Types | `/person-gatein/person-types/` | 2 (visitor, labour) | Yes (config) |
| Raw Material GE entries (via GRPO) | `/grpo/all-entries/` | 5 | Yes |
| QC Arrival Slips (RM tracking) | `/quality-control/arrival-slips/` | 8 | Yes |

**Summary:** The sales dispatch (outbound FG) and visitor/labour gate management modules are fully live with real operational data. Raw material gate-in is live but tracked via the GRPO/QC module (GE-prefix entries), not a standalone gate-core endpoint. BST, job-work, rejected-materials, customer-returns, repair-parts, construction, fixed-assets, and maintenance gate flows are configured in the UI but have zero actual gate entries for Jivo Mart.

---

## Reference — UI routes (from bundle)
- `/gate`
- `/gate/arrivals`
- `/gate/arrivals/:arrivalId/gatepass`
- `/gate/bst-in`
- `/gate/bst-in/new`
- `/gate/bst-in/new/attachments`
- `/gate/bst-in/new/review`
- `/gate/bst-in/new/step1`
- `/gate/bst-out`
- `/gate/bst-out/new`
- `/gate/bst-out/new/attachments`
- `/gate/bst-out/new/gatepass`
- `/gate/bst-out/new/review`
- `/gate/bst-out/new/step2`
- `/gate/bst-out/new/weighment`
- `/gate/bst-return`
- `/gate/bst-return/new`
- `/gate/bst-return/new/attachments`
- `/gate/bst-return/new/review`
- `/gate/bst-return/new/step1`
- `/gate/construction`
- `/gate/construction/all`
- `/gate/construction/edit/:entryId/attachments`
- `/gate/construction/edit/:entryId/review`
- `/gate/construction/edit/:entryId/step1`
- `/gate/construction/edit/:entryId/step2`
- `/gate/construction/new`
- `/gate/construction/new/attachments`
- `/gate/construction/new/review`
- `/gate/construction/new/step2`
- `/gate/customer-return`
- `/gate/customer-return/:entryId`
- `/gate/customer-return/new`
- `/gate/customer-return/new/attachments`
- `/gate/daily-needs`
- `/gate/daily-needs/all`
- `/gate/daily-needs/edit/:entryId/attachments`
- `/gate/daily-needs/edit/:entryId/review`
- `/gate/daily-needs/edit/:entryId/step1`
- `/gate/daily-needs/edit/:entryId/step2`
- `/gate/daily-needs/new`
- `/gate/daily-needs/new/attachments`
- `/gate/daily-needs/new/review`
- `/gate/daily-needs/new/step2`
- `/gate/empty-vehicle-in`
- `/gate/empty-vehicle-in/new`
- `/gate/empty-vehicle-in/new/attachments`
- `/gate/empty-vehicle-in/new/review`
- `/gate/empty-vehicle-in/new/weighment`
- `/gate/empty-vehicle-out`
- `/gate/empty-vehicle-out/:entryId`
- `/gate/empty-vehicle-out/new`
- `/gate/empty-vehicle-out/new/weighment`
- `/gate/fixed-assets`
- `/gate/fixed-assets/all`
- `/gate/fixed-assets/edit/:entryId/attachments`
- `/gate/fixed-assets/edit/:entryId/review`
- `/gate/fixed-assets/edit/:entryId/step1`
- `/gate/fixed-assets/edit/:entryId/step2`
- `/gate/fixed-assets/new`
- `/gate/fixed-assets/new/attachments`
- `/gate/fixed-assets/new/review`
- `/gate/fixed-assets/new/step2`
- `/gate/job-work`
- `/gate/job-work/new`
- `/gate/job-work/new/attachments`
- `/gate/job-work/new/review`
- `/gate/job-work/new/step2`
- `/gate/labour`
- `/gate/labour/verify`
- `/gate/maintenance`
- `/gate/maintenance/all`
- `/gate/maintenance/edit/:entryId/attachments`
- `/gate/maintenance/edit/:entryId/review`
- `/gate/maintenance/edit/:entryId/step1`
- `/gate/maintenance/edit/:entryId/step2`
- `/gate/maintenance/new`
- `/gate/maintenance/new/attachments`
- `/gate/maintenance/new/review`
- `/gate/maintenance/new/step2`
- `/gate/new`
- `/gate/raw-materials`
- `/gate/raw-materials/all`
- `/gate/raw-materials/edit/:entryId/attachments`
- `/gate/raw-materials/edit/:entryId/review`
- `/gate/raw-materials/edit/:entryId/step1`
- `/gate/raw-materials/edit/:entryId/step2`
- `/gate/raw-materials/edit/:entryId/step3`
- `/gate/raw-materials/edit/:entryId/step4`
- `/gate/raw-materials/new`
- `/gate/raw-materials/new/attachments`
- `/gate/raw-materials/new/review`
- `/gate/raw-materials/new/step2`
- `/gate/raw-materials/new/step3`
- `/gate/raw-materials/new/step4`
- `/gate/rejected-materials`
- `/gate/rejected-materials/new`
- `/gate/rejected-materials/new/items`
- `/gate/rejected-materials/new/weighment`
- `/gate/rejected-qc-return`
- `/gate/rejected-qc-return/new`
- `/gate/rejected-qc-return/new/items`
- `/gate/rejected-qc-return/new/weighment`
- `/gate/repair-movement`
- `/gate/repair-parts-in`
- `/gate/repair-parts-in/:entryId`
- `/gate/repair-parts-in/new`
- `/gate/repair-parts-out`
- `/gate/repair-parts-out/:entryId`
- `/gate/repair-parts-out/new`
- `/gate/sales-dispatch`
- `/gate/sales-dispatch/:entryId`
- `/gate/sales-dispatch/barcode-reports`
- `/gate/sales-dispatch/new`
- `/gate/sales-dispatch/new/attachments`
- `/gate/sales-dispatch/new/barcode-scan`
- `/gate/sales-dispatch/new/gatepass`
- `/gate/sales-dispatch/new/weighment`
- `/gate/visitor-labour`
- `/gate/visitor-labour/all`
- `/gate/visitor-labour/contractor/:contractorId/labours`
- `/gate/visitor-labour/contractors`
- `/gate/visitor-labour/entry/:entryId`
- `/gate/visitor-labour/inside`
- `/gate/visitor-labour/labours`
- `/gate/visitor-labour/new`
- `/gate/visitor-labour/visitors`

## Reference — captured API endpoints + record counts (this section)
- `/daily-needs-gatein/gate-entries/daily-need/categories/` -> 1 (list)
- `/gate-core/arrivals/` -> 117 (list, cross-company; JIVO_MART involved in 24)
- `/gate-core/bst-ins/` -> 0 (list)
- `/gate-core/bst-ins/eligible-outs/` -> 0 (list)
- `/gate-core/bst-outs/` -> 0 (list)
- `/gate-core/bst-outs/sap-transfers/` -> 50 (list, SAP source docs; all status "O")
- `/gate-core/bst-returns/` -> 0 (list)
- `/gate-core/bst-returns/eligible-outs/` -> 0 (list)
- `/gate-core/empty-vehicle-ins/` -> 36 (list, EVGI-prefix; all reason=DISPATCH)
- `/gate-core/empty-vehicle-ins/eligible/` -> 0 (list)
- `/gate-core/empty-vehicle-ins/reasons/` -> 5 (enum: BST, DISPATCH, REPAIR_MOVEMENT, JOB_WORK, OTHER)
- `/gate-core/empty-vehicle-outs/` -> 1 (list, EVGO-prefix)
- `/gate-core/empty-vehicle-outs/eligible-entries/` -> 43 (list, DOCKV-prefix entries inside)
- `/gate-core/job-work/` -> 0 (list)
- `/gate-core/job-work/sap-grpos/` -> 0 (list)
- `/gate-core/job-work/sap-production-orders/` -> 0 (list)
- `/gate-core/rejected-qc-returns/` -> 0 (list)
- `/gate-core/sales-dispatch/` -> 38 (list, DOCK-prefix; 35 DISPATCHED, 2 DOCKED, 1 PRINT_COMMITTED)
- `/gate-core/sales-dispatch/documents/` -> 200 (list, SAP invoices awaiting dispatch)
- `/gate-core/sales-dispatch/lock/` -> 1 (object, is_locked: false)
- `/gate-core/sales-dispatch/pending-bookings/` -> 0 (list)
- `/gate-core/sales-dispatch/reports/` -> 1 (object, counts summary)
- `/person-gatein/entries/` -> 206 (paginated; 205 visitor + 1 labour; 2 IN / 203 OUT / 1 CANCELLED)
- `/person-gatein/visitors/` -> 149 (visitor master)
- `/person-gatein/labours/` -> 3 (labour master)
- `/person-gatein/contractors/` -> 2 (contractor master)
- `/person-gatein/gates/` -> 1 (Front gate)
- `/person-gatein/person-types/` -> 2 (visitor, labour)
- `/grpo/all-entries/` -> 5 (raw material GE-prefix gate entries, all QC_PENDING)

Linked: [[docs/factory/FACTORY_MAP|FACTORY_MAP]] · [[docs/FACTORY_CLI_PLAN|FACTORY_CLI_PLAN]] · [[docs/READ_ONLY_LAW|READ_ONLY_LAW]]
