---
title: "DATA-MODEL — what the factory data means"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: reference
tags: [jivogpt, factory-cli, data-model]
---

# DATA-MODEL — what the factory data means

> **Provenance — imported 2026-07-19; source snapshot 2026-06-30.** This note came from the JIVO_MART-only `daman8271/jivo-factory-intel` baseline. For the current three-company study and the live-verified 2026-07-19 state, use [[docs/factory/FACTORY_MAP|FACTORY_MAP]] and [[CLI/factory-cli/README|the current CLI guide]].

The semantic foundation: Jivo Mart's business, the 46-entity catalog, the foreign-key graph, the SAP
item-code bridge, and the honest gaps. Read **[[CLI/factory-cli/VAULT-GUIDE|`VAULT-GUIDE.md`]]** for how to find
these things in the vault, and **[[CLI/factory-cli/ARCHITECTURE|`ARCHITECTURE.md`]]** for how they get there.

> Figures are **as of the 2026-07-01 refresh** (`render-proof.json`). Each refresh is a full-replace
> mirror, so use git history to move through time and date-stamp anything you report.

---

## 1. The business in a nutshell

**Jivo Mart** is the **retail / dispatch arm** of an edible-oil group. The `ji.jivo.in` app is a
factory-floor operating system and **SAP Business One (SAP-B1) companion**: it governs gate entry/exit,
inspects inbound material, posts goods receipts into SAP, tracks finished-goods inventory across ~31
warehouses, barcodes and traces every carton, and runs scan-to-ship dispatch — reading from and writing
back to SAP-B1 (item master OITM, GRPO, AR invoices, inventory transfers, production orders).

**One app, three sibling companies, one SAP system.** Every API call carries `Company-Code: JIVO_MART`
(a missing header → `403`). The three companies share one physical complex and one SAP-B1 (each its own
HANA schema):

| Company | Code | id | Role | In scope? |
|---|---|---|---|---|
| Jivo Oil | `JIVO_OIL` | 1 | the manufacturer | no |
| **Jivo Mart** | **`JIVO_MART`** | **2** | **retail / dispatch arm** | **yes — this repo** |
| Jivo Beverages | `JIVO_BEVERAGES` | 3 | beverages arm | no |

**Jivo Mart does NOT manufacture** — this one fact shapes the entire data-presence pattern. It
**receives finished, already-barcoded cartons from Jivo Oil via an intercompany barcode-transfer rail**,
holds them across the warehouses, then **scan-to-ship dispatches** them against SAP invoices. So the
inbound-logistics, inventory, labelling, barcode-traceability, and outbound-dispatch muscles are heavily
exercised, while in-house **Production (MES)** and **Maintenance (CMMS)** are built but **idle**, and the
inbound-receipt (QC → GRPO) chain is configured but stalled (0 GRPOs ever posted). Two surfaces are
deliberately **shared across all three companies** — vehicle **Arrivals** (the weighbridge log) and the
**intercompany barcode-transfer** rail (one truck's arrival note carries gate-ins/outs for all three).

The full per-page app study (13 sections, what every page does + the data behind it) lives in
**`app-model/`**.

---

## 2. The entity catalog

The **46 rendered entity types**, grouped by domain (first path segment), with real per-entity note
counts from `render-proof.json`. **16,938 record notes total.** `barcode__boxes` (8,500) +
`gate-core__sales-dispatch__documents` (1,236) + `barcode__scan__history` (1,100) are the largest
entities.

| Domain | Entity (slug) | Notes | Notes |
|---|---|---:|---|
| **accounts** (1) | `accounts__users` | 63 | app users |
| **barcode** (12) | `barcode__boxes` | **8,500** | the largest entity; carton master (prefix `box`) |
| | `barcode__scan__history` | **1,100** | scan events |
| | `barcode__items__oitm` | 420 | **the SAP item master** (prefix `oitm`) |
| | `barcode__pallets` | 592 | pallets (prefix `pal`) |
| | `barcode__dispatch__reports` | 57 | dispatch reports |
| | `barcode__dispatch__reports__boxes` | 1,000 | hard-capped at 1000 |
| | `barcode__dispatch__reports__pallets` | 592 | |
| | `barcode__dispatch__reports__rejected-scans` | 962 | |
| | `barcode__dispatch__sessions__active` | 55 | |
| | `barcode__dispatch__sessions__completed` | 2 | |
| | `barcode__print__history` | 16 | label print events |
| | `barcode__loose` | 7 | loose units |
| **gate-core** (8) | `gate-core__sales-dispatch__documents` | 1,236 | gap-busted from a 200-cap |
| | `gate-core__arrivals` | 139 | weighbridge log (prefix `arr`; cross-company) |
| | `gate-core__bst-outs__sap-transfers` | 50 | intercompany transfers |
| | `gate-core__empty-vehicle-outs__eligible-entries` | 48 | |
| | `gate-core__empty-vehicle-ins` | 41 | |
| | `gate-core__sales-dispatch` | 43 | |
| | `gate-core__empty-vehicle-ins__reasons` | 5 | enum |
| | `gate-core__empty-vehicle-outs` | 1 | |
| **vehicle-management** (3) | `vehicle-management__vehicles` | 346 | (prefix `veh`) |
| | `vehicle-management__transporters` | 89 | (prefix `trn`) |
| | `vehicle-management__vehicle-types` | 7 | enum (prefix `vty`) |
| **driver-management** (1) | `driver-management__drivers` | 303 | (prefix `drv`) |
| **person-gatein** (6) | `person-gatein__entries` | 211 | gap-captured domain |
| | `person-gatein__visitors` | 154 | (prefix `vis`) |
| | `person-gatein__labours` | 3 | |
| | `person-gatein__contractors` | 2 | |
| | `person-gatein__person-types` | 2 | enum (prefix `ptype`) |
| | `person-gatein__gates` | 1 | (prefix `pgate`) |
| **po** (2) | `po__vendors` | 212 | (prefix `ven`) |
| | `po__warehouses` | 31 | the ~31 warehouses (prefix `wh`) |
| **production-execution** (1) | `production-execution__sap__items` | 193 | gap-captured via search proxy |
| **quality-control** (3) | `quality-control__sap-items` | 193 | gap-captured via search proxy |
| | `quality-control__arrival-slips` | 8 | inbound slips (stuck `NOT_STARTED`) |
| | `quality-control__inspections` | 8 | |
| **notifications** (2) | `notifications` | 144 | |
| | `notifications__preferences` | 39 | |
| **docking-admin** (2) | `docking-admin__partial-scan-requests` | 26 | |
| | `docking-admin__scan-skip-requests` | 12 | |
| **grpo** (2) | `grpo__service__pending` | 8 | |
| | `grpo__all-entries` | 5 | |
| **company** (1) | `company__companies` | 3 | gap-captured (prefix `comp`) |
| **dispatch** (1) | `dispatch__bilty-grpo__pending` | 8 | |
| **daily-needs-gatein** (1) | `…__gate-entries__daily-need__categories` | 1 | enum |

---

## 3. Curated wikilink targets (TARGETS)

`render.py` holds a **`TARGETS`** dict — 14 slugs that get a fixed short prefix (instead of the full
slug) so cross-folder `[[prefix-key]]` wikilinks resolve cleanly. These are the join hubs of the graph:

| Raw slug | Prefix | Title | Key field | Count |
|---|---|---|---|---:|
| `vehicle-management__vehicles` | `veh` | Vehicle | `id` | 346 |
| `vehicle-management__vehicle-types` | `vty` | Vehicle Type | `id` | 7 |
| `vehicle-management__transporters` | `trn` | Transporter | `id` | 89 |
| `driver-management__drivers` | `drv` | Driver | `id` | 303 |
| `gate-core__arrivals` | `arr` | Gate Arrival | `id` | 139 |
| `barcode__pallets` | `pal` | Pallet | `id` | 592 |
| `barcode__boxes` | `box` | Barcode Box | `id` | 8,500 |
| `barcode__items__oitm` | `oitm` | SAP Item (OITM) | `item_code` | 420 |
| `po__vendors` | `ven` | Vendor | `vendor_code` | 212 |
| `po__warehouses` | `wh` | Warehouse | `warehouse_code` | 31 |
| `company__companies` | `comp` | Company | `id` | 3 |
| `person-gatein__person-types` | `ptype` | Person Type | `id` | 2 |
| `person-gatein__visitors` | `vis` | Visitor | `id` | 154 |
| `person-gatein__gates` | `pgate` | Gate | `id` | 1 |

Every other (non-target) entity uses its **full slug as the note prefix** (e.g.
`barcode__dispatch__reports__boxes-1000`), with keyfield = `id` if present, else the first field.

---

## 4. The foreign-key graph

`render.py` holds an **`FK`** map (field name → target prefix). A `## Related` wikilink is emitted only
when a record's field name is in this map **and** the resolved id exists in that target's registry
(built in render PASS 1). `fk_value()` accepts a scalar **or** a nested `{id|pk|code|value: …}` dict:

```
vehicle, vehicle_id                         → veh     (Vehicle)
vehicle_type, vehicle_type_id               → vty     (Vehicle Type)
transporter, transporter_id                 → trn     (Transporter)
driver, driver_id                           → drv     (Driver)
arrival, arrival_id                         → arr     (Gate Arrival)
pallet, pallet_id, source_pallet_id         → pal     (Pallet)
box, box_id                                 → box     (Barcode Box)
vendor, vendor_code                         → ven     (Vendor)
warehouse, warehouse_code                   → wh      (Warehouse)
company, company_id                         → comp    (Company)
person_type                                 → ptype   (Person Type)
visitor                                     → vis     (Visitor)
gate, gate_in, gate_out                     → pgate   (Gate)
```

This is what turns 16,938 isolated records into a navigable graph: a box links to its `oitm` item and
`pal` pallet; an arrival links to its `drv` driver and `veh` vehicle; and so on.

---

## 5. The SAP item-code bridge

This is the seam that connects the factory to the rest of the data bank.

- **`SAP_FIELDS = {item_code, material_code, sku_code, component_code, po_item_code}`.** For each
  record, every value found in those fields is collected.
- If the code exists in the **`oitm`** registry, a `- item -> [[oitm-<code>]]` wikilink is added to
  `## Related`.
- **If the code matches `^FG\d+$`** (a finished good), the note gets a tag `bridge/<code>` **and** the
  mapping `code → {slug}/{noteid}` is recorded in **`bridge_links`**.
- `bridge_links` is written to **`vault/_bridge.json`** as
  `{ "FG0000004": ["barcode__boxes/box-112501", …], … }` — **421 distinct FG codes, 10,695 references.**
- **FG-only by design.** Only `^FG\d+$` codes enter `_bridge.json`; **PM** (packaging) and **RM**
  (raw-material) codes do not — though they still get an `[[oitm-…]]` link if the oitm registry has them.
- **Downstream:** the data-bank's `factory_pillar.py` reads `_bridge.json` and appends a `## Factory
  lens` to each **product node** whose `FG####` appears in its frontmatter `sap_codes`. That is the
  fusion seam — the bridge lives on the *product* nodes, not on the factory notes (see § 8).

---

## 6. The note-id scheme & frontmatter

**Note id / filename / wikilink target** = `f"{prefix}-{slugify(keyvalue)}"` — e.g. `arr-1`,
`box-100226`, `oitm-FG0000030`, or `barcode__dispatch__reports__boxes-1000` for non-target entities.

- `slugify()` maps any non-`[A-Za-z0-9_-]` char → `-`, strips, and truncates to **80 chars**.
- **Dedup:** within an entity, a repeated key gets `-2`, `-3`, … appended (a `used` set), so note ids
  are unique and lossless.

The **real frontmatter schema** (from `render.py` — **not** the `vault-schema.md` version):

```yaml
---
type: factory-<prefix>          # e.g. factory-box, factory-arr, factory-oitm
id: <keyvalue>
title: "<derived title>"        # title_of(): name/title/item_name/vehicle_number/entry_no/… else "<Title> <id>"
entity: <human title>           # e.g. "Barcode Box", "Gate Arrival"
source_endpoint: <ep>           # e.g. /barcode/boxes/
company: JIVO_MART
tags:
  - type/factory-<prefix>
  - source/factory
  - company/JIVO_MART
  - bridge/<FG####>             # ONLY if the record carries an FG item code
---
```

Body: `# <title>` → a one-line blockquote provenance → `## Fields` (lossless dump — scalars as
`- **field:** value`, non-scalars as a fenced ```json block) → `## Related` (sorted unique wikilinks).

---

## 7. What's NOT modeled

Honest about the limits:

- **The 49 `object`-kind endpoints are captured but NOT rendered as notes.** Of 152 endpoints, 49 are
  single-object responses — dashboards, summaries, options, WMS overviews (`/warehouse/wms/*`), SAP
  plan-dashboards, production analytics, intercompany dashboard, sales-dispatch lock, inventory-age
  report — and live **only** in `raw/*.json`. The raw JSON is retained (no data lost), but they have no
  vault notes and no entity folder.
- **The 59 empty modules** returned `count:0` (no notes, only a `_HOME.md` mention). They are dormant
  **because Jivo Mart doesn't manufacture** — it's the dispatch arm. They group as:
  - **Production (MES)** — lines, machines, runs, sap/orders, waste, line-clearance, checklist
    templates, costs/analytics. *Jivo Oil manufactures, not Jivo Mart.*
  - **Maintenance (CMMS)** — assets (+ categories/departments/locations/documents/photos), work-orders,
    pm-plans/-executions/-checklist-items, spares (+ categories/movements/requests), vendor-visits.
    *Schema-complete, zero master data entered.*
  - **Inbound QC chain stalled** — all inspection status views (awaiting-chemist/-qam, completed, draft,
    rejected, return-to-vendor), material-types, print-documents, production-qc(+pending). *(0 GRPOs
    ever posted; 8 arrival slips stuck `NOT_STARTED`.)*
  - **Gate inbound sub-flows unused** — bst-ins(+eligible), bst-returns(+eligible),
    job-work(+sap-grpos/sap-production-orders), rejected-qc-returns, sales-dispatch/pending-bookings,
    barcode/dispatch/sessions/closed.
  - **Dispatch accounting tail not yet posted** — bilty-grpo/history, open-bilties,
    transporter-invoices/history.
  - **WMS write-side stubs** — warehouse/bom-requests, warehouse/fg-receipts (no in-house production to
    feed them).
- **The bridge is FG-only.** PM/RM SAP codes are not recorded in `_bridge.json` (§5), so the
  factory→product join is finished-goods-only by design.

> One-line synthesis: Jivo Mart runs the app as a **finished-goods receiving-and-dispatch hub**;
> manufacturing, maintenance, inbound-QC and GRPO-posting are present but dormant.

---

## 8. Cross-repo — how factory bridges to the data bank

This repo is the **4th pillar** of the JIVO data bank. The data-bank repo's `factory_pillar.py` (in
`/root/jivo-data-bank/bin/`, run by the event-driven data-bank chain after the noon upstream jobs) does
the fusion:

1. **`copytree(vault/ → combined-vault/factory/)`** — **verbatim**, an exact byte match (the bridge
   lives on product nodes, not factory notes), with a per-file sha256 zero-loss proof merged into the
   combined manifest.
2. **Builds the SAP bridge:** reads `factory/_bridge.json`, and for every `products/*.md` whose
   frontmatter `sap_codes` contains an `FG####` present in the bridge, appends a **`## Factory lens`**
   listing where that code shows up in factory (`[[oitm-FG…]]` first, then box/dispatch notes, sampled,
   with "… +N more (tag `bridge/FG…`)"). Idempotent.
3. Appends a `## Factory pillar` pointer to `Home.md`, then runs the **fail-closed** verify (exits
   nonzero unless `prefix_ok AND zero_loss_ok`).

So the data bank gives each product **three lenses** — competitor-price (`ecom/`), JIVO-volume
(`jivo/`), and **factory** (this repo) — joined by the SAP code `FG####`.

---

## 9. Provenance & deeper reading

- **In this repo:** **[[CLI/factory-cli/app-model/README|`app-model/`]]** — the 13-section whole-app study (what every page
  does + the data behind it); **`render-proof.json`** — the per-entity counts + bridge totals;
  **`raw/`** — the lossless raw JSON (including the unrendered `object` endpoints); **`research/`** —
  `API-FACTS.md`, `get200.txt` (152 verified endpoints), `domain-schemas.json`;
  **[[CLI/factory-cli/PLAN|`PLAN.md`]]** and **[[CLI/factory-cli/REFRESH-RUNBOOK|`REFRESH-RUNBOOK.md`]]** (the plan + operations).
- **The CLI:** `jivo-factory-pp-cli` (read-only; source `/root/printing-press/library/jivo-factory`;
  spec `spec.yaml`).
- **The sibling source repos:** `daman8271/jivo-intel` (the `ecom.jivo.in` app vault → `jivo/`) and
  `daman8271/ecom-intel` (the competitor-price scraper → `ecom/`); both fuse with this pillar in
  `daman8271/jivo-data-bank`.

> ⚠️ Do **not** treat `vault-schema.md` as a description of the shipped vault — it is an aspirational
> design (pretty domain folders, dozens of entities) that `render.py` never built. The authority on
> what the vault *is* is `render.py` + `render-proof.json` + this document.

Linked: [[docs/factory/FACTORY_MAP|FACTORY_MAP]] · [[docs/FACTORY_CLI_PLAN|FACTORY_CLI_PLAN]] · [[docs/READ_ONLY_LAW|READ_ONLY_LAW]]
