---
title: "Jivo Mart UI Route Map (per section) — extracted from ji.jivo.in bundle"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: map
tags: [jivogpt, factory-cli, routes]
---

# Jivo Mart UI Route Map (per section) — extracted from ji.jivo.in bundle

> **Provenance — imported 2026-07-19; source snapshot 2026-06-30.** This note came from the JIVO_MART-only `daman8271/jivo-factory-intel` baseline. For the current three-company study and the live-verified 2026-07-19 state, use [[docs/factory/FACTORY_MAP|FACTORY_MAP]] and [[CLI/factory-cli/README|the current CLI guide]].

> Each section's react-router pages. Sub-paths = subpages/steps. API prefixes feed each.


## Admin  (UI /admin · API /admin, /docking-admin, /accounts)
**UI routes (3):**
- `/admin`
- `/admin/docking/partial-dispatch-approvals`
- `/admin/docking/scan-approvals`

## Dashboards  (UI /dashboards · API /dashboards, /sap, /non-moving-rm, /inventory-age, /sales-planning-requirement, /stock)
**UI routes (17):**
- `/dashboards`
- `/dashboards/dispatch-pipeline`
- `/dashboards/dispatch-plans`
- `/dashboards/inventory-age`
- `/dashboards/inventory-age/filter-options/`
- `/dashboards/inventory-age/report/`
- `/dashboards/non-moving`
- `/dashboards/production-movement`
- `/dashboards/sales-planning-requirement`
- `/dashboards/sales-planning-requirement/analysis/`
- `/dashboards/sales-planning-requirement/refresh/`
- `/dashboards/sales-planning-requirement/report/`
- `/dashboards/sales-planning-requirement/status/`
- `/dashboards/sap-plan`
- `/dashboards/stock-levels`
- `/dashboards/stock/`
- `/dashboards/stock/as-of/`

## Dispatch  (UI /dispatch, /dispatch-plans · API /dispatch, /dispatch-plans)
**UI routes (34):**
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

## Gate  (UI /gate · API /gate-core, /daily-needs-gatein, /person-gatein, /raw-material-gatein, /fixed-asset-gatein, /maintenance-gatein, /construction-gatein, /weighment, /security-checks, /labour-count)
**UI routes (127):**
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

## Vehicle Management  (UI /vehicle-management · API /vehicle-management, /driver-management)
**UI routes (14):**
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

## Quality Control  (UI /qc · API /quality-control)
**UI routes (19):**
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

## GRPO  (UI /grpo · API /grpo)
**UI routes (27):**
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

## Production  (UI /production · API /production-execution, /production-planning)
**UI routes (31):**
- `/production`
- `/production/execution`
- `/production/execution/breakdowns`
- `/production/execution/line-clearance`
- `/production/execution/line-clearance/:clearanceId`
- `/production/execution/line-clearance/create`
- `/production/execution/line-management`
- `/production/execution/machine-checklists`
- `/production/execution/master-data`
- `/production/execution/reports`
- `/production/execution/reports/cost-analysis`
- `/production/execution/reports/daily`
- `/production/execution/reports/downtime-pareto`
- `/production/execution/reports/monthly-summary`
- `/production/execution/reports/oee-trend`
- `/production/execution/reports/plan-vs-production`
- `/production/execution/reports/procurement-vs-planned`
- `/production/execution/reports/resource-consumption`
- `/production/execution/reports/waste-trend`
- `/production/execution/runs/:runId`
- `/production/execution/runs/:runId/breakdowns`
- `/production/execution/runs/:runId/qc`
- `/production/execution/runs/:runId/resources`
- `/production/execution/runs/:runId/yield`
- `/production/execution/start-run`
- `/production/execution/waste`
- `/production/planning`
- `/production/planning/:planId`
- `/production/planning/:planId/edit`
- `/production/planning/bulk-import`
- `/production/planning/create`

## Maintenance  (UI /maintenance · API /maintenance)
**UI routes (35):**
- `/maintenance`
- `/maintenance/alerts/`
- `/maintenance/asset-categories/`
- `/maintenance/asset-departments/`
- `/maintenance/asset-documents/`
- `/maintenance/asset-locations/`
- `/maintenance/asset-photos/`
- `/maintenance/assets`
- `/maintenance/assets/`
- `/maintenance/assets/:assetId`
- `/maintenance/automation`
- `/maintenance/dashboard/`
- `/maintenance/masters`
- `/maintenance/options/`
- `/maintenance/pm`
- `/maintenance/pm-checklist-items/`
- `/maintenance/pm-executions/`
- `/maintenance/pm-plans/`
- `/maintenance/pm-plans/generate-due/`
- `/maintenance/reports`
- `/maintenance/reports/`
- `/maintenance/scan/lookup/`
- `/maintenance/scan/work-order/`
- `/maintenance/spare-categories/`
- `/maintenance/spare-movements/`
- `/maintenance/spare-requests/`
- `/maintenance/spares`
- `/maintenance/spares/`
- `/maintenance/spares/low-stock/`
- `/maintenance/spares/stock/`
- `/maintenance/vendor-visits/`
- `/maintenance/work-order-photos/`
- `/maintenance/work-orders`
- `/maintenance/work-orders/`
- `/maintenance/work-orders/:workOrderId`

## Warehouse  (UI /warehouse · API /warehouse)
**UI routes (19):**
- `/warehouse`
- `/warehouse/bom-requests`
- `/warehouse/bom-requests/`
- `/warehouse/bom-requests/:requestId`
- `/warehouse/bom-requests/create/`
- `/warehouse/fg-receipts`
- `/warehouse/fg-receipts/`
- `/warehouse/fg-receipts/create/`
- `/warehouse/stock/check/`
- `/warehouse/wms/batches/expiry/`
- `/warehouse/wms/billing/overview/`
- `/warehouse/wms/dashboard/`
- `/warehouse/wms/item-groups/`
- `/warehouse/wms/sales-orders/backlog/`
- `/warehouse/wms/stock/movements/`
- `/warehouse/wms/stock/overview/`
- `/warehouse/wms/transfers/overview/`
- `/warehouse/wms/warehouses/`
- `/warehouse/wms/warehouses/summary/`

## WMS  (UI /wms · API /wms, /warehouse/wms)
**UI routes (7):**
- `/wms`
- `/wms/batches`
- `/wms/billing`
- `/wms/orders`
- `/wms/stock`
- `/wms/transfers`
- `/wms/warehouses`

## Barcode  (UI /barcode · API /barcode)
**UI routes (50):**
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

## Notifications  (UI /notifications · API /notifications)
**UI routes (10):**
- `/notifications`
- `/notifications/`
- `/notifications/devices/register/`
- `/notifications/devices/unregister/`
- `/notifications/mark-read/`
- `/notifications/preferences/`
- `/notifications/send`
- `/notifications/send/`
- `/notifications/test/`
- `/notifications/unread-count/`

Linked: [[docs/factory/FACTORY_MAP|FACTORY_MAP]] · [[docs/FACTORY_CLI_PLAN|FACTORY_CLI_PLAN]] · [[docs/READ_ONLY_LAW|READ_ONLY_LAW]]
