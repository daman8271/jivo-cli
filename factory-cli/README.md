---
title: "Jivo Factory CLI"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: reference
tags: [jivogpt, factory-cli, cli]
---

# Jivo Factory CLI

JIVO factory management CLI (ji.jivo.in / factory.jivo.in) — read-only access to all 3 companies (JIVO_MART, JIVO_OIL, JIVO_BEVERAGES via --company / JIVO_FACTORY_COMPANY): gate, vehicles, quality control, GRPO, barcode traceability, dispatch, production, WMS, maintenance & dashboards

Created by [@daman8271](https://github.com/daman8271).

## Install

The recommended path installs both the `jivo-factory-pp-cli` binary and the `pp-jivo-factory` agent skill (Claude Code, Codex, Cursor, Gemini CLI, GitHub Copilot, and other agents supported by the upstream [`skills`](https://github.com/vercel-labs/skills) CLI) in one shot:

```bash
npx -y @mvanhorn/printing-press-library install jivo-factory
```

For CLI only (no skill):

```bash
npx -y @mvanhorn/printing-press-library install jivo-factory --cli-only
```

For skill only — installs the skill into the same agents as the default command above, but skips the CLI binary (use this to update or reinstall just the skill):

```bash
npx -y @mvanhorn/printing-press-library install jivo-factory --skill-only
```

To constrain the skill install to one or more specific agents (repeatable — agent names match the [`skills`](https://github.com/vercel-labs/skills) CLI):

```bash
npx -y @mvanhorn/printing-press-library install jivo-factory --agent claude-code
npx -y @mvanhorn/printing-press-library install jivo-factory --agent claude-code --agent codex
```

### Without Node (Go fallback)

If `npx` isn't available (no Node, offline), install the CLI directly via Go (requires Go 1.26.4 or newer):

```bash
go install github.com/mvanhorn/printing-press-library/library/developer-tools/jivo-factory/cmd/jivo-factory-pp-cli@latest
```

This installs the CLI only — no skill.

### Pre-built binary

Download a pre-built binary for your platform from the [latest release](https://github.com/mvanhorn/printing-press-library/releases/tag/jivo-factory-current). On macOS, clear the Gatekeeper quarantine: `xattr -d com.apple.quarantine <binary>`. On Unix, mark it executable: `chmod +x <binary>`.

<!-- pp-hermes-install-anchor -->
## Install for Hermes

Install the CLI binary first. The installer writes binaries to a per-user managed bin directory by default: `$HOME/.local/bin` on macOS/Linux and `%LOCALAPPDATA%\Programs\PrintingPress\bin` on Windows.

```bash
npx -y @mvanhorn/printing-press-library install jivo-factory --cli-only
```

Then install the focused Hermes skill.

From the Hermes CLI:

```bash
hermes skills install mvanhorn/printing-press-library/cli-skills/pp-jivo-factory --force
```

Inside a Hermes chat session:

```bash
/skills install mvanhorn/printing-press-library/cli-skills/pp-jivo-factory --force
```

Restart the Hermes session or gateway if the newly installed skill is not visible immediately.

## Install for OpenClaw
Install both the CLI binary and the focused OpenClaw skill. The installer defaults binaries to a per-user bin directory (`$HOME/.local/bin` on macOS/Linux, `%LOCALAPPDATA%\Programs\PrintingPress\bin` on Windows):

```bash
npx -y @mvanhorn/printing-press-library install jivo-factory --agent openclaw
```

Restart the OpenClaw session or gateway if the newly installed skill is not visible immediately.

## Use with Claude Desktop

This CLI ships an [MCPB](https://github.com/modelcontextprotocol/mcpb) bundle — Claude Desktop's standard format for one-click MCP extension installs (no JSON config required).

To install:

1. Download the `.mcpb` for your platform from the [latest release](https://github.com/mvanhorn/printing-press-library/releases/tag/jivo-factory-current).
2. Double-click the `.mcpb` file. Claude Desktop opens and walks you through the install.
3. Fill in `JIVO_FACTORY_TOKEN` when Claude Desktop prompts you.

Requires Claude Desktop 1.0.0 or later. Pre-built bundles ship for macOS Apple Silicon (`darwin-arm64`) and Windows (`amd64`, `arm64`); for other platforms, use the manual config below.

<details>
<summary>Manual JSON config (advanced)</summary>

If you can't use the MCPB bundle (older Claude Desktop, unsupported platform), install the MCP binary and configure it manually.


```bash
go install github.com/mvanhorn/printing-press-library/library/developer-tools/jivo-factory/cmd/jivo-factory-pp-mcp@latest
```

Add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "jivo-factory": {
      "command": "jivo-factory-pp-mcp",
      "env": {
        "JIVO_FACTORY_TOKEN": "<your-key>"
      }
    }
  }
}
```

</details>

## Quick Start

### 1. Install

See [Install](#install) above.

### 2. Set Up Credentials

Get your access token from your API provider's developer portal, then store it:

```bash
jivo-factory-pp-cli auth set-token YOUR_TOKEN_HERE
```

Or set it via environment variable:

```bash
export JIVO_FACTORY_TOKEN="your-token-here"
```

### 3. Verify Setup

```bash
jivo-factory-pp-cli doctor
```

This checks your configuration and credentials.

### 4. Try Your First Command

```bash
jivo-factory-pp-cli notifications list
```

## Usage

Run `jivo-factory-pp-cli --help` for the full command reference and flag list.

## Exact product identity

The JivoGPT workspace build carries a hand-authored, read-only `product` command group that consumes the same released [[CLI/product-identity/README|Product Identity Bridge]] as jivo-desk. It performs no Factory API request and never decides identity from a product name. Regeneration or installation from an older upstream Printing Press release must reapply patch 0006 before this local command is assumed present.

```bash
jivo-factory-pp-cli product resolve amazon:B078T3Q3SH --agent
jivo-factory-pp-cli product resolve JID-0116 --agent
jivo-factory-pp-cli product resolve FG0000315 --company beverages --agent
jivo-factory-pp-cli product resolve FG0000315 --all-companies --agent
jivo-factory-pp-cli product search "canola bottle" --agent
jivo-factory-pp-cli product catalog --company mart --agent
jivo-factory-pp-cli product verify --agent
jivo-factory-pp-cli product coverage --agent
```

Factory item codes are not globally unique. A bare code such as `FG0000315` is rejected unless `--company` is explicit; `--all-companies` is the deliberate collision-inspection mode. The stable Factory key is `company + SAP schema + item_code`, while the scraper key is `platform + listing_id`. Text search only returns candidates.

The map is discovered through `--identity-map`, `JIVO_PRODUCT_IDENTITY_MAP`, or the repository-relative `CLI/product-identity/v1/product-identity-map.json`. It must be accompanied by the trusted detached `release-attestation.json` and all six frozen evidence artifacts. The CLI pins the approved attestation digest, recomputes the map and evidence hashes, and rejects an alternate or edited bundle with exit `6`. Missing, draft, incomplete, ambiguous, tampered, or unsupported releases therefore fail closed. See [[Connections/FACTORY__JIVO_DESK|Factory to Jivo Desk Connection]] for released coverage and boundaries.

## Commands

### accounts

Accounts & users

- **`jivo-factory-pp-cli accounts departments`** - GET /accounts/departments/ — departments list (15 rows, shared across companies)
- **`jivo-factory-pp-cli accounts me`** - GET /accounts/me/ — accounts me
- **`jivo-factory-pp-cli accounts users`** - GET /accounts/users/ — accounts users

### barcode

Barcode & traceability — boxes, pallets, dispatch sessions, intercompany

- **`jivo-factory-pp-cli barcode boxes`** - GET /barcode/boxes/ — barcode boxes
- **`jivo-factory-pp-cli barcode dispatch-reports`** - GET /barcode/dispatch/reports/ — barcode dispatch reports
- **`jivo-factory-pp-cli barcode dispatch-reports-boxes`** - GET /barcode/dispatch/reports/boxes/ — barcode dispatch reports boxes
- **`jivo-factory-pp-cli barcode dispatch-reports-pallets`** - GET /barcode/dispatch/reports/pallets/ — barcode dispatch reports pallets
- **`jivo-factory-pp-cli barcode dispatch-reports-rejected-scans`** - GET /barcode/dispatch/reports/rejected-scans/ — barcode dispatch reports rejected scans
- **`jivo-factory-pp-cli barcode dispatch-sessions`** - GET /barcode/dispatch/sessions/ — barcode dispatch sessions (all)
- **`jivo-factory-pp-cli barcode dispatch-sessions-active`** - GET /barcode/dispatch/sessions/active/ — barcode dispatch sessions active
- **`jivo-factory-pp-cli barcode dispatch-sessions-closed`** - GET /barcode/dispatch/sessions/closed/ — barcode dispatch sessions closed
- **`jivo-factory-pp-cli barcode dispatch-sessions-completed`** - GET /barcode/dispatch/sessions/completed/ — barcode dispatch sessions completed
- **`jivo-factory-pp-cli barcode dispatch-sessions-from-bill`** - GET /barcode/dispatch/sessions/from-bill/ — barcode dispatch sessions from bill
- **`jivo-factory-pp-cli barcode dispatch-settings`** - GET /barcode/dispatch/settings/ — barcode dispatch settings
- **`jivo-factory-pp-cli barcode intercompany-dashboard`** - GET /barcode/intercompany/dashboard/ — barcode intercompany dashboard
- **`jivo-factory-pp-cli barcode intercompany-trace`** - GET /barcode/intercompany/trace/ — trace an intercompany barcode
- **`jivo-factory-pp-cli barcode intercompany-transfers`** - GET /barcode/intercompany/transfers/ — barcode intercompany transfers list
- **`jivo-factory-pp-cli barcode items-oitm`** - GET /barcode/items/oitm/ — barcode items oitm
- **`jivo-factory-pp-cli barcode loose`** - GET /barcode/loose/ — barcode loose
- **`jivo-factory-pp-cli barcode pallets`** - GET /barcode/pallets/ — barcode pallets
- **`jivo-factory-pp-cli barcode print-history`** - GET /barcode/print/history/ — barcode print history
- **`jivo-factory-pp-cli barcode production-release-oil`** - GET /barcode/production-release-oil/ — oil production release (JIVO_OIL only; 503 for other companies)
- **`jivo-factory-pp-cli barcode scan-history`** - GET /barcode/scan/history/ — barcode scan history

### company

Company master — the Select-Company screen

- **`jivo-factory-pp-cli company`** - GET /company/companies/ — the 3 companies backing the Select-Company screen

### daily-needs-gatein

Daily-needs gate entries

- **`jivo-factory-pp-cli daily-needs-gatein`** - GET /daily-needs-gatein/gate-entries/daily-need/categories/ — daily needs gatein gate entries daily need categories

### dashboards

Admin dashboards (stock, inventory-age, dispatch pipeline, SAP plan)

- **`jivo-factory-pp-cli dashboards inventory-age-filter-options`** - GET /dashboards/inventory-age/filter-options/ — dashboards inventory age filter options
- **`jivo-factory-pp-cli dashboards inventory-age-report`** - GET /dashboards/inventory-age/report/ — dashboards inventory age report
- **`jivo-factory-pp-cli dashboards sales-planning-requirement-analysis`** - GET /dashboards/sales-planning-requirement/analysis/ — dashboards sales planning requirement analysis
- **`jivo-factory-pp-cli dashboards sales-planning-requirement-report`** - GET /dashboards/sales-planning-requirement/report/ — dashboards sales planning requirement report
- **`jivo-factory-pp-cli dashboards sales-planning-requirement-status`** - GET /dashboards/sales-planning-requirement/status/ — dashboards sales planning requirement status
- **`jivo-factory-pp-cli dashboards stock`** - GET /dashboards/stock/ — dashboards stock
- **`jivo-factory-pp-cli dashboards stock-as-of`** - GET /dashboards/stock/as-of/ — stock snapshot as of a date

### dispatch

Dispatch — docking, bilty-GRPO, transporter invoices

- **`jivo-factory-pp-cli dispatch bilty-grpo-history`** - GET /dispatch/bilty-grpo/history/ — dispatch bilty grpo history
- **`jivo-factory-pp-cli dispatch bilty-grpo-options`** - GET /dispatch/bilty-grpo/options/ — dispatch bilty grpo options
- **`jivo-factory-pp-cli dispatch bilty-grpo-pending`** - GET /dispatch/bilty-grpo/pending/ — dispatch bilty grpo pending
- **`jivo-factory-pp-cli dispatch bilty-grpo-preview`** - GET /dispatch/bilty-grpo/preview/{dispatch_plan_id}/ — bilty-GRPO posting preview for a dispatch plan
- **`jivo-factory-pp-cli dispatch open-bilties`** - GET /dispatch/open-bilties/ — dispatch open bilties
- **`jivo-factory-pp-cli dispatch transporter-invoices-history`** - GET /dispatch/transporter-invoices/history/ — dispatch transporter invoices history

### dispatch-plans

Dispatch plans & pipeline

- **`jivo-factory-pp-cli dispatch-plans bills`** - GET /dispatch-plans/bills/ — bills in a date window
- **`jivo-factory-pp-cli dispatch-plans pipeline`** - GET /dispatch-plans/pipeline/ — dispatch plans pipeline

### docking-admin

Docking admin scan approvals

- **`jivo-factory-pp-cli docking-admin partial-scan-requests`** - GET /docking-admin/partial-scan-requests/ — docking admin partial scan requests
- **`jivo-factory-pp-cli docking-admin scan-skip-requests`** - GET /docking-admin/scan-skip-requests/ — docking admin scan skip requests

### driver-management

Drivers

- **`jivo-factory-pp-cli driver-management drivers`** - GET /driver-management/drivers/ — driver management drivers
- **`jivo-factory-pp-cli driver-management drivers-names`** - GET /driver-management/drivers/names/ — driver management drivers names

### gate-core

Gate — arrivals, BST in/out/return, empty-vehicle, job-work, sales-dispatch gate-out

- **`jivo-factory-pp-cli gate-core arrivals`** - GET /gate-core/arrivals/ — gate core arrivals
- **`jivo-factory-pp-cli gate-core arrivals-expected`** - GET /gate-core/arrivals/expected/ — expected arrival for a vehicle
- **`jivo-factory-pp-cli gate-core bst-ins`** - GET /gate-core/bst-ins/ — gate core bst ins
- **`jivo-factory-pp-cli gate-core bst-ins-eligible-outs`** - GET /gate-core/bst-ins/eligible-outs/ — gate core bst ins eligible outs
- **`jivo-factory-pp-cli gate-core bst-outs`** - GET /gate-core/bst-outs/ — gate core bst outs
- **`jivo-factory-pp-cli gate-core bst-outs-sap-transfers`** - GET /gate-core/bst-outs/sap-transfers/ — gate core bst outs sap transfers
- **`jivo-factory-pp-cli gate-core bst-returns`** - GET /gate-core/bst-returns/ — gate core bst returns
- **`jivo-factory-pp-cli gate-core bst-returns-eligible-outs`** - GET /gate-core/bst-returns/eligible-outs/ — gate core bst returns eligible outs
- **`jivo-factory-pp-cli gate-core empty-vehicle-ins`** - GET /gate-core/empty-vehicle-ins/ — gate core empty vehicle ins
- **`jivo-factory-pp-cli gate-core empty-vehicle-ins-eligible`** - GET /gate-core/empty-vehicle-ins/eligible/ — gate core empty vehicle ins eligible
- **`jivo-factory-pp-cli gate-core empty-vehicle-ins-reasons`** - GET /gate-core/empty-vehicle-ins/reasons/ — gate core empty vehicle ins reasons
- **`jivo-factory-pp-cli gate-core empty-vehicle-outs`** - GET /gate-core/empty-vehicle-outs/ — gate core empty vehicle outs
- **`jivo-factory-pp-cli gate-core empty-vehicle-outs-eligible-entries`** - GET /gate-core/empty-vehicle-outs/eligible-entries/ — gate core empty vehicle outs eligible entries
- **`jivo-factory-pp-cli gate-core job-work`** - GET /gate-core/job-work/ — gate core job work
- **`jivo-factory-pp-cli gate-core job-work-sap-grpos`** - GET /gate-core/job-work/sap-grpos/ — gate core job work sap grpos
- **`jivo-factory-pp-cli gate-core job-work-sap-production-orders`** - GET /gate-core/job-work/sap-production-orders/ — gate core job work sap production orders
- **`jivo-factory-pp-cli gate-core rejected-qc-returns`** - GET /gate-core/rejected-qc-returns/ — gate core rejected qc returns
- **`jivo-factory-pp-cli gate-core sales-dispatch`** - GET /gate-core/sales-dispatch/ — gate core sales dispatch
- **`jivo-factory-pp-cli gate-core sales-dispatch-documents`** - GET /gate-core/sales-dispatch/documents/ — gate core sales dispatch documents
- **`jivo-factory-pp-cli gate-core sales-dispatch-lock`** - GET /gate-core/sales-dispatch/lock/ — gate core sales dispatch lock
- **`jivo-factory-pp-cli gate-core sales-dispatch-pending-bookings`** - GET /gate-core/sales-dispatch/pending-bookings/ — gate core sales dispatch pending bookings
- **`jivo-factory-pp-cli gate-core sales-dispatch-reports`** - GET /gate-core/sales-dispatch/reports/ — gate core sales dispatch reports

### grpo

GRPO — goods-receipt POs (material & service)

- **`jivo-factory-pp-cli grpo all-entries`** - GET /grpo/all-entries/ — grpo all entries
- **`jivo-factory-pp-cli grpo history`** - GET /grpo/history/ — grpo history
- **`jivo-factory-pp-cli grpo history-detail`** - GET /grpo/history/{posting_id}/ — a posted material GRPO
- **`jivo-factory-pp-cli grpo pending`** - GET /grpo/pending/ — grpo pending
- **`jivo-factory-pp-cli grpo preview`** - GET /grpo/preview/{vehicle_entry_id}/ — GRPO preview for a vehicle entry
- **`jivo-factory-pp-cli grpo service-history`** - GET /grpo/service/history/ — grpo service history
- **`jivo-factory-pp-cli grpo service-history-detail`** - GET /grpo/service/history/{posting_id}/ — a posted service GRPO
- **`jivo-factory-pp-cli grpo service-options`** - GET /grpo/service/options/ — grpo service options
- **`jivo-factory-pp-cli grpo service-pending`** - GET /grpo/service/pending/ — grpo service pending
- **`jivo-factory-pp-cli grpo service-preview`** - GET /grpo/service/preview/{dispatch_plan_id}/ — service-GRPO preview for a dispatch plan
- **`jivo-factory-pp-cli grpo summary`** - GET /grpo/summary/ — grpo summary

### maintenance

Maintenance CMMS — assets, PM, spares, work orders

- **`jivo-factory-pp-cli maintenance alerts`** - GET /maintenance/alerts/ — maintenance alerts
- **`jivo-factory-pp-cli maintenance asset-categories`** - GET /maintenance/asset-categories/ — maintenance asset categories
- **`jivo-factory-pp-cli maintenance asset-departments`** - GET /maintenance/asset-departments/ — maintenance asset departments
- **`jivo-factory-pp-cli maintenance asset-documents`** - GET /maintenance/asset-documents/ — maintenance asset documents
- **`jivo-factory-pp-cli maintenance asset-locations`** - GET /maintenance/asset-locations/ — maintenance asset locations
- **`jivo-factory-pp-cli maintenance asset-photos`** - GET /maintenance/asset-photos/ — maintenance asset photos
- **`jivo-factory-pp-cli maintenance assets`** - GET /maintenance/assets/ — maintenance assets
- **`jivo-factory-pp-cli maintenance dashboard`** - GET /maintenance/dashboard/ — maintenance dashboard
- **`jivo-factory-pp-cli maintenance options`** - GET /maintenance/options/ — maintenance options
- **`jivo-factory-pp-cli maintenance pm-checklist-items`** - GET /maintenance/pm-checklist-items/ — maintenance pm checklist items
- **`jivo-factory-pp-cli maintenance pm-executions`** - GET /maintenance/pm-executions/ — maintenance pm executions
- **`jivo-factory-pp-cli maintenance pm-plans`** - GET /maintenance/pm-plans/ — maintenance pm plans
- **`jivo-factory-pp-cli maintenance reports`** - GET /maintenance/reports/ — maintenance reports
- **`jivo-factory-pp-cli maintenance scan-lookup`** - GET /maintenance/scan/lookup/ — asset/spare scan lookup
- **`jivo-factory-pp-cli maintenance spare-categories`** - GET /maintenance/spare-categories/ — maintenance spare categories
- **`jivo-factory-pp-cli maintenance spare-movements`** - GET /maintenance/spare-movements/ — maintenance spare movements
- **`jivo-factory-pp-cli maintenance spare-requests`** - GET /maintenance/spare-requests/ — maintenance spare requests
- **`jivo-factory-pp-cli maintenance spares`** - GET /maintenance/spares/ — maintenance spares
- **`jivo-factory-pp-cli maintenance spares-low-stock`** - GET /maintenance/spares/low-stock/ — maintenance spares low stock
- **`jivo-factory-pp-cli maintenance spares-stock`** - GET /maintenance/spares/stock/ — spare stock lookup by code
- **`jivo-factory-pp-cli maintenance vendor-visits`** - GET /maintenance/vendor-visits/ — maintenance vendor visits
- **`jivo-factory-pp-cli maintenance work-order-photos`** - GET /maintenance/work-order-photos/ — maintenance work order photos
- **`jivo-factory-pp-cli maintenance work-orders`** - GET /maintenance/work-orders/ — maintenance work orders

### non-moving-rm

Non-moving raw material

- **`jivo-factory-pp-cli non-moving-rm item-groups`** - GET /non-moving-rm/item-groups/ — non moving rm item groups
- **`jivo-factory-pp-cli non-moving-rm report`** - GET /non-moving-rm/report/ — non-moving raw-material report (replaces the dead bare endpoint)

### notifications

Notifications & device tokens

- **`jivo-factory-pp-cli notifications list`** - GET /notifications/ — notifications
- **`jivo-factory-pp-cli notifications preferences`** - GET /notifications/preferences/ — notifications preferences
- **`jivo-factory-pp-cli notifications unread-count`** - GET /notifications/unread-count/ — notifications unread count

### person-gatein

Person gate-in — visitors, labour, contractors at the campus gate

- **`jivo-factory-pp-cli person-gatein contractors`** - GET /person-gatein/contractors/ — contractor master
- **`jivo-factory-pp-cli person-gatein entries`** - GET /person-gatein/entries/ — person gate-in entries (paginated)
- **`jivo-factory-pp-cli person-gatein gates`** - GET /person-gatein/gates/ — gate master
- **`jivo-factory-pp-cli person-gatein labours`** - GET /person-gatein/labours/ — labour master
- **`jivo-factory-pp-cli person-gatein person-types`** - GET /person-gatein/person-types/ — person type master
- **`jivo-factory-pp-cli person-gatein visitors`** - GET /person-gatein/visitors/ — visitor master

### po

Purchase orders — open POs, vendors, warehouses

- **`jivo-factory-pp-cli po vendors`** - GET /po/vendors/ — po vendors
- **`jivo-factory-pp-cli po warehouses`** - GET /po/warehouses/ — po warehouses

### production-execution

Production execution (MES) — runs, lines, machines, OEE, waste

- **`jivo-factory-pp-cli production-execution breakdown-categories`** - GET /production-execution/breakdown-categories/ — production execution breakdown categories
- **`jivo-factory-pp-cli production-execution checklist-templates`** - GET /production-execution/checklist-templates/ — production execution checklist templates
- **`jivo-factory-pp-cli production-execution costs-analytics`** - GET /production-execution/costs/analytics/ — production execution costs analytics
- **`jivo-factory-pp-cli production-execution line-clearance`** - GET /production-execution/line-clearance/ — production execution line clearance
- **`jivo-factory-pp-cli production-execution line-configs`** - GET /production-execution/line-configs/ — production execution line configs
- **`jivo-factory-pp-cli production-execution line-configs-auto-fill`** - GET /production-execution/line-configs/auto-fill/ — auto-fill config for a production line
- **`jivo-factory-pp-cli production-execution lines`** - GET /production-execution/lines/ — production execution lines
- **`jivo-factory-pp-cli production-execution machine-checklists`** - GET /production-execution/machine-checklists/ — production execution machine checklists
- **`jivo-factory-pp-cli production-execution machines`** - GET /production-execution/machines/ — production execution machines
- **`jivo-factory-pp-cli production-execution reports-analytics`** - GET /production-execution/reports/analytics/ — production execution reports analytics
- **`jivo-factory-pp-cli production-execution reports-analytics-cost-analysis`** - GET /production-execution/reports/analytics/cost-analysis/ — production execution reports analytics cost analysis
- **`jivo-factory-pp-cli production-execution reports-analytics-downtime`** - GET /production-execution/reports/analytics/downtime/ — production execution reports analytics downtime
- **`jivo-factory-pp-cli production-execution reports-analytics-downtime-pareto`** - GET /production-execution/reports/analytics/downtime-pareto/ — production execution reports analytics downtime pareto
- **`jivo-factory-pp-cli production-execution reports-analytics-monthly-summary`** - GET /production-execution/reports/analytics/monthly-summary/ — production execution reports analytics monthly summary
- **`jivo-factory-pp-cli production-execution reports-analytics-oee`** - GET /production-execution/reports/analytics/oee/ — production execution reports analytics oee
- **`jivo-factory-pp-cli production-execution reports-analytics-oee-trend`** - GET /production-execution/reports/analytics/oee-trend/ — production execution reports analytics oee trend
- **`jivo-factory-pp-cli production-execution reports-analytics-plan-vs-production`** - GET /production-execution/reports/analytics/plan-vs-production/ — production execution reports analytics plan vs production
- **`jivo-factory-pp-cli production-execution reports-analytics-procurement-vs-planned`** - GET /production-execution/reports/analytics/procurement-vs-planned/ — procurement fulfillment vs plan for a SAP order
- **`jivo-factory-pp-cli production-execution reports-analytics-resource-consumption`** - GET /production-execution/reports/analytics/resource-consumption/ — production execution reports analytics resource consumption
- **`jivo-factory-pp-cli production-execution reports-analytics-waste`** - GET /production-execution/reports/analytics/waste/ — production execution reports analytics waste
- **`jivo-factory-pp-cli production-execution reports-analytics-waste-trend`** - GET /production-execution/reports/analytics/waste-trend/ — production execution reports analytics waste trend
- **`jivo-factory-pp-cli production-execution reports-daily-production`** - GET /production-execution/reports/daily-production/ — daily production report
- **`jivo-factory-pp-cli production-execution reports-line-clearance`** - GET /production-execution/reports/line-clearance/ — production execution reports line clearance
- **`jivo-factory-pp-cli production-execution reports-production-movement`** - GET /production-execution/reports/production-movement/ — production execution reports production movement
- **`jivo-factory-pp-cli production-execution reports-production-movement-filter-options`** - GET /production-execution/reports/production-movement/filter-options/ — production execution reports production movement filter options
- **`jivo-factory-pp-cli production-execution runs`** - GET /production-execution/runs/ — production execution runs
- **`jivo-factory-pp-cli production-execution sap-bom`** - GET /production-execution/sap/bom/ — bill of materials for an item
- **`jivo-factory-pp-cli production-execution sap-items`** - GET /production-execution/sap/items/ — production execution sap items
- **`jivo-factory-pp-cli production-execution sap-orders`** - GET /production-execution/sap/orders/ — production execution sap orders
- **`jivo-factory-pp-cli production-execution waste`** - GET /production-execution/waste/ — production execution waste

### quality-control

Quality control — arrival slips, inspections, material types

- **`jivo-factory-pp-cli quality-control arrival-slips`** - GET /quality-control/arrival-slips/ — quality control arrival slips
- **`jivo-factory-pp-cli quality-control inspections`** - GET /quality-control/inspections/ — quality control inspections
- **`jivo-factory-pp-cli quality-control inspections-actionable`** - GET /quality-control/inspections/actionable/ — quality control inspections actionable
- **`jivo-factory-pp-cli quality-control inspections-awaiting-chemist`** - GET /quality-control/inspections/awaiting-chemist/ — quality control inspections awaiting chemist
- **`jivo-factory-pp-cli quality-control inspections-awaiting-qam`** - GET /quality-control/inspections/awaiting-qam/ — quality control inspections awaiting qam
- **`jivo-factory-pp-cli quality-control inspections-completed`** - GET /quality-control/inspections/completed/ — quality control inspections completed
- **`jivo-factory-pp-cli quality-control inspections-counts`** - GET /quality-control/inspections/counts/ — quality control inspections counts
- **`jivo-factory-pp-cli quality-control inspections-draft`** - GET /quality-control/inspections/draft/ — quality control inspections draft
- **`jivo-factory-pp-cli quality-control inspections-pending`** - GET /quality-control/inspections/pending/ — quality control inspections pending
- **`jivo-factory-pp-cli quality-control inspections-rejected`** - GET /quality-control/inspections/rejected/ — quality control inspections rejected
- **`jivo-factory-pp-cli quality-control inspections-return-to-vendor`** - GET /quality-control/inspections/return-to-vendor/ — quality control inspections return to vendor
- **`jivo-factory-pp-cli quality-control material-types`** - GET /quality-control/material-types/ — quality control material types
- **`jivo-factory-pp-cli quality-control print-documents`** - GET /quality-control/print-documents/ — quality control print documents
- **`jivo-factory-pp-cli quality-control production-qc`** - GET /quality-control/production-qc/ — quality control production qc
- **`jivo-factory-pp-cli quality-control production-qc-counts`** - GET /quality-control/production-qc/counts/ — quality control production qc counts
- **`jivo-factory-pp-cli quality-control production-qc-pending`** - GET /quality-control/production-qc/pending/ — quality control production qc pending
- **`jivo-factory-pp-cli quality-control sap-items`** - GET /quality-control/sap-items/ — quality control sap items

### sap

SAP plan dashboard

- **`jivo-factory-pp-cli sap plan-dashboard-details`** - GET /sap/plan-dashboard/details/ — sap plan dashboard details
- **`jivo-factory-pp-cli sap plan-dashboard-procurement`** - GET /sap/plan-dashboard/procurement/ — sap plan dashboard procurement
- **`jivo-factory-pp-cli sap plan-dashboard-summary`** - GET /sap/plan-dashboard/summary/ — sap plan dashboard summary

### vehicle-management

Vehicle management — vehicles, transporters, entries, types

- **`jivo-factory-pp-cli vehicle-management transporters`** - GET /vehicle-management/transporters/ — vehicle management transporters
- **`jivo-factory-pp-cli vehicle-management transporters-names`** - GET /vehicle-management/transporters/names/ — vehicle management transporters names
- **`jivo-factory-pp-cli vehicle-management vehicle-entries`** - GET /vehicle-management/vehicle-entries/ — vehicle entries in a window
- **`jivo-factory-pp-cli vehicle-management vehicle-entries-count`** - GET /vehicle-management/vehicle-entries/count/ — vehicle entry counts in a window
- **`jivo-factory-pp-cli vehicle-management vehicle-entries-list-by-status`** - GET /vehicle-management/vehicle-entries/list-by-status/ — vehicle entries grouped by status
- **`jivo-factory-pp-cli vehicle-management vehicle-types`** - GET /vehicle-management/vehicle-types/ — vehicle management vehicle types
- **`jivo-factory-pp-cli vehicle-management vehicles`** - GET /vehicle-management/vehicles/ — vehicle management vehicles
- **`jivo-factory-pp-cli vehicle-management vehicles-names`** - GET /vehicle-management/vehicles/names/ — vehicle management vehicles names

### warehouse

Warehouse — FG receipts, BOM requests, WMS

- **`jivo-factory-pp-cli warehouse bom-requests`** - GET /warehouse/bom-requests/ — warehouse bom requests
- **`jivo-factory-pp-cli warehouse fg-receipts`** - GET /warehouse/fg-receipts/ — warehouse fg receipts
- **`jivo-factory-pp-cli warehouse wms-batches-expiry`** - GET /warehouse/wms/batches/expiry/ — warehouse wms batches expiry
- **`jivo-factory-pp-cli warehouse wms-billing-overview`** - GET /warehouse/wms/billing/overview/ — warehouse wms billing overview
- **`jivo-factory-pp-cli warehouse wms-dashboard`** - GET /warehouse/wms/dashboard/ — warehouse wms dashboard
- **`jivo-factory-pp-cli warehouse wms-item-groups`** - GET /warehouse/wms/item-groups/ — warehouse wms item groups
- **`jivo-factory-pp-cli warehouse wms-sales-orders-backlog`** - GET /warehouse/wms/sales-orders/backlog/ — warehouse wms sales orders backlog
- **`jivo-factory-pp-cli warehouse wms-stock-movements`** - GET /warehouse/wms/stock/movements/ — warehouse wms stock movements
- **`jivo-factory-pp-cli warehouse wms-stock-overview`** - GET /warehouse/wms/stock/overview/ — warehouse wms stock overview
- **`jivo-factory-pp-cli warehouse wms-transfers-overview`** - GET /warehouse/wms/transfers/overview/ — warehouse wms transfers overview
- **`jivo-factory-pp-cli warehouse wms-warehouses`** - GET /warehouse/wms/warehouses/ — warehouse wms warehouses
- **`jivo-factory-pp-cli warehouse wms-warehouses-summary`** - GET /warehouse/wms/warehouses/summary/ — warehouse wms warehouses summary


## Output Formats

```bash
# Human-readable table (default in terminal, JSON when piped)
jivo-factory-pp-cli notifications list

# JSON for scripting and agents
jivo-factory-pp-cli notifications list --json

# Filter to specific fields
jivo-factory-pp-cli notifications list --json --select id,name,status

# Dry run — show the request without sending
jivo-factory-pp-cli notifications list --dry-run

# Agent mode — JSON + compact + no prompts in one flag
jivo-factory-pp-cli notifications list --agent
```

## Agent Usage

This CLI is designed for AI agent consumption:

- **Non-interactive** - never prompts, every input is a flag
- **Pipeable** - `--json` output to stdout, errors to stderr
- **Filterable** - `--select id,name` returns only fields you need
- **Previewable** - `--dry-run` shows the request without sending
- **Read-only by default** - this CLI does not create, update, delete, publish, send, or mutate remote resources
- **Offline-friendly** - sync/search commands can use the local SQLite store when available
- **Agent-safe by default** - no colors or formatting unless `--human-friendly` is set

Exit codes: `0` success, `2` usage error, `3` not found, `4` auth error, `5` API error, `7` rate limited, `10` config error.

## Health Check

```bash
jivo-factory-pp-cli doctor
```

Verifies configuration, credentials, and connectivity to the API.

## Configuration

Config file: `~/.config/jivo-factory-pp-cli/config.toml`

Static request headers can be configured under `headers`; per-command header overrides take precedence.

Environment variables:

| Name | Kind | Required | Description |
| --- | --- | --- | --- |
| `JIVO_FACTORY_TOKEN` | per_call | Yes | Set to your API credential. |

### agentcookie (optional)

If you use agentcookie to sync secrets across machines, this CLI auto-adopts agentcookie-managed credentials with no extra setup. When the daemon writes to this CLI's config, `jivo-factory-pp-cli doctor` reports `agentcookie: detected` and `auth-status` labels the source as `agentcookie`. Skip this section if you don't use agentcookie - the CLI works the same as any other.

## Troubleshooting
**Authentication errors (exit code 4)**
- Run `jivo-factory-pp-cli doctor` to check credentials
- Verify the environment variable is set: `echo $JIVO_FACTORY_TOKEN`
**Not found errors (exit code 3)**
- Check the resource ID is correct
- Run the `list` command to see available items

## Regeneration Safety

This printed tree has deliberate local safeguards, three-company request scoping, and a live-API pagination correction. Before or after any regeneration, review [[CLI/factory-cli/.printing-press-patches/README|the Factory local patch ledger]] and re-apply every entry whose evidence still holds.

---

Generated by [CLI Printing Press](https://github.com/mvanhorn/cli-printing-press)

Linked: [[CLI/factory-cli/.printing-press-patches/README|Factory patch ledger]] · [[CLI/factory-cli/AGENTS|Agent guide]] · [[CLI/factory-cli/SKILL|Agent skill]] · [[CLI/factory-cli/INTEL-README|Intelligence vault guide]] · [[CLI/factory-cli/app-model/README|App model]] · [[CLI/factory-cli/research/API-FACTS|API facts]] · [[CLI/factory-cli/vault-schema|Vault schema]] · [[docs/factory/FACTORY_MAP|FACTORY_MAP]] · [[docs/FACTORY_CLI_PLAN|FACTORY_CLI_PLAN]] · [[docs/READ_ONLY_LAW|READ_ONLY_LAW]]
