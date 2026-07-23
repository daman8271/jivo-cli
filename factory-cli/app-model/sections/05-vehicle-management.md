---
title: "Vehicle Management — Jivo Mart app-model"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: reference
tags: [jivogpt, factory-cli, vehicle-management]
---

# Vehicle Management — Jivo Mart app-model

> **Provenance — imported 2026-07-19; source snapshot 2026-06-30.** This note came from the JIVO_MART-only `daman8271/jivo-factory-intel` baseline. For the current three-company study and the live-verified 2026-07-19 state, use [[docs/factory/FACTORY_MAP|FACTORY_MAP]] and [[CLI/factory-cli/README|the current CLI guide]].
> Last updated: 2026-06-30. Jivo Mart (JIVO_MART) only.

## 1. Purpose — what this section is for in the factory

Vehicle Management is the master-data and operational-log module for every vehicle, driver, and transporter that moves goods into or out of the Jivo Mart factory. It serves two distinct but tightly coupled roles:

**Master registry**: Maintains the standing lists of registered vehicles (340), transporters (88), drivers (296), and vehicle types (7). These records are referenced by nearly every other module — Gate Entry, Dispatch, QC/GRPO, Barcode/Dispatch Sessions — wherever a vehicle or driver identity needs to be recorded or validated.

**Entry log and dispatch linking**: Tracks each physical gate-entry event for a vehicle, keyed by entry type (RAW_MATERIAL inbound, DISPATCH outbound, or EMPTY_VEHICLE for returns and movements). The Dispatch Linking page specifically manages the step where an outbound dispatch plan is paired with the physical vehicle that arrives to load goods.

In factory operations, this section is consulted at every gate checkpoint: security staff look up or register the vehicle/driver, then the correct entry type is created so downstream modules (Gate Core, QC, Docking) receive the vehicle's operational context.

---

## 2. Page tree

```
/vehicle-management                        Landing — section overview
├── /vehicle-management/vehicles           Vehicle Registry — list, search, add
│   └── /vehicle-management/vehicles/         (canonical URL with trailing slash)
│       └── names/                            Lightweight id→vehicle_number list (dropdowns)
├── /vehicle-management/transporters       Transporter Registry — list, search, add
│   └── /vehicle-management/transporters/     (canonical URL)
│       └── names/                            Lightweight id→name list (dropdowns)
├── /vehicle-management/drivers            Driver Registry — list, search, add
├── /vehicle-management/vehicle-types/     Vehicle Type Reference — static lookup list
├── /vehicle-management/entries            Vehicle Entry Log
│   └── /vehicle-management/vehicle-entries/          Entry list (filtered: entry_type + date range)
│       ├── count/                                     Count by status (entry_type + date range)
│       └── list-by-status/                            Filter by status + entry_type + date range
└── /vehicle-management/dispatch-linking   Dispatch–Vehicle Linking Board
```

**Page descriptions:**

| Route | What it does |
|---|---|
| `/vehicle-management` | Section landing; links to sub-pages. |
| `/vehicle-management/vehicles` | Paginated list of all registered vehicles; search by reg number; add new vehicle (vehicle_number, type, transporter, capacity). |
| `/vehicle-management/vehicles/names/` | Read-only lightweight list: `{id, vehicle_number}` for 340 vehicles; used to populate selection dropdowns in Gate Entry and Dispatch forms. |
| `/vehicle-management/transporters` | Paginated list of 88 transporters; search by name; add new transporter (name, contact_person, mobile, GSTIN). |
| `/vehicle-management/transporters/names/` | Lightweight `{id, name}` list for 88 transporters; dropdown population. |
| `/vehicle-management/drivers` | Paginated list of 296 drivers; search by name; add new driver (name, mobile, license_no, id_proof_type, id_proof_number, photo). |
| `/vehicle-management/vehicle-types/` | Static reference list of 7 vehicle types; not user-editable from this section. |
| `/vehicle-management/entries` | Log of all vehicle gate entries, filterable by `entry_type` (RAW_MATERIAL, DISPATCH, EMPTY_VEHICLE, BST, JOB_WORK, etc.) and date range. Shows status breakdown and per-entry detail. |
| `/vehicle-management/dispatch-linking` | Board showing active dispatch plans and their linkage status to physical vehicle entries. Operators use this to pair an arriving truck (EVGI) with its corresponding dispatch plan so the pipeline can advance from EMPTY_IN to READY_TO_DOCK. |

---

## 3. Per-page detail

### 3.1 Vehicle Registry (`/vehicle-management/vehicles`)

**Purpose**: The authoritative list of all trucks and other vehicles permitted to enter the factory. Each vehicle is linked to a transporter and assigned a type.

**API endpoint**: `GET /vehicle-management/vehicles/`
Returns a flat list (no pagination envelope — all 340 records returned in one response).

**Key fields**:

| Field | Type | Description |
|---|---|---|
| `id` | int | Internal PK |
| `vehicle_number` | string | Registration number (e.g. `HR69F6098`) |
| `vehicle_type` | object | Nested `{id, name}` — one of 7 types |
| `transporter` | object | Nested full transporter record |
| `capacity_ton` | decimal string | Load capacity in metric tons |
| `created_at` | datetime | When vehicle was registered |

**Live sample** (verified 2026-06-30):
```json
{
  "id": 83,
  "vehicle_number": "AS01PC0599",
  "vehicle_type": {"id": 3, "name": "Truck"},
  "transporter": {
    "id": 4,
    "name": "Kaushik logistics",
    "contact_person": "Mr kaushik",
    "mobile_no": "9017131750",
    "gstin": ""
  },
  "capacity_ton": "999.00",
  "created_at": "2026-03-20T16:31:09.706236+05:30"
}
```

**Vehicle count by type** (live, 2026-06-30):

| Type | ID | Count |
|---|---|---|
| Truck | 3 | 327 |
| By Hand | 9 | 4 |
| Car | 4 | 4 |
| Eco Van | 7 | 4 |
| Bike | 5 | 1 |
| Courier | 8 | 0 |
| Cycle | 6 | 0 |

Courier and Cycle types exist in the reference list but have no vehicles registered against them in Jivo Mart.

---

### 3.2 Transporter Registry (`/vehicle-management/transporters`)

**Purpose**: Master list of all transport companies / logistics partners who bring or take goods on behalf of Jivo Mart. Most vehicles are associated with a transporter; "Jivo Wellness" / "Jivo" transporters represent Jivo's own fleet for inter-company movements.

**API endpoint**: `GET /vehicle-management/transporters/`
Returns a flat list; 88 records.

**Key fields**:

| Field | Type | Description |
|---|---|---|
| `id` | int | Internal PK |
| `name` | string | Company/transporter name |
| `contact_person` | string | Point of contact |
| `mobile_no` | string | Contact phone |
| `gstin` | string | GST identification number (many blank) |
| `created_at` | datetime | Registration date |

**Live sample** (verified 2026-06-30):
```json
{
  "id": 81,
  "name": "Amazon Freight (ASSPL)",
  "contact_person": "rishabh",
  "mobile_no": "8802345622",
  "gstin": "29AAICA3918J1ZE",
  "created_at": "2026-06-17T11:15:40.531209+05:30"
}
```

Notable transporters active in dispatch operations: Arnav Transport Service (id=54), Abhiman Express (77), Amazon Freight ASSPL (81), Bhargave Road Carrier (50), PICK & SHIP (85), MAHAVIR TRANSPORT COMPANY (64), Jivo Wellness pvt ltd (30 — own fleet), Jivo (31 — own fleet), JIVO WELLNESS PVT LTD (22 — alternate entry for own fleet). Many transporters have placeholder GSTIN (`""`) indicating they are unregistered or data not captured at onboarding.

---

### 3.3 Driver Registry (`/vehicle-management/drivers`)

**Purpose**: Registry of all drivers authorized to enter the factory. Drivers are associated with vehicle movements at gate entry. License and ID proof are collected for compliance.

**API endpoint**: `GET /driver-management/drivers/`
Returns a flat list; 296 records.

**Key fields**:

| Field | Type | Description |
|---|---|---|
| `id` | int | Internal PK |
| `name` | string | Driver name (often formatted as "Name Mobile" e.g. "Jaivind 9582295755") |
| `mobile_no` | string | Mobile number |
| `license_no` | string | Driving licence number |
| `id_proof_type` | string | `"Aadhar"` or `"Other"` |
| `id_proof_number` | string | ID proof number |
| `photo` | string \| null | URL to uploaded photo, or null |
| `created_at` | datetime | Registration timestamp |

**Live samples** (verified 2026-06-30):
```json
[
  {
    "id": 306,
    "name": "Imran 9389618148",
    "mobile_no": "9389618148",
    "license_no": "UP2320150002792",
    "id_proof_type": "Other",
    "id_proof_number": "UP2320150002792",
    "photo": null,
    "created_at": "2026-06-29T18:46:22.046915+05:30"
  },
  {
    "id": 11,
    "name": "Guransh Singh",
    "mobile_no": "1234567890",
    "license_no": "MH0220150001234",
    "id_proof_type": "Aadhar",
    "id_proof_number": "123456789012",
    "photo": "https://factory.jivo.in/media/drivers/photos/facotylogoRemoveBG.PNG",
    "created_at": "2026-02-19T11:37:09.462483+05:30"
  }
]
```

Observation: Most drivers are added dynamically as they arrive; many have the mobile number appended to the name as a quick lookup key. id=11 (Guransh Singh) is the earliest registered driver (2026-02-19, first day of operations). Photo upload is rare — most `photo` fields are `null`.

---

### 3.4 Vehicle Type Reference (`/vehicle-management/vehicle-types/`)

**Purpose**: Static reference list defining the classification of vehicles allowed at the factory. Used to categorize vehicles in the vehicle registry and in gate entry forms.

**API endpoint**: `GET /vehicle-management/vehicle-types/`
Returns all 7 records in one call.

**Complete list** (live, 2026-06-30):

| ID | Name |
|---|---|
| 5 | Bike |
| 9 | By Hand |
| 4 | Car |
| 8 | Courier |
| 6 | Cycle |
| 7 | Eco Van |
| 3 | Truck |

"By Hand" and "Courier" are conceptual types for small deliveries not arriving by a conventional wheeled vehicle. "Eco Van" is a medium-duty variant distinct from trucks.

---

### 3.5 Vehicle Entry Log (`/vehicle-management/entries`)

**Purpose**: The operational log of every vehicle gate entry event. Each record represents a specific vehicle arriving at the factory for a declared purpose. The entry type determines which downstream module takes over.

**API endpoint**: `GET /vehicle-management/vehicle-entries/`
**Required query params**: `entry_type` (e.g. `RAW_MATERIAL`, `DISPATCH`) AND `from_date` + `to_date` (ISO date strings).

Supporting endpoints:
- `GET /vehicle-management/vehicle-entries/count/?entry_type=&from_date=&to_date=` — returns `{total_vehicle_entries: [{status, count}]}`
- `GET /vehicle-management/vehicle-entries/list-by-status/?entry_type=&status=&from_date=&to_date=` — same shape, filtered by status

**Entry number prefix**: `GE-YYYY-NNNN` (e.g. `GE-2026-8750`)

**Key fields**:

| Field | Type | Description |
|---|---|---|
| `id` | int | Internal PK |
| `entry_no` | string | Human-readable GE- prefixed entry number |
| `company` | object | Nested company: `{id:2, code:"JIVO_MART"}` |
| `vehicle` | object | Full nested vehicle record |
| `driver` | object | Full nested driver record |
| `status` | string | `QC_PENDING`, `COMPLETED`, etc. |
| `entry_type` | string | `RAW_MATERIAL` (only active type seen for JIVO_MART) |
| `entry_time` | datetime | Gate entry timestamp |
| `remarks` | string | Optional security notes |
| `suppliers` | array | `[{supplier_code, supplier_name}]` — SAP vendor codes (e.g. `VENDA000277`) |
| `qc_final_status` | string \| null | Filled after QC completes |

**Live sample** (verified 2026-06-30):
```json
{
  "id": 466,
  "entry_no": "GE-2026-8750",
  "company": {"id": 2, "name": "Jivo Mart", "code": "JIVO_MART"},
  "vehicle": {
    "id": 164, "vehicle_number": "DL01LW6036",
    "vehicle_type": {"id": 3, "name": "Truck"},
    "transporter": {"id": 49, "name": "C.v.s packaging", "mobile_no": "9050705410"}
  },
  "driver": {"id": 144, "name": "Vikram 9050705410", "mobile_no": "9050705410"},
  "status": "QC_PENDING",
  "entry_time": "2026-05-19T13:18:09.474142+05:30",
  "entry_type": "RAW_MATERIAL",
  "suppliers": [{"supplier_code": "VENDA000277", "supplier_name": "CVS PACKAGING PRIVATE LIMITED"}],
  "qc_final_status": null
}
```

**Data presence**: Only `entry_type=RAW_MATERIAL` returned data for JIVO_MART. 5 active entries, all in `QC_PENDING` status (oldest: 2026-05-02). `DISPATCH`, `INBOUND`, `OUTBOUND`, `SALES`, `BST`, `JOB_WORK`, `REJECTED_QC_RETURN`, `DOCKING`, `EMPTY`, `RETURN` types all returned empty for the full date range tested (2026-01-01 to 2026-06-30). The outbound dispatch vehicle entries are tracked separately via gate-core's empty-vehicle-ins (`EVGI-` series) and docking vehicle entries (`DOCKV-` series) — those are not surfaced through this endpoint.

---

### 3.6 Dispatch–Vehicle Linking (`/vehicle-management/dispatch-linking`)

**Purpose**: The dispatch linking page is the workflow interface where an empty vehicle that has arrived at the factory gate (an `EVGI-` Empty Vehicle Gate In with `reason=DISPATCH`) is formally paired with one or more outbound dispatch plans. This action advances the dispatch plan's pipeline stage from `EMPTY_IN` to `READY_TO_DOCK`.

**API endpoint**: No dedicated `/vehicle-management/dispatch-linking/` REST endpoint exists — the page is a 404 at the bare path. It is built on the `/dispatch-plans/pipeline/` API (Kanban board returning pipeline stage columns with plan cards) filtered to plans in `EMPTY_IN` status, combined with the `/gate-core/empty-vehicle-ins/` and `/gate-core/empty-vehicle-outs/eligible-entries/` endpoints.

**Relationship**: Each `EmptyVehicleGateIn` (EVGI) record has a `pipeline_status` embedded object that shows the linked dispatch plan's current stage and counts. E.g.:
```json
{
  "entry_no": "EVGI-20260629-0019",
  "reason": "DISPATCH",
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

**Live data note**: The `/vehicle-management/dispatch-linking` UI route returns HTTP 404 when probed as a standalone API path — it is a pure frontend page assembling data from multiple other API calls. 36 active EVGI entries (all `reason=DISPATCH`) are confirmed live for JIVO_MART.

---

## 4. Workflows (multi-step flows + statuses)

### 4.1 Outbound Dispatch Vehicle Flow (EVGI + DOCKV series)

This is the primary daily flow. Every outbound shipment from the factory requires an empty truck to arrive, be matched to its dispatch plan, dock at the warehouse for loading, and exit with a signed gate pass.

```
Step 1: DISPATCH PLAN BOOKED
  DispatchPlan record created in dispatch module (stage: BOOKED)
  Links to SAP invoice (sap_invoice_doc_num), customer, vehicle assignment

Step 2: EMPTY VEHICLE GATE IN (EVGI-YYYYMMDD-NNNN)
  Security creates EmptyVehicleGateIn record
  reason = DISPATCH
  Fields: vehicle_number (looked up from Vehicles master), driver, transporter,
          gate_in_date + in_time, document_reference (e.g. "Dispatch 606260185")
  VehicleEntry record (EVGI series, id=vehicle_entry) is simultaneously created
  DispatchPlan pipeline stage advances to: EMPTY_IN

Step 3: DISPATCH LINKING
  On the dispatch-linking page, operator confirms which dispatch plan(s)
  are assigned to this vehicle entry.
  DispatchPlan.linked_vehicle_entry_id = VehicleEntry.id
  DispatchPlan pipeline advances to: READY_TO_DOCK

Step 4: DOCKING (DOCKV-YYYYMMDD-NNNN)
  Vehicle docks at warehouse bay; a DOCKV VehicleEntry is created
  (entry_type=SALES_DISPATCH, tracked in gate-core eligible-entries)
  DispatchPlan stage: DOCKED
  Barcode scanning of boxes/pallets begins (tracked in barcode module)

Step 5: PHOTO ATTACHED
  Dispatch officer attaches vehicle photo to dispatch record
  DispatchPlan stage: PHOTO_ATTACHED

Step 6: GATE PASS GENERATION
  Gate pass printed (PDF); DOCK SalesDispatch entry created
  DispatchPlan stages: READY_FOR_GATEPASS → GATEPASS_PRINTED → PRINT_COMMITTED

Step 7: DISPATCH GATE OUT (DOCK-YYYYMMDD-NNNN)
  SalesDispatch gate-out record created; vehicle exits with gate pass
  DispatchPlan stage: DISPATCHED
  EVGI record's pipeline_status.stage = "DISPATCHED"

Step 8: OPTIONAL — EMPTY VEHICLE GATE OUT (EVGO-YYYYMMDD-NNNN)
  If a loaded truck needs to exit without completing dispatch (e.g. cancelled),
  an EVGO record closes the EVGI session.
  status: COMPLETED
```

**Pipeline stages observed**: `BOOKED` → `EMPTY_IN` → `READY_TO_DOCK` → `DOCKED` → `PHOTO_ATTACHED` → `READY_FOR_GATEPASS` → `GATEPASS_PRINTED` → `PRINT_COMMITTED` → `DISPATCHED` (terminal success) or `REJECTED` (terminal failure).

### 4.2 Inbound Raw Material Vehicle Flow (GE series)

```
Step 1: Vehicle arrives with raw material / packaging material
  Security creates Vehicle Entry via /vehicle-management/vehicle-entries/
  entry_no: GE-YYYY-NNNN
  entry_type: RAW_MATERIAL
  Fields: vehicle, driver, entry_time, suppliers[] (SAP vendor code)
  Initial status: QC_PENDING

Step 2: QC Inspection
  Quality Control module receives the arrival slip linked to this vehicle entry
  (vehicle_entry_id FK on ArrivalSlip)
  Status remains QC_PENDING until QC decision

Step 3: GRPO Posting
  After QC approval, GRPOEntry is created against the vehicle_entry_id
  Status → COMPLETED when all PO lines are posted to SAP
```

**Statuses observed for JIVO_MART**: All 5 current GE entries are in `QC_PENDING`. No `COMPLETED` GE entries visible in current date range (suggesting older data may be archived or entries are a recent backlog).

### 4.3 Empty Vehicle Out Flow (EVGO series)

Used for vehicles that entered the factory but are leaving without completing a delivery/dispatch (e.g. cancelled load, bulk clearance of dock-waiting trucks).

```
EVGI (any reason) created
  ↓ vehicle present at factory
EVGO created, linked to VehicleEntry (vehicle_entry_no = original EVGI entry_no)
  vehicle_entry_type: EMPTY_VEHICLE
  status: COMPLETED
  gate_out_date + out_time recorded
  security_name + remarks
```

Only 1 EVGO record found in JIVO_MART (EVGO-20260621-0003), with remark "Bulk empty-out of pending-at-dock trucks (no load)."

---

## 5. Cross-section connections

| Connection | Detail |
|---|---|
| **Vehicle Management → Gate Core** | `EmptyVehicleGateIn` and `EmptyVehicleGateOut` (in Gate Core section) embed Vehicle.id and Driver.id FKs sourced from this section's registries. Vehicle entries created here (GE-, EVGI-, DOCKV-) are the operational records that Gate Core acts upon. |
| **Vehicle Management → Dispatch Plans** | `DispatchPlan.vehicle_id` → Vehicle master; `DispatchPlan.transporter_id` → Transporter master; `DispatchPlan.driver_id` → Driver master; `DispatchPlan.linked_vehicle_entry_id` → VehicleEntry (EVGI) created in this section. |
| **Vehicle Management → Barcode / Dispatch Sessions** | `SalesDispatch` (gate-out record) and `DispatchSession` (barcode scan session) both carry `vehicle_number` and `transporter_name` strings sourced from this section's masters. |
| **Vehicle Management → QC & GRPO** | Inbound GE- entries link to `ArrivalSlip.vehicle_entry_id` (Quality Control section); `GRPOEntry.vehicle_entry_id` closes the inbound material loop. |
| **Vehicle Management → Docking Admin** | `PartialScanRequest` and `ScanSkipRequest` both reference `SalesDispatch.entry_no` which is created from a DOCKV vehicle entry originated here. |
| **Vehicle Management → Dispatch section** | Dispatch's bilty-GRPO service entries use `linked_vehicle_entry_id` (DOCKV series) to post service invoices post-dispatch. |

**Data flow summary**: Vehicle master → Gate Entry (EVGI or GE) → [Dispatch pipeline OR QC pipeline] → Gate Out (DOCK or EVGO) → SAP posting.

---

## 6. Data presence for Jivo Mart

| Endpoint / Page | Count | Status | Notes |
|---|---|---|---|
| `/vehicle-management/vehicles/` | **340** | Live | 327 Trucks, 4 By Hand, 4 Car, 4 Eco Van, 1 Bike |
| `/vehicle-management/vehicles/names/` | **340** | Live | Lightweight view, same count |
| `/vehicle-management/transporters/` | **88** | Live | Mix of 3PL + Jivo's own fleet entries |
| `/vehicle-management/transporters/names/` | **88** | Live | Lightweight view |
| `/vehicle-management/vehicle-types/` | **7** | Live | Static reference, fully populated |
| `/driver-management/drivers/` | **296** | Live | Active drivers; most added per-dispatch |
| `/driver-management/drivers/names/` | **296** | Live | Lightweight view |
| `/vehicle-management/vehicle-entries/` (RAW_MATERIAL) | **5** | Live – sparse | All QC_PENDING; oldest 2026-05-02 |
| `/vehicle-management/vehicle-entries/` (all other types) | **0** | Empty | Dispatch entries tracked via gate-core instead |
| `/vehicle-management/vehicle-entries/count/` | Live | Live | Returns status breakdown; only RAW_MATERIAL yields data |
| `/vehicle-management/vehicle-entries/list-by-status/` | Live | Live | Same filter behavior as list endpoint |
| `/vehicle-management/dispatch-linking` | — | UI-only | No standalone API; assembles from dispatch-plans pipeline + gate-core EVGI |
| `/vehicle-management/entries` (UI) | — | Renders from vehicle-entries API | Gated by entry_type + date params |
| `gate-core empty-vehicle-ins` (EVGI series) | **36** | Live | All reason=DISPATCH; latest 2026-06-29 |
| `gate-core empty-vehicle-outs` (EVGO series) | **1** | Live – sparse | Only 1 record |
| `gate-core empty-vehicle-outs/eligible-entries` | **43** | Live | Mix of DOCKV + EVGI entries eligible for exit |

**Pages with no live data in JIVO_MART**: The `Courier` and `Cycle` vehicle types have zero registered vehicles. BST, Job Work, Rejected QC Return entry types have no vehicle entries. Empty Vehicle Gate Outs (EVGO) have only 1 historical record — the factory does not routinely create formal EVGO records; vehicles exit after DOCK sales-dispatch gate-out instead.

---

## Reference — UI routes (from bundle)
- `/vehicle-management`
- `/vehicle-management/dispatch-linking`
- `/vehicle-management/drivers`
- `/vehicle-management/entries`
- `/vehicle-management/transporters`
- `/vehicle-management/transporters/`
- `/vehicle-management/transporters/names/`
- `/vehicle-management/vehicle-entries/`
- `/vehicle-management/vehicle-entries/count/`
- `/vehicle-management/vehicle-entries/list-by-status/`
- `/vehicle-management/vehicle-types/`
- `/vehicle-management/vehicles`
- `/vehicle-management/vehicles/`
- `/vehicle-management/vehicles/names/`

## Reference — captured API endpoints + record counts (this section)
- `/driver-management/drivers/` -> 296 (list)
- `/driver-management/drivers/names/` -> 296 (list)
- `/vehicle-management/transporters/` -> 88 (list)
- `/vehicle-management/transporters/names/` -> 88 (list)
- `/vehicle-management/vehicle-types/` -> 7 (list)
- `/vehicle-management/vehicles/` -> 340 (list)
- `/vehicle-management/vehicles/names/` -> 340 (list)
- `/vehicle-management/vehicle-entries/?entry_type=RAW_MATERIAL&from_date=…&to_date=…` -> 5 (QC_PENDING)
- `/vehicle-management/vehicle-entries/count/?entry_type=RAW_MATERIAL&…` -> `{status:"QC_PENDING", count:5}`
- `/vehicle-management/vehicle-entries/?entry_type=<other_types>` -> 0 (empty for all other types)

Linked: [[docs/factory/FACTORY_MAP|FACTORY_MAP]] · [[docs/FACTORY_CLI_PLAN|FACTORY_CLI_PLAN]] · [[docs/READ_ONLY_LAW|READ_ONLY_LAW]]
