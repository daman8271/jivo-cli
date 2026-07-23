---
title: "Jivo Mart Factory App — Whole-App Model"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: reference
tags: [jivogpt, factory-cli, app-model]
---

# Jivo Mart Factory App — Whole-App Model

> **Provenance — imported 2026-07-19; source snapshot 2026-06-30.** This note came from the JIVO_MART-only `daman8271/jivo-factory-intel` baseline. For the current three-company study and the live-verified 2026-07-19 state, use [[docs/factory/FACTORY_MAP|FACTORY_MAP]] and [[CLI/factory-cli/README|the current CLI guide]].
> Synthesis of the 13 section studies. Tenant in scope: **Jivo Mart (JIVO_MART)** only. Live-verified 2026-06-30 against `factory.jivo.in/api/v1`.

---

## 1. What the app IS

`factory.jivo.in` is a **factory-floor operating system and SAP Business One (SAP-B1) companion**. It is the digital control tower that wraps a physical edible-oil plant: it governs who and what enters/leaves the gate, inspects inbound material, posts goods receipts into SAP, tracks finished-goods inventory across 31 warehouses, labels and traces every carton, and runs the scan-to-ship dispatch of trucks — all while reading from and writing back to a SAP-B1 ERP (item master, GRPO, AR invoices, inventory transfers, production orders).

It is **multi-tenant across three sibling companies** that share one SAP system and one physical complex:
- **Jivo Oil** (`JIVO_OIL`) — the manufacturer (out of scope here)
- **Jivo Beverages** (`JIVO_BEVERAGES`) — beverages arm (out of scope here)
- **Jivo Mart** (`JIVO_MART`) — **the retail / dispatch arm, the subject of this model**

Every API call is scoped by a `Company-Code: JIVO_MART` header. A few surfaces are deliberately shared across all three tenants (notably the cross-company **vehicle Arrivals** weighbridge log and the **intercompany barcode transfer** rail), but everything else in this document is Jivo Mart's slice.

The critical fact that shapes everything below: **Jivo Mart does not really manufacture.** It receives finished, already-barcoded cartons from Jivo Oil via an intercompany transfer rail, holds them in warehouses, and dispatches them to customers. So the app's *inbound-logistics, inventory, labelling, and outbound-dispatch* muscles are heavily exercised, while its *production (MES) and maintenance (CMMS)* muscles are built but idle.

The app is organized into **13 sections**, mapped to physical factory stages plus three cross-cutting layers (Admin, Dashboards, Notifications).

---

## 2. The physical factory flow (end-to-end)

The 13 sections line up along the path a vehicle and its goods take through the plant. There are two main material directions — **inbound** (supplier/intercompany goods coming in) and **outbound** (finished goods shipping out) — bridged by the warehouse.

```
            ┌──────────────────────────── CROSS-CUTTING LAYERS ────────────────────────────┐
            │  ADMIN (users, permissions, scan-exception approvals)                         │
            │  DASHBOARDS (stock, dispatch pipeline, inventory age, SAP plan)               │
            │  NOTIFICATIONS (39 event types → in-app inbox + FCM push)                     │
            └───────────────────────────────────────────────────────────────────────────────┘

  ════════════════════════════ INBOUND (raw / packaging material) ════════════════════════════
   Supplier truck arrives
        │
   [GATE]  ARV- arrival (weighbridge tare) ──► GE- raw-material gate-in
        │      (Vehicle Management supplies the vehicle/driver/transporter identity)
        ▼
   [QUALITY CONTROL]  Arrival slip per PO line → chemist → QA manager → PASS/FAIL
        │
        ▼
   [GRPO]  material GRPO posted to SAP (PO → goods receipt; warehouse BH-JM, AP to vendor)
        │
        ▼
   [WAREHOUSE / WMS]  stock booked into SAP inventory

  ════════════════════════════ THE TWILIGHT OF "PRODUCTION" ══════════════════════════════════
   [PRODUCTION (MES)]  — for Jivo Mart this stage is NOT run in-house.
        Finished goods are manufactured by JIVO_OIL and handed over via the
        intercompany BARCODE rail (see below). MES exists but is unconfigured.

  ════════════════════════════ OUTBOUND (finished goods) ═════════════════════════════════════
   [BARCODE]  JIVO_OIL → JIVO_MART intercompany transfer (boxes BOX-…, pallets PLT-… become Mart stock)
        │      every carton tracked CREATE → PALLETIZE → (TRANSFER) → DISPATCH
        ▼
   [WAREHOUSE / WMS]  stock sits in BH-PF/BH-FGM, then SAP inventory transfers relay it
        │              to regional warehouses (BH-FGM→DL-INT→DL-FG, DL-MP→DL-EC, …)
        ▼
   SAP AR invoice created
        │
   [DISPATCH]  DispatchPlan BOOKED → empty truck called in
        │
   [GATE]  EVGI- empty-vehicle gate-in (Vehicle Management identifies the truck)
        │
   [DISPATCH / BARCODE]  DOCKV- docking session → scan-to-ship every box against the invoice
        │                 → truck photo → weighment → QR gatepass (DCK/JIVO_MART/2026-27/…)
        ▼
   [GATE]  DOCK- sales-dispatch gate-out committed → truck DEPARTS
        │
   [DISPATCH / GRPO]  post-dispatch accounting: bilty-GRPO (freight service GRPO) → transporter AP invoice
```

**Stage → section map:**

| Physical stage | Owning section(s) | Key entity / prefix |
|---|---|---|
| Vehicle/driver/transporter identity (pre-gate master data) | **Vehicle Management** | Vehicle (340), Driver (296), Transporter (88) |
| Vehicle arrives at gate; weighment; person access | **Gate** | Arrival `ARV-`, Person entry, weighbridge tare |
| Inbound material gate-in | **Gate** | RM gate entry `GE-YYYY-NNNN` |
| Inspect inbound material | **Quality Control** | ArrivalSlip → Inspection |
| Post SAP goods receipt | **GRPO** (material) | GRPOEntry → SAP GRPO doc |
| Hold/visibility of stock | **Warehouse** + **WMS** | SAP OITM/OINM, 31 warehouses |
| Manufacture goods | **Production** (MES) | *(idle for Mart; done by Jivo Oil)* |
| Receive finished cartons; label & trace | **Barcode** | Box `BOX-`, Pallet `PLT-`, Transfer `ICBT-` |
| Plan & execute outbound dispatch | **Dispatch** | DispatchPlan, SalesDispatch `DOCK-` |
| Empty-truck gate-in / loaded gate-out | **Gate** | `EVGI-`, `DOCKV-`, `DOCK-` |
| Post-dispatch freight accounting | **Dispatch** + **GRPO** (service) | bilty-GRPO, transporter AP invoice |
| Access control + scan-exception sign-off | **Admin** | users/permissions, partial-scan & scan-skip approvals |
| Cross-module intelligence | **Dashboards** | 8 read-only dashboards |
| Event alerting | **Notifications** | 39 event types, FCM push |

---

## 3. The 13 sections at a glance

| # | Section | Purpose | Key data / entities | Jivo Mart data state |
|---|---|---|---|---|
| 01 | **Admin** | User/permission management + docking scan-exception approval queues | 62 users, 6 departments, 871 permission strings; partial-scan (21) & scan-skip (12) approvals | **Data-rich** (access + active approval queues) |
| 02 | **Dashboards** | Cross-module read-only intelligence (8 dashboards) | Stock levels (43,575 rows), dispatch pipeline, inventory age (602 FG rows), SAP plan, production movement | **Mostly data-rich**; sales-planning + some configs empty |
| 03 | **Dispatch** | Outbound freight control: vehicle-linking, docking/gatepass, bilty-GRPO, transporter invoices | DispatchPlan (19), SalesDispatch `DOCK-` (38), bilty-GRPO pending (6) | **Data-rich upstream**; accounting tail (bilty/AP) not yet posted |
| 04 | **Gate** | Physical security/logistics control: arrivals, inbound gate-ins, FG gate-out, person access | Arrivals (117), EVGI (36), DOCK (38), persons (206), visitors (149) | **Data-rich** for dispatch + persons; most inbound sub-types empty |
| 05 | **Vehicle Management** | Master registry of vehicles/drivers/transporters + entry log | Vehicles (340), Drivers (296), Transporters (88), Types (7) | **Data-rich** (masters); only RAW_MATERIAL entry type active |
| 06 | **Quality Control** | Inbound material inspection (arrival slips) + production QC | 8 arrival slips (all packaging, all NOT_STARTED) | **Barely used** — inbound stuck in QC limbo; production QC empty |
| 07 | **GRPO** | SAP goods-receipt posting: material (inbound) + service (freight) | Material entries (5, all QC_PENDING), service pending (6) | **Barely used** — 0 GRPOs posted (material or service) |
| 08 | **Production** | MES: planning + execution (runs, OEE, breakdowns, waste) | 1 historical SAP order; production-movement report (live) | **Largely empty** — 0 lines/runs; only SAP-side reports populated |
| 09 | **Maintenance** | CMMS: assets, work orders, PM plans, spares, vendor visits | Full enum schema + 43 users; everything else 0 | **Empty** — schema-complete, zero master data entered |
| 10 | **Warehouse** | Finished-goods WMS: dashboard, stock, billing, transfers, FG receipts, BOM | 268 SKUs, ₹9.96 cr, 953 stock rows, 757 billing items | **Data-rich** (read side); FG receipts + BOM requests empty |
| 11 | **WMS** | Same backend as Warehouse — inventory control tower over 31 warehouses | Dashboard, stock overview, batch expiry (300), SO backlog (86) | **Data-rich**; batch-expiry dates blank, min-stock benchmarks all 0 |
| 12 | **Barcode** | FG track-and-trace + scan-to-ship + intercompany transfer | Boxes (27,206), Pallets (583), Scans (15,031), IC transfers (1,017) | **Most data-rich section in the app** |
| 13 | **Notifications** | Event alert backbone (in-app inbox + FCM push) | 39 event types; inbox (135, all gate person-entry) | **Data-rich infra**; this account sees only gate events |

> **Note — Warehouse vs WMS:** sections 10 and 11 are two documents over **one backend** (`/warehouse/wms/*`). "Warehouse" also covers the write-side stubs (`/warehouse/fg-receipts/`, `/warehouse/bom-requests/`, `/warehouse/stock/check/`); "WMS" is the read-side inventory cockpit. They report the same headline numbers (268 SKUs, ₹9.96 cr, 31 warehouses, 953 stock rows).

---

## 4. Cross-section data-flow graph

The sections hand off to each other along a small number of **shared keys**. The integer `DispatchPlan.plan_id`, the SAP `doc_num`/`doc_entry`, and the family of `entry_no` prefixes are the joins that stitch the whole app together.

```
                       ┌──────────────────┐
                       │ VEHICLE MGMT      │  vehicles / drivers / transporters (masters)
                       └───────┬───────────┘
                               │  supplies identity FKs to every gate event
                               ▼
   (inbound)   ┌──────────┐  GE-   ┌──────────────┐ accepted ┌────────┐ SAP GRPO ┌──────────────┐
   supplier ──►│  GATE    ├───────►│ QUALITY      ├─────────►│ GRPO   ├─────────►│ WAREHOUSE /  │
              │ (RM in)   │ slips  │ CONTROL      │          │(material)│         │ WMS (BH-JM)  │
               └──────────┘        └──────────────┘          └────────┘          └──────────────┘

   (intake)    ┌──────────────────────────────┐  ICBT- (box ownership → JIVO_MART)
   JIVO_OIL ──►│ BARCODE  intercompany xfer    ├───────────────────────────┐
               └──────────────────────────────┘                            ▼
                                                                  ┌──────────────┐ SAP inventory
                                                                  │ WAREHOUSE /  │ transfers (type 67)
                                                                  │ WMS          │ BH-FGM→DL-INT→DL-FG …
                                                                  └──────┬───────┘
                                                                         │ SAP AR invoice created
                                                                         ▼
   (outbound)  ┌──────────────┐ plan_id ┌──────────────┐ DOCKV  ┌──────────────┐ DOCK- ┌──────────┐
   AR invoice ►│  DISPATCH    ├────────►│ BARCODE      ├───────►│ DISPATCH     ├──────►│  GATE    ├─► truck
              │ DispatchPlan │ scan     │ dispatch     │ scan   │ gatepass +   │ gate  │ gate-out │   leaves
              │ (BOOKED)     │ session  │ session      │ verify │ weighment    │ -out  │ (DOCK-)  │
               └──────┬───────┘         └──────────────┘        └──────┬───────┘       └──────────┘
                      │ EVGI- (empty truck in, via Gate + Vehicle Mgmt)│
                      │                                                ▼  post-dispatch
                      │                                        ┌──────────────┐ SAP service GRPO
                      └───────────────────────────────────────►│ GRPO (service)│ + transporter AP invoice
                                                                └──────────────┘

   ADMIN ─── approves partial-scan / scan-skip exceptions raised during BARCODE docking scan
   DASHBOARDS ─── reads from Gate, WMS, Dispatch, Production, GRPO (no writes)
   NOTIFICATIONS ─── observes every section's state changes; routes user back via click_action_url
```

**The load-bearing joins:**

| Bridge key | Connects | Example |
|---|---|---|
| `DispatchPlan.plan_id` | Dispatch pipeline ⇄ Barcode dispatch session ⇄ Gate `DOCK-` ⇄ GRPO service entry | plan 690 = `DOCK-20260629-0022` = invoice 706260665 |
| SAP `doc_num` / `doc_entry` | Everything ⇄ SAP-B1 | AR invoice `706260665`; PO `426224589`; transfer `626674697` |
| `entry_no` prefix family | Gate ⇄ Vehicle Mgmt ⇄ QC ⇄ GRPO ⇄ Dispatch | `ARV-`, `EVGI-`, `EVGO-`, `DOCKV-`, `DOCK-`, `GE-` |
| `box_barcode` / `pallet_id` | Barcode ⇄ Warehouse ⇄ Dispatch scan ⇄ intercompany trace | `BOX-20260610-XX-5228`, `PLT-20260629-XX-096` |
| `ICBT-` transfer number | Barcode ⇄ Jivo Oil (cross-company) | `ICBT-20260629191556184924` |
| `vehicle_entry_id` | Gate `GE-` ⇄ QC ArrivalSlip ⇄ GRPO material entry | VE 466 = `GE-2026-8750` |
| item code prefix | Every section ⇄ SAP OITM | `FG…` finished, `PM…` packaging, `RM…` raw |
| warehouse code | WMS ⇄ Barcode ⇄ Gate ⇄ GRPO ⇄ Production | `BH-FGM`, `DL-MP`, `BH-JM`, `DL-EC` |
| `User.id` (Admin) | identity backbone for every audit field | `created_by`, `requested_by`, `reviewed_by`, `scanned_by` |

The **Arrivals** (`ARV-`) record is the one shared multi-tenant artifact: a single physical truck can carry gate-ins and gate-outs for JIVO_MART, JIVO_OIL, and JIVO_BEVERAGES under one arrival number.

---

## 5. The SAP-B1 integration story

The app is, at its core, a **floor-level front-end and workflow engine bolted onto SAP Business One**. SAP holds the books of record (item master, inventory, accounting documents); the factory app captures the physical reality (who scanned what, which truck, which weighment) and posts the resulting documents back into SAP.

**SAP objects the app reads and writes:**

| SAP-B1 object | Role in the app | Where it surfaces |
|---|---|---|
| **OITM** (item master) | Authoritative FG/PM/RM catalogue; batch-management flags | `/barcode/items/oitm/` (group 102, `manage_batch_numbers=true`); item codes everywhere |
| **OINM** (inventory movement ledger) | Source for live + historical stock | WMS stock, `/dashboards/stock/as-of/` (point-in-time reconstruction) |
| **GRPO** (Goods Receipt PO) | Inbound material receipt **and** outbound freight service receipt | GRPO section (material → warehouse + AP; service → freight expense) |
| **AR Invoice / Delivery** (tx types 13/15) | Outbound sales documents that drive dispatch | Dispatch (`sap_doc_num`), barcode dispatch sessions, WMS `AR_INVOICE` movements |
| **Inventory Transfer** (tx type 67) | Inter-warehouse stock relays + BST source docs | WMS transfers (chained doc pairs); Gate BST (50 eligible SAP docs) |
| **Production Order** | Plan/component-shortfall view | `/sap/plan-dashboard/` (1 historical order for Mart) |
| **AP Invoice** (tx type 18) | Transporter freight billing | Dispatch transporter-invoices (not yet posted) |
| **GL accounts / tax codes / branches** | Posting configuration | `/grpo/service/options/`, `/dispatch/bilty-grpo/options/` (8 branches, 24 tax codes, ~400–992 GL accounts) |
| **Vendor (VENDA-) / Customer (CUSTA-)** masters | Party identity on receipts/invoices | GRPO suppliers, WMS sales-order backlog |

**Document-number model:** SAP exposes every document with two ids — `doc_entry` (internal numeric primary key, e.g. `5041`) and `doc_num` (the human-facing number printed on paperwork, e.g. PO `426224589`, invoice `706260665`). The app consistently carries both, using `doc_entry` for linkage and `doc_num` for display. Posting a GRPO returns a fresh `sap_doc_num` that the app stores back on its own record.

**Intercompany model:** Jivo Oil, Jivo Mart, and Jivo Beverages are distinct SAP company databases (each with its own HANA schema, e.g. `JIVO_MART_HANADB`). Finished goods move between them as **intercompany barcode transfers** — Jivo Oil scans boxes out, they appear in Jivo Mart's inventory with full cross-company trace (`MANUFACTURED@JIVO_OIL → SCANNED → TRANSFER_COMPLETED@JIVO_MART`). The GL/customer masters even carry per-state intercompany accounts (`JIVO MART PVT LTD - DL/HR/PB/KT/RJ/UP`).

**Important integration gaps for Jivo Mart (where the app runs ahead of SAP write-back):**
- **Barcode dispatch SAP sync is `NOT_CONFIGURED`** — scan-to-ship sessions complete *internally* without writing the delivery back to SAP-B1. The app records the physical dispatch; SAP reconciliation happens by another path.
- **Intercompany transfers** carry `sap_enabled: false` — the box ownership change is tracked in-app, not mirrored as a SAP transfer.
- **No material GRPO has ever been posted** (5 entries stuck in QC); **no service GRPO posted** (6 pending) — the SAP write step at the end of both inbound and freight chains is queued but unexercised.
- **`production-release-oil`** points at a HANA table (`PRODUCTION_RELEASE_OIL`) that doesn't exist in the Mart schema — broken for this tenant.
- The **Sales-Planning-vs-Requirement** dashboard's SAP HANA stored procedure explicitly supports only `JIVO_OIL` and `JIVO_BEVERAGES` — never runs for Mart.

---

## 6. What Jivo Mart actually uses heavily vs barely

Jivo Mart is the **retail / dispatch arm**, not a manufacturer. That single fact predicts the entire data-presence pattern: the **outbound-logistics spine is fully alive**, while **in-house production and plant-maintenance are dormant**, and the **inbound-receipt chain is configured but stalled**.

### Heavily used (live, high-volume operational data)

- **Barcode** — the busiest section in the app: **27,206 boxes**, **583 pallets**, **15,031 scan events**, **57 dispatch sessions**, **1,017 intercompany transfers** (994 from Jivo Oil = 353,790 PCS — this is Mart's *de facto* "production intake").
- **Gate (outbound + persons)** — **38 `DOCK-` dispatches** (35 departed), **117 arrivals**, **36 `EVGI-` empty-vehicle gate-ins**, **206 person entries / 149 visitors**. The FG gate-out workflow is the daily heartbeat.
- **Vehicle Management** — **340 vehicles, 296 drivers, 88 transporters** continuously referenced by every gate and dispatch event.
- **Dispatch** — **19 plans**, **38 docking entries**, **6 bilty-GRPO** in flight; the pipeline cycles fully on dispatch days.
- **Warehouse / WMS (read side)** — **268 SKUs / ₹9.96 cr** on hand, **953 stock-overview rows**, **757 billing-reconciliation items** (₹236 cr received cumulative), **86 open sales orders**, **14 active inter-warehouse transfers**. Rich, live, daily.
- **Dashboards** — stock levels (43,575 rows), dispatch pipeline, inventory age all render live.
- **Admin** — **62 users**, and the **scan-exception approval queues** are a routine daily step (33 approvals, all signed off by one reviewer, EP000) because Mart is migrating old pre-barcode stock.
- **Notifications** — live infra (135 inbox records, FCM push), though this account sees only gate person-entry events.

### Barely used / unconfigured (built but idle for Jivo Mart)

- **Production (MES)** — **0 lines, 0 machines, 0 runs, 0 breakdowns, 0 waste**. Only the SAP-side `plan-dashboard` (1 old order) and the `production-movement` report (SAP OINM mirror) have data. *Manufacturing is Jivo Oil's job; Mart doesn't run the floor.*
- **Maintenance (CMMS)** — **fully schema-complete but entirely empty**: 0 assets, 0 work orders, 0 PM plans, 0 spares, 0 vendor visits. Only the options enum + 43-user list return data. Awaiting first onboarding.
- **Quality Control** — **8 packaging-material arrival slips, all stuck NOT_STARTED since May 2026**; production QC, material-type masters, and parameter library all empty. The chemist workflow is effectively unexercised.
- **GRPO (both flows)** — **0 documents posted**. 5 material entries blocked at QC, 6 service entries awaiting bilty. The end-of-chain SAP posting step is queued but never completed.
- **WMS operational/config gaps** — `fg-receipts` and `bom-requests` empty (no in-house production to feed them); **batch-expiry dates blank on all 300 batches**; **min-stock benchmarks are 0 for all 43,575 items** (so every stock health flag reads "none"); inventory-age `effective_date` pinned to a single seed date.
- **Gate inbound sub-flows** — BST, job-work, rejected-materials, customer-returns, repair-parts, construction, fixed-assets, daily-needs and maintenance gate-ins are all **0** (several have no server endpoint at all). Only raw-material gate-in (via the QC/GRPO `GE-` path) and person access are live.

### One-line synthesis of the pattern

> Jivo Mart runs the app as a **finished-goods receiving-and-dispatch hub**: cartons arrive pre-made and pre-barcoded from Jivo Oil over the intercompany rail, get held and relayed across 31 warehouses, then scanned onto trucks and gated out against SAP invoices. The manufacturing, maintenance, inbound-QC, and GRPO-posting modules are present and schema-complete but largely dormant — because, for this tenant, those activities happen elsewhere (Jivo Oil) or simply haven't been switched on yet.

Linked: [[docs/factory/FACTORY_MAP|FACTORY_MAP]] · [[docs/FACTORY_CLI_PLAN|FACTORY_CLI_PLAN]] · [[docs/READ_ONLY_LAW|READ_ONLY_LAW]]
