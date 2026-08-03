# JIVO Factory CLI

**Read-only access to every live endpoint of JIVO's factory system across all three companies, with an offline mirror and an agent-native surface.**

Covers gate entry, vehicles, quality control, GRPO, barcode traceability, dispatch, production, warehouse transfers, maintenance, marketplace fulfilment, bottle blowing and labour. Every endpoint was live-verified before it shipped: dead routes are excluded, required parameters are declared, and endpoints that mutate on GET are refused outright.

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

## Authentication

Authenticate once with 'auth login' using JIVO_FACTORY_EMAIL and JIVO_FACTORY_PASSWORD; the CLI stores only the rotating JWT pair, never the password. Access tokens last about 25 hours and refresh tokens about 7 days, so a daily refresh keeps auth alive indefinitely. Every request also carries a Company-Code header set from --company.

## Quick Start

```bash
# check config and connectivity before anything else
jivo-factory-pp-cli doctor --dry-run


# confirm who you are and which companies you can see
jivo-factory-pp-cli accounts me --json


# a plain read against the default company (JIVO_MART)
jivo-factory-pp-cli gate-core arrivals --json --limit 5


# an Oil-only endpoint; its HANA view exists in no other company
jivo-factory-pp-cli barcode production-release-oil --company oil --json

```

## Recipes


### Who is at the gate right now

```bash
jivo-factory-pp-cli person-gatein entry-inside --json
```

Lists everyone currently inside the plant, from the person gate-in module.

### Narrow a large response before reading it

```bash
jivo-factory-pp-cli marketplace orders --agent --select results.order_id,results.buyer_name,results.status --limit 20
```

Marketplace orders returns thousands of rows; --select keeps only the fields that matter so an agent does not burn context on the full payload.

### Is in-house bottle blowing cheaper than buying

```bash
jivo-factory-pp-cli blowing reports-make-vs-buy --company oil --date-from 2026-07-01 --date-to 2026-07-31 --json
```

Compares in-house blow cost per bottle against the supplier landed price, with breakeven volume and a MAKE/BUY verdict.

### Mirror locally, then join across domains

```bash
jivo-factory-pp-cli sync --resources barcode,grpo,quality-control && jivo-factory-pp-cli sql "SELECT resource_type, COUNT(*) FROM resources GROUP BY resource_type"
```

The API has no server-side aggregation; sync once and answer cross-domain questions locally.

### Check one company against another

```bash
jivo-factory-pp-cli grpo pending --company oil --json --select doc_num,item_code,quantity
```

Most endpoints are identical across companies, so the same command answers the same question for Mart, Oil or Beverages.

## Usage

Run `jivo-factory-pp-cli --help` for the full command reference and flag list.

## Commands

### accounts

The "platform" group is the plumbing the rest of the factory app sits on: who you are, who else exists, what the app tells people, and the one hand-off point with JIVO's separate order system. /accoun

- **`jivo-factory-pp-cli accounts departments`** - List the factory's department master (IT, Ecom, Account, Store, Dock, Quality, Fire, production(oil), …) used by attendance, labour-count and gate-in forms.
- **`jivo-factory-pp-cli accounts me`** - Show the signed-in account: name, employee code, the companies it can switch to, and its full permission list.
- **`jivo-factory-pp-cli accounts users`** - List every factory app user (name, email, employee code, active/staff flags) — the notification-recipient picker.

### attendance

This group covers three small, separate parts of the gate operation. (1) **Attendance** is the manual attendance register — the app's own subtitle is "Manual attendance register — used when the punchi

- **`jivo-factory-pp-cli attendance attendance-employees`** - List the employee master used by the manual attendance register (code, name, department, active flag).
- **`jivo-factory-pp-cli attendance attendance-export`** - Download an Excel (.xlsx) sheet of manual attendance marks for a date range.
- **`jivo-factory-pp-cli attendance attendance-records`** - List manual attendance marks (IN/OUT punches with photo proof) for a date or date range.

### barcode

This is JIVO's carton-level traceability system — the barcode that gets stuck on every box coming off a filling line, and everything that happens to that box afterwards. A production run generates BOX

- **`jivo-factory-pp-cli barcode box`** - One carton in full — including its embedded movement history (create, pallet in/out, warehouse moves). Required: id.
- **`jivo-factory-pp-cli barcode box-history`** - Movement log for one carton — but it returns an empty list for every box I tried; use `box` instead. Required: id.
- **`jivo-factory-pp-cli barcode boxes`** - List carton barcodes — item, batch, qty, pallet, warehouse and status for every box.
- **`jivo-factory-pp-cli barcode dispatch-report-detail`** - Full dispatch report for one session — header, bill lines, the units scanned against each, and every scan. Required: id.
- **`jivo-factory-pp-cli barcode dispatch-reports`** - Dispatch summary per bill — expected vs dispatched vs pending quantity and boxes, and SAP sync state.
- **`jivo-factory-pp-cli barcode dispatch-reports-boxes`** - Box-level dispatch report — every carton, its pallet, its bill and whether it has shipped.
- **`jivo-factory-pp-cli barcode dispatch-reports-pallets`** - Pallet-level dispatch report — boxes on each pallet, how many shipped, how many remain.
- **`jivo-factory-pp-cli barcode dispatch-reports-rejected-scans`** - Scans the system refused during dispatch — the barcode, the reason and the code, per bill and operator.
- **`jivo-factory-pp-cli barcode dispatch-sap-sync-logs`** - SAP posting attempts for one dispatch session — what was sent and what came back. Required: id.
- **`jivo-factory-pp-cli barcode dispatch-scan-logs`** - Every scan attempt in one dispatch session, accepted and rejected, with the exact message the scanner showed. Required: id.
- **`jivo-factory-pp-cli barcode dispatch-session`** - One dispatch session in full — bill header, lines, scanned units and counters. Required: id.
- **`jivo-factory-pp-cli barcode dispatch-sessions`** - All dispatch sessions — one per SAP bill being loaded, with expected vs scanned vs pending quantity and SAP sync state.
- **`jivo-factory-pp-cli barcode dispatch-sessions-active`** - Dispatch sessions still open on the floor — loading in progress or not yet started.
- **`jivo-factory-pp-cli barcode dispatch-sessions-closed`** - Dispatch sessions a supervisor force-closed short of the full bill quantity.
- **`jivo-factory-pp-cli barcode dispatch-sessions-completed`** - Dispatch sessions where every bill line has been scanned out.
- **`jivo-factory-pp-cli barcode dispatch-sessions-from-bill`** - GET /barcode/dispatch/sessions/from-bill/
- **`jivo-factory-pp-cli barcode intercompany-dashboard`** - Today's intercompany movement plus lifetime totals per route and the latest transfers.
- **`jivo-factory-pp-cli barcode intercompany-trace`** - Follow one barcode across companies — where it is now, who made it, and its transfer history. Required: search.
- **`jivo-factory-pp-cli barcode intercompany-transfer`** - One intercompany transfer with its full barcode line list. Required: id.
- **`jivo-factory-pp-cli barcode intercompany-transfers`** - Stock physically moved between JIVO companies by barcode scan — with every box on each transfer.
- **`jivo-factory-pp-cli barcode item-detail`** - Item group lookup for one SAP item code — used to decide which label template applies. Required: item_code.
- **`jivo-factory-pp-cli barcode items-oitm`** - SAP item master as the barcode module sees it — UoM, batch flags and pieces-per-box for label generation.
- **`jivo-factory-pp-cli barcode lookup`** - Resolve any scanned barcode to what it actually is — box, pallet or unknown. Required: barcode.
- **`jivo-factory-pp-cli barcode loose`** - Loose stock — part-used cartons booked out with a reason, and what they were later repacked into.
- **`jivo-factory-pp-cli barcode loose-item`** - One loose-stock record — source box/pallet, reason and repack destination. Required: id.
- **`jivo-factory-pp-cli barcode pallet`** - One pallet in full, with the list of boxes currently sitting on it. Required: id.
- **`jivo-factory-pp-cli barcode pallet-history`** - Movement log for one pallet — returns an empty list in practice; use `pallet` instead. Required: id.
- **`jivo-factory-pp-cli barcode pallets`** - List pallets — item, batch, box counts (total/available/dispatched), warehouse and status.
- **`jivo-factory-pp-cli barcode print-history`** - Label print audit trail — every original print and reprint, with printer, operator and reprint reason.
- **`jivo-factory-pp-cli barcode production-release-oil`** - Oil production orders released for labelling — planned quantity converted to box count, box size and litres.
- **`jivo-factory-pp-cli barcode scan-history`** - Every barcode scan the factory has made — type, entity, result, operator and device.
- **`jivo-factory-pp-cli barcode verify-request`** - One pallet verification request with its findings — matched, missing and foreign boxes. Required: id.
- **`jivo-factory-pp-cli barcode verify-requests`** - Queue of pallet re-count requests raised when a pallet's contents are disputed.
- **`jivo-factory-pp-cli barcode voided-boxes`** - Audit list of every voided carton — who voided it, when, and why.
- **`jivo-factory-pp-cli barcode voided-pallets`** - Audit list of every voided pallet — box count, quantity, who and why.

### blowing

The blowing module tracks JIVO's own PET bottle-making: a blow-moulding machine heats plastic "preforms" (test-tube-shaped blanks bought from a supplier) and blows them into finished bottles. Operator

- **`jivo-factory-pp-cli blowing audit`** - Who changed a blowing master and what they changed — field-by-field old/new, with the user's email and timestamp. Required: entity_type, entity_id.
- **`jivo-factory-pp-cli blowing breakdown-categories`** - The pick-list of reasons a blowing machine stopped — Machine, PM Short, RM Short, Labour Short.
- **`jivo-factory-pp-cli blowing buy-prices`** - What a supplier charges for the finished bottle — buy price plus freight, duties, carrying and QA allowance, giving the landed cost per bottle used in make-vs-buy.
- **`jivo-factory-pp-cli blowing cost-rates`** - The Cost Master — one rate per cost category (operator, labour, electricity, packing, scrap credit, industry benchmark), company-wide or overridden per machine.
- **`jivo-factory-pp-cli blowing machines`** - Blow-moulding machines — name, number of heads, linked SAP warehouse and depreciation per day.
- **`jivo-factory-pp-cli blowing make-vs-buy`** - Per bottle size over a date range: what it cost us to blow vs what the supplier charges landed, with breakeven volume, period savings and a MAKE/BUY verdict. Required: date_from, date_to.
- **`jivo-factory-pp-cli blowing preform-specs`** - The bottle sizes we blow — preform make and gram weight, preforms per box, preform rate per bottle, SAP item, and the cost/reject standards runs are measured against.
- **`jivo-factory-pp-cli blowing rate-configs`** - The older dated rate sheet — operator, labour, electricity, scrap, packing, maintenance, overhead and QA rates effective from a date.
- **`jivo-factory-pp-cli blowing report-daily`** - One day's blowing output and cost, totalled and split by machine and by bottle size. Required: date.
- **`jivo-factory-pp-cli blowing report-monthly`** - A month of blowing — totals plus a day-by-day table of production, rejection, electricity units, net cost and ₹/bottle. Required: year, month.
- **`jivo-factory-pp-cli blowing run`** - One run in full — production readings, manpower, the running/breakdown timeline, and the complete costing with every cost line. Required: id.
- **`jivo-factory-pp-cli blowing runs`** - List blowing production runs — date, machine, bottle size, production, rejection %, ₹/bottle, net cost and status.
- **`jivo-factory-pp-cli blowing sap-items`** - Search SAP's item master from inside blowing, to link a preform spec to its real SAP item code.
- **`jivo-factory-pp-cli blowing variances`** - Actual vs standard per run over a date range — make cost/bottle, reject % and electricity units/bottle, flagged when they breach the target. Required: date_from, date_to.

### company

company

- **`jivo-factory-pp-cli company`** - GET /company/companies/

### construction-gatein

These five prefixes are the "what came in the gate" flows, split by what kind of material arrived: raw material / packing material against a purchase order, daily-needs (canteen food and consumables),

- **`jivo-factory-pp-cli construction-gatein construction-categories`** - List the material categories a construction gate entry can be filed under (civil/building work).
- **`jivo-factory-pp-cli construction-gatein construction-entry`** - Read the construction material detail recorded against one gate entry — project, work order, contractor, what was brought in. Required: entry_id.

### daily-needs-gatein

These five prefixes are the "what came in the gate" flows, split by what kind of material arrived: raw material / packing material against a purchase order, daily-needs (canteen food and consumables),

- **`jivo-factory-pp-cli daily-needs-gatein daily-need-entry`** - Read the daily-needs consumables detail on one gate entry — supplier, bill/challan, line items and receiving department. Required: entry_id.
- **`jivo-factory-pp-cli daily-needs-gatein gate-entries-daily-need-categories`** - List the daily-needs categories (canteen food / routine consumables) a gate entry can be filed under.

### dashboards

This is the factory app's read-only reporting corner — the five "management dashboard" screens the plant and purchase teams open when they want to know what stock is sitting where, how old it is, what

- **`jivo-factory-pp-cli dashboards inventory-age-filter-options`** - The company's own list of item groups, sub-groups, warehouses and varieties — the authoritative pick-list for every other filter in this group.
- **`jivo-factory-pp-cli dashboards inventory-age-report`** - Every item sitting in stock with how many days it has been there, its litres and its stock value, plus a per-warehouse rollup.
- **`jivo-factory-pp-cli dashboards sales-planning-requirement-analysis`** - Self-documentation for the sales-plan report: which SAP procedure feeds it, what each column means, where it is cached and when the scheduler reruns it.
- **`jivo-factory-pp-cli dashboards sales-planning-requirement-report`** - Monthly forecast demand vs stock in hand, minimum stock and open POs — the net shortage per item for the current planning month.
- **`jivo-factory-pp-cli dashboards sales-planning-requirement-status`** - When the sales-plan report was last rebuilt from SAP, by whom, how long it took and whether it succeeded.
- **`jivo-factory-pp-cli dashboards stock`** - On-hand stock vs its minimum-stock benchmark, per item per warehouse, flagged healthy / low / critical.
- **`jivo-factory-pp-cli dashboards stock-as-of`** - The same stock-vs-benchmark view reconstructed as it stood on a chosen past date. Required: as_of_date.
- **`jivo-factory-pp-cli dashboards stock-benchmark-item-warehouses`** - Per-warehouse breakdown of one item's on-hand vs benchmark — un-aggregates a row the list view merged. Required: item_code, warehouse.

### dispatch

The dispatch domain follows a SAP sales invoice from the moment it becomes a "dispatch bill" to the moment the truck clears the gate and the transporter gets paid. /dispatch-plans/ is the planning hal

- **`jivo-factory-pp-cli dispatch bilty-grpo-history`** - Every transporter bilty that has been posted (or failed to post) to SAP as a service GRPO, with the SAP document number and the freight lines.
- **`jivo-factory-pp-cli dispatch bilty-grpo-options`** - The SAP master-data pick-lists used when booking a bilty as a service GRPO — branches, tax codes, G/L accounts, SAC codes, locations, varieties, projects, sub-accounts and expense codes.
- **`jivo-factory-pp-cli dispatch bilty-grpo-pending`** - Booked dispatch vehicle bookings that still need their transporter bilty posted to SAP as a service GRPO — the freight-booking to-do list.
- **`jivo-factory-pp-cli dispatch open-bilties`** - Bilties whose service GRPO is posted in SAP but which have not yet been rolled into a transporter A/P invoice — the freight payables waiting to be billed.
- **`jivo-factory-pp-cli dispatch transporter-invoices-history`** - Transporter A/P invoices submitted or posted to SAP from bilty GRPOs.

### dispatch-plans

The dispatch domain follows a SAP sales invoice from the moment it becomes a "dispatch bill" to the moment the truck clears the gate and the transporter gets paid. /dispatch-plans/ is the planning hal

- **`jivo-factory-pp-cli dispatch-plans bills`** - SAP sales invoices in a date window with the factory's dispatch-planning overlay (vehicle, transporter, driver, bilty, freight, planned dispatch date) attached to each one. Required: date_from, date_to.
- **`jivo-factory-pp-cli dispatch-plans dispatch-fulfilment-bills`** - Bill-by-bill fulfilment list — what was billed versus what actually went out the gate, with the fulfilment rate, gatepass number and the individual gate-out events per invoice.
- **`jivo-factory-pp-cli dispatch-plans dispatch-fulfilment-summary`** - Dispatch fulfilment headline for a date range — value/weight/litres/trucks dispatched, open backlog by booking status, a daily trend line and the top 50 customers by dispatched value.
- **`jivo-factory-pp-cli dispatch-plans dispatch-plans-bill-by-number`** - Look up one dispatch bill by its SAP invoice number, with its planning overlay and its line items. Required: bill_number.
- **`jivo-factory-pp-cli dispatch-plans pipeline`** - Live dispatch board — every vehicle currently in the dispatch flow, bucketed into the 10 pipeline stages from 'Booked' through 'Docked' to 'Dispatched'.

### docking-admin

The dispatch domain follows a SAP sales invoice from the moment it becomes a "dispatch bill" to the moment the truck clears the gate and the transporter gets paid. /dispatch-plans/ is the planning hal

- **`jivo-factory-pp-cli docking-admin partial-scan-requests`** - Requests to dispatch a vehicle when the scanned box count is short of the invoice count (e.g. 515 of 521 scanned), with the shortfall reason and the supervisor's decision.
- **`jivo-factory-pp-cli docking-admin scan-skip-requests`** - Requests from the dock to dispatch a vehicle WITHOUT barcode scanning (old barcodes, loose cartons, drums), and whether a supervisor approved them.

### driver-management

This is the factory's transport master file plus the gate's vehicle-entry log. Three master lists sit under it — Vehicles (registration number, type, capacity, owning transporter), Transporters (conta

- **`jivo-factory-pp-cli driver-management drivers`** - All drivers on file — mobile, driving licence, ID proof and photo.
- **`jivo-factory-pp-cli driver-management drivers-names`** - Slim id + name list of drivers, for pickers.

### fixed-asset-gatein

These five prefixes are the "what came in the gate" flows, split by what kind of material arrived: raw material / packing material against a purchase order, daily-needs (canteen food and consumables),

- **`jivo-factory-pp-cli fixed-asset-gatein`** - List the capital-asset categories a fixed-asset gate entry can be filed under (machinery, IT, furniture, vehicles...).

### gate-core

gate-core is the shared gate engine underneath every category-specific gate app (raw-material, daily-needs, maintenance, construction, fixed-asset gatein). Its central object is an **arrival** — one p

- **`jivo-factory-pp-cli gate-core arrival-gatepass-readiness`** - Pre-flight check before printing a truck's combined gatepass — is every company on this truck ready, and which are locked. Required: id.
- **`jivo-factory-pp-cli gate-core arrivals`** - Trucks at the gate — one row per physical vehicle arrival, with every company's gate-in and gate-out on that truck.
- **`jivo-factory-pp-cli gate-core arrivals-expected`** - What a given vehicle is expected to pick up — the companies and booked bills waiting for that truck, before you gate it in. Required: vehicle_id.
- **`jivo-factory-pp-cli gate-core bst-in`** - One legacy BST-in record by id. Required: id.
- **`jivo-factory-pp-cli gate-core bst-ins`** - Branch stock transfers received back in through the gate (legacy path).
- **`jivo-factory-pp-cli gate-core bst-ins-eligible-outs`** - BST-outs that are still open and can be received back in.
- **`jivo-factory-pp-cli gate-core bst-out`** - One BST gate-out entry by id. Required: id.
- **`jivo-factory-pp-cli gate-core bst-outs`** - Branch stock transfers going out through the gate — stock leaving one JIVO warehouse for another.
- **`jivo-factory-pp-cli gate-core bst-outs-sap-transfer`** - One SAP stock-transfer document by its DocEntry, with line detail. Required: doc_entry.
- **`jivo-factory-pp-cli gate-core bst-outs-sap-transfers`** - SAP stock-transfer documents available to attach to a BST gate-out — search by document number.
- **`jivo-factory-pp-cli gate-core bst-return`** - One legacy BST-return record by id. Required: id.
- **`jivo-factory-pp-cli gate-core bst-returns`** - BST material coming back after a failed or partial transfer (legacy path).
- **`jivo-factory-pp-cli gate-core bst-returns-eligible-outs`** - BST-outs eligible to be returned.
- **`jivo-factory-pp-cli gate-core construction-gate-entry`** - Full view of a construction-material gate entry. Required: id.
- **`jivo-factory-pp-cli gate-core daily-need-gate-entry`** - Full view of a daily-need consumables gate entry. Required: id.
- **`jivo-factory-pp-cli gate-core dispatch-tracking`** - Where every dispatched truck is now — in transit, delivered, returned, or overdue against its expected reach date.
- **`jivo-factory-pp-cli gate-core dispatch-tracking-updates`** - The status-update trail for one dispatched truck — each in-transit event with its location, remark and proof. Required: arrival_id.
- **`jivo-factory-pp-cli gate-core empty-vehicle-in`** - One empty-vehicle gate-in record by id. Required: id.
- **`jivo-factory-pp-cli gate-core empty-vehicle-ins`** - Empty vehicles gated in — the per-company gate-in record for a truck arriving to load, with its live pipeline stage.
- **`jivo-factory-pp-cli gate-core empty-vehicle-ins-eligible`** - Gate-in entries still open and eligible for the next step — the working queue at the gate.
- **`jivo-factory-pp-cli gate-core empty-vehicle-ins-reasons`** - The valid reasons an empty vehicle can be gated in — use this to populate or validate the reason filter.
- **`jivo-factory-pp-cli gate-core empty-vehicle-out`** - One empty gate-out record by id. Required: id.
- **`jivo-factory-pp-cli gate-core empty-vehicle-outs`** - Vehicles sent back out empty — the gate-out record for a truck that came in but did not load.
- **`jivo-factory-pp-cli gate-core empty-vehicle-outs-eligible-entries`** - Vehicle entries that are allowed to leave empty right now — the pick-list for recording an empty gate-out.
- **`jivo-factory-pp-cli gate-core gate-attachments`** - Files attached to a gate entry — photos, e-way bills, weighment slips. Required: gate_entry_id.
- **`jivo-factory-pp-cli gate-core inside-dispatch-vehicles`** - Trucks currently parked inside the plant with their loaded bills — who is inside and what is on each vehicle.
- **`jivo-factory-pp-cli gate-core job-work`** - Job-work movements at the gate — material sent out to a job worker and coming back, tied to the SAP production order.
- **`jivo-factory-pp-cli gate-core job-work-detail`** - One job-work gate record by id. Required: id.
- **`jivo-factory-pp-cli gate-core job-work-sap-grpo`** - One SAP GRPO by DocEntry, for job-work attachment. Required: doc_entry.
- **`jivo-factory-pp-cli gate-core job-work-sap-grpos`** - SAP goods-receipt POs available to attach to a job-work entry — search by GRPO number.
- **`jivo-factory-pp-cli gate-core job-work-sap-production-order`** - One SAP production order by DocEntry, with its component list. Required: doc_entry.
- **`jivo-factory-pp-cli gate-core job-work-sap-production-orders`** - SAP production orders available to link to a job-work entry — planned vs completed vs remaining quantity.
- **`jivo-factory-pp-cli gate-core maintenance-gate-entry`** - Full view of a maintenance-material gate entry. Required: id.
- **`jivo-factory-pp-cli gate-core raw-material-gate-entry`** - Full view of a raw-material gate entry — the complete record the review screen shows. Required: id.
- **`jivo-factory-pp-cli gate-core rejected-qc-return`** - One rejected-QC return record by id. Required: id.
- **`jivo-factory-pp-cli gate-core rejected-qc-returns`** - QC-rejected material leaving the plant — goods sent back out after failing quality control.
- **`jivo-factory-pp-cli gate-core sales-dispatch`** - Customer dispatches at the gate ('docking') — one row per company per truck, from docked through gatepass to dispatched, with the SAP invoice, customer, weights and gatepass number.
- **`jivo-factory-pp-cli gate-core sales-dispatch-attachments`** - Documents photographed or uploaded against a dispatch — e-way bill, bilty, truck photo. Required: id.
- **`jivo-factory-pp-cli gate-core sales-dispatch-barcode-scans`** - Whether a dispatch has been matched to a barcode scanning session, and how many boxes it covers. Required: id.
- **`jivo-factory-pp-cli gate-core sales-dispatch-box-scans`** - Every carton barcode scanned onto a dispatch — the box-level proof of what physically went on the truck. Required: id.
- **`jivo-factory-pp-cli gate-core sales-dispatch-detail`** - One dispatch in full — every SAP document, line item, attachment and box scan on it. Required: id.
- **`jivo-factory-pp-cli gate-core sales-dispatch-document`** - One SAP document (invoice or stock transfer) with its lines, as the dock sees it. Required: document_type, doc_entry.
- **`jivo-factory-pp-cli gate-core sales-dispatch-documents`** - SAP invoices and stock transfers available to load onto a truck — the bill pick-list at the dock.
- **`jivo-factory-pp-cli gate-core sales-dispatch-gatepass-prints`** - Print history for a dispatch's gatepass — who printed which copy, when, and any reprint reason. Required: id.
- **`jivo-factory-pp-cli gate-core sales-dispatch-pending-bookings`** - Bills booked to a truck but not yet docked — loads that are planned and still waiting to enter the dispatch flow.
- **`jivo-factory-pp-cli gate-core sales-dispatch-reports`** - Gate-out control report — dispatch counts bucketed by stage (waiting inside, missing photo, gatepass pending, printed-not-committed, ready, dispatched, rejected) with the full rows behind each bucket.
- **`jivo-factory-pp-cli gate-core unit-choices`** - The units of measure the gate apps offer — use it to resolve or validate a unit id.

### grpo

GRPO = "Goods Receipt PO" — the step where material that has physically arrived at a JIVO plant gets booked into SAP as a purchase receipt. It has two completely separate halves that share the /grpo/

- **`jivo-factory-pp-cli grpo all-entries`** - Every raw-material gate entry visible to GRPO — including trucks still at the gate or sitting with QC — with supplier, PO numbers and per-item accepted/rejected quantity.
- **`jivo-factory-pp-cli grpo attachments`** - Documents attached to a material GRPO posting (supplier invoice, weighment slip) and whether each one made it into SAP. Required: posting_id.
- **`jivo-factory-pp-cli grpo history`** - Log of every material GRPO posting ATTEMPT — posted, failed or saved-as-draft — with the SAP document number or the verbatim SAP error.
- **`jivo-factory-pp-cli grpo history-detail`** - GET /grpo/history/{posting_id}/
- **`jivo-factory-pp-cli grpo inspection-report`** - The full QC inspection report behind a receipt — chemist and QA-manager decisions, parameter results, accept/reject verdict and its attachments. Required: arrival_slip_id.
- **`jivo-factory-pp-cli grpo pending`** - Gate entries that have cleared QC and are waiting to be posted to SAP — the actual GRPO work queue, grouped by supplier so several POs can be merged into one receipt.
- **`jivo-factory-pp-cli grpo preview`** - Everything needed to post a gate entry to SAP — PO lines, QC status, accepted quantity, price, tax code, warehouse and GL account — read-only, before anyone posts. Required: vehicle_entry_id.
- **`jivo-factory-pp-cli grpo service-history`** - Log of transport-service GRPO postings — which bilty was booked against which transporter, for how much, and its SAP document number.
- **`jivo-factory-pp-cli grpo service-history-detail`** - GET /grpo/service/history/{posting_id}/
- **`jivo-factory-pp-cli grpo service-options`** - The SAP master lists a freight booking has to pick from — branches, tax codes, GL accounts, SAC codes, locations, varieties, projects, sub-accounts and expense codes.
- **`jivo-factory-pp-cli grpo service-pending`** - Dispatched vehicles whose transporter freight (bilty) has not yet been booked to SAP as a service purchase — the freight-booking backlog.
- **`jivo-factory-pp-cli grpo summary`** - GRPO dashboard totals for one company: entries and POs awaiting posting, QC accepted/rejected quantity, and posted/failed posting counts.

### labour-count

This domain covers how JIVO's factory counts contract ("casual") labour on and off the site each day. Two separate Django apps live here and they solve the same problem twice. `labour_gate` (paths und

- **`jivo-factory-pp-cli labour-count gate-board`** - The gate's verification board for a shift — every submitted/verified department sheet with its headcount, how many have been marked out and the variance. Required: work_date, shift.
- **`jivo-factory-pp-cli labour-count sheet-history`** - List of daily labour-count sheets a department filed — date, shift, headcount, workflow status and gate variance.

### labour-gate

This domain covers how JIVO's factory counts contract ("casual") labour on and off the site each day. Two separate Django apps live here and they solve the same problem twice. `labour_gate` (paths und

- **`jivo-factory-pp-cli labour-gate gate-day`** - Every contractor's labour in/out tally at the gate for one date — how many came in, how many have left, how many are still inside. Required: date.
- **`jivo-factory-pp-cli labour-gate gate-entry-audit`** - Full who/what/when audit trail for one gate labour entry — every in, edit, mark-out, undo, delete and restore. Required: id.

### maintenance

The `/maintenance/` group is the factory's plant-engineering system — everything that keeps machines running and the site safe. It covers six workflows that share one asset register: (1) **Assets** —

- **`jivo-factory-pp-cli maintenance alerts`** - Live maintenance alert feed — PM due, breakdown escalation, low critical spare, AMC/warranty expiry.
- **`jivo-factory-pp-cli maintenance asset-categories`** - Asset category master (e.g. 'Filling machines'), with how many assets sit in each.
- **`jivo-factory-pp-cli maintenance asset-departments`** - Maintenance's own department master (separate from the HR/org department list), with asset counts.
- **`jivo-factory-pp-cli maintenance asset-documents`** - Documents filed against an asset — manual, warranty, AMC contract, service report, calibration certificate.
- **`jivo-factory-pp-cli maintenance asset-locations`** - Asset location master (plant area / line), with asset counts.
- **`jivo-factory-pp-cli maintenance asset-photos`** - Photos attached to assets, including the monthly condition photo.
- **`jivo-factory-pp-cli maintenance assets`** - The plant asset register — every machine/component with its category, location, department, status, make/model/serial, warranty and AMC dates.
- **`jivo-factory-pp-cli maintenance dashboard`** - One-screen plant health: asset counts by status, open/critical work orders, breakdowns and production downtime minutes, PM compliance, spare risk and vendor visits.
- **`jivo-factory-pp-cli maintenance maintenance-asset-document-get`** - One asset document record. Required: id.
- **`jivo-factory-pp-cli maintenance maintenance-asset-get`** - Full record for one asset. Required: id.
- **`jivo-factory-pp-cli maintenance maintenance-asset-photo-get`** - One asset photo record. Required: id.
- **`jivo-factory-pp-cli maintenance maintenance-fire-categories`** - Fire & safety item category master (Helmets, Reflective jacket, …) with item counts.
- **`jivo-factory-pp-cli maintenance maintenance-fire-issue-get`** - One PPE/fire-equipment issue slip with its line items. Required: id.
- **`jivo-factory-pp-cli maintenance maintenance-fire-issues`** - The safety-equipment issue register — who took what PPE out, when it is due back, and whether it came back OK, damaged or lost.
- **`jivo-factory-pp-cli maintenance maintenance-fire-item-get`** - One fire-safety store item. Required: id.
- **`jivo-factory-pp-cli maintenance maintenance-fire-items`** - Fire & safety store master — extinguishers, hydrants, PPE, jackets, boots — with stock, reorder level and which assets each item covers.
- **`jivo-factory-pp-cli maintenance maintenance-fire-low-stock`** - Fire-safety items at or below reorder level — the safety-store reorder shortlist.
- **`jivo-factory-pp-cli maintenance maintenance-fire-movements`** - Fire & safety store stock ledger — every issue, return, consumption and adjustment with quantity and value.
- **`jivo-factory-pp-cli maintenance maintenance-fire-report-attachments`** - Files attached to a whole fire inspection report.
- **`jivo-factory-pp-cli maintenance maintenance-fire-report-get`** - One fire inspection round with its full equipment checklist. Required: id.
- **`jivo-factory-pp-cli maintenance maintenance-fire-report-items`** - Per-equipment lines on a fire inspection round — pump, hydrant, extinguisher, sprinkler — each marked OK, Not Okay or Needs Attention with a reading and remarks.
- **`jivo-factory-pp-cli maintenance maintenance-fire-report-photos`** - Photos attached to a fire-inspection checklist line.
- **`jivo-factory-pp-cli maintenance maintenance-fire-reports`** - Shift-wise fire-safety inspection rounds — one report per shift per area, with its equipment checklist and how many items needed attention.
- **`jivo-factory-pp-cli maintenance maintenance-fire-request-get`** - One fire-store request. Required: id.
- **`jivo-factory-pp-cli maintenance maintenance-fire-requests`** - Requests for fire-safety items from the safety store, through issue, consumption and return of unused stock.
- **`jivo-factory-pp-cli maintenance maintenance-material-indent-attachments`** - Files attached to a material indent (quotations, photos, bills).
- **`jivo-factory-pp-cli maintenance maintenance-material-indent-get`** - One material indent with all its line items, shortfalls and step-by-step approval trail. Required: id.
- **`jivo-factory-pp-cli maintenance maintenance-material-indents`** - Maintenance purchase demands through their 6-step life — submitted to store, pending purchase approval, approved, purchased, arrived at gate, received into store — with line items, shortfalls and attachments.
- **`jivo-factory-pp-cli maintenance maintenance-pm-execution-get`** - One PM execution with its full checklist result set. Required: id.
- **`jivo-factory-pp-cli maintenance maintenance-safety-fine-get`** - One safety fine with its evidence photos. Required: id.
- **`jivo-factory-pp-cli maintenance maintenance-safety-fine-photos`** - Evidence photos attached to a safety fine.
- **`jivo-factory-pp-cli maintenance maintenance-safety-fines`** - Safety fines raised against a worker or contractor — what PPE was missing, where, how much, and whether it has been recovered.
- **`jivo-factory-pp-cli maintenance maintenance-safety-violation-types`** - The safety violation master — each violation and its default fine amount, plus how many fines have been raised under it.
- **`jivo-factory-pp-cli maintenance maintenance-spare-get`** - One spare part. Required: id.
- **`jivo-factory-pp-cli maintenance maintenance-spare-request-get`** - One spare request. Required: id.
- **`jivo-factory-pp-cli maintenance maintenance-vendor-visit-get`** - One vendor visit. Required: id.
- **`jivo-factory-pp-cli maintenance maintenance-work-order-get`** - Full record for one work order, including root cause, corrective/preventive action and timing. Required: id.
- **`jivo-factory-pp-cli maintenance maintenance-work-order-photo-get`** - One work-order photo record. Required: id.
- **`jivo-factory-pp-cli maintenance maintenance-work-permit-attachments`** - Files attached to a permit-to-work (JSA, isolation certificate, gas-test record).
- **`jivo-factory-pp-cli maintenance maintenance-work-permit-get`** - One permit-to-work in full, including its workers, hazards, PPE, isolations and approval chain. Required: id.
- **`jivo-factory-pp-cli maintenance maintenance-work-permit-workers`** - The named workers on a permit-to-work and whether each has signed on.
- **`jivo-factory-pp-cli maintenance maintenance-work-permits`** - Permit-to-work register — hot work, height, confined space and the rest — with validity window, hazards, PPE, isolations, workers, approvals and renewals.
- **`jivo-factory-pp-cli maintenance options`** - The dropdown catalogue for the whole module — every status/priority/type enum plus the live category, location, department, spare-category, machine and user master lists.
- **`jivo-factory-pp-cli maintenance pm-checklist-items`** - The checklist template lines under a PM plan — what the technician has to tick, measure or record.
- **`jivo-factory-pp-cli maintenance pm-executions`** - Actual PM rounds generated from the plans — what was due, what got done, what was skipped, with the checklist results.
- **`jivo-factory-pp-cli maintenance pm-plans`** - Preventive-maintenance plans — which asset gets serviced how often, and when it is next due.
- **`jivo-factory-pp-cli maintenance reports`** - Twelve canned maintenance reports (daily, monthly, PM compliance, breakdown, downtime pareto, MTTR, MTBF, asset history, spare consumption, critical spare, vendor visit, utility downtime) for a date range.
- **`jivo-factory-pp-cli maintenance spare-categories`** - Spare category master.
- **`jivo-factory-pp-cli maintenance spare-movements`** - The spare stock ledger — every receipt, issue, consumption, return and adjustment with quantity and value.
- **`jivo-factory-pp-cli maintenance spare-requests`** - Requests raised off a work order for spares from the maintenance store, through issue, consumption and return of unused parts.
- **`jivo-factory-pp-cli maintenance spares`** - Maintenance spare-part master with local stock, reorder level, criticality and which assets each part fits.
- **`jivo-factory-pp-cli maintenance spares-low-stock`** - Spares at or below reorder level — the reorder shortlist.
- **`jivo-factory-pp-cli maintenance vendor-visits`** - External vendor / AMC visits booked against a work order, with planned vs actual times, gate entries, service report and invoice.
- **`jivo-factory-pp-cli maintenance work-order-photos`** - Before/after photos attached to a work order.
- **`jivo-factory-pp-cli maintenance work-orders`** - Maintenance work orders — complaints, breakdowns and jobs against an asset, with downtime, response/repair time and spare cost.

### maintenance-gatein

These five prefixes are the "what came in the gate" flows, split by what kind of material arrived: raw material / packing material against a purchase order, daily-needs (canteen food and consumables),

- **`jivo-factory-pp-cli maintenance-gatein maintenance-entry`** - Read the maintenance spare/tool detail on one gate entry — part number, urgency, receiving department, linked work order. Required: entry_id.
- **`jivo-factory-pp-cli maintenance-gatein maintenance-types`** - List the maintenance categories a spare-part / tool gate entry can be filed under.

### marketplace

This is the catalogue and reconciliation half of JIVO's Marketplace module — the cell that fulfils Flipkart/Amazon orders out of the Mayapuri e-com warehouse. The operator flow is: Upload an order she

- **`jivo-factory-pp-cli marketplace batch`** - Show one uploaded order sheet — filename, status, row/order/line counts and its import summary. Required: id.
- **`jivo-factory-pp-cli marketplace batch-issuance-csv`** - Download the issuance sheet for one order sheet as CSV — required vs approved vs issued vs received, per item. Required: id.
- **`jivo-factory-pp-cli marketplace batch-stock-list`** - Consolidated stock list for one order sheet — what the warehouse must issue, FG and packing material, plus SKUs that could not be mapped. Required: id.
- **`jivo-factory-pp-cli marketplace batch-variants`** - Order lines in a batch where the SKU can ship as more than one SAP item and an operator must choose which. Required: id.
- **`jivo-factory-pp-cli marketplace batches`** - List uploaded marketplace order sheets (imports) with parse counts and status.
- **`jivo-factory-pp-cli marketplace combos`** - List combo / multi-pack definitions — one marketplace listing that ships as several SAP items.
- **`jivo-factory-pp-cli marketplace dispatch-board`** - The full Outward board for one sheet - every order, its address, its tracking IDs, scan state, DN/GI numbers and who confirmed it. Required: id, channel.
- **`jivo-factory-pp-cli marketplace dispatch-orders-in-range`** - Every order across all sheets uploaded in a date window, in the same shape as the board - the bulk export the Outward screen uses. Required: channel.
- **`jivo-factory-pp-cli marketplace dispatch-sheets`** - Scanning progress per uploaded sheet - how many tracking IDs are scanned out of how many, per sheet. Required: channel.
- **`jivo-factory-pp-cli marketplace dispatches-list`** - Outward dispatches - one per order scanned out, with its SAP delivery-note and goods-issue numbers and posting status.
- **`jivo-factory-pp-cli marketplace dn-awaiting-approval`** - How many marketplace delivery notes are sitting in SAP waiting for approval before they post.
- **`jivo-factory-pp-cli marketplace dn-export-csv`** - Download one posted SAP delivery note's item-level detail as CSV. Required: id.
- **`jivo-factory-pp-cli marketplace dn-posted`** - SAP delivery notes already posted for marketplace dispatches, with the orders and internal invoice numbers on each.
- **`jivo-factory-pp-cli marketplace dn-sheets`** - Per sheet, how many dispatches are still awaiting a SAP delivery note and how many are already posted. Required: channel.
- **`jivo-factory-pp-cli marketplace dn-summary`** - Exactly what a delivery note would contain if it were cut right now - the lines, the value, and which orders are held back for want of stock. Required: channel.
- **`jivo-factory-pp-cli marketplace gate-queue`** - Confirmed parcels waiting at the gate, grouped by sheet, with pending/approved/held counts. Required: channel.
- **`jivo-factory-pp-cli marketplace gate-sheet`** - The gate check-list for one sheet - each parcel's order, destination, tracking IDs, DN number and gate decision. Required: id, channel.
- **`jivo-factory-pp-cli marketplace issue-requests-list`** - Stock issue requests (MPIR-nn) raised to a JIVO warehouse for a sheet, and where each one is in the approve/issue/receive chain.
- **`jivo-factory-pp-cli marketplace orders-list`** - Every marketplace order imported from the Flipkart/Amazon seller sheet, with its lines and whether it is ready to dispatch.
- **`jivo-factory-pp-cli marketplace packing-queue`** - Orders waiting to be packed, with how many lines each has.
- **`jivo-factory-pp-cli marketplace packing-summary`** - How many orders are waiting on each SAP item - the 'what to bring to the packing bench' rollup.
- **`jivo-factory-pp-cli marketplace reconciliation`** - Per-order-item deviation report — portal ordered vs outward vs inward vs physical quantity, flagging mismatches.
- **`jivo-factory-pp-cli marketplace reconciliation-export-csv`** - Download the reconciliation deviation report as CSV for a channel and date range — the only working way to date-scope it. Required: channel.
- **`jivo-factory-pp-cli marketplace report-export-csv`** - Download a marketplace report as CSV - orders/dispatch, internal invoices, SAP delivery notes, returns or reconciliation - filtered by channel and a date range. Required: slug.
- **`jivo-factory-pp-cli marketplace returns-list`** - Inward marketplace returns - parcels that came back, with their Return Note and internal credit doc numbers.
- **`jivo-factory-pp-cli marketplace sap-items`** - Type-ahead search over SAP item codes/names, used when mapping a marketplace SKU to a finished good.
- **`jivo-factory-pp-cli marketplace sku-mappings`** - List every marketplace listing→SAP item mapping: which FSN/SKU ships as which finished good or combo.
- **`jivo-factory-pp-cli marketplace warehouse-insights`** - Warehouse scoreboard for a channel — quantities required/approved/issued/received/dispatched, issue-request pipeline, and issued-vs-dispatched per item.
- **`jivo-factory-pp-cli marketplace warehouses`** - Master list linking each marketplace channel to a SAP godown, customer CardCode and delivery-note posting settings.

### non-moving-rm

This is the factory app's read-only reporting corner — the five "management dashboard" screens the plant and purchase teams open when they want to know what stock is sitting where, how old it is, what

- **`jivo-factory-pp-cli non-moving-rm item-groups`** - Item-group code/name list used by the Non-Moving screen's Material Type dropdown.
- **`jivo-factory-pp-cli non-moving-rm report`** - Dead and slow-moving stock — items whose last movement is older than N days, with quantity, value at risk and consumption ratio. Required: age, item_group.

### notifications

The "platform" group is the plumbing the rest of the factory app sits on: who you are, who else exists, what the app tells people, and the one hand-off point with JIVO's separate order system. /accoun

- **`jivo-factory-pp-cli notifications list`** - Read the alert feed for this company — gate entries, QC decisions, GRPO/FG postings, dispatch bookings, indents and returnables — newest first, optionally only unread or only read.
- **`jivo-factory-pp-cli notifications unread-count`** - How many unread alerts this account has in this company — the number on the bell badge.

### oms

The "platform" group is the plumbing the rest of the factory app sits on: who you are, who else exists, what the app tells people, and the one hand-off point with JIVO's separate order system. /accoun

- **`jivo-factory-pp-cli oms invoice-audit`** - The factory-side decision trail on one OMS invoice — who approved or rejected it here, and when. Required: id.
- **`jivo-factory-pp-cli oms invoice-history`** - Every version of one OMS invoice as it moved through approval — who submitted it, the status at that point, and the full SAP payload snapshot. Required: id.
- **`jivo-factory-pp-cli oms invoices`** - The invoice-approval queue for one warehouse: invoices raised in OMS waiting to be checked against physical stock and batches before they post to SAP. Required: whs.
- **`jivo-factory-pp-cli oms pending-count`** - How many OMS invoices are waiting on this warehouse (the badge next to Invoice Approval), split pending vs edited. Required: whs.

### person-gatein

This is the factory's people register at the gate — who walked into the plant, when, through which gate, why, and whether they have walked back out. It covers two kinds of person: **visitors** (outsid

- **`jivo-factory-pp-cli person-gatein contractors`** - The labour-contractor master — contractor name, contact person, mobile and contract expiry date.
- **`jivo-factory-pp-cli person-gatein entries`** - The full gate register — every visitor and labour entry ever recorded, with entry/exit time, gate, purpose, vehicle and status.
- **`jivo-factory-pp-cli person-gatein gate-labour`** - One labourer's master record — contractor, skill, permit validity and whether they are still active. Required: id.
- **`jivo-factory-pp-cli person-gatein gate-person-dashboard`** - Security supervisor's live board: how many visitors and labours are inside the plant right now, today's entries/exits, gate-wise headcount, and the last 10 entries.
- **`jivo-factory-pp-cli person-gatein gate-person-inside`** - Who is inside the plant right now — the live 'currently inside' list security reads at shift handover.
- **`jivo-factory-pp-cli person-gatein gate-person-search`** - Free-text search across the gate register — find an entry by person name, purpose, vehicle number or remarks. Required: q.
- **`jivo-factory-pp-cli person-gatein gates`** - The gate master — which physical gates people can be checked in and out through.
- **`jivo-factory-pp-cli person-gatein labours`** - The contract-labour master — every registered labourer, their contractor, skill and work-permit expiry.
- **`jivo-factory-pp-cli person-gatein person-types`** - The person-type lookup that maps the numeric person_type filter to a word — 1 = visitor, 2 = labour.
- **`jivo-factory-pp-cli person-gatein visitors`** - The visitor master — everyone ever registered at the gate, with mobile, the company they came from, ID proof and blacklist flag.

### po

This corner of the factory app answers one question: can we actually build what SAP says we are going to build, and what do we have to buy to close the gap. The "SAP Material Plan" screen (web route /

- **`jivo-factory-pp-cli po open-po-items`** - Look up ONE open purchase order by its PO number and return its header plus every line's remaining quantity — what the gate uses to confirm an arriving truck's PO. Required: po_number.
- **`jivo-factory-pp-cli po open-pos`** - Open (not fully received) SAP purchase orders for one supplier, with every line's ordered / received / remaining quantity and rate. Required: supplier_code.
- **`jivo-factory-pp-cli po vendors`** - SAP vendor master for the selected company — code and name only, used to pick a supplier before looking up open POs.
- **`jivo-factory-pp-cli po warehouses`** - SAP warehouse codes and names for the selected company — the source of valid --warehouse values elsewhere in this domain.

### production-execution

This is the factory's shop-floor execution system (MES) for the Bhakharpur plant — it is where a production run is born, tracked minute by minute, and costed. An operator sets up master data once (lin

- **`jivo-factory-pp-cli production-execution breakdown-categories`** - List the reason categories a line stoppage can be booked to (Machine, PM Short, RM Short, Labour, Other).
- **`jivo-factory-pp-cli production-execution checklist-templates`** - List the reusable machine-checklist templates (the checkpoint sets operators tick off per machine).
- **`jivo-factory-pp-cli production-execution cost-rates`** - Read the standing cost rates (electricity, labour, salary, maintenance, overhead, waste recovery…) used to cost a production run.
- **`jivo-factory-pp-cli production-execution costs-analytics`** - The run-cost ledger: every run's stored cost record with its component cost lines.
- **`jivo-factory-pp-cli production-execution line-clearance`** - List pre-production line clearance records — the QA sign-off that a line is clean and set up before a run starts.
- **`jivo-factory-pp-cli production-execution line-clearance-detail`** - Full detail of one line clearance including every checkpoint and its result. Required: id.
- **`jivo-factory-pp-cli production-execution line-configs`** - List the saved line presets (line + SKU + rated speed + labour/manpower counts) that pre-fill a new run.
- **`jivo-factory-pp-cli production-execution line-configs-auto-fill`** - Look up the matching saved preset for a line + SKU, as the Start Run screen does before pre-filling the form. Required: line_id.
- **`jivo-factory-pp-cli production-execution lines`** - List the physical filling/packing lines in the plant, with standard running hours per day and month.
- **`jivo-factory-pp-cli production-execution machine-checklists`** - List filled-in machine checklist entries for a machine and date/month.
- **`jivo-factory-pp-cli production-execution machines`** - List individual machines on a line (filler, capper, labeler…) used for machine-level checklists and downtime attribution.
- **`jivo-factory-pp-cli production-execution recon-material`** - Material the app says was issued vs what SAP actually transferred into the production-consumption warehouse BH-PC.
- **`jivo-factory-pp-cli production-execution recon-production`** - App-recorded production vs SAP finished-goods receipts into BH-PF — the check that what the plant says it made actually got posted in SAP.
- **`jivo-factory-pp-cli production-execution recon-wastage`** - App wastage logs vs SAP scrap actually transferred into the wastage warehouse BH-WST.
- **`jivo-factory-pp-cli production-execution reports-analytics`** - Headline production numbers for a period: runs, cases produced, running minutes, breakdown minutes, availability %.
- **`jivo-factory-pp-cli production-execution reports-analytics-cost-analysis`** - Cost per run and per case for a period, split into material, labour, machine, utilities, overhead and waste-recovery credit.
- **`jivo-factory-pp-cli production-execution reports-analytics-downtime`** - Stoppage reasons for a period, rolled up by the free-text reason operators typed.
- **`jivo-factory-pp-cli production-execution reports-analytics-downtime-pareto`** - Downtime Pareto by breakdown category, plus by machine, a daily trend and MTBF/MTTR.
- **`jivo-factory-pp-cli production-execution reports-analytics-monthly-summary`** - Twelve-month rollup for a year: runs, production, OEE, cost split and breakdown minutes per month, plus an annual total.
- **`jivo-factory-pp-cli production-execution reports-analytics-oee`** - OEE (availability × performance × quality) for a period, with a per-run breakdown.
- **`jivo-factory-pp-cli production-execution reports-analytics-oee-trend`** - OEE over time (daily/weekly/monthly) with a by-line comparison and per-run detail.
- **`jivo-factory-pp-cli production-execution reports-analytics-plan-vs-production`** - SAP production orders against what the plant actually produced — planned vs actual, variance and achievement %.
- **`jivo-factory-pp-cli production-execution reports-analytics-procurement-vs-planned`** - For one SAP production order: BOM requirement vs what was actually procured and consumed, per component. Required: sap_doc_entry.
- **`jivo-factory-pp-cli production-execution reports-analytics-resource-consumption`** - Day-by-day utility and labour consumption against production, with cost per case.
- **`jivo-factory-pp-cli production-execution reports-analytics-waste`** - Wastage rolled up by material and by approval status for a period.
- **`jivo-factory-pp-cli production-execution reports-analytics-waste-trend`** - Wastage over time with breakdowns by material, by reason and by approval status, plus waste-as-%-of-production.
- **`jivo-factory-pp-cli production-execution reports-daily-production`** - Every production run on one date, with its segments — the shift report a plant head asks for each morning. Required: date.
- **`jivo-factory-pp-cli production-execution reports-line-clearance`** - Date-filtered line clearance register — the audit trail of who cleared which line on which day.
- **`jivo-factory-pp-cli production-execution reports-production-movement`** - SAP stock movements in and out of the production warehouses — every receipt, issue, transfer and invoice line with quantity and value.
- **`jivo-factory-pp-cli production-execution reports-production-movement-filter-options`** - The valid warehouse codes and SAP transaction-type codes for the production-movement report, per company.
- **`jivo-factory-pp-cli production-execution run-breakdowns`** - List every stoppage logged against one run, with duration, category and any linked maintenance work order. Required: id.
- **`jivo-factory-pp-cli production-execution run-compressed-air`** - Compressed-air consumption and cost lines booked to one run. Required: id.
- **`jivo-factory-pp-cli production-execution run-detail`** - Full detail of one production run including every timing segment and every logged breakdown. Required: id.
- **`jivo-factory-pp-cli production-execution run-electricity`** - Electricity consumption and cost lines booked to one run. Required: id.
- **`jivo-factory-pp-cli production-execution run-gas`** - Gas consumption and cost lines booked to one run. Required: id.
- **`jivo-factory-pp-cli production-execution run-labour`** - Costed labour lines for one run — worker count, hours worked, rate and total cost. Required: id.
- **`jivo-factory-pp-cli production-execution run-machine-costs`** - Machine cost lines booked to one run. Required: id.
- **`jivo-factory-pp-cli production-execution run-machine-runtime`** - Per-machine running time recorded against one run. Required: id.
- **`jivo-factory-pp-cli production-execution run-manpower`** - Manpower entries booked to one run (headcount and role). Required: id.
- **`jivo-factory-pp-cli production-execution run-materials`** - Material consumption lines for one run — BOM quantity, opening/issued/closing, wastage and the warehouse approval state per material. Required: id.
- **`jivo-factory-pp-cli production-execution run-overhead`** - Overhead cost lines booked to one run. Required: id.
- **`jivo-factory-pp-cli production-execution run-qc-inprocess`** - In-process QC checks recorded during one run. Required: id.
- **`jivo-factory-pp-cli production-execution run-water`** - Water consumption and cost lines booked to one run. Required: id.
- **`jivo-factory-pp-cli production-execution runs`** - List production runs — the core shift-level record: date, line, SKU, required vs produced quantity, running minutes, breakdown minutes and status.
- **`jivo-factory-pp-cli production-execution sap-bom`** - Read the SAP bill of materials for one finished-goods item — what goes into one unit and at what price. Required: item_code.
- **`jivo-factory-pp-cli production-execution sap-items`** - Search the SAP item master for a SKU to raise a run against. Required: search.
- **`jivo-factory-pp-cli production-execution sap-order-detail`** - One SAP production order with its full component list (BOM lines, planned vs issued qty, warehouse and unit price). Required: id.
- **`jivo-factory-pp-cli production-execution sap-orders`** - List OPEN SAP production orders (status Released) available to raise a run against — planned vs completed quantity per order.
- **`jivo-factory-pp-cli production-execution waste`** - List wastage logs — material scrapped during a run, with the four-signature approval chain (engineer, asst. manager, stores, HOD).
- **`jivo-factory-pp-cli production-execution waste-detail`** - Full detail of one wastage log including every approval signature and timestamp. Required: id.
- **`jivo-factory-pp-cli production-execution yield-report`** - Per-run yield pack: the run, all its material lines, machine runtimes and manpower in one call. Required: id.

### quality-control

Quality Control is the QA department's own workflow inside the factory app, and it holds three separate flows plus its own master data. (1) Raw-material inspection: when a truck's material reaches QA

- **`jivo-factory-pp-cli quality-control arrival-slips`** - List QA arrival slips — the intake record raised against each PO item when material reaches QA at gate-in.
- **`jivo-factory-pp-cli quality-control inspections`** - List every raw-material QC inspection with its workflow stage and both sign-off decisions.
- **`jivo-factory-pp-cli quality-control inspections-actionable`** - Everything the QA team must act on right now — pending plus draft plus anything awaiting a decision.
- **`jivo-factory-pp-cli quality-control inspections-awaiting-chemist`** - Submitted inspections waiting on the QA Chemist's verdict (workflow stage SUBMITTED).
- **`jivo-factory-pp-cli quality-control inspections-awaiting-qam`** - Chemist-approved inspections waiting on the QA Manager's verdict (stage QA_CHEMIST_APPROVED).
- **`jivo-factory-pp-cli quality-control inspections-completed`** - Fully signed-off inspections; filter by final verdict to get accepted lots or on-hold lots.
- **`jivo-factory-pp-cli quality-control inspections-counts`** - One-line QC scoreboard: how many raw-material inspections sit in each stage right now.
- **`jivo-factory-pp-cli quality-control inspections-draft`** - Inspections a chemist started filling but has not submitted.
- **`jivo-factory-pp-cli quality-control inspections-pending`** - Arrival slips submitted to QA but with no inspection started yet — the chemist's to-do queue.
- **`jivo-factory-pp-cli quality-control inspections-rejected`** - Inspections rejected by QA — the lots that failed inspection.
- **`jivo-factory-pp-cli quality-control inspections-return-to-vendor`** - Rejected lots that are to go back to the vendor, with the gate return-entry number once one is raised.
- **`jivo-factory-pp-cli quality-control material-types`** - List QC material types — the master categories (bottle, cap, carton, label, jerry can…) that carry the inspection parameter sets.
- **`jivo-factory-pp-cli quality-control print-documents`** - List the document-ID templates printed at the bottom of QC report forms (e.g. QA-FRM-14-00-06-03 on the raw-material inspection print).
- **`jivo-factory-pp-cli quality-control production-qc`** - List production QC sessions — in-process and final quality checks recorded against production runs.
- **`jivo-factory-pp-cli quality-control production-qc-counts`** - Production QC scoreboard: how many QC sessions are draft, submitted, approved and rejected.
- **`jivo-factory-pp-cli quality-control production-qc-pending`** - Production QC sessions submitted and waiting for approval — the FG-release approval queue.
- **`jivo-factory-pp-cli quality-control qc-arrival-slip-get`** - Show one QA arrival slip in full, including its COA/COQ attachment URLs. Required: id.
- **`jivo-factory-pp-cli quality-control qc-inspection-get`** - Full raw-material inspection report: header, material type, both sign-offs, every parameter result and the attachments. Required: id.
- **`jivo-factory-pp-cli quality-control qc-inspections-decision-changed`** - Inspections where the QA Manager overturned an earlier verdict — the audit queue for changed decisions.
- **`jivo-factory-pp-cli quality-control qc-material-type-get`** - Show one QC material type and the SAP item codes mapped to it. Required: id.
- **`jivo-factory-pp-cli quality-control qc-material-type-parameters`** - The QC parameter specification for a material type — what gets checked, the standard value, limits and UOM. Required: id.
- **`jivo-factory-pp-cli quality-control qc-online-monitoring`** - List in-line quality monitoring records — shift-wise QA checks taken on a filling line during production.
- **`jivo-factory-pp-cli quality-control qc-online-monitoring-get`** - One in-line monitoring record with every reading taken — pH, TDS, turbidity, hardness, torque per filling head, rub and closure tests. Required: id.
- **`jivo-factory-pp-cli quality-control qc-online-monitoring-lines`** - The production lines available for QC — the lookup behind every `line` filter in this domain.
- **`jivo-factory-pp-cli quality-control qc-online-monitoring-runs`** - Production runs a QA operator can attach an in-line monitoring record to.
- **`jivo-factory-pp-cli quality-control qc-online-monitoring-specs`** - The in-line monitoring parameter specs — the acceptable range for pH, TDS, turbidity, alkalinity and the rest.
- **`jivo-factory-pp-cli quality-control qc-parameter-get`** - Show one QC parameter spec (limits, standard value, UOM, whether it is mandatory). Required: id.
- **`jivo-factory-pp-cli quality-control qc-production-running-runs`** - Production runs currently open on the lines, with whether each still needs a QC check.
- **`jivo-factory-pp-cli quality-control qc-production-session-get`** - Full production QC session: who checked it, who approved it, and every parameter result with pass/fail. Required: id.
- **`jivo-factory-pp-cli quality-control sap-items`** - Search the SAP item master from inside QC, to find the item code to map to a material type.

### returnable-items

This is JIVO's RGP/NRGP gate-pass book — the register of material that leaves the factory gate and is meant to come back. A department raises a pass for a pump, motor, mould shaft, cutter, cooler, or

- **`jivo-factory-pp-cli returnable-items attachments`** - Delivery challans and photos attached to gate passes, with a direct file URL for each.
- **`jivo-factory-pp-cli returnable-items dashboard`** - One-glance returnable summary — how many passes sit in each state, how many are outstanding, and how old the outstanding ones are.
- **`jivo-factory-pp-cli returnable-items gatepass`** - Show one gate pass in full — party, department, dates, approvals, vehicle/driver, every line item, every return event and every attachment. Required: id.
- **`jivo-factory-pp-cli returnable-items gatepass-item`** - Show one gate-pass line item by its own id. Required: id.
- **`jivo-factory-pp-cli returnable-items gatepass-items`** - Line-item register across all gate passes — every physical thing sent out, with quantity out, quantity returned and what is still pending.
- **`jivo-factory-pp-cli returnable-items gatepasses`** - List returnable/non-returnable gate passes — material sent out of the gate for repair, exchange or job work, and whether it has come back.
- **`jivo-factory-pp-cli returnable-items options`** - The dropdown vocabulary for this module — the exact status, purpose, out-condition and return-condition codes with their human labels.
- **`jivo-factory-pp-cli returnable-items pending-approval`** - The approver's inbox — gate passes submitted by a department and waiting for sign-off before they may go to the gate.
- **`jivo-factory-pp-cli returnable-items pending-gate-in`** - The inbound guard's list — material that is still out with an outside party and has not been logged back in.
- **`jivo-factory-pp-cli returnable-items pending-gate-out`** - The outbound guard's release queue — approved gate passes whose material has not yet physically left the gate.
- **`jivo-factory-pp-cli returnable-items report`** - Flat gate-pass register for export — one row per pass with the dates that matter, filterable by status and by the date it was raised.
- **`jivo-factory-pp-cli returnable-items return-events`** - Every time material came back through the gate — when, on which vehicle, verified by whom, and in what condition each item arrived.
- **`jivo-factory-pp-cli returnable-items sap-items`** - Look up a SAP item by name or code to put on a gate pass — returns item code, name and unit of measure. Required: search.
- **`jivo-factory-pp-cli returnable-items timeline`** - The audit trail of one gate pass — who submitted, approved, released it at the gate, logged the return, and when. Required: id.

### sap

This corner of the factory app answers one question: can we actually build what SAP says we are going to build, and what do we have to buy to close the gap. The "SAP Material Plan" screen (web route /

- **`jivo-factory-pp-cli sap plan-dashboard-details`** - Same open production orders as the summary but with every BOM component line nested — required, issued, remaining, stock on hand/committed/on-order, shortfall and per-component stock status.
- **`jivo-factory-pp-cli sap plan-dashboard-procurement`** - Shortfall rolled up by component across all open production orders, with a suggested purchase quantity and the production orders that need it — the buy list.
- **`jivo-factory-pp-cli sap plan-dashboard-sku`** - Full BOM component breakdown for ONE open production order — required vs issued vs remaining, available stock and shortfall per component. Required: prod_order_entry.
- **`jivo-factory-pp-cli sap plan-dashboard-summary`** - One row per open SAP production order: planned vs completed qty, due date, warehouse and how many of its BOM components are short — the 'which orders are at risk' view.

### vehicle-management

This is the factory's transport master file plus the gate's vehicle-entry log. Three master lists sit under it — Vehicles (registration number, type, capacity, owning transporter), Transporters (conta

- **`jivo-factory-pp-cli vehicle-management transporters`** - All transport companies on file, with contact person, mobile and GSTIN.
- **`jivo-factory-pp-cli vehicle-management transporters-names`** - Slim id + name list of transporters, for pickers.
- **`jivo-factory-pp-cli vehicle-management vehicle-entries`** - The gate log: every vehicle that entered the plant for one movement type in a date window, with vehicle, driver, status and supplier. Required: entry_type, from_date, to_date.
- **`jivo-factory-pp-cli vehicle-management vehicle-entries-count`** - How many gate entries of one movement type sit in each status over a date window — the 'how many trucks are still waiting on QC' number. Required: entry_type, from_date, to_date.
- **`jivo-factory-pp-cli vehicle-management vehicle-entries-list-by-status`** - The same gate log, but filtered to one status — the only way to actually filter entries by status. Required: status, entry_type, from_date, to_date.
- **`jivo-factory-pp-cli vehicle-management vehicle-types`** - The fixed list of vehicle categories used across the plant (Truck, Car, Bike, Cycle, Eco Van, Courier, By Hand).
- **`jivo-factory-pp-cli vehicle-management vehicles`** - Every vehicle registered with the factory — registration number, type, capacity in tonnes and which transporter owns it.
- **`jivo-factory-pp-cli vehicle-management vehicles-names`** - Slim id + registration-number list of all vehicles, for pickers and lookups.

### warehouse

The warehouse module is the factory floor's stock-handling desk — its own landing page calls it "Material requests, finished goods, branch transfers, and goods receipts". Three live workflows sit unde

- **`jivo-factory-pp-cli warehouse bom-request-get`** - One material request with every requested line, the stock available in each warehouse, and what was approved versus issued. Required: id.
- **`jivo-factory-pp-cli warehouse bom-requests`** - Material requests raised by production against a run — what the line asked for, what the warehouse approved, and whether the materials have actually been issued.
- **`jivo-factory-pp-cli warehouse bst-gate-inwards`** - Security gate's inbound list — branch transfers the gate should expect to arrive.
- **`jivo-factory-pp-cli warehouse bst-gate-outwards`** - Security gate's outbound list — branch transfers the gate should expect to leave, so it can match vehicle and driver before letting the truck out.
- **`jivo-factory-pp-cli warehouse bst-get`** - One branch stock transfer in full — its SAP source docs, line items, box scans, scan progress and any partial-transfer request. Required: id.
- **`jivo-factory-pp-cli warehouse bst-incoming`** - Branch stock transfers heading INTO this company from another branch or company — the receiving desk's worklist.
- **`jivo-factory-pp-cli warehouse bst-incoming-get`** - One inbound branch transfer in full, including short-shipment detail and the partial-transfer approval record. Required: id.
- **`jivo-factory-pp-cli warehouse bst-list`** - Branch stock transfers dispatched FROM this company — every outgoing BST with route, SAP doc, boxes scanned, vehicle, driver and status.
- **`jivo-factory-pp-cli warehouse bst-partial-transfers`** - Short-shipment approval queue — where a receiving branch scanned fewer boxes than the SAP document promised and a supervisor must approve or reject the difference.
- **`jivo-factory-pp-cli warehouse bst-sap-transfer-get`** - One SAP stock-transfer or invoice document with its lines and cartons-per-box maths, as the BST screen sees it. Required: doc_entry.
- **`jivo-factory-pp-cli warehouse bst-sap-transfers`** - SAP stock-transfer and sales-invoice documents available to build a branch transfer from — the pick-list the 'New BST' screen searches.
- **`jivo-factory-pp-cli warehouse fg-receipt-get`** - One finished-goods receipt, including the SAP posting result or the SAP error text if the post failed. Required: id.
- **`jivo-factory-pp-cli warehouse fg-receipts`** - Finished goods coming off production runs — good versus rejected quantity, which warehouse they went into, and whether the receipt reached SAP.
- **`jivo-factory-pp-cli warehouse wms-item-groups`** - The company's SAP item-group master (FINISHED, RAW MATERIAL, PACKAGING MATERIAL, …) with its numeric group codes.
- **`jivo-factory-pp-cli warehouse wms-warehouses`** - The company's SAP warehouse master — every warehouse code and name, as the app's warehouse dropdowns see it.

### wms

The warehouse module is the factory floor's stock-handling desk — its own landing page calls it "Material requests, finished goods, branch transfers, and goods receipts". Three live workflows sit unde

- **`jivo-factory-pp-cli wms wms-cell-purposes`** - What each kind of grid cell is for — fork-lift path, storage, staging and so on, with its map colour.
- **`jivo-factory-pp-cli wms wms-get`** - Fetch one WMS record by its UUID from any of the collections above. Required: collection, id.
- **`jivo-factory-pp-cli wms wms-inventory`** - What is physically sitting in the WMS today, box by box, with unit of measure and weight/volume where known.
- **`jivo-factory-pp-cli wms wms-locations`** - Every physical rack cell in the WMS grid — its code, row/column/level, type, purpose and whether it is active.
- **`jivo-factory-pp-cli wms wms-materials`** - Material definitions used by the WMS location material-rules.
- **`jivo-factory-pp-cli wms wms-movements`** - WMS movement log — every putaway, pick and transfer performed on the floor, with the item, box count and who did it.
- **`jivo-factory-pp-cli wms wms-pallets`** - Pallets tracked on the WMS floor — which item and how many boxes are on each, and where it is standing.
- **`jivo-factory-pp-cli wms wms-templates`** - Saved warehouse-grid layout templates used by the WMS designer screen.
- **`jivo-factory-pp-cli wms wms-warehouses`** - Physical WMS warehouses — the rack-grid definitions (rows x columns x levels) the floor app maps pallets onto. Different thing from the SAP warehouse master.
- **`jivo-factory-pp-cli wms wms-zones`** - Named zones a warehouse grid is divided into.


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

### API-specific

- **HTTP 401 'Token is expired'** — Run 'auth login' again; access tokens last ~25h and refresh tokens ~7d.
- **403 WRONG_COMPANY on any marketplace command** — Marketplace is enabled only for JIVO_MART. Drop --company or set it to mart.
- **503 on barcode production-release-oil** — Pass --company oil. The HANA view PRODUCTION_RELEASE_OIL exists only in the Oil schema.
- **A blowing command returns an empty list** — Blowing is enabled everywhere but only holds data in Oil. Pass --company oil.
- **400 with a message naming a parameter** — That parameter is required. The error body names it verbatim and the command declares it as a required flag.

---

Generated by [CLI Printing Press](https://github.com/mvanhorn/cli-printing-press)
