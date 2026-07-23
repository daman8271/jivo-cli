---
name: pp-jivo-factory
title: Jivo Factory — Printing Press CLI Skill
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: skill
tags: [jivogpt, factory, cli, skill]
description: "Printing Press CLI for Jivo Factory. JIVO factory management CLI (ji.jivo.in / factory.jivo."
author: "daman8271"
license: "Apache-2.0"
argument-hint: "<command> [args] | install cli|mcp"
allowed-tools: "Read Bash"
metadata:
  openclaw:
    requires:
      bins:
        - jivo-factory-pp-cli
    install:
      - kind: go
        bins: [jivo-factory-pp-cli]
        module: github.com/mvanhorn/printing-press-library/library/developer-tools/jivo-factory/cmd/jivo-factory-pp-cli
---

# Jivo Factory — Printing Press CLI

## Prerequisites: Install the CLI

This skill drives the `jivo-factory-pp-cli` binary. **You must verify the CLI is installed before invoking any command from this skill.** If it is missing, install it first:

1. Install via the Printing Press installer. It defaults binaries to `$HOME/.local/bin` on macOS/Linux and `%LOCALAPPDATA%\Programs\PrintingPress\bin` on Windows:
   ```bash
   npx -y @mvanhorn/printing-press-library install jivo-factory --cli-only
   ```
2. Verify: `jivo-factory-pp-cli --version`
3. Ensure the reported install directory is on `$PATH` for the agent/runtime that will invoke this skill.

If the `npx` install fails (no Node, offline, etc.), fall back to a direct Go install (requires Go 1.26.4 or newer). This installs into `$GOPATH/bin` (default `$HOME/go/bin`), so add that directory to `$PATH` instead:

```bash
go install github.com/mvanhorn/printing-press-library/library/developer-tools/jivo-factory/cmd/jivo-factory-pp-cli@latest
```

If `--version` reports "command not found" after install, the runtime cannot see the binary directory on `$PATH`. Do not proceed with skill commands until verification succeeds.

JIVO factory management CLI (ji.jivo.in / factory.jivo.in) — read-only access to all 3 companies (JIVO_MART, JIVO_OIL, JIVO_BEVERAGES via --company / JIVO_FACTORY_COMPANY): gate, vehicles, quality control, GRPO, barcode traceability, dispatch, production, WMS, maintenance & dashboards

## When Not to Use This CLI

Do not activate this CLI for requests that require creating, updating, deleting, publishing, commenting, upvoting, inviting, ordering, sending messages, booking, purchasing, or changing remote state. This printed CLI exposes read-only commands for inspection, export, sync, and analysis.

## Command Reference

**accounts** — Accounts & users

- `jivo-factory-pp-cli accounts departments` — GET /accounts/departments/ — departments list (15 rows, shared across companies)
- `jivo-factory-pp-cli accounts me` — GET /accounts/me/ — accounts me
- `jivo-factory-pp-cli accounts users` — GET /accounts/users/ — accounts users

**barcode** — Barcode & traceability — boxes, pallets, dispatch sessions, intercompany

- `jivo-factory-pp-cli barcode boxes` — GET /barcode/boxes/ — barcode boxes
- `jivo-factory-pp-cli barcode dispatch-reports` — GET /barcode/dispatch/reports/ — barcode dispatch reports
- `jivo-factory-pp-cli barcode dispatch-reports-boxes` — GET /barcode/dispatch/reports/boxes/ — barcode dispatch reports boxes
- `jivo-factory-pp-cli barcode dispatch-reports-pallets` — GET /barcode/dispatch/reports/pallets/ — barcode dispatch reports pallets
- `jivo-factory-pp-cli barcode dispatch-reports-rejected-scans` — GET /barcode/dispatch/reports/rejected-scans/ — barcode dispatch reports rejected scans
- `jivo-factory-pp-cli barcode dispatch-sessions` — GET /barcode/dispatch/sessions/ — barcode dispatch sessions (all)
- `jivo-factory-pp-cli barcode dispatch-sessions-active` — GET /barcode/dispatch/sessions/active/ — barcode dispatch sessions active
- `jivo-factory-pp-cli barcode dispatch-sessions-closed` — GET /barcode/dispatch/sessions/closed/ — barcode dispatch sessions closed
- `jivo-factory-pp-cli barcode dispatch-sessions-completed` — GET /barcode/dispatch/sessions/completed/ — barcode dispatch sessions completed
- `jivo-factory-pp-cli barcode dispatch-sessions-from-bill` — GET /barcode/dispatch/sessions/from-bill/ — barcode dispatch sessions from bill
- `jivo-factory-pp-cli barcode dispatch-settings` — GET /barcode/dispatch/settings/ — barcode dispatch settings
- `jivo-factory-pp-cli barcode intercompany-dashboard` — GET /barcode/intercompany/dashboard/ — barcode intercompany dashboard
- `jivo-factory-pp-cli barcode intercompany-trace` — GET /barcode/intercompany/trace/ — trace an intercompany barcode
- `jivo-factory-pp-cli barcode intercompany-transfers` — GET /barcode/intercompany/transfers/ — barcode intercompany transfers list
- `jivo-factory-pp-cli barcode items-oitm` — GET /barcode/items/oitm/ — barcode items oitm
- `jivo-factory-pp-cli barcode loose` — GET /barcode/loose/ — barcode loose
- `jivo-factory-pp-cli barcode pallets` — GET /barcode/pallets/ — barcode pallets
- `jivo-factory-pp-cli barcode print-history` — GET /barcode/print/history/ — barcode print history
- `jivo-factory-pp-cli barcode production-release-oil` — GET /barcode/production-release-oil/ — oil production release (JIVO_OIL only; 503 for other companies)
- `jivo-factory-pp-cli barcode scan-history` — GET /barcode/scan/history/ — barcode scan history

**company** — Company master — the Select-Company screen

- `jivo-factory-pp-cli company` — GET /company/companies/ — the 3 companies backing the Select-Company screen

**daily-needs-gatein** — Daily-needs gate entries

- `jivo-factory-pp-cli daily-needs-gatein` — GET /daily-needs-gatein/gate-entries/daily-need/categories/ — daily needs gatein gate entries daily need categories

**dashboards** — Admin dashboards (stock, inventory-age, dispatch pipeline, SAP plan)

- `jivo-factory-pp-cli dashboards inventory-age-filter-options` — GET /dashboards/inventory-age/filter-options/ — dashboards inventory age filter options
- `jivo-factory-pp-cli dashboards inventory-age-report` — GET /dashboards/inventory-age/report/ — dashboards inventory age report
- `jivo-factory-pp-cli dashboards sales-planning-requirement-analysis` — GET /dashboards/sales-planning-requirement/analysis/ — dashboards sales planning requirement analysis
- `jivo-factory-pp-cli dashboards sales-planning-requirement-report` — GET /dashboards/sales-planning-requirement/report/ — dashboards sales planning requirement report
- `jivo-factory-pp-cli dashboards sales-planning-requirement-status` — GET /dashboards/sales-planning-requirement/status/ — dashboards sales planning requirement status
- `jivo-factory-pp-cli dashboards stock` — GET /dashboards/stock/ — dashboards stock
- `jivo-factory-pp-cli dashboards stock-as-of` — GET /dashboards/stock/as-of/ — stock snapshot as of a date

**dispatch** — Dispatch — docking, bilty-GRPO, transporter invoices

- `jivo-factory-pp-cli dispatch bilty-grpo-history` — GET /dispatch/bilty-grpo/history/ — dispatch bilty grpo history
- `jivo-factory-pp-cli dispatch bilty-grpo-options` — GET /dispatch/bilty-grpo/options/ — dispatch bilty grpo options
- `jivo-factory-pp-cli dispatch bilty-grpo-pending` — GET /dispatch/bilty-grpo/pending/ — dispatch bilty grpo pending
- `jivo-factory-pp-cli dispatch bilty-grpo-preview` — GET /dispatch/bilty-grpo/preview/{dispatch_plan_id}/ — bilty-GRPO posting preview for a dispatch plan
- `jivo-factory-pp-cli dispatch open-bilties` — GET /dispatch/open-bilties/ — dispatch open bilties
- `jivo-factory-pp-cli dispatch transporter-invoices-history` — GET /dispatch/transporter-invoices/history/ — dispatch transporter invoices history

**dispatch-plans** — Dispatch plans & pipeline

- `jivo-factory-pp-cli dispatch-plans bills` — GET /dispatch-plans/bills/ — bills in a date window
- `jivo-factory-pp-cli dispatch-plans pipeline` — GET /dispatch-plans/pipeline/ — dispatch plans pipeline

**docking-admin** — Docking admin scan approvals

- `jivo-factory-pp-cli docking-admin partial-scan-requests` — GET /docking-admin/partial-scan-requests/ — docking admin partial scan requests
- `jivo-factory-pp-cli docking-admin scan-skip-requests` — GET /docking-admin/scan-skip-requests/ — docking admin scan skip requests

**driver-management** — Drivers

- `jivo-factory-pp-cli driver-management drivers` — GET /driver-management/drivers/ — driver management drivers
- `jivo-factory-pp-cli driver-management drivers-names` — GET /driver-management/drivers/names/ — driver management drivers names

**gate-core** — Gate — arrivals, BST in/out/return, empty-vehicle, job-work, sales-dispatch gate-out

- `jivo-factory-pp-cli gate-core arrivals` — GET /gate-core/arrivals/ — gate core arrivals
- `jivo-factory-pp-cli gate-core arrivals-expected` — GET /gate-core/arrivals/expected/ — expected arrival for a vehicle
- `jivo-factory-pp-cli gate-core bst-ins` — GET /gate-core/bst-ins/ — gate core bst ins
- `jivo-factory-pp-cli gate-core bst-ins-eligible-outs` — GET /gate-core/bst-ins/eligible-outs/ — gate core bst ins eligible outs
- `jivo-factory-pp-cli gate-core bst-outs` — GET /gate-core/bst-outs/ — gate core bst outs
- `jivo-factory-pp-cli gate-core bst-outs-sap-transfers` — GET /gate-core/bst-outs/sap-transfers/ — gate core bst outs sap transfers
- `jivo-factory-pp-cli gate-core bst-returns` — GET /gate-core/bst-returns/ — gate core bst returns
- `jivo-factory-pp-cli gate-core bst-returns-eligible-outs` — GET /gate-core/bst-returns/eligible-outs/ — gate core bst returns eligible outs
- `jivo-factory-pp-cli gate-core empty-vehicle-ins` — GET /gate-core/empty-vehicle-ins/ — gate core empty vehicle ins
- `jivo-factory-pp-cli gate-core empty-vehicle-ins-eligible` — GET /gate-core/empty-vehicle-ins/eligible/ — gate core empty vehicle ins eligible
- `jivo-factory-pp-cli gate-core empty-vehicle-ins-reasons` — GET /gate-core/empty-vehicle-ins/reasons/ — gate core empty vehicle ins reasons
- `jivo-factory-pp-cli gate-core empty-vehicle-outs` — GET /gate-core/empty-vehicle-outs/ — gate core empty vehicle outs
- `jivo-factory-pp-cli gate-core empty-vehicle-outs-eligible-entries` — GET /gate-core/empty-vehicle-outs/eligible-entries/ — gate core empty vehicle outs eligible entries
- `jivo-factory-pp-cli gate-core job-work` — GET /gate-core/job-work/ — gate core job work
- `jivo-factory-pp-cli gate-core job-work-sap-grpos` — GET /gate-core/job-work/sap-grpos/ — gate core job work sap grpos
- `jivo-factory-pp-cli gate-core job-work-sap-production-orders` — GET /gate-core/job-work/sap-production-orders/ — gate core job work sap production orders
- `jivo-factory-pp-cli gate-core rejected-qc-returns` — GET /gate-core/rejected-qc-returns/ — gate core rejected qc returns
- `jivo-factory-pp-cli gate-core sales-dispatch` — GET /gate-core/sales-dispatch/ — gate core sales dispatch
- `jivo-factory-pp-cli gate-core sales-dispatch-documents` — GET /gate-core/sales-dispatch/documents/ — gate core sales dispatch documents
- `jivo-factory-pp-cli gate-core sales-dispatch-lock` — GET /gate-core/sales-dispatch/lock/ — gate core sales dispatch lock
- `jivo-factory-pp-cli gate-core sales-dispatch-pending-bookings` — GET /gate-core/sales-dispatch/pending-bookings/ — gate core sales dispatch pending bookings
- `jivo-factory-pp-cli gate-core sales-dispatch-reports` — GET /gate-core/sales-dispatch/reports/ — gate core sales dispatch reports

**grpo** — GRPO — goods-receipt POs (material & service)

- `jivo-factory-pp-cli grpo all-entries` — GET /grpo/all-entries/ — grpo all entries
- `jivo-factory-pp-cli grpo history` — GET /grpo/history/ — grpo history
- `jivo-factory-pp-cli grpo history-detail` — GET /grpo/history/{posting_id}/ — a posted material GRPO
- `jivo-factory-pp-cli grpo pending` — GET /grpo/pending/ — grpo pending
- `jivo-factory-pp-cli grpo preview` — GET /grpo/preview/{vehicle_entry_id}/ — GRPO preview for a vehicle entry
- `jivo-factory-pp-cli grpo service-history` — GET /grpo/service/history/ — grpo service history
- `jivo-factory-pp-cli grpo service-history-detail` — GET /grpo/service/history/{posting_id}/ — a posted service GRPO
- `jivo-factory-pp-cli grpo service-options` — GET /grpo/service/options/ — grpo service options
- `jivo-factory-pp-cli grpo service-pending` — GET /grpo/service/pending/ — grpo service pending
- `jivo-factory-pp-cli grpo service-preview` — GET /grpo/service/preview/{dispatch_plan_id}/ — service-GRPO preview for a dispatch plan
- `jivo-factory-pp-cli grpo summary` — GET /grpo/summary/ — grpo summary

**maintenance** — Maintenance CMMS — assets, PM, spares, work orders

- `jivo-factory-pp-cli maintenance alerts` — GET /maintenance/alerts/ — maintenance alerts
- `jivo-factory-pp-cli maintenance asset-categories` — GET /maintenance/asset-categories/ — maintenance asset categories
- `jivo-factory-pp-cli maintenance asset-departments` — GET /maintenance/asset-departments/ — maintenance asset departments
- `jivo-factory-pp-cli maintenance asset-documents` — GET /maintenance/asset-documents/ — maintenance asset documents
- `jivo-factory-pp-cli maintenance asset-locations` — GET /maintenance/asset-locations/ — maintenance asset locations
- `jivo-factory-pp-cli maintenance asset-photos` — GET /maintenance/asset-photos/ — maintenance asset photos
- `jivo-factory-pp-cli maintenance assets` — GET /maintenance/assets/ — maintenance assets
- `jivo-factory-pp-cli maintenance dashboard` — GET /maintenance/dashboard/ — maintenance dashboard
- `jivo-factory-pp-cli maintenance options` — GET /maintenance/options/ — maintenance options
- `jivo-factory-pp-cli maintenance pm-checklist-items` — GET /maintenance/pm-checklist-items/ — maintenance pm checklist items
- `jivo-factory-pp-cli maintenance pm-executions` — GET /maintenance/pm-executions/ — maintenance pm executions
- `jivo-factory-pp-cli maintenance pm-plans` — GET /maintenance/pm-plans/ — maintenance pm plans
- `jivo-factory-pp-cli maintenance reports` — GET /maintenance/reports/ — maintenance reports
- `jivo-factory-pp-cli maintenance scan-lookup` — GET /maintenance/scan/lookup/ — asset/spare scan lookup
- `jivo-factory-pp-cli maintenance spare-categories` — GET /maintenance/spare-categories/ — maintenance spare categories
- `jivo-factory-pp-cli maintenance spare-movements` — GET /maintenance/spare-movements/ — maintenance spare movements
- `jivo-factory-pp-cli maintenance spare-requests` — GET /maintenance/spare-requests/ — maintenance spare requests
- `jivo-factory-pp-cli maintenance spares` — GET /maintenance/spares/ — maintenance spares
- `jivo-factory-pp-cli maintenance spares-low-stock` — GET /maintenance/spares/low-stock/ — maintenance spares low stock
- `jivo-factory-pp-cli maintenance spares-stock` — GET /maintenance/spares/stock/ — spare stock lookup by code
- `jivo-factory-pp-cli maintenance vendor-visits` — GET /maintenance/vendor-visits/ — maintenance vendor visits
- `jivo-factory-pp-cli maintenance work-order-photos` — GET /maintenance/work-order-photos/ — maintenance work order photos
- `jivo-factory-pp-cli maintenance work-orders` — GET /maintenance/work-orders/ — maintenance work orders

**non-moving-rm** — Non-moving raw material

- `jivo-factory-pp-cli non-moving-rm item-groups` — GET /non-moving-rm/item-groups/ — non moving rm item groups
- `jivo-factory-pp-cli non-moving-rm report` — GET /non-moving-rm/report/ — non-moving raw-material report (replaces the dead bare endpoint)

**notifications** — Notifications & device tokens

- `jivo-factory-pp-cli notifications list` — GET /notifications/ — notifications
- `jivo-factory-pp-cli notifications preferences` — GET /notifications/preferences/ — notifications preferences
- `jivo-factory-pp-cli notifications unread-count` — GET /notifications/unread-count/ — notifications unread count

**person-gatein** — Person gate-in — visitors, labour, contractors at the campus gate

- `jivo-factory-pp-cli person-gatein contractors` — GET /person-gatein/contractors/ — contractor master
- `jivo-factory-pp-cli person-gatein entries` — GET /person-gatein/entries/ — person gate-in entries (paginated)
- `jivo-factory-pp-cli person-gatein gates` — GET /person-gatein/gates/ — gate master
- `jivo-factory-pp-cli person-gatein labours` — GET /person-gatein/labours/ — labour master
- `jivo-factory-pp-cli person-gatein person-types` — GET /person-gatein/person-types/ — person type master
- `jivo-factory-pp-cli person-gatein visitors` — GET /person-gatein/visitors/ — visitor master

**po** — Purchase orders — open POs, vendors, warehouses

- `jivo-factory-pp-cli po vendors` — GET /po/vendors/ — po vendors
- `jivo-factory-pp-cli po warehouses` — GET /po/warehouses/ — po warehouses

**production-execution** — Production execution (MES) — runs, lines, machines, OEE, waste

- `jivo-factory-pp-cli production-execution breakdown-categories` — GET /production-execution/breakdown-categories/ — production execution breakdown categories
- `jivo-factory-pp-cli production-execution checklist-templates` — GET /production-execution/checklist-templates/ — production execution checklist templates
- `jivo-factory-pp-cli production-execution costs-analytics` — GET /production-execution/costs/analytics/ — production execution costs analytics
- `jivo-factory-pp-cli production-execution line-clearance` — GET /production-execution/line-clearance/ — production execution line clearance
- `jivo-factory-pp-cli production-execution line-configs` — GET /production-execution/line-configs/ — production execution line configs
- `jivo-factory-pp-cli production-execution line-configs-auto-fill` — GET /production-execution/line-configs/auto-fill/ — auto-fill config for a production line
- `jivo-factory-pp-cli production-execution lines` — GET /production-execution/lines/ — production execution lines
- `jivo-factory-pp-cli production-execution machine-checklists` — GET /production-execution/machine-checklists/ — production execution machine checklists
- `jivo-factory-pp-cli production-execution machines` — GET /production-execution/machines/ — production execution machines
- `jivo-factory-pp-cli production-execution reports-analytics` — GET /production-execution/reports/analytics/ — production execution reports analytics
- `jivo-factory-pp-cli production-execution reports-analytics-cost-analysis` — GET /production-execution/reports/analytics/cost-analysis/ — production execution reports analytics cost analysis
- `jivo-factory-pp-cli production-execution reports-analytics-downtime` — GET /production-execution/reports/analytics/downtime/ — production execution reports analytics downtime
- `jivo-factory-pp-cli production-execution reports-analytics-downtime-pareto` — GET /production-execution/reports/analytics/downtime-pareto/ — production execution reports analytics downtime pareto
- `jivo-factory-pp-cli production-execution reports-analytics-monthly-summary` — GET /production-execution/reports/analytics/monthly-summary/ — production execution reports analytics monthly summary
- `jivo-factory-pp-cli production-execution reports-analytics-oee` — GET /production-execution/reports/analytics/oee/ — production execution reports analytics oee
- `jivo-factory-pp-cli production-execution reports-analytics-oee-trend` — GET /production-execution/reports/analytics/oee-trend/ — production execution reports analytics oee trend
- `jivo-factory-pp-cli production-execution reports-analytics-plan-vs-production` — GET /production-execution/reports/analytics/plan-vs-production/ — production execution reports analytics plan vs
- `jivo-factory-pp-cli production-execution reports-analytics-procurement-vs-planned` — GET /production-execution/reports/analytics/procurement-vs-planned/ — procurement fulfillment vs plan for a SAP order
- `jivo-factory-pp-cli production-execution reports-analytics-resource-consumption` — GET /production-execution/reports/analytics/resource-consumption/ — production execution reports analytics resource
- `jivo-factory-pp-cli production-execution reports-analytics-waste` — GET /production-execution/reports/analytics/waste/ — production execution reports analytics waste
- `jivo-factory-pp-cli production-execution reports-analytics-waste-trend` — GET /production-execution/reports/analytics/waste-trend/ — production execution reports analytics waste trend
- `jivo-factory-pp-cli production-execution reports-daily-production` — GET /production-execution/reports/daily-production/ — daily production report
- `jivo-factory-pp-cli production-execution reports-line-clearance` — GET /production-execution/reports/line-clearance/ — production execution reports line clearance
- `jivo-factory-pp-cli production-execution reports-production-movement` — GET /production-execution/reports/production-movement/ — production execution reports production movement
- `jivo-factory-pp-cli production-execution reports-production-movement-filter-options` — GET /production-execution/reports/production-movement/filter-options/ — production execution reports production
- `jivo-factory-pp-cli production-execution runs` — GET /production-execution/runs/ — production execution runs
- `jivo-factory-pp-cli production-execution sap-bom` — GET /production-execution/sap/bom/ — bill of materials for an item
- `jivo-factory-pp-cli production-execution sap-items` — GET /production-execution/sap/items/ — production execution sap items
- `jivo-factory-pp-cli production-execution sap-orders` — GET /production-execution/sap/orders/ — production execution sap orders
- `jivo-factory-pp-cli production-execution waste` — GET /production-execution/waste/ — production execution waste

**quality-control** — Quality control — arrival slips, inspections, material types

- `jivo-factory-pp-cli quality-control arrival-slips` — GET /quality-control/arrival-slips/ — quality control arrival slips
- `jivo-factory-pp-cli quality-control inspections` — GET /quality-control/inspections/ — quality control inspections
- `jivo-factory-pp-cli quality-control inspections-actionable` — GET /quality-control/inspections/actionable/ — quality control inspections actionable
- `jivo-factory-pp-cli quality-control inspections-awaiting-chemist` — GET /quality-control/inspections/awaiting-chemist/ — quality control inspections awaiting chemist
- `jivo-factory-pp-cli quality-control inspections-awaiting-qam` — GET /quality-control/inspections/awaiting-qam/ — quality control inspections awaiting qam
- `jivo-factory-pp-cli quality-control inspections-completed` — GET /quality-control/inspections/completed/ — quality control inspections completed
- `jivo-factory-pp-cli quality-control inspections-counts` — GET /quality-control/inspections/counts/ — quality control inspections counts
- `jivo-factory-pp-cli quality-control inspections-draft` — GET /quality-control/inspections/draft/ — quality control inspections draft
- `jivo-factory-pp-cli quality-control inspections-pending` — GET /quality-control/inspections/pending/ — quality control inspections pending
- `jivo-factory-pp-cli quality-control inspections-rejected` — GET /quality-control/inspections/rejected/ — quality control inspections rejected
- `jivo-factory-pp-cli quality-control inspections-return-to-vendor` — GET /quality-control/inspections/return-to-vendor/ — quality control inspections return to vendor
- `jivo-factory-pp-cli quality-control material-types` — GET /quality-control/material-types/ — quality control material types
- `jivo-factory-pp-cli quality-control print-documents` — GET /quality-control/print-documents/ — quality control print documents
- `jivo-factory-pp-cli quality-control production-qc` — GET /quality-control/production-qc/ — quality control production qc
- `jivo-factory-pp-cli quality-control production-qc-counts` — GET /quality-control/production-qc/counts/ — quality control production qc counts
- `jivo-factory-pp-cli quality-control production-qc-pending` — GET /quality-control/production-qc/pending/ — quality control production qc pending
- `jivo-factory-pp-cli quality-control sap-items` — GET /quality-control/sap-items/ — quality control sap items

**sap** — SAP plan dashboard

- `jivo-factory-pp-cli sap plan-dashboard-details` — GET /sap/plan-dashboard/details/ — sap plan dashboard details
- `jivo-factory-pp-cli sap plan-dashboard-procurement` — GET /sap/plan-dashboard/procurement/ — sap plan dashboard procurement
- `jivo-factory-pp-cli sap plan-dashboard-summary` — GET /sap/plan-dashboard/summary/ — sap plan dashboard summary

**vehicle-management** — Vehicle management — vehicles, transporters, entries, types

- `jivo-factory-pp-cli vehicle-management transporters` — GET /vehicle-management/transporters/ — vehicle management transporters
- `jivo-factory-pp-cli vehicle-management transporters-names` — GET /vehicle-management/transporters/names/ — vehicle management transporters names
- `jivo-factory-pp-cli vehicle-management vehicle-entries` — GET /vehicle-management/vehicle-entries/ — vehicle entries in a window
- `jivo-factory-pp-cli vehicle-management vehicle-entries-count` — GET /vehicle-management/vehicle-entries/count/ — vehicle entry counts in a window
- `jivo-factory-pp-cli vehicle-management vehicle-entries-list-by-status` — GET /vehicle-management/vehicle-entries/list-by-status/ — vehicle entries grouped by status
- `jivo-factory-pp-cli vehicle-management vehicle-types` — GET /vehicle-management/vehicle-types/ — vehicle management vehicle types
- `jivo-factory-pp-cli vehicle-management vehicles` — GET /vehicle-management/vehicles/ — vehicle management vehicles
- `jivo-factory-pp-cli vehicle-management vehicles-names` — GET /vehicle-management/vehicles/names/ — vehicle management vehicles names

**warehouse** — Warehouse — FG receipts, BOM requests, WMS

- `jivo-factory-pp-cli warehouse bom-requests` — GET /warehouse/bom-requests/ — warehouse bom requests
- `jivo-factory-pp-cli warehouse fg-receipts` — GET /warehouse/fg-receipts/ — warehouse fg receipts
- `jivo-factory-pp-cli warehouse wms-batches-expiry` — GET /warehouse/wms/batches/expiry/ — warehouse wms batches expiry
- `jivo-factory-pp-cli warehouse wms-billing-overview` — GET /warehouse/wms/billing/overview/ — warehouse wms billing overview
- `jivo-factory-pp-cli warehouse wms-dashboard` — GET /warehouse/wms/dashboard/ — warehouse wms dashboard
- `jivo-factory-pp-cli warehouse wms-item-groups` — GET /warehouse/wms/item-groups/ — warehouse wms item groups
- `jivo-factory-pp-cli warehouse wms-sales-orders-backlog` — GET /warehouse/wms/sales-orders/backlog/ — warehouse wms sales orders backlog
- `jivo-factory-pp-cli warehouse wms-stock-movements` — GET /warehouse/wms/stock/movements/ — warehouse wms stock movements
- `jivo-factory-pp-cli warehouse wms-stock-overview` — GET /warehouse/wms/stock/overview/ — warehouse wms stock overview
- `jivo-factory-pp-cli warehouse wms-transfers-overview` — GET /warehouse/wms/transfers/overview/ — warehouse wms transfers overview
- `jivo-factory-pp-cli warehouse wms-warehouses` — GET /warehouse/wms/warehouses/ — warehouse wms warehouses
- `jivo-factory-pp-cli warehouse wms-warehouses-summary` — GET /warehouse/wms/warehouses/summary/ — warehouse wms warehouses summary


### Finding the right command

When you know what you want to do but not which command does it, ask the CLI directly:

```bash
jivo-factory-pp-cli which "<capability in your own words>"
```

`which` resolves a natural-language capability query to the best matching command from this CLI's curated feature index. Exit code `0` means at least one match; exit code `2` means no confident match — fall back to `--help` or use a narrower query.

## Auth Setup

Run `jivo-factory-pp-cli auth setup` for the URL and steps to obtain a token (add `--launch` to open the URL). Then store it:

```bash
jivo-factory-pp-cli auth set-token YOUR_TOKEN_HERE
```

Or set `JIVO_FACTORY_TOKEN` as an environment variable.

Run `jivo-factory-pp-cli doctor` to verify setup.

## Agent Mode

Add `--agent` to any command. Expands to: `--json --compact --no-input --no-color --yes`.

- **Pipeable** — JSON on stdout, errors on stderr
- **Filterable** — `--select` keeps a subset of fields. Dotted paths descend into nested structures; arrays traverse element-wise. Critical for keeping context small on verbose APIs:

  ```bash
  jivo-factory-pp-cli notifications list --agent --select id,name,status
  ```
- **Previewable** — `--dry-run` shows the request without sending
- **Offline-friendly** — sync/search commands can use the local SQLite store when available
- **Non-interactive** — never prompts, every input is a flag
- **Read-only** — do not use this CLI for create, update, delete, publish, comment, upvote, invite, order, send, or other mutating requests

### Response envelope

Commands that read from the local store or the API wrap output in a provenance envelope:

```json
{
  "meta": {"source": "live" | "local", "synced_at": "...", "reason": "..."},
  "results": <data>
}
```

Parse `.results` for data and `.meta.source` to know whether it's live or local. A human-readable `N results (live)` summary is printed to stderr only when stdout is a terminal AND no machine-format flag (`--json`, `--csv`, `--compact`, `--quiet`, `--plain`, `--select`) is set — piped/agent consumers and explicit-format runs get pure JSON on stdout.

## Agent Feedback

When you (or the agent) notice something off about this CLI, record it:

```
jivo-factory-pp-cli feedback "the --since flag is inclusive but docs say exclusive"
jivo-factory-pp-cli feedback --stdin < notes.txt
jivo-factory-pp-cli feedback list --json --limit 10
```

Entries are stored locally at `~/.local/share/jivo-factory-pp-cli/feedback.jsonl`. They are never POSTed unless `JIVO_FACTORY_FEEDBACK_ENDPOINT` is set AND either `--send` is passed or `JIVO_FACTORY_FEEDBACK_AUTO_SEND=true`. Default behavior is local-only.

Write what *surprised* you, not a bug report. Short, specific, one line: that is the part that compounds.

## Output Delivery

Every command accepts `--deliver <sink>`. The output goes to the named sink in addition to (or instead of) stdout, so agents can route command results without hand-piping. Three sinks are supported:

| Sink | Effect |
|------|--------|
| `stdout` | Default; write to stdout only |
| `file:<path>` | Atomically write output to `<path>` (tmp + rename) |
| `webhook:<url>` | POST the output body to the URL (`application/json` or `application/x-ndjson` when `--compact`) |

Unknown schemes are refused with a structured error naming the supported set. Webhook failures return non-zero and log the URL + HTTP status on stderr.

## Named Profiles

A profile is a saved set of flag values, reused across invocations. Use it when a scheduled agent calls the same command every run with the same configuration - HeyGen's "Beacon" pattern.

```
jivo-factory-pp-cli profile save briefing --json
jivo-factory-pp-cli --profile briefing notifications list
jivo-factory-pp-cli profile list --json
jivo-factory-pp-cli profile show briefing
jivo-factory-pp-cli profile delete briefing --yes
```

Explicit flags always win over profile values; profile values win over defaults. `agent-context` lists all available profiles under `available_profiles` so introspecting agents discover them at runtime.

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 2 | Usage error (wrong arguments) |
| 3 | Resource not found |
| 4 | Authentication required |
| 5 | API error (upstream issue) |
| 7 | Rate limited (wait and retry) |
| 10 | Config error |

## Argument Parsing

Parse `$ARGUMENTS`:

1. **Empty, `help`, or `--help`** → show `jivo-factory-pp-cli --help` output
2. **Starts with `install`** → ends with `mcp` → MCP installation; otherwise → see Prerequisites above
3. **Anything else** → Direct Use (execute as CLI command with `--agent`)

## MCP Server Installation

1. Install the MCP server:
   ```bash
   go install github.com/mvanhorn/printing-press-library/library/developer-tools/jivo-factory/cmd/jivo-factory-pp-mcp@latest
   ```
2. Register with Claude Code:
   ```bash
   claude mcp add jivo-factory-pp-mcp -- jivo-factory-pp-mcp
   ```
3. Verify: `claude mcp list`

## Direct Use

1. Check if installed: `which jivo-factory-pp-cli`
   If not found, offer to install (see Prerequisites at the top of this skill).
2. Match the user query to the best command from the Unique Capabilities and Command Reference above.
3. Execute with the `--agent` flag:
   ```bash
   jivo-factory-pp-cli <command> [subcommand] [args] --agent
   ```
4. If ambiguous, drill into subcommand help: `jivo-factory-pp-cli <command> --help`.

Linked: [[docs/factory/FACTORY_MAP|FACTORY_MAP]] · [[docs/FACTORY_CLI_PLAN|FACTORY_CLI_PLAN]] · [[docs/READ_ONLY_LAW|READ_ONLY_LAW]]
