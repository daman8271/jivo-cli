---
title: EXIM to Factory Connection
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: connection
tags: [jivogpt, connection, exim, factory, sap, read-only]
---

# EXIM to Factory Connection

## Connection verdict

**Observed exact PO-level bridge, governance-gated; no stock-lot-to-Factory foreign key.** A live read-only audit on 2026-07-19 found 10 distinct EXIM business PO numbers across 11 lines in Factory Oil's GRPO pipeline. All 11 lines agreed exactly on vendor code/name, SAP item code/name, and UOM; three sampled previews also agreed on PO date. Factory preview resolved those business PO numbers to PO `DocEntry` and `LineNum`. This is real record-level evidence, not merely business adjacency.

The biggest blocker is company identity. EXIM is scoped to **Jivo Wellness**. Factory operational data is selected by `Company-Code` and separated into `JIVO_OIL`, `JIVO_MART`, and `JIVO_BEVERAGES` HANA schemas. There is **no proven mapping from EXIM's Jivo Wellness scope to Factory `JIVO_OIL`**. Label similarity, shared warehouses, or an `OIL` category cannot establish that mapping.

Use two separate statuses:

```text
source-local PO bridge evidence = OBSERVED_EXACT
enterprise release eligibility = BLOCKED_COMPANY_ALIAS_UNAPPROVED
```

## Why they connect

The two systems cover adjacent stages of the inbound-to-production chain:

- EXIM follows imported or contracted raw material through supplier, location, ETA, arrival, bilty, and optional GRPO number.
- Factory follows a gate entry through QC, material GRPO, SAP warehouse receipt, production consumption, finished-goods receipt, WMS, and dispatch.
- Both expose SAP-looking item, supplier, warehouse, PO, GRPO, and date fields. The PO/vendor/item/UOM bridge is now live-profiled; company equivalence, tank-grade identity, lot/batch continuity, and customs-to-dispatch continuity remain unresolved.

## Evidence from system A

System A is EXIM. As of 2026-07-19, EXIM has **65 printed CLI tools**. The read table in [[API-INVENTORY]] contains 67 rows, but duplicates `GET /dc/`; it therefore represents **66 unique read-labelled routes**, not 67 unique routes.

`GET /sap_sync/open-grpos/` is an unresolved exception: [[sap_sync_open-grpos]] shows real GRPO rows, but the route sits in the sync namespace, requires `open_grpos:[sync]`, and may refresh SAP as a side effect. It is a **GET-that-may-refresh conflict and is excluded from every safe recipe and validation run** in this note.

Relevant proven EXIM fields include:

- `item_code`, `item_name`, `vendor_code`, `vendor_name`, `arrival_date`, `bility_number`, and nullable `grpo_number` on import stock rows in [[CLI/exim/endpoints/stock-status|stock-status]].
- SAP-synced `item_code` and `item_name` on the RM and FG masters in [[items_rm]] and [[items_fg]].
- `PO_NUMBER`, `VENDOR_CODE`, `ItemCode`, `ITEM_NAME`, `WAREHOUSE`, `PO_DATE`, and `DUE_DATE` on [[sap-sync_open-pos]].
- Warehouse/category inventory aggregates on [[sap-sync_inventory]] and [[sap-sync_finished-inventory]].

The live audit measured:

- 18 EXIM open-PO rows / 17 distinct PO numbers;
- 10 distinct PO overlaps / 11 overlapping EXIM lines;
- 7 EXIM PO numbers unmatched in the current Factory Oil snapshot;
- 131/137 EXIM party codes present in Factory Oil, with 131/131 exact names;
- 6/7 EXIM warehouse codes present in Factory Oil;
- 91 stock-status rows using 27 distinct local material-grade codes;
- **0/27** stock-grade-code overlap with the 23-code EXIM SAP RM master.

EXIM stock/tank grades such as `RM00CN` and SAP RM items such as `RM0000003`
are different namespaces. The direct EXIM-local edge is
`stock-status.id = tank item-wise-average.breakdown[].stock_id`; the reviewed
`material_grade_to_sap_item` bridge does not yet exist.

## Evidence from system B

System B is Factory. [[FACTORY_MAP]] proves that operational requests require one of three `Company-Code` values and that most plant data reads a separate HANA schema. [[FACTORY_VERIFICATION]] confirms the company parameter is material to both requests and cache identity.

Factory exposes the adjacent operational fields:

- Jivo Oil QC rows expose `po_item_code`, supplier context, billed/arrival-slip `billing_qty`, and status in [[docs/factory/oil/Quality-Control|Quality-Control]]. Received and QC quantities are instead evidenced by the GRPO rows below.
- Jivo Oil GRPO rows expose nested `item_code`, received and QC quantities, `sap_doc_entry` on previews, and `sap_doc_num`, `base_entry`, `base_line`, and posting dates on histories in [[docs/factory/oil/GRPO|GRPO]].
- Warehouse/WMS rows expose `item_code`, `warehouse`, `warehouse_code`, `sap_doc_entry`, batch numbers, movements, quantities, and posting dates in [[docs/factory/oil/Warehouse|Warehouse]] and [[docs/factory/oil/WMS|WMS]].

The same audit observed 503 Factory Oil GRPO pipeline entries / 279 distinct PO
numbers. The 11 overlapping EXIM lines expanded to 25 Factory receipt-item rows,
proving a one-PO-to-many-truck-receipts relationship. None of the 10 overlapping
POs had exact current aggregate quantity equality; six said zero received in
EXIM while Factory already had positive receipts. Quantity is reconciliation
state, not identity.

A real collision disproves a bare-code equality rule: EXIM's captured `FG0000424` is **“COLD PRESS SUNFLOWER 1 LTR 24 PCS”**, while the 2026-07-19 Factory Mart/`JIVO_MART` WMS evidence captures the same code as **“FIRST PRESSED MUSTARD OIL 1 LTR 20 PCS.”** The cited Factory row does not record an exact SAP schema, so that qualifier is still missing. An item match therefore requires **company/schema/date plus `item_name` and pack validation**; the bare code is insufficient.

## Join contract table

| Canonical key | A field | B field | Required qualifiers | Confidence |
|---|---|---|---|---|
| `company_key` | implicit Jivo Wellness scope | `Company-Code`; HANA schema | dated, approved company-alias mapping | **Missing evidence — blocked** |
| `item_key` | open-PO SAP `ItemCode`; stock/tank local grade `item_code` | `item_code` / `ItemCode` plus item description | keep SAP item and local-grade namespaces separate; company, schema, source date, name, pack, UOM | **Observed exact on 11/11 PO lines; tank-grade → SAP RM is missing; `FG0000424` conflicts** |
| `party_key` | `vendor_code`, `card_code`, vendor name | supplier/card code and name | company, BP type, exact code; name only as validation | **Observed 131 exact code+name overlaps; governance-gated** |
| `po_docnum_key` | `PO_NUMBER`, business-facing PO number | GRPO-pipeline `po_number`, then preview enrichment | company, object type=PO, id kind=`DocNum`, vendor, item, UOM, date | **Observed exact: 10 POs / 11 lines; governance-gated** |
| `po_docentry_key` | no explicit PO `DocEntry` on open-PO rows | preview `sap_doc_entry`; history `base_entry` | company, object type=PO, id kind=`DocEntry`; never compare directly to `PO_NUMBER` | **Factory enrichment only; EXIM does not expose it** |
| `grpo_number_key` | `grpo_number` | `sap_doc_num` | company, document type=GRPO, posting date, supplier; never substitute `sap_doc_entry` | **Candidate — medium after company proof** |
| `warehouse_key` | `WAREHOUSE` / `Warehouse` | `warehouse`, `warehouse_code` | company/schema, exact code, effective date | **Observed 6/7 EXIM overlaps; governance-gated** |
| `material_flow_key` | PO + vendor + SAP item + warehouse + UOM + date | PO + supplier + SAP item + receipt/QC/gate rows | approved company, typed PO enrichment, one-to-many preservation; quantity reconciled separately | **Observed exact PO continuity; not yet enterprise-releasable** |

`DocEntry` is an SAP internal primary key and `DocNum` is a business-facing document number. They must never be conflated, even when both are numeric or appear near the same PO/GRPO.

## Observed flow and missing seam

```text
EXIM stock lot[id, local grade] --stock_id--> EXIM tank breakdown
              |
              X 0/27 local-grade codes match the SAP RM master
              |
              v reviewed material_grade_to_sap_item map required

EXIM open PO[PO number + vendor + SAP RM + warehouse + UOM + date]
              ||
              || 10 POs / 11 lines observed exact
              \/
Factory Oil GRPO pipeline[po_number]
              |
              +--> preview: PO DocEntry + LineNum
              +--> gate / arrival / QC / truck receipt
              +--> GRPO: DocNum/DocEntry + PO base_entry/base_line
```

## Read-only questions unlocked

- Which EXIM material arrivals have a plausible Factory gate/QC/GRPO continuation after company and item validation?
- Which EXIM open PO lines appear to have no corresponding Factory received/QC quantity within a defined date window?
- Which warehouse/category totals move in the same direction across EXIM and Factory after UOM and as-of alignment?
- Which item-code candidates fail name or pack validation and must be quarantined from automated joining?

## Gaps/do-not-assume

- Do not assume Jivo Wellness equals Factory `JIVO_OIL`; that mapping is unproven.
- Do not join on bare `item_code`; `FG0000424` is a confirmed description and pack conflict.
- Do not equate EXIM stock/tank-grade `item_code` with SAP RM `ItemCode`; live overlap is 0/27.
- Do not treat a value-chain transition as a shared database, direct foreign key, or running federated join.
- Do not equate `DocEntry`, `DocNum`, PO number, GRPO number, local row id, gate-entry id, or posting id.
- No stable EXIM lot/batch key shared with Factory is documented; quantity/date proximity is semantic evidence only.
- Do not require exact PO-level quantities: one PO line can span many truck receipts and source posting state lags.
- Factory GRPO preview is GET/read-declared, but backend side-effect freedom is unproven; do not schedule it as a 24/7 collector until separately attested.
- Never call `/sap_sync/open-grpos/` while its possible refresh side effect remains unresolved.

## Validation checklist

- [ ] Obtain an authoritative dated mapping from EXIM Jivo Wellness to a Factory `Company-Code` and HANA schema.
- [x] Profile current EXIM open-PO, party, warehouse, stock-grade, and Factory Oil overlap.
- [x] Reproduce the 10-PO / 11-line bridge with exact vendor/item/UOM qualifiers.
- [ ] Profile item-code overlap separately for all three Factory companies where the relation is semantically applicable.
- [ ] Reject or quarantine every code whose normalized name, pack, or UOM disagrees; include `FG0000424` as a regression fixture.
- [ ] Create an effective-dated, human-reviewed EXIM stock/tank-grade → SAP RM registry.
- [ ] Label every SAP identifier as `DocEntry`, `DocNum`, PO number, GRPO number, or source-local id before comparison.
- [ ] Compare supplier codes and warehouse codes only inside the proven company scope.
- [ ] Preserve one-to-many receipts; align event dates, source as-of dates, quantities, and UOMs; publish left/right unmatched, collision, and cap counts.
- [ ] Use only printed/read-safe endpoints and keep `/sap_sync/open-grpos/` excluded.

---
Linked: [[CONNECTIONS_MOC]] · [[VALUE_CHAIN]] · [[EXIM_HUB]] · [[FACTORY_HUB]] · [[EXIM_MAP]] · [[FACTORY_MAP]] · [[READ_ONLY_LAW]]
