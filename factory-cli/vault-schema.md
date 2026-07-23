---
title: "Factory Source-Vault Schema — JIVO_MART (Jivo Mart)"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: reference
tags: [jivogpt, factory-cli, schema]
---

# Factory Source-Vault Schema — JIVO_MART (Jivo Mart)

> **Provenance — imported 2026-07-19; source snapshot 2026-06-30.** This note came from the JIVO_MART-only `daman8271/jivo-factory-intel` baseline. For the current three-company study and the live-verified 2026-07-19 state, use [[docs/factory/FACTORY_MAP|FACTORY_MAP]] and [[CLI/factory-cli/README|the current CLI guide]].

> **Purpose:** One Obsidian note per entity, YAML frontmatter + key-field body + `[[wikilinks]]` for every foreign key, MOC hub per entity type, Home MOC over all hubs. Mirrors the proven `jivo-intel` formula exactly. This vault becomes the **4th pillar `factory/`** of `jivo-data-bank`, bridged to existing product nodes by **SAP item code**.
>
> **Scope:** Company-Code `JIVO_MART` (company id=2). CLI binary: `jivo-factory-pp-cli` (`~/go/bin`, authenticated). Base: `https://factory.jivo.in/api/v1`.
>
> **Note-id convention:** every note filename = a short stable slug prefix + the entity's **key field value** (e.g. `veh-300.md`). Because every prefix is globally unique, `[[slug-key]]` wikilinks resolve vault-wide regardless of folder. Frontmatter is always `type / id / title / tags / company`; the body carries the important fields then a `## Related` block holding the wikilinks.

---

## 1. Directory layout under `factory/`

```
factory/
├── _HOME.md                              ← Home MOC (links every hub)
│
├── fleet-gate/
│   ├── _moc-fleet-gate.md                ← domain MOC
│   ├── vehicles/            (veh-*)            + _moc-vehicle.md
│   ├── vehicle-types/       (vehtype-*)        + _moc-vehicle-type.md
│   ├── transporters/        (transporter-*)    + _moc-transporter.md
│   ├── drivers/             (driver-*)         + _moc-driver.md
│   ├── arrivals/            (arrival-*)        + _moc-arrival.md
│   ├── empty-vehicle-ins/   (evgi-*)           + _moc-empty-vehicle-in.md
│   ├── empty-vehicle-outs/  (evgo-*)           + _moc-empty-vehicle-out.md
│   ├── empty-in-reasons/    (evi-reason-*)     + _moc-empty-in-reason.md
│   ├── vehicle-entries/     (ventry-*)         + _moc-vehicle-entry.md
│   ├── bst-ins/             (bstin-*)          + _moc-bst-in.md
│   ├── bst-outs/            (bstout-*)         + _moc-bst-out.md
│   ├── bst-returns/         (bstret-*)         + _moc-bst-return.md
│   ├── bst-sap-transfers/   (bstsap-*)         + _moc-bst-sap-transfer.md
│   ├── job-works/           (jobwork-*)        + _moc-job-work.md
│   ├── job-work-grpos/      (jw-grpo-*)        + _moc-job-work-grpo.md
│   ├── job-work-prod-orders/(jw-po-*)          + _moc-job-work-prod-order.md
│   ├── rejected-qc-returns/ (qcreturn-*)       + _moc-rejected-qc-return.md
│   ├── sales-dispatches/    (salesdispatch-*)  + _moc-sales-dispatch.md
│   ├── sales-dispatch-docs/ (sdd-*)            + _moc-sales-dispatch-doc.md
│   ├── sales-dispatch-locks/(sdlock-*)         + _moc-sales-dispatch-lock.md
│   ├── dispatch-plans/      (plan-*)           + _moc-dispatch-plan.md
│   ├── partial-scan-reqs/   (psr-*)            + _moc-partial-scan-req.md
│   ├── scan-skip-reqs/      (ssr-*)            + _moc-scan-skip-req.md
│   └── daily-need-cats/     (dnc-*)            + _moc-daily-need-cat.md
│
├── quality-grpo/
│   ├── _moc-quality-grpo.md
│   ├── arrival-slips/       (slip-*)           + _moc-arrival-slip.md
│   ├── inspections/         (inspection-*)     + _moc-inspection.md
│   ├── material-types/      (mattype-*)        + _moc-material-type.md
│   ├── print-documents/     (printdoc-*)       + _moc-print-document.md
│   ├── production-qc/       (prodqc-*)         + _moc-production-qc.md
│   ├── grpo-entries/        (grpo-*)           + _moc-grpo-entry.md
│   └── grpo-service-entries/(grpo-svc-*)       + _moc-grpo-service-entry.md
│
├── barcode/
│   ├── _moc-barcode.md
│   ├── boxes/               (box-*)            + _moc-box.md
│   ├── pallets/             (pallet-*)         + _moc-pallet.md
│   ├── dispatch-sessions/   (session-*)        + _moc-dispatch-session.md
│   ├── session-lines/       (sessionline-*)    + _moc-session-line.md
│   ├── scanned-units/       (scanunit-*)       + _moc-scanned-unit.md
│   ├── dispatch-reports/    (dreport-*)        + _moc-dispatch-report.md
│   ├── dispatch-report-boxes/(drbox-*)         + _moc-dispatch-report-box.md
│   ├── dispatch-report-pallets/(drpallet-*)    + _moc-dispatch-report-pallet.md
│   ├── rejected-scans/      (rejscan-*)        + _moc-rejected-scan.md
│   ├── dispatch-settings/   (dispatch-settings)+ _moc-dispatch-settings.md
│   ├── intercompany-transfers/(ict-*)          + _moc-intercompany-transfer.md
│   ├── intercompany-transfer-lines/(ictline-*) + _moc-intercompany-transfer-line.md
│   ├── loose-items/         (loose-*)          + _moc-loose-item.md
│   ├── print-history/       (printhist-*)      + _moc-print-history.md
│   └── scan-history/        (scanhist-*)       + _moc-scan-history.md
│
├── dispatch-billing/
│   ├── _moc-dispatch-billing.md
│   ├── transporter-invoices/(transporter-invoice-*) + _moc-transporter-invoice.md
│   ├── branches/            (branch-*)         + _moc-branch.md
│   ├── tax-codes/           (taxcode-*)        + _moc-tax-code.md
│   └── gl-accounts/         (gl-*)             + _moc-gl-account.md
│         (DispatchPlan / pipeline / bilty-grpo / open-bilty all resolve to plan-* in fleet-gate)
│
├── procurement/
│   ├── _moc-procurement.md
│   └── vendors/             (vendor-*)         + _moc-vendor.md
│
├── production/
│   ├── _moc-production.md
│   ├── lines/               (line-*)           + _moc-line.md
│   ├── machines/            (machine-*)        + _moc-machine.md
│   ├── production-runs/     (run-*)            + _moc-production-run.md
│   ├── sap-orders/          (saporder-*)       + _moc-sap-order.md
│   ├── waste-logs/          (waste-*)          + _moc-waste-log.md
│   ├── breakdown-categories/(breakdown-cat-*)  + _moc-breakdown-category.md
│   ├── checklist-templates/ (checklist-tmpl-*) + _moc-checklist-template.md
│   ├── line-configs/        (lineconfig-*)     + _moc-line-config.md
│   ├── line-clearances/     (lineclear-*)      + _moc-line-clearance.md
│   └── machine-checklists/  (machinechecklist-*)+ _moc-machine-checklist.md
│
├── maintenance/
│   ├── _moc-maintenance.md
│   ├── assets/              (asset-*)          + _moc-asset.md
│   ├── asset-categories/    (asset-cat-*)      + _moc-asset-category.md
│   ├── asset-departments/   (asset-dept-*)     + _moc-asset-department.md
│   ├── asset-locations/     (asset-loc-*)      + _moc-asset-location.md
│   ├── asset-documents/     (asset-doc-*)      + _moc-asset-document.md
│   ├── asset-photos/        (asset-photo-*)    + _moc-asset-photo.md
│   ├── work-orders/         (wo-*)             + _moc-work-order.md
│   ├── work-order-photos/   (wo-photo-*)       + _moc-work-order-photo.md
│   ├── pm-plans/            (pmplan-*)         + _moc-pm-plan.md
│   ├── pm-executions/       (pmexec-*)         + _moc-pm-execution.md
│   ├── pm-checklist-items/  (pmcheck-*)        + _moc-pm-checklist-item.md
│   ├── spares/              (spare-*)          + _moc-spare.md
│   ├── spare-categories/    (spare-cat-*)      + _moc-spare-category.md
│   ├── spare-movements/     (spare-move-*)     + _moc-spare-movement.md
│   ├── spare-requests/      (spare-req-*)      + _moc-spare-request.md
│   └── vendor-visits/       (vendorvisit-*)    + _moc-vendor-visit.md
│
├── warehouse/
│   ├── _moc-warehouse.md
│   ├── warehouses/          (warehouse-*)      + _moc-warehouse.md
│   ├── item-groups/         (itemgroup-*)      + _moc-item-group.md
│   ├── wms-stock/           (stock-*)          + _moc-wms-stock.md
│   ├── wms-movements/       (wms-move-*)       + _moc-wms-movement.md
│   ├── wms-batches/         (batch-*)          + _moc-wms-batch.md
│   ├── wms-transfers/       (wms-transfer-*)   + _moc-wms-transfer.md
│   ├── wms-sales-order-lines/(so-*)            + _moc-wms-sales-order-line.md
│   ├── wms-billing/         (billing-*)        + _moc-wms-billing.md
│   ├── bom-requests/        (bom-req-*)        + _moc-bom-request.md
│   └── fg-receipts/         (fg-receipt-*)     + _moc-fg-receipt.md
│
├── dashboards-accounts/
│   ├── _moc-dashboards-accounts.md
│   ├── users/               (user-*)           + _moc-user.md
│   ├── me/                  (me)               + _moc-me.md
│   ├── notifications/       (notif-*)          + _moc-notification.md
│   ├── notification-prefs/  (notifpref-*)      + _moc-notification-pref.md
│   ├── dashboard-stock/     (dstock-*)         + _moc-dashboard-stock.md
│   ├── inventory-age/       (invage-*)         + _moc-inventory-age.md
│   ├── sales-planning/      (salesplan-*)      + _moc-sales-planning.md
│   ├── production-orders/   (prodorder-*)      + _moc-production-order.md
│   ├── prod-order-components/(prodorder-comp-*) + _moc-prod-order-component.md
│   └── procurement-shortfalls/(procshortfall-*) + _moc-procurement-shortfall.md
│
└── _bridge/                              ← SAP/SKU + shared-master nodes (fusion seam)
    ├── _moc-bridge.md
    ├── sap-items/           (item-*)           + _moc-sap-item.md   ← canonical product master (OITM)
    ├── companies/           (company-*)        + _moc-company.md
    ├── customers/           (customer-*)       + _moc-customer.md
    └── sap-invoices/        (sap-invoice-*)    + _moc-sap-invoice.md
```

**Deduplication rules (one canonical note, many endpoints feed it):**
- `ItemOITM` / production `SAPItem` / `QCSAPItem` → **one** canonical master `item-{item_code}` under `_bridge/sap-items/`.
- `Warehouse` (po-warehouses / wms-warehouses) → **one** `warehouse-{code}`.
- `ItemGroup` (fleet non-moving-rm / WMSItemGroup / NonMovingRMItemGroup / InventoryAgeFilterOptions.item_groups) → **one** `itemgroup-{code}`.
- `DispatchPlan` is **one** entity (`plan-{id}`); `dispatch bilty-grpo-pending/-history`, `dispatch open-bilties`, and the `dispatch-plans` pipeline-card view are all lifecycle/projection views of it → all link to `plan-{id}`.
- `SalesDispatch` == the dispatch-domain `GateOutEntry` → `salesdispatch-{id}`.
- `Company`, `Customer`, `SAPInvoice`, `SAPItem` are **bridge nodes**: created on-demand the first time any entity references them.

---

## 2. Per-entity specification

> Notation: `{field}` = substitute the record's value. Wikilinks list each FK as `field → [[target-id]]`. Array FKs emit one wikilink per element.

### Domain: fleet-gate

**Vehicle** — `vehicles/veh-{id}.md`
- FM: `type: Vehicle · id · title: "{vehicle_number}" · tags: [factory, fleet-gate, vehicle] · company: JIVO_MART`
- Body: vehicle_number, capacity_ton, created_at
- Wikilinks: `transporter → [[transporter-{transporter}]]` · `vehicle_type → [[vehtype-{vehicle_type}]]`

**VehicleType** — `vehicle-types/vehtype-{id}.md`
- FM: `type: VehicleType · id · title: "{name}" · tags: […, vehicle-type]`
- Body: name · Wikilinks: none

**Transporter** — `transporters/transporter-{id}.md`
- FM: `type: Transporter · id · title: "{name}"`
- Body: name, contact_person, mobile_no, gstin, created_at · Wikilinks: none

**Driver** — `drivers/driver-{id}.md`
- FM: `type: Driver · id · title: "{name}"`
- Body: name, mobile_no, license_no, id_proof_type, id_proof_number, photo, created_at · Wikilinks: none

**Arrival** — `arrivals/arrival-{id}.md`
- FM: `type: Arrival · id · title: "{arrival_no}"`
- Body: arrival_no, vehicle_no, driver_name, gate_in_date, in_time, tare_weight, weighbridge_slip_no, security_name, status, gate_out_date, out_time, departed_at, gatepass_no, gatepass_printed_at, gatepass_committed_at
- Wikilinks: `vehicle → [[veh-{vehicle}]]` · `driver → [[driver-{driver}]]` · `gate_ins[].id → [[evgi-{id}]]` (one each) · `gate_outs[].id → [[salesdispatch-{id}]]` (one each)

**EmptyVehicleGateIn** — `empty-vehicle-ins/evgi-{id}.md`
- FM: `type: EmptyVehicleGateIn · id · title: "{entry_no}"`
- Body: entry_no, company_code, company_name, vehicle_entry_no, vehicle_number, vehicle_type, transporter_name, driver_name, driver_mobile, reason, reason_display, gate_in_date, in_time, document_reference, document_notes, pipeline_status, bst_gate_out_id, bst_gate_out_entry_no, security_name, created_at, updated_at; **SAP:** sap_doc_entry, sap_doc_num, sap_from_warehouse, sap_to_warehouse
- Wikilinks: `vehicle → [[veh-{vehicle}]]` · `driver → [[driver-{driver}]]` · `vehicle_entry → [[ventry-{vehicle_entry}]]` · `company → [[company-{company_code}]]` · `reason → [[evi-reason-{reason}]]` · `sap_from_warehouse → [[warehouse-{sap_from_warehouse}]]` · `sap_to_warehouse → [[warehouse-{sap_to_warehouse}]]`

**EmptyVehicleGateOut** — `empty-vehicle-outs/evgo-{id}.md`
- FM: `type: EmptyVehicleGateOut · id · title: "{entry_no}"`
- Body: entry_no, vehicle_entry_no, vehicle_entry_type, vehicle_number, driver_name, driver_mobile, gate_out_date, out_time, security_name, status, cancel_reason, remarks, created_at
- Wikilinks: `vehicle → [[veh-{vehicle}]]` · `driver → [[driver-{driver}]]` · `vehicle_entry → [[ventry-{vehicle_entry}]]` · `company → [[company-{company_code}]]`

**EmptyVehicleInReason** — `empty-in-reasons/evi-reason-{value}.md`
- FM: `type: EmptyVehicleInReason · id: {value} · title: "{label}"`
- Body: value, label · Wikilinks: none (enum: BST, DISPATCH, REPAIR_MOVEMENT, JOB_WORK, OTHER)

**VehicleEntry** — `vehicle-entries/ventry-{id}.md`
- FM: `type: VehicleEntry · id · title: "{entry_no}"` (DOCKV-/EVGI- prefixed sessions)
- Body: entry_no, entry_type, status, entry_time, vehicle_number, vehicle_type, driver_name, driver_mobile, remarks, release_invoice_count, release_cancels_docking
- Wikilinks: `vehicle_id → [[veh-{vehicle_id}]]` · `driver_id → [[driver-{driver_id}]]`

**BstIn / BstOut / BstReturn** — `bst-ins/bstin-{id}.md` · `bst-outs/bstout-{id}.md` · `bst-returns/bstret-{id}.md`
- FM: `type · id · title` · Body+Wikilinks: **shape inferred only — endpoints empty.** Hubs created; notes generated when data appears.

**BstOutSapTransfer** — `bst-sap-transfers/bstsap-{doc_entry}.md`
- FM: `type: BstOutSapTransfer · id: {doc_entry} · title: "{doc_num}"`
- Body: doc_num, doc_date, doc_status, from_warehouse, to_warehouse, branch_id, line_count, total_quantity, comments, reference; **SAP:** doc_entry, doc_num
- Wikilinks: `from_warehouse → [[warehouse-{from_warehouse}]]` · `to_warehouse → [[warehouse-{to_warehouse}]]` · `branch_id → [[branch-{branch_id}]]`

**JobWork / JobWorkSapGrpo / JobWorkSapProductionOrder / RejectedQcReturn** — `job-works/jobwork-{id}.md` · `job-work-grpos/jw-grpo-{id}.md` · `job-work-prod-orders/jw-po-{id}.md` · `rejected-qc-returns/qcreturn-{id}.md`
- FM: `type · id · title` · **empty endpoints — hub-only until populated.**

**SalesDispatch** — `sales-dispatches/salesdispatch-{id}.md` (DOCK- prefix; == dispatch `GateOutEntry`)
- FM: `type: SalesDispatch · id · title: "{entry_no}"`
- Body: entry_no, company_code, company_name, vehicle_entry_no, vehicle_number, vehicle_type, transporter_name, driver_name, driver_mobile, dispatch_date, sap_doc_num, sap_doc_entry, sap_doc_date, sap_doc_total, sap_branch_name, sap_reference, customer_code, customer_name, ship_to_code, ship_to_address, place_of_supply, bp_gstin, eway_bill, warehouses, item_summary, document_count, document_numbers, document_type, arrival_status, gatepass_print_locked, pipeline_status, created_at, updated_at; **SAP:** sap_doc_entry, sap_doc_num, sap_reference, item_summary(FG codes)
- Wikilinks: `vehicle → [[veh-{vehicle}]]` · `transporter → [[transporter-{transporter}]]` · `driver → [[driver-{driver}]]` · `arrival → [[arrival-{arrival}]]` · `dispatch_plan → [[plan-{dispatch_plan}]]` · `vehicle_entry → [[ventry-{vehicle_entry}]]` · `company → [[company-{company_code}]]` · `customer_code → [[customer-{customer_code}]]` · `sap_doc_num → [[sap-invoice-{sap_doc_num}]]` · `item_summary[].item_code → [[item-{item_code}]]` (one per FG code) · embedded documents → `[[sdd-{doc_entry}]]`

**SalesDispatchDocument** — `sales-dispatch-docs/sdd-{doc_entry}.md`
- FM: `type: SalesDispatchDocument · id: {doc_entry} · title: "{doc_num}"`
- Body: doc_num, doc_date, doc_total, branch_id, branch_name, card_code, card_name, ship_to_code, ship_to_address, place_of_supply, bp_gstin, eway_bill, vehicle_no, transporter_name, warehouses, item_summary, total_quantity, total_litres, total_boxes, total_weight, line_count; **SAP:** doc_entry, doc_num, item_summary
- Wikilinks: `plan.id → [[plan-{plan.id}]]` · `branch_id → [[branch-{branch_id}]]` · `card_code → [[customer-{card_code}]]` · `doc_num → [[sap-invoice-{doc_num}]]` · `item_summary[].item_code → [[item-{item_code}]]`

**SalesDispatchLock** — `sales-dispatch-locks/sdlock-{id}.md` (singleton per company)
- FM: `type: SalesDispatchLock · id · title: "Lock {company_code}"`
- Body: is_locked, reason, changed_by_name, changed_at, created_at, updated_at
- Wikilinks: `company → [[company-{company_code}]]` · `changed_by → [[user-{changed_by}]]`

**DispatchPlan** — `dispatch-plans/plan-{id}.md` (canonical; absorbs bilty-grpo & pipeline-card views)
- FM: `type: DispatchPlan · id · title: "{invoice_number}"`
- Body: sap_invoice_doc_num, invoice_number, eway_bill, dispatch_date, priority, booking_status, pipeline_status, stage, stage_label, vehicle_no, transporter_name, transporter_gstin, driver_name, driver_mobile_no, driver_license_no, place_of_supply, customer_name, bilty_no, bilty_date, freight, kanta_weight, remarks, empty_gate_in_entry_no, gate_out_entry_no, gate_out_status; **SAP:** sap_invoice_doc_entry, sap_invoice_doc_num, sac_entry, sac_code
- Wikilinks: `vehicle_id → [[veh-{vehicle_id}]]` · `transporter_id → [[transporter-{transporter_id}]]` · `driver_id → [[driver-{driver_id}]]` · `linked_vehicle_entry_id → [[ventry-{linked_vehicle_entry_id}]]` · `gate_out_id → [[salesdispatch-{gate_out_id}]]` · `gate_out_vehicle_entry_id → [[ventry-{gate_out_vehicle_entry_id}]]` · `empty_gate_in_entry_no → [[evgi-{...}]]` (resolve EVGI entry_no→id) · `sap_invoice_doc_num → [[sap-invoice-{sap_invoice_doc_num}]]`

**PartialScanRequest** — `partial-scan-reqs/psr-{id}.md`
- FM: `type: PartialScanRequest · id · title: "{entry_no}"`
- Body: entry_no, vehicle_no, customer_name, sap_doc_num, document_type, dispatch_status, scanned_boxes, expected_boxes, reason, status, requested_by_name, requested_at, reviewed_by_name, reviewed_at, review_notes, created_at, updated_at; **SAP:** sap_doc_num
- Wikilinks: `sales_dispatch → [[salesdispatch-{sales_dispatch}]]` · `requested_by → [[user-{requested_by}]]` · `reviewed_by → [[user-{reviewed_by}]]` · `sap_doc_num → [[sap-invoice-{sap_doc_num}]]`

**ScanSkipRequest** — `scan-skip-reqs/ssr-{id}.md`
- FM: `type: ScanSkipRequest · id · title: "{entry_no}"`
- Body: entry_no, vehicle_no, customer_name, sap_doc_num, document_type, dispatch_status, reason, status, requested_by_name, requested_at, reviewed_by_name, reviewed_at, review_notes, created_at, updated_at; **SAP:** sap_doc_num
- Wikilinks: `sales_dispatch → [[salesdispatch-{sales_dispatch}]]` · `requested_by → [[user-{requested_by}]]` · `reviewed_by → [[user-{reviewed_by}]]` · `sap_doc_num → [[sap-invoice-{sap_doc_num}]]`

**DailyNeedCategory** — `daily-need-cats/dnc-{id}.md`
- FM: `type: DailyNeedCategory · id · title: "{category_name}"` · Body: category_name · Wikilinks: none

### Domain: quality-grpo

**ArrivalSlip** — `arrival-slips/slip-{id}.md`
- FM: `type: ArrivalSlip · id · title: "{entry_no}"`
- Body: entry_no, po_item_code, item_name, party_name, arrival_datetime, billing_qty, billing_uom, status, is_submitted, submitted_at, submitted_by_name, truck_no_as_per_bill, commercial_invoice_no, eway_bill_no, bilty_no, has_certificate_of_analysis, has_certificate_of_quantity, in_time_to_qa, remarks, attachments; **SAP:** po_item_code
- Wikilinks: `po_item_receipt → [[grpo-poir-{po_item_receipt}]]`* · `po_receipt_id → [[grpo-{...}]]`* · `vehicle_entry_id → [[ventry-{vehicle_entry_id}]]` · `submitted_by → [[user-{submitted_by}]]` · `po_item_code → [[item-{po_item_code}]]`
  *(POItemReceipt / POReceipt are PO-domain nodes; until a PO pillar exists they resolve to the GRPOEntry that carries them — see §4 note.)*

**Inspection** — `inspections/inspection-{arrival_slip_id}.md` (1:1 with ArrivalSlip)
- FM: `type: Inspection · id: {arrival_slip_id} · title: "{report_no|entry_no}"`
- Body: inspection_id, entry_no, report_no, internal_lot_no, po_item_code, item_name, party_name, billing_qty, billing_uom, workflow_status, final_status, effective_final_status, qc_stage, qc_decision, factory_head_decision, factory_head_decided_at, material_type_name, chemist_decision, manager_decision, rejected_qc_return_entry_no, created_at, submitted_at; **SAP:** po_item_code
- Wikilinks: `arrival_slip_id → [[slip-{arrival_slip_id}]]` · `rejected_qc_return_entry_id → [[ventry-{rejected_qc_return_entry_id}]]` · `material_type_name → [[mattype-{...}]]` (resolve name→id) · `po_item_code → [[item-{po_item_code}]]`

**MaterialType** — `material-types/mattype-{id}.md` · FM: `type · id · title: "{name}"` · Body: name · (empty)
**PrintDocument** — `print-documents/printdoc-{id}.md` · (empty, hub-only)
**ProductionQC** — `production-qc/prodqc-{id}.md` · (empty, hub-only)

**GRPOEntry** — `grpo-entries/grpo-{vehicle_entry_id}.md`
- FM: `type: GRPOEntry · id: {vehicle_entry_id} · title: "{entry_no}"`
- Body: entry_no, status, status_label, phase, is_ready_for_grpo, is_fully_posted, entry_time, total_po_count, posted_po_count, pending_po_count, suppliers, po_numbers, po_receipts; **SAP:** po_receipts[].items[].item_code
- Wikilinks: `vehicle_entry_id → [[ventry-{vehicle_entry_id}]]` · `suppliers[].supplier_code → [[vendor-{supplier_code}]]` (one each) · `po_receipts[].items[].item_code → [[item-{item_code}]]` (one each) · `po_receipts[].po_number → [[sap-invoice-{po_number}]]`** (PO# bridge)
  *(POReceipt/POItemReceipt embedded sub-objects are rendered inline in the body table; they have no standalone endpoint, so no separate notes.)*

**GRPOServiceEntry** — `grpo-service-entries/grpo-svc-{dispatch_plan_id}.md`
- FM: `type: GRPOServiceEntry · id: {dispatch_plan_id} · title: "{sap_invoice_doc_num}"`
- Body: sap_invoice_doc_entry, sap_invoice_doc_num, booking_status, dispatch_date, vehicle_no, driver_name, transporter_name, transporter_gstin, source_state, bilty_no, bilty_date, freight, total_freight, invoice_count, created_at, updated_at; **SAP:** sap_invoice_doc_entry, sap_invoice_doc_num
- Wikilinks: `dispatch_plan_id → [[plan-{dispatch_plan_id}]]` · `linked_vehicle_entry_id → [[ventry-{linked_vehicle_entry_id}]]` · `sap_invoice_doc_num → [[sap-invoice-{sap_invoice_doc_num}]]`

### Domain: barcode

**BarcodeBox** — `boxes/box-{id}.md` (~151k)
- FM: `type: BarcodeBox · id · title: "{box_barcode}"`
- Body: box_barcode, item_code, item_name, batch_number, qty, uom, mfg_date, exp_date, current_warehouse, current_bin, status, production_line, dispatched_at, removed_from_pallet_at, removed_from_pallet_reason, created_by_name, created_at; **SAP:** item_code
- Wikilinks: `pallet → [[pallet-{pallet}]]` · `dispatch_session → [[session-{dispatch_session}]]` · `created_by → [[user-{created_by}]]` · `item_code → [[item-{item_code}]]` · `current_warehouse → [[warehouse-{current_warehouse}]]` · `batch_number → [[batch-{batch_number}]]`

**Pallet** — `pallets/pallet-{id}.md` (~3,170)
- FM: `type: Pallet · id · title: "{pallet_id}"`
- Body: pallet_id, item_code, item_name, batch_number, box_count, total_boxes, available_boxes, dispatched_boxes, max_box_count, total_qty, uom, mfg_date, exp_date, current_warehouse, current_bin, status, production_line, dispatched_at, created_by_name, created_at; **SAP:** item_code
- Wikilinks: `dispatch_session → [[session-{dispatch_session}]]` · `created_by → [[user-{created_by}]]` · `item_code → [[item-{item_code}]]` · `current_warehouse → [[warehouse-{current_warehouse}]]` · `batch_number → [[batch-{batch_number}]]`

**DispatchSession** — `dispatch-sessions/session-{id}.md` (~306 across active/completed/closed)
- FM: `type: DispatchSession · id · title: "{bill_number}"`
- Body: bill_number, sap_system_type, sap_object_type, sap_doc_entry, sap_doc_num, delivery_number, reference_delivery_number, customer_code, customer_name, ship_to_code, ship_to_name, bill_date, status, total_expected_qty, total_scanned_qty, pending_qty, total_remaining_qty, removed_box_count, sap_dispatch_status, sap_update_status, sap_sync_status, line_count, completed_line_count, accepted_scan_count, rejected_scan_count, pallet_scan_count, box_scan_count, started_at, completed_at, dispatched_at, closed_at, cancelled_at, dispatched_by_name, completed_by_name, closed_by_name, created_by_name, created_at; **SAP:** sap_doc_num, delivery_number
- Wikilinks: `dispatched_by/completed_by/closed_by/created_by → [[user-{…}]]` · `customer_code → [[customer-{customer_code}]]` · `sap_doc_num → [[sap-invoice-{sap_doc_num}]]` · embedded `lines[].id → [[sessionline-{id}]]` · embedded `scanned_units[].id → [[scanunit-{id}]]`

**DispatchSessionLine** — `session-lines/sessionline-{id}.md` (embedded in session)
- FM: `type: DispatchSessionLine · id · title: "{material_code} @ {bill_number}"`
- Body: sequence_no, sap_line_no, material_code, material_description, bill_qty, expected_qty, scanned_qty, remaining_qty, pending_qty, bill_boxes, expected_boxes, scanned_boxes, pending_boxes, uom, batch_number, warehouse_code, serial_required, status; **SAP:** material_code
- Wikilinks: `parent session → [[session-{session_id}]]` · `material_code → [[item-{material_code}]]` · `warehouse_code → [[warehouse-{warehouse_code}]]` · `batch_number → [[batch-{batch_number}]]`

**ScannedUnit** — `scanned-units/scanunit-{id}.md` (embedded)
- FM: `type: ScannedUnit · id · title: "{barcode_value}"`
- Body: barcode_value, entity_type, barcode_type, box_barcode, item_code, item_name, material_code, batch_number, original_qty, available_qty, required_pending_qty, total_box_qty, dispatch_qty, remaining_qty, qty, uom, warehouse, scan_status, status_after_scan, dispatch_doc_no, dispatch_date_time, scanned_by_name, customer_name, scanned_at; **SAP:** item_code, material_code
- Wikilinks: `line → [[sessionline-{line}]]` · `box → [[box-{box}]]` · `pallet → [[pallet-{pallet}]]` · `scan_log → [[scanhist-{scan_log}]]` · `item_code → [[item-{item_code}]]`

**DispatchReport** — `dispatch-reports/dreport-{session_id}.md`
- FM: `type: DispatchReport · id: {session_id} · title: "{bill_number}"`
- Body: bill_number, delivery_number, customer_code, customer_name, status, created_by, completed_by, started_at, completed_at, total_expected_qty, total_dispatched_qty, pending_qty, total_expected_boxes, total_dispatched_boxes, pending_boxes, sap_sync_status, sap_sync_error
- Wikilinks: `session_id → [[session-{session_id}]]` · `customer_code → [[customer-{customer_code}]]`

**DispatchReportBox** — `dispatch-report-boxes/drbox-{box_id}.md`
- FM: `type: DispatchReportBox · id: {box_id} · title: "{box_barcode}"`
- Body: box_barcode, material_code, quantity, uom, pallet_barcode, box_status, dispatch_session_id, bill_number, dispatched_time, removed_from_pallet; **SAP:** material_code
- Wikilinks: `box_id → [[box-{box_id}]]` · `pallet_barcode → [[pallet-{…}]]` (resolve pallet_id→id) · `dispatch_session_id → [[session-{dispatch_session_id}]]` · `material_code → [[item-{material_code}]]`

**DispatchReportPallet** — `dispatch-report-pallets/drpallet-{pallet_id}.md`
- FM: `type: DispatchReportPallet · id: {pallet_id} · title: "{pallet_barcode}"`
- Body: pallet_barcode, pallet_status, total_boxes, dispatched_boxes, remaining_boxes, dispatch_session_id, bill_number, dispatched_time
- Wikilinks: `pallet_id → [[pallet-{pallet_id}]]` · `dispatch_session_id → [[session-{dispatch_session_id}]]`

**RejectedScan** — `rejected-scans/rejscan-{scan_id}.md` (~6,243)
- FM: `type: RejectedScan · id: {scan_id} · title: "{barcode}"`
- Body: barcode, scan_type, rejection_reason, rejection_code, bill_number, user, scan_time
- Wikilinks: `bill_number → [[session-{…}]]` (resolve bill_number→session id)

**DispatchSettings** — `dispatch-settings/dispatch-settings.md` (singleton)
- FM: `type: DispatchSettings · id: singleton · title: "Dispatch Settings"`
- Body: allow_partial_dispatch, allow_partial_pallet_dispatch, allow_box_dispatch_from_pallet, require_sequential_item_scanning, require_sap_sync_on_completion, allow_manual_close, allow_admin_override, created_at, updated_at · Wikilinks: none

**IntercompanyTransfer** — `intercompany-transfers/ict-{id}.md` (~1,021)
- FM: `type: IntercompanyTransfer · id · title: "{transfer_number}"`
- Body: transfer_number, source_company_code, source_company_name, destination_company_code, destination_company_name, entity_type, status, total_barcodes, total_qty, uom, sap_enabled, sap_doc_entry, sap_doc_num, sap_status, sap_error, notes, device_id, reversed_at, reversed_by_name, created_by_name, created_at, updated_at; **SAP:** sap_doc_num
- Wikilinks: `source_company_code → [[company-{source_company_code}]]` · `destination_company_code → [[company-{destination_company_code}]]` · `sap_doc_num → [[sap-invoice-{sap_doc_num}]]` · embedded `lines[].id → [[ictline-{id}]]`

**IntercompanyTransferLine** — `intercompany-transfer-lines/ictline-{id}.md` (embedded; ~27,875 barcodes)
- FM: `type: IntercompanyTransferLine · id · title: "{barcode}"`
- Body: barcode, item_code, item_name, batch_number, qty, uom, from_company_code, from_company_name, to_company_code, to_company_name, created_at; **SAP:** item_code
- Wikilinks: `box → [[box-{box}]]` · `from_company_code → [[company-{from_company_code}]]` · `to_company_code → [[company-{to_company_code}]]` · `item_code → [[item-{item_code}]]` · parent `[[ict-{transfer_id}]]`

**ItemOITM** → **canonical SAP item master**, see `_bridge/sap-items/item-{item_code}.md` in §5.

**LooseItem** — `loose-items/loose-{id}.md` (~727)
- FM: `type: LooseItem · id · title: "{item_code} {batch_number}"`
- Body: item_code, item_name, batch_number, qty, original_qty, uom, source_box_barcode, source_pallet_id, reason, reason_notes, current_warehouse, status, repacked_into_barcode, created_by_name, created_at, updated_at; **SAP:** item_code
- Wikilinks: `source_box → [[box-{source_box}]]` · `source_pallet → [[pallet-{source_pallet}]]` · `repacked_into_box → [[box-{repacked_into_box}]]` · `created_by → [[user-{created_by}]]` · `item_code → [[item-{item_code}]]` · `current_warehouse → [[warehouse-{current_warehouse}]]`

**PrintHistory** — `print-history/printhist-{id}.md` (~156k)
- FM: `type: PrintHistory · id · title: "{label_type} {reference_code}"`
- Body: label_type, reference_id, reference_code, print_type, reprint_reason, printed_by_name, printed_at, printer_name
- Wikilinks: `reference_id → [[box-{reference_id}]]` *(if label_type=BOX)* **or** `→ [[pallet-{reference_id}]]` *(if label_type=PALLET)* · `printed_by → [[user-{printed_by}]]`

**ScanHistory** — `scan-history/scanhist-{id}.md` (~25k)
- FM: `type: ScanHistory · id · title: "{barcode_raw}"`
- Body: scan_type, barcode_raw, barcode_parsed, entity_type, entity_id, scan_result, context_ref_type, context_ref_id, scanned_by_name, scanned_at, device_info
- Wikilinks: `entity_id → [[box-{entity_id}]]`/`[[pallet-{entity_id}]]` (per entity_type) · `context_ref_id → [[session-{context_ref_id}]]` *(when context_ref_type=SALES_DISPATCH)* · `scanned_by → [[user-{scanned_by}]]`

### Domain: dispatch-billing

**TransporterInvoice** — `transporter-invoices/transporter-invoice-{id}.md` (empty)
- FM: `type: TransporterInvoice · id · title: "{invoice_no}"`
- Body: transporter_name, transporter_gstin, invoice_no, invoice_date, amount
- Wikilinks: `transporter_gstin → [[transporter-{…}]]` (resolve gstin→id once populated) · related `[[plan-{dispatch_plan_id}]]`

**Branch** — `branches/branch-{branch_id}.md` (from bilty-grpo-options)
- FM: `type: Branch · id: {branch_id} · title: "{branch_name}"` · Body: branch_name, state · Wikilinks: none

**TaxCode** — `tax-codes/taxcode-{tax_code}.md`
- FM: `type: TaxCode · id: {tax_code} · title: "{tax_name}"` · Body: tax_name, rate · Wikilinks: none

**GLAccount** — `gl-accounts/gl-{account_code}.md`
- FM: `type: GLAccount · id: {account_code} · title: "{account_name}"` · Body: account_name; **SAP:** account_code · Wikilinks: none

> `BiltyGrpoHistory`, `OpenBilty`, `DispatchPlanPipelineCard` = lifecycle/projection views of **DispatchPlan** → they do **not** mint new notes; they enrich `plan-{id}` (set `pipeline_status`, `stage`, `bilty_*`). `BiltyGrpoOptions` is the composite reference object that seeds Branch/TaxCode/GLAccount notes.

### Domain: procurement

**Vendor** — `procurement/vendors/vendor-{vendor_code}.md` (212)
- FM: `type: Vendor · id: {vendor_code} · title: "{vendor_name}"`
- Body: vendor_code, vendor_name *(prefix family: VENDA=external supplier, ORGV=internal imprest)* · Wikilinks: none

> `Warehouse`, `NonMovingRMItemGroup` from the `po` group are **deduped** into `warehouse/warehouses/warehouse-{code}` and `warehouse/item-groups/itemgroup-{code}` respectively.

### Domain: production *(all endpoints empty — hubs + inferred schema only)*

**Line** `production-runs?` — `lines/line-{id}.md` · Body: name, status · Wikilinks: none
**Machine** — `machines/machine-{id}.md` · Body: name, status, level · Wikilinks: `line_id → [[line-{line_id}]]`
**ProductionRun** — `production-runs/run-{id}.md` · Body: planned_qty, actual_qty, status, start_time, end_time, oee_percent, availability_percent; SAP: sap_order_id · Wikilinks: `line_id → [[line-{line_id}]]` · `sap_order_id → [[saporder-{sap_order_id}]]`
**SAPOrder** — `sap-orders/saporder-{id}.md` · Body: order_number, item_code, planned_qty, status; SAP: item_code, order_number · Wikilinks: `item_code → [[item-{item_code}]]`
**WasteLog** — `waste-logs/waste-{id}.md` · Body: material_code, quantity, reason, approval_status; SAP: material_code · Wikilinks: `run_id → [[run-{run_id}]]` · `material_code → [[item-{material_code}]]`
**BreakdownCategory** — `breakdown-categories/breakdown-cat-{id}.md` · Body: name · Wikilinks: none
**ChecklistTemplate** — `checklist-templates/checklist-tmpl-{id}.md` · Body: name, input_type · Wikilinks: `machine_id → [[machine-{machine_id}]]`
**LineConfig** — `line-configs/lineconfig-{id}.md` · Wikilinks: `line_id → [[line-{line_id}]]`
**LineClearance** — `line-clearances/lineclear-{id}.md` · Body: cleared_by, cleared_at, status · Wikilinks: `line_id → [[line-{line_id}]]`
**MachineChecklist** — `machine-checklists/machinechecklist-{id}.md` · Body: status · Wikilinks: `machine_id → [[machine-{machine_id}]]` · `template_id → [[checklist-tmpl-{template_id}]]`

### Domain: maintenance *(all endpoints empty — hubs + inferred schema; enums from `maintenance options`)*

**MaintenanceAsset** — `assets/asset-{id}.md` · Body: name, status(RUNNING/IDLE/BREAKDOWN/UNDER_PM/UNDER_REPAIR/RETIRED), level(PLANT/AREA/LINE/MACHINE/COMPONENT/UTILITY) · Wikilinks: `category_id → [[asset-cat-{…}]]` · `location_id → [[asset-loc-{…}]]` · `department_id → [[asset-dept-{…}]]` · `line_id → [[line-{line_id}]]`
**AssetCategory/Department/Location** — `asset-cat-{id}` / `asset-dept-{id}` / `asset-loc-{id}` · Body: name · Wikilinks: none
**AssetDocument** — `asset-documents/asset-doc-{id}.md` · Body: document_type(MANUAL/WARRANTY/AMC/SERVICE_REPORT/CALIBRATION/OTHER), url · Wikilinks: `asset_id → [[asset-{asset_id}]]`
**AssetPhoto** — `asset-photos/asset-photo-{id}.md` · Body: url · Wikilinks: `asset_id → [[asset-{asset_id}]]`
**WorkOrder** — `work-orders/wo-{id}.md` · Body: work_type, status, priority, assigned_to, created_at, completed_at, production_downtime_minutes · Wikilinks: `asset_id → [[asset-{asset_id}]]` · `line_id → [[line-{line_id}]]` · `department_id → [[asset-dept-{department_id}]]` · `assigned_to → [[user-{assigned_to}]]`
**WorkOrderPhoto** — `work-order-photos/wo-photo-{id}.md` · Wikilinks: `work_order_id → [[wo-{work_order_id}]]`
**PMPlan** — `pm-plans/pmplan-{id}.md` · Body: name, frequency, next_due · Wikilinks: `asset_id → [[asset-{asset_id}]]`
**PMExecution** — `pm-executions/pmexec-{id}.md` · Body: scheduled_date, completed_date, status · Wikilinks: `pm_plan_id → [[pmplan-{pm_plan_id}]]` · `asset_id → [[asset-{asset_id}]]`
**PMChecklistItem** — `pm-checklist-items/pmcheck-{id}.md` · Body: task_text, input_type · Wikilinks: `pm_plan_id → [[pmplan-{pm_plan_id}]]`
**Spare** — `spares/spare-{id}.md` · Body: spare_code, name, quantity, min_level, unit, stock_status · Wikilinks: `category_id → [[spare-cat-{category_id}]]`
**SpareCategory** — `spare-categories/spare-cat-{id}.md` · Body: name · Wikilinks: none
**SpareMovement** — `spare-movements/spare-move-{id}.md` · Body: quantity, direction, date · Wikilinks: `spare_id → [[spare-{spare_id}]]` · `work_order_id → [[wo-{work_order_id}]]`
**SpareRequest** — `spare-requests/spare-req-{id}.md` · Body: quantity, status · Wikilinks: `spare_id → [[spare-{spare_id}]]` · `work_order_id → [[wo-{work_order_id}]]`
**VendorVisit** — `vendor-visits/vendorvisit-{id}.md` · Body: vendor_name, visit_type, status, scheduled_date · Wikilinks: `asset_id → [[asset-{asset_id}]]`

### Domain: warehouse (WMS — live data)

**Warehouse** — `warehouses/warehouse-{code}.md` (31) · FM: `type: Warehouse · id: {code} · title: "{name}"` · Body: name *(loc prefixes BH/DL/PB/KT/RJ/UP/DP)* · Wikilinks: none
**ItemGroup** — `item-groups/itemgroup-{code}.md` (10) · FM: `type: ItemGroup · id: {code} · title: "{name}"` · Body: name *(106=RAW MATERIAL,102=FINISHED,105=PACKAGING)*; SAP: item_group_code · Wikilinks: none
**WMSStockItem** — `wms-stock/stock-{item_code}-{warehouse_code}.md` (953) · Body: item_name, item_group, uom, on_hand, committed, on_order, available, avg_price, stock_value, min_level, max_level, last_purchase_price, stock_status; SAP: item_code · Wikilinks: `warehouse_code → [[warehouse-{warehouse_code}]]` · `item_group → [[itemgroup-{item_group}]]` · `item_code → [[item-{item_code}]]`
**WMSStockMovement** — `wms-movements/wms-move-{doc_num}.md` (~200) · Body: date, item_code, item_name, warehouse_code, in_qty, out_qty, quantity, direction, transaction_type(AR_INVOICE/TRANSFER/GRPO/Production Order 202), reference, created_by; SAP: item_code · Wikilinks: `warehouse_code → [[warehouse-{warehouse_code}]]` · `item_code → [[item-{item_code}]]`
**WMSBatch** — `wms-batches/batch-{batch_number}.md` (300) · Body: item_code, item_name, warehouse_code, expiry_date, manufacturing_date, sap_status, quantity, days_to_expiry, expiry_status; SAP: item_code · Wikilinks: `warehouse_code → [[warehouse-{warehouse_code}]]` · `item_code → [[item-{item_code}]]`
**WMSTransfer** — `wms-transfers/wms-transfer-{doc_entry}.md` (14) · FM: `id: {doc_entry} · title: "{doc_num}"` · Body: doc_num, doc_date, header_from_warehouse, header_to_warehouse, comments, lines[line_num,item_code,item_name,quantity]; SAP: item_code · Wikilinks: `from_warehouse → [[warehouse-{from_warehouse}]]` · `to_warehouse → [[warehouse-{to_warehouse}]]` · `lines[].item_code → [[item-{item_code}]]`
**WMSSalesOrderLine** — `wms-sales-order-lines/so-{doc_entry}-{line_num}.md` (86 orders/300 lines) · Body: doc_num, doc_date, due_date, customer_code, customer_name, item_code, item_name, warehouse_code, ordered_qty, open_qty, delivered_qty, fulfillment_pct; SAP: item_code · Wikilinks: `warehouse_code → [[warehouse-{warehouse_code}]]` · `customer_code → [[customer-{customer_code}]]` · `item_code → [[item-{item_code}]]`
**WMSBillingItem** — `wms-billing/billing-{item_code}-{warehouse_code}.md` (757) · Body: item_name, received_qty, received_value, billed_qty, billed_value, unbilled_qty, unbilled_value, status(FULLY/PARTIALLY/UNBILLED), first_grpo_date, last_grpo_date; SAP: item_code · Wikilinks: `warehouse_code → [[warehouse-{warehouse_code}]]` · `item_code → [[item-{item_code}]]`
**BOMRequest** — `bom-requests/bom-req-{id}.md` (empty) · Body: item_code, status, requested_by, requested_at; SAP: item_code · Wikilinks: `item_code → [[item-{item_code}]]` · `requested_by → [[user-{requested_by}]]`
**FGReceipt** — `fg-receipts/fg-receipt-{id}.md` (empty) · Body: item_code, quantity, warehouse_code, receipt_date; SAP: item_code · Wikilinks: `item_code → [[item-{item_code}]]` · `warehouse_code → [[warehouse-{warehouse_code}]]`

### Domain: dashboards-accounts

**User** — `users/user-{id}.md` (~25) · Body: email, full_name, employee_code, is_active, is_staff, date_joined · Wikilinks: none
**AuthenticatedUserProfile** — `me/me.md` (singleton) · Body: email, full_name, employee_code, is_active, is_staff, is_superuser, date_joined, permissions · Wikilinks: `companies[].company_id → [[company-{company_code}]]` (map id→code) · self `[[user-{id}]]`
**Notification** — `notifications/notif-{id}.md` (~25k) · Body: title, body, notification_type, click_action_url, reference_type, reference_id, is_read, read_at, created_at, extra_data · Wikilinks: `notification_type → [[notifpref-{notification_type}]]` · `reference_id → [[<polymorphic per reference_type>]]` (e.g. reference_type=person_entry → person-entry node; gate_entry → `[[ventry-{reference_id}]]`)
**NotificationPreference** — `notification-prefs/notifpref-{code}.md` (23) · FM: `id: {code} · title: "{name}"` · Body: name, description, is_enabled · Wikilinks: none
**StockItem** (dashboards stock) — `dashboard-stock/dstock-{item_code}-{warehouse}.md` · Body: item_name, on_hand, min_stock, uom, stock_status, health_ratio, movement_status, last_consumption_date, days_since_last_consumption, warehouse_count, has_warning; SAP: item_code · Wikilinks: `warehouse → [[warehouse-{warehouse}]]` · `item_code → [[item-{item_code}]]`
**InventoryAgeReportRow** — `inventory-age/invage-{item_code}-{warehouse}.md` · Body: item_name, is_litre, item_group, unit, variety, sku, sub_group, on_hand, litres, in_stock_value, calc_price, effective_date, days_age; SAP: item_code · Wikilinks: `warehouse → [[warehouse-{warehouse}]]` · `item_group → [[itemgroup-{item_group}]]` · `item_code → [[item-{item_code}]]`
**SalesPlanningRequirementRow** — `sales-planning/salesplan-{item_code}.md` (empty for JIVO_MART) · Body: item_name, planned_qty, base_required_qty, min_stock, stock_in_hand, required_qty, open_po_qty, net_shortage_qty, report_execution_at; SAP: item_code · Wikilinks: `item_code → [[item-{item_code}]]`
**ProductionOrder** — `production-orders/prodorder-{prod_order_entry}.md` (1) · FM: `id: {prod_order_entry} · title: "{prod_order_num}"` · Body: prod_order_num, sku_code, sku_name, planned_qty, completed_qty, status, due_date, post_date, priority, warehouse, total_components, components_with_shortfall, total_remaining_component_qty; SAP: sku_code, prod_order_num · Wikilinks: `warehouse → [[warehouse-{warehouse}]]` · `sku_code → [[item-{sku_code}]]` · components → `[[prodorder-comp-{prod_order_entry}-{component_line}]]`
**ProductionOrderComponent** — `prod-order-components/prodorder-comp-{prod_order_entry}-{component_line}.md` · Body: component_code, component_name, component_planned_qty, component_issued_qty, component_remaining_qty, component_warehouse, base_qty, uom, stock_on_hand, stock_committed, stock_on_order, net_available, shortfall_qty, vendor_lead_time, default_vendor, stock_status; SAP: component_code · Wikilinks: `prod_order_entry → [[prodorder-{prod_order_entry}]]` · `component_warehouse → [[warehouse-{component_warehouse}]]` · `component_code → [[item-{component_code}]]` · `default_vendor → [[vendor-{…}]]` (if code)
**ProcurementShortfall** — `procurement-shortfalls/procshortfall-{component_code}.md` (empty) · Body: SAP: component_code · Wikilinks: `component_code → [[item-{component_code}]]`

### Bridge nodes (`_bridge/`)

**SAPItem / Item Master (OITM)** — `_bridge/sap-items/item-{item_code}.md` — see §5.
**Company** — `_bridge/companies/company-{company_code}.md` (3 known) · FM: `id: {company_code} · title: "{company_name}"` · Body: company_id (1=JIVO_OIL,2=JIVO_MART,3=JIVO_BEVERAGES), company_code · Wikilinks: none
**Customer** — `_bridge/customers/customer-{customer_code}.md` · FM: `id: {customer_code} · title: "{customer_name}"` · Body: customer_code, customer_name, ship_to, gstin · Wikilinks: none
**SAPInvoice** — `_bridge/sap-invoices/sap-invoice-{doc_num}.md` · FM: `id: {doc_num} · title: "SAP Inv {doc_num}"` · Body: doc_entry, doc_num, doc_date, doc_total · Wikilinks: backlinks resolve from DispatchPlan/SalesDispatch/GRPOServiceEntry.

---

## 3. MOC hub notes

**Per-entity-type MOC** — `_moc-<entity>.md` inside each entity folder:
```markdown
---
type: MOC
title: "<Entity> — Map of Content"
tags: [factory, moc, <domain>, <entity-type>]
company: JIVO_MART
---
# <Entity> ({count} notes)
> <one-line definition + key field + entry-no prefix>
**Capture:** `jivo-factory-pp-cli <cli_command> --json`
## Notes
- [[slug-key1]] — title
- [[slug-key2]] — title
…  (Dataview alt: ```dataview TABLE title FROM "factory/<domain>/<folder>" WHERE type = "<Entity>" ```)
## Upstream / Downstream
- Upstream FKs: <list of entity types this links TO>
- Downstream: <entity types that link to this>
```

**Per-domain MOC** — `factory/<domain>/_moc-<domain>.md`: lists every entity-type MOC in that domain + a domain relationship summary.

**Home MOC** — `factory/_HOME.md`:
```markdown
---
type: HomeMOC
title: "JIVO Factory (Jivo Mart) — Home"
tags: [factory, moc, home]
company: JIVO_MART
---
# JIVO Factory Source-Vault — JIVO_MART
The manufacturing/supply lens of jivo-data-bank. Source: factory.jivo.in/api/v1, Company-Code JIVO_MART (id=2).
## Domains
- [[_moc-fleet-gate]] · [[_moc-quality-grpo]] · [[_moc-barcode]] · [[_moc-dispatch-billing]]
- [[_moc-procurement]] · [[_moc-production]] · [[_moc-maintenance]] · [[_moc-warehouse]] · [[_moc-dashboards-accounts]]
## Bridge (SAP/SKU seam to jivo-data-bank)
- [[_moc-bridge]] · [[_moc-sap-item]] · [[_moc-company]] · [[_moc-customer]] · [[_moc-sap-invoice]]
## Material flow spine
VehicleEntry → ArrivalSlip → Inspection → GRPOEntry  (inbound)
DispatchPlan → SalesDispatch / DispatchSession (barcode) → IntercompanyTransfer  (outbound)
```

---

## 4. Cross-entity link graph (`A --(field)--> B`)

**fleet-gate**
- Vehicle --(transporter)--> Transporter
- Vehicle --(vehicle_type)--> VehicleType
- Arrival --(vehicle)--> Vehicle · Arrival --(driver)--> Driver
- Arrival --(gate_ins[].id)--> EmptyVehicleGateIn · Arrival --(gate_outs[].id)--> SalesDispatch
- EmptyVehicleGateIn --(vehicle)--> Vehicle · --(driver)--> Driver · --(vehicle_entry)--> VehicleEntry · --(company)--> Company · --(reason)--> EmptyVehicleInReason · --(sap_from_warehouse/sap_to_warehouse)--> Warehouse
- EmptyVehicleGateOut --(vehicle)--> Vehicle · --(driver)--> Driver · --(vehicle_entry)--> VehicleEntry · --(company)--> Company
- VehicleEntry --(vehicle_id)--> Vehicle · --(driver_id)--> Driver
- BstOutSapTransfer --(from_warehouse/to_warehouse)--> Warehouse · --(branch_id)--> Branch
- SalesDispatch --(vehicle)--> Vehicle · --(transporter)--> Transporter · --(driver)--> Driver · --(arrival)--> Arrival · --(dispatch_plan)--> DispatchPlan · --(vehicle_entry)--> VehicleEntry · --(company)--> Company · --(customer_code)--> Customer · --(sap_doc_num)--> SAPInvoice · --(item_summary[].item_code)--> SAPItem · --(documents[])--> SalesDispatchDocument
- SalesDispatchDocument --(plan.id)--> DispatchPlan · --(branch_id)--> Branch · --(card_code)--> Customer · --(doc_num)--> SAPInvoice · --(item_summary[].item_code)--> SAPItem
- SalesDispatchLock --(company)--> Company · --(changed_by)--> User
- DispatchPlan --(vehicle_id)--> Vehicle · --(transporter_id)--> Transporter · --(driver_id)--> Driver · --(linked_vehicle_entry_id)--> VehicleEntry · --(gate_out_id / gate_out_vehicle_entry_id)--> SalesDispatch / VehicleEntry · --(empty_gate_in_entry_no)--> EmptyVehicleGateIn · --(sap_invoice_doc_num)--> SAPInvoice
- PartialScanRequest / ScanSkipRequest --(sales_dispatch)--> SalesDispatch · --(requested_by/reviewed_by)--> User · --(sap_doc_num)--> SAPInvoice

**quality-grpo**
- ArrivalSlip --(vehicle_entry_id)--> VehicleEntry · --(submitted_by)--> User · --(po_item_code)--> SAPItem · --(po_receipt_id/po_item_receipt)--> GRPOEntry (PO receipt carrier)
- Inspection --(arrival_slip_id)--> ArrivalSlip · --(rejected_qc_return_entry_id)--> VehicleEntry · --(material_type_name)--> MaterialType · --(po_item_code)--> SAPItem
- GRPOEntry --(vehicle_entry_id)--> VehicleEntry · --(suppliers[].supplier_code)--> Vendor · --(po_receipts[].items[].item_code)--> SAPItem · --(po_receipts[].po_number)--> SAPInvoice(PO#)
- GRPOServiceEntry --(dispatch_plan_id)--> DispatchPlan · --(linked_vehicle_entry_id)--> VehicleEntry · --(sap_invoice_doc_num)--> SAPInvoice

**barcode**
- BarcodeBox --(pallet)--> Pallet · --(dispatch_session)--> DispatchSession · --(created_by)--> User · --(item_code)--> SAPItem · --(current_warehouse)--> Warehouse · --(batch_number)--> WMSBatch
- Pallet --(dispatch_session)--> DispatchSession · --(created_by)--> User · --(item_code)--> SAPItem · --(current_warehouse)--> Warehouse · --(batch_number)--> WMSBatch
- DispatchSession --(created_by/dispatched_by/completed_by/closed_by)--> User · --(customer_code)--> Customer · --(sap_doc_num)--> SAPInvoice · --(lines[])--> DispatchSessionLine · --(scanned_units[])--> ScannedUnit
- DispatchSessionLine --(material_code)--> SAPItem · --(warehouse_code)--> Warehouse · --(batch_number)--> WMSBatch · --(session)--> DispatchSession
- ScannedUnit --(line)--> DispatchSessionLine · --(box)--> BarcodeBox · --(pallet)--> Pallet · --(scan_log)--> ScanHistory · --(item_code)--> SAPItem
- DispatchReport --(session_id)--> DispatchSession · --(customer_code)--> Customer
- DispatchReportBox --(box_id)--> BarcodeBox · --(pallet_barcode)--> Pallet · --(dispatch_session_id)--> DispatchSession · --(material_code)--> SAPItem
- DispatchReportPallet --(pallet_id)--> Pallet · --(dispatch_session_id)--> DispatchSession
- RejectedScan --(bill_number)--> DispatchSession
- IntercompanyTransfer --(source_company_code/destination_company_code)--> Company · --(sap_doc_num)--> SAPInvoice · --(lines[])--> IntercompanyTransferLine
- IntercompanyTransferLine --(box)--> BarcodeBox · --(from_company_code/to_company_code)--> Company · --(item_code)--> SAPItem
- LooseItem --(source_box/repacked_into_box)--> BarcodeBox · --(source_pallet)--> Pallet · --(created_by)--> User · --(item_code)--> SAPItem · --(current_warehouse)--> Warehouse
- PrintHistory --(reference_id)--> BarcodeBox|Pallet · --(printed_by)--> User
- ScanHistory --(entity_id)--> BarcodeBox|Pallet · --(context_ref_id)--> DispatchSession · --(scanned_by)--> User

**dispatch-billing**
- TransporterInvoice --(transporter_gstin)--> Transporter · --(refs)--> DispatchPlan
- BstOutSapTransfer / DispatchPlan --(branch_id)--> Branch · --(gl account_code)--> GLAccount

**production**
- Machine --(line_id)--> Line · ProductionRun --(line_id)--> Line · --(sap_order_id)--> SAPOrder
- SAPOrder --(item_code)--> SAPItem · WasteLog --(run_id)--> ProductionRun · --(material_code)--> SAPItem
- ChecklistTemplate --(machine_id)--> Machine · LineConfig/LineClearance --(line_id)--> Line · MachineChecklist --(machine_id)--> Machine · --(template_id)--> ChecklistTemplate

**maintenance**
- MaintenanceAsset --(category_id)--> AssetCategory · --(location_id)--> AssetLocation · --(department_id)--> AssetDepartment · --(line_id)--> Line
- AssetDocument/AssetPhoto/PMPlan/VendorVisit --(asset_id)--> MaintenanceAsset
- WorkOrder --(asset_id)--> MaintenanceAsset · --(line_id)--> Line · --(department_id)--> AssetDepartment · --(assigned_to)--> User
- WorkOrderPhoto --(work_order_id)--> WorkOrder · PMExecution --(pm_plan_id)--> PMPlan · --(asset_id)--> MaintenanceAsset · PMChecklistItem --(pm_plan_id)--> PMPlan
- Spare --(category_id)--> SpareCategory · SpareMovement/SpareRequest --(spare_id)--> Spare · --(work_order_id)--> WorkOrder

**warehouse**
- WMSStockItem --(warehouse_code)--> Warehouse · --(item_group)--> ItemGroup · --(item_code)--> SAPItem
- WMSStockMovement/WMSBatch --(warehouse_code)--> Warehouse · --(item_code)--> SAPItem
- WMSTransfer --(from_warehouse/to_warehouse)--> Warehouse · --(lines[].item_code)--> SAPItem
- WMSSalesOrderLine --(warehouse_code)--> Warehouse · --(customer_code)--> Customer · --(item_code)--> SAPItem
- WMSBillingItem --(warehouse_code)--> Warehouse · --(item_code)--> SAPItem
- BOMRequest --(item_code)--> SAPItem · --(requested_by)--> User · FGReceipt --(item_code)--> SAPItem · --(warehouse_code)--> Warehouse

**dashboards-accounts**
- AuthenticatedUserProfile --(companies[].company_id)--> Company
- Notification --(notification_type)--> NotificationPreference · --(reference_id, polymorphic via reference_type)--> VehicleEntry / person-entry / gate-entry
- StockItem/InventoryAgeReportRow --(warehouse)--> Warehouse · --(item_group)--> ItemGroup · --(item_code)--> SAPItem
- SalesPlanningRequirementRow --(item_code)--> SAPItem
- ProductionOrder --(warehouse)--> Warehouse · --(sku_code)--> SAPItem · --(components)--> ProductionOrderComponent
- ProductionOrderComponent --(prod_order_entry)--> ProductionOrder · --(component_warehouse)--> Warehouse · --(component_code)--> SAPItem · --(default_vendor)--> Vendor
- ProcurementShortfall --(component_code)--> SAPItem

---

## 5. SAP / SKU bridge points → jivo-data-bank product nodes

**Canonical bridge node** — `_bridge/sap-items/item-{item_code}.md` (consolidates `barcode items-oitm` (OITM master, ~500), production `sap-items`, QC `sap-items`):
```markdown
---
type: SAPItem
id: "{item_code}"          # e.g. FG0000143, PM0000087, RM-prefix
title: "{item_name}"
tags: [factory, bridge, sap-item, "{item_group_code}"]
sap_item_code: "{item_code}"   # ← FUSION KEY
company: JIVO_MART
product: "[[{item_code}]]"      # ← link to jivo-data-bank product node (same SAP code)
---
# {item_name} ({item_code})
inventory_uom · sales_uom · purchase_uom · manage_batch_numbers · manage_serial_numbers · is_inventory_item · is_sales_item · is_purchase_item · valid_for · frozen_for
## Related
- item_group_code → [[itemgroup-{item_group_code}]]
- Product (data-bank) → [[{item_code}]]   # bridged by SAP item code
## Backlinks (factory usage)  ← Obsidian auto-populates: every BarcodeBox/Pallet/WMSStockItem/SalesDispatch/GRPOEntry/… that carries this code
```

**Every factory entity that carries an SAP item code / SKU** (these all emit `--(item_code|material_code|component_code|sku_code|po_item_code)--> [[item-{code}]]`):

| Domain | Entities carrying SAP item/SKU |
|---|---|
| barcode | BarcodeBox, Pallet, DispatchSessionLine, ScannedUnit, DispatchReportBox, IntercompanyTransferLine, LooseItem, ItemOITM |
| quality-grpo | ArrivalSlip (`po_item_code`), Inspection (`po_item_code`), GRPOEntry (`po_receipts[].items[].item_code`) |
| fleet-gate | SalesDispatch (`item_summary[]` FG codes), SalesDispatchDocument (`item_summary[]`), ItemGroup (`item_group_code`) |
| production | SAPOrder (`item_code`), WasteLog (`material_code`) |
| warehouse | WMSStockItem, WMSStockMovement, WMSBatch, WMSTransfer, WMSSalesOrderLine, WMSBillingItem, BOMRequest, FGReceipt |
| dashboards | StockItem, InventoryAgeReportRow, SalesPlanningRequirementRow, ProductionOrder (`sku_code`), ProductionOrderComponent (`component_code`), ProcurementShortfall (`component_code`) |

**Other SAP-document bridges** (not product, but SAP system seams): `SAPInvoice` (`sap_doc_num` / `sap_invoice_doc_num` / PO numbers — SalesDispatch, DispatchPlan, GRPOServiceEntry, IntercompanyTransfer, DispatchSession), `BstOutSapTransfer` & `WMSTransfer` (`doc_entry/doc_num`), `GLAccount` (`account_code`), `Company` (`company_code`/`company_id`).

**Fusion mechanism (Phase C, into `jivo-data-bank`):**
1. Mount this vault at `jivo-data-bank/factory/`.
2. For each `item-{item_code}` note, set `product:` frontmatter to a wikilink targeting the existing data-bank product node addressed by the **same SAP item code** (FG/PM/RM prefix). If the data-bank product index keys on a different alias, add an alias `aliases: ["{item_code}"]` to the product node so `[[{item_code}]]` resolves.
3. SAP item code prefixes: **FG**=Finished Good, **PM**=Packaging Material, **RM**=Raw Material, group codes 102/105/106. The `factory/` pillar is the *manufacturing/supply lens*; the bridge node is the only place a factory entity touches the product graph — all 30+ item-bearing factory entities reach product nodes transitively through `item-{code}`.

---

## 6. Data presence table

| Domain | Entity | Status | Record count / note |
|---|---|---|---|
| fleet-gate | Vehicle | LIVE | 300+ |
| fleet-gate | VehicleType | LIVE | 7 |
| fleet-gate | Transporter | LIVE | 90+ |
| fleet-gate | Driver | LIVE | 306+ |
| fleet-gate | Arrival | LIVE | 117+ |
| fleet-gate | EmptyVehicleGateIn | LIVE | 230+ |
| fleet-gate | EmptyVehicleGateOut | LIVE (sparse) | few (1 seen) |
| fleet-gate | EmptyVehicleInReason | LIVE | 5 (enum) |
| fleet-gate | VehicleEntry | LIVE | 1254+ |
| fleet-gate | BstIn / BstOut / BstReturn | EMPTY | infer-only |
| fleet-gate | BstOutSapTransfer | LIVE | 3000+ |
| fleet-gate | JobWork / JobWorkSapGrpo / JobWorkSapProductionOrder | EMPTY | infer-only |
| fleet-gate | RejectedQcReturn | EMPTY | infer-only |
| fleet-gate | SalesDispatch | LIVE | 230+ |
| fleet-gate | SalesDispatchDocument | LIVE | many |
| fleet-gate | SalesDispatchLock | LIVE | 1 (singleton/co) |
| fleet-gate | DispatchPlan | LIVE | 690+ |
| fleet-gate | PartialScanRequest | LIVE | 40+ |
| fleet-gate | ScanSkipRequest | LIVE | 50+ |
| fleet-gate | DailyNeedCategory | LIVE | 1 |
| quality-grpo | ArrivalSlip | LIVE | 589+ ids (8 in pending view) |
| quality-grpo | Inspection | LIVE (NOT_STARTED) | 8 active; inspection_id null |
| quality-grpo | MaterialType | EMPTY | infer-only |
| quality-grpo | PrintDocument / ProductionQC / QCSAPItem | EMPTY | infer-only |
| quality-grpo | GRPOEntry | LIVE | 5 (all QC_PENDING); pending/history empty |
| quality-grpo | GRPOServiceEntry | LIVE | 6 pending; history empty |
| barcode | BarcodeBox | LIVE | ~151,000+ |
| barcode | Pallet | LIVE | ~3,170+ |
| barcode | DispatchSession | LIVE | ~188 active / ~118 completed / 0 closed |
| barcode | DispatchSessionLine / ScannedUnit | LIVE (embedded) | within sessions |
| barcode | DispatchReport / -Box / -Pallet | LIVE (projection) | ~188 / ~151k / ~3,170 |
| barcode | RejectedScan | LIVE | ~6,243+ |
| barcode | DispatchSettings | LIVE | 1 (singleton) |
| barcode | IntercompanyTransfer | LIVE | ~1,021 |
| barcode | IntercompanyTransferLine | LIVE (embedded) | ~27,875 barcodes |
| barcode | ItemOITM (→ SAPItem) | LIVE | ~500+ |
| barcode | LooseItem | LIVE | ~727 |
| barcode | PrintHistory | LIVE | ~156,354+ |
| barcode | ScanHistory | LIVE | ~25,212+ |
| dispatch-billing | DispatchPlan (views) | LIVE | 6 pending (deduped to plan-*) |
| dispatch-billing | BiltyGrpoHistory / OpenBilty | EMPTY | views of DispatchPlan |
| dispatch-billing | Branch | LIVE (ref) | 8 |
| dispatch-billing | TaxCode | LIVE (ref) | 24 |
| dispatch-billing | GLAccount | LIVE (ref) | multiple |
| dispatch-billing | TransporterInvoice | EMPTY | infer-only |
| procurement | Vendor | LIVE | 212 |
| procurement | Warehouse (deduped) | LIVE | 31 |
| procurement | ItemGroup (deduped) | LIVE | 10 |
| production | Line / Machine / ProductionRun / SAPOrder / SAPItem / WasteLog / BreakdownCategory / ChecklistTemplate / LineConfig / LineClearance / MachineChecklist | EMPTY | MES configured, not populated — schema inferred from analytics endpoints |
| maintenance | all 17 entities (assets, work-orders, pm-*, spares, vendor-visits…) | EMPTY | CMMS configured, not populated — enums from `maintenance options` |
| warehouse | Warehouse | LIVE | 31 |
| warehouse | WMSItemGroup (→ItemGroup) | LIVE | 9 |
| warehouse | WMSStockItem | LIVE | 953 |
| warehouse | WMSStockMovement | LIVE | ~200+ recent |
| warehouse | WMSBatch | LIVE | 300 |
| warehouse | WMSTransfer | LIVE | 14 docs / 200 lines |
| warehouse | WMSSalesOrderLine | LIVE | 86 orders / 300 lines |
| warehouse | WMSBillingItem | LIVE | 757 |
| warehouse | BOMRequest / FGReceipt | EMPTY | infer-only |
| dashboards-accounts | User | LIVE | ~25+ |
| dashboards-accounts | AuthenticatedUserProfile (me) | LIVE | 1 self |
| dashboards-accounts | Notification | LIVE | 25,000+ (max id 25856) |
| dashboards-accounts | NotificationPreference | LIVE | 23+ |
| dashboards-accounts | StockItem | LIVE | many |
| dashboards-accounts | InventoryAgeReportRow | LIVE | many |
| dashboards-accounts | SalesPlanningRequirementRow | EMPTY (scope) | JIVO_MART not in supported_companies (OIL/BEV only) |
| dashboards-accounts | ProductionOrder | LIVE | 1 active |
| dashboards-accounts | ProductionOrderComponent | LIVE | 1 (nested) |
| dashboards-accounts | ProcurementShortfall | EMPTY / NEEDS-PARAMS | empty for JIVO_MART scope |

> **Legend:** LIVE = real Jivo Mart rows pulled. EMPTY = endpoint exists, returned `[]` (hub + schema note only, no entity notes until populated). NEEDS-PARAMS / scope = empty because JIVO_MART is out of the endpoint's supported-companies scope.

---

## 7. Capture plan (Phase B) — exact CLI per entity

> All commands: `jivo-factory-pp-cli <cmd> --json 2>/dev/null | jq .` (binary on PATH, authenticated, `Company-Code: JIVO_MART`). Lightweight `*-names` subviews are NOT separate entities — skip. Empty endpoints are still pulled to confirm 0 rows and lock the hub.

| Entity | CLI command |
|---|---|
| Vehicle | `jivo-factory-pp-cli vehicle-management vehicles` |
| VehicleType | `jivo-factory-pp-cli vehicle-management vehicle-types` |
| Transporter | `jivo-factory-pp-cli vehicle-management transporters` |
| Driver | `jivo-factory-pp-cli driver-management drivers` |
| Arrival | `jivo-factory-pp-cli gate-core arrivals` |
| EmptyVehicleGateIn | `jivo-factory-pp-cli gate-core empty-vehicle-ins` |
| EmptyVehicleGateOut | `jivo-factory-pp-cli gate-core empty-vehicle-outs` |
| EmptyVehicleInReason | `jivo-factory-pp-cli gate-core empty-vehicle-ins-reasons` |
| VehicleEntry | `jivo-factory-pp-cli gate-core empty-vehicle-outs-eligible-entries` |
| BstIn / BstOut / BstReturn | `jivo-factory-pp-cli gate-core bst-ins` · `… bst-outs` · `… bst-returns` |
| BstOutSapTransfer | `jivo-factory-pp-cli gate-core bst-outs-sap-transfers` |
| JobWork / JobWorkSapGrpo / JobWorkSapProductionOrder | `jivo-factory-pp-cli gate-core job-work` · `… job-work-sap-grpos` · `… job-work-sap-production-orders` |
| RejectedQcReturn | `jivo-factory-pp-cli gate-core rejected-qc-returns` |
| SalesDispatch | `jivo-factory-pp-cli gate-core sales-dispatch` |
| SalesDispatchDocument | `jivo-factory-pp-cli gate-core sales-dispatch-documents` |
| SalesDispatchLock | `jivo-factory-pp-cli gate-core sales-dispatch-lock` |
| DispatchPlan (+ pipeline view) | `jivo-factory-pp-cli dispatch-plans` |
| PartialScanRequest | `jivo-factory-pp-cli docking-admin partial-scan-requests` |
| ScanSkipRequest | `jivo-factory-pp-cli docking-admin scan-skip-requests` |
| DailyNeedCategory | `jivo-factory-pp-cli daily-needs-gatein` |
| ArrivalSlip | `jivo-factory-pp-cli quality-control arrival-slips` |
| Inspection | `jivo-factory-pp-cli quality-control inspections` |
| MaterialType | `jivo-factory-pp-cli quality-control material-types` |
| PrintDocument | `jivo-factory-pp-cli quality-control print-documents` |
| ProductionQC | `jivo-factory-pp-cli quality-control production-qc` |
| QCSAPItem | `jivo-factory-pp-cli quality-control sap-items` |
| GRPOEntry | `jivo-factory-pp-cli grpo all-entries` |
| GRPOServiceEntry | `jivo-factory-pp-cli grpo service-pending` |
| BarcodeBox | `jivo-factory-pp-cli barcode boxes` |
| Pallet | `jivo-factory-pp-cli barcode pallets` |
| DispatchSession (+lines, +scanned_units embedded) | `jivo-factory-pp-cli barcode dispatch-sessions-active` · `… dispatch-sessions-completed` · `… dispatch-sessions-closed` |
| DispatchReport | `jivo-factory-pp-cli barcode dispatch-reports` |
| DispatchReportBox | `jivo-factory-pp-cli barcode dispatch-reports-boxes` |
| DispatchReportPallet | `jivo-factory-pp-cli barcode dispatch-reports-pallets` |
| RejectedScan | `jivo-factory-pp-cli barcode dispatch-reports-rejected-scans` |
| DispatchSettings | `jivo-factory-pp-cli barcode dispatch-settings` |
| IntercompanyTransfer (+lines) | `jivo-factory-pp-cli barcode intercompany-dashboard` |
| ItemOITM (→ SAPItem master) | `jivo-factory-pp-cli barcode items-oitm` |
| LooseItem | `jivo-factory-pp-cli barcode loose` |
| PrintHistory | `jivo-factory-pp-cli barcode print-history` |
| ScanHistory | `jivo-factory-pp-cli barcode scan-history` |
| Branch / TaxCode / GLAccount | `jivo-factory-pp-cli dispatch bilty-grpo-options` |
| TransporterInvoice | `jivo-factory-pp-cli dispatch transporter-invoices-history` |
| (DispatchPlan billing views) | `jivo-factory-pp-cli dispatch bilty-grpo-pending` · `… bilty-grpo-history` · `… open-bilties` |
| Vendor | `jivo-factory-pp-cli po vendors` |
| Warehouse | `jivo-factory-pp-cli po warehouses` (or `warehouse wms-warehouses`) |
| ItemGroup | `jivo-factory-pp-cli non-moving-rm` (or `warehouse wms-item-groups`) |
| Line | `jivo-factory-pp-cli production-execution lines` |
| Machine | `jivo-factory-pp-cli production-execution machines` |
| ProductionRun | `jivo-factory-pp-cli production-execution runs` |
| SAPOrder | `jivo-factory-pp-cli production-execution sap-orders` |
| SAPItem (production view) | `jivo-factory-pp-cli production-execution sap-items` |
| WasteLog | `jivo-factory-pp-cli production-execution waste` |
| BreakdownCategory | `jivo-factory-pp-cli production-execution breakdown-categories` |
| ChecklistTemplate | `jivo-factory-pp-cli production-execution checklist-templates` |
| LineConfig | `jivo-factory-pp-cli production-execution line-configs` |
| LineClearance | `jivo-factory-pp-cli production-execution line-clearance` |
| MachineChecklist | `jivo-factory-pp-cli production-execution machine-checklists` |
| MaintenanceAsset | `jivo-factory-pp-cli maintenance assets` |
| AssetCategory / AssetDepartment / AssetLocation | `jivo-factory-pp-cli maintenance asset-categories` · `… asset-departments` · `… asset-locations` |
| AssetDocument / AssetPhoto | `jivo-factory-pp-cli maintenance asset-documents` · `… asset-photos` |
| WorkOrder / WorkOrderPhoto | `jivo-factory-pp-cli maintenance work-orders` · `… work-order-photos` |
| PMPlan / PMExecution / PMChecklistItem | `jivo-factory-pp-cli maintenance pm-plans` · `… pm-executions` · `… pm-checklist-items` |
| Spare / SpareCategory / SpareMovement / SpareRequest | `jivo-factory-pp-cli maintenance spares` · `… spare-categories` · `… spare-movements` · `… spare-requests` |
| VendorVisit | `jivo-factory-pp-cli maintenance vendor-visits` |
| WMSStockItem | `jivo-factory-pp-cli warehouse wms-stock-overview` |
| WMSStockMovement | `jivo-factory-pp-cli warehouse wms-stock-movements` |
| WMSBatch | `jivo-factory-pp-cli warehouse wms-batches-expiry` |
| WMSTransfer | `jivo-factory-pp-cli warehouse wms-transfers-overview` |
| WMSSalesOrderLine | `jivo-factory-pp-cli warehouse wms-sales-orders-backlog` |
| WMSBillingItem | `jivo-factory-pp-cli warehouse wms-billing-overview` |
| BOMRequest / FGReceipt | `jivo-factory-pp-cli warehouse bom-requests` · `… fg-receipts` |
| User | `jivo-factory-pp-cli accounts users` |
| AuthenticatedUserProfile (me) | `jivo-factory-pp-cli accounts me` |
| Notification | `jivo-factory-pp-cli notifications list` |
| NotificationPreference | `jivo-factory-pp-cli notifications preferences` |
| StockItem | `jivo-factory-pp-cli dashboards stock` |
| InventoryAgeReportRow | `jivo-factory-pp-cli dashboards inventory-age-report` |
| InventoryAgeFilterOptions (seeds ItemGroup/Warehouse refs) | `jivo-factory-pp-cli dashboards inventory-age-filter-options` |
| SalesPlanningRequirementRow | `jivo-factory-pp-cli dashboards sales-planning-requirement-report` |
| ProductionOrder | `jivo-factory-pp-cli sap plan-dashboard-summary` |
| ProductionOrderComponent | `jivo-factory-pp-cli sap plan-dashboard-details` |
| ProcurementShortfall | `jivo-factory-pp-cli sap plan-dashboard-procurement` |

**Capture order (respects FK dependencies — masters first):**
1. **Bridge & masters:** `barcode items-oitm` (SAPItem), `po vendors`, `po warehouses`, `non-moving-rm`/`wms-item-groups` (ItemGroup), `accounts users`, `accounts me`, `dispatch bilty-grpo-options` (Branch/TaxCode/GLAccount), Company nodes (from `me.companies` + barcode company codes).
2. **fleet-gate masters:** vehicle-types, transporters, drivers, vehicles.
3. **Sessions/entries:** vehicle-entries, arrivals, empty-vehicle-ins/-outs, bst-*, sales-dispatch(+documents/lock), dispatch-plans.
4. **quality-grpo:** arrival-slips → inspections → grpo all-entries → grpo service-pending.
5. **barcode txns:** boxes, pallets, dispatch-sessions-*, dispatch-reports-*, rejected-scans, loose, intercompany-dashboard, print-history, scan-history.
6. **warehouse WMS:** wms-stock/-movements/-batches/-transfers/-sales-orders/-billing, bom-requests, fg-receipts.
7. **dashboards/sap:** stock, inventory-age-report, production-orders (sap plan-dashboard-*), notifications.
8. **Empty endpoints last:** production-execution *, maintenance *, dispatch transporter-invoices, sales-planning — pull once to confirm 0 rows, write hub + schema stub only.

**Per-record rendering:** for each `results[]` element, emit one note at `factory/<domain>/<folder>/<slug>-<keyvalue>.md` using the frontmatter+body+wikilink spec in §2; on first sight of any referenced `item_code` / `customer_code` / `company_code` / `sap_doc_num` not yet present, stub the matching `_bridge/` node. After all pulls, regenerate every `_moc-*.md` (list notes) and `_HOME.md`.

Linked: [[docs/factory/FACTORY_MAP|FACTORY_MAP]] · [[docs/FACTORY_CLI_PLAN|FACTORY_CLI_PLAN]] · [[docs/READ_ONLY_LAW|READ_ONLY_LAW]]
