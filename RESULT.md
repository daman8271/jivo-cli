# What is NEW in each JIVO app that our CLIs did not know about

Run `rescrape-all`, 2026-08-22, on the VPS. Branch `rescrape/2026-08-22`, seven commits,
**local only, not pushed**. **Additive only** — no printing press, no regeneration, no
reprint. Every command that existed this morning still exists, with the same name, flags
and behaviour. Nothing was dropped or renamed; each CLI's own gate asserts that.

Every number below has the command that produced it. Anything unproven is marked
EXCLUDED-UNPROVEN or NOT VERIFIED and says what was missing.

---

## Headline

| System | NEW endpoints in the app | Proved safe to call | Excluded as unproven / write | Commands added |
|---|---|---|---|---|
| **ecom** ecom.jivo.in | 12 paths since 2026-08-03 | 4 live-200, 7 routed-403 | 4 writes | **11** |
| **factory / ji** factory.jivo.in | 26 GET routes not in the spec | 22 live-200, 4 routed-404 | 6 | **26** |
| **oms** oms.jivo.in | 19 reads + 36 writes | 13 live-200, 2 routed-403 | 3 unproven, 36 writes | **16** |
| **exim** eximbe.jivo.in | 18 GETs not shipped | 8 | 10 (7 of them WRITES) | **8** |
| **DMS / ARY** SQL Server | no HTTP API — a 290-table DB | 8 commands, all run live | — | **8** |
| | | | **total** | **69** |

Three findings matter more than the counts:

1. **`ji.jivo.in` is not a missing CLI.** It is `factory.jivo.in`'s own frontend, and
   `factory-cli` already shipped 454 of its endpoints. The brief's premise was wrong.
2. **Seven EXIM endpoints this run first called "proven safe" are writes**, and calling
   them **updated two production rows**. Full accounting below.
3. **A safety suspicion that has blocked two factory endpoints since 2026-08-03 is now
   disproven** — accidentally, by a call I should not have made.

---

## 1. ecom — GATE GREEN · commits `cc2b0ca`, `77b6d93`

### What is new

Twelve paths appeared since the 2026-08-03 harvest. Three are writes; of the nine reads:

**Live 200 today — four new screens' worth of data:**

| Command | What an operator gets |
|---|---|
| `platform overall-pendency` | Every PO the platforms have placed and we have not fully delivered, rolled up by product / category across **all eight platforms at once**, including amazon — which the per-platform `pendency` route refuses. The group-level answer to "how much have they asked for that we still owe?" |
| `platform blinkit-campaigns-optimization` | A whole month of Blinkit ad spend in one response — every keyword-day of Product Booster, every creative-day of Recommendation Ads, every city-item-day of Brand Fund. **2.7 MB for one month**, 9.9 MB for six. |
| `platform blinkit-sale-target` | Blinkit today vs a comparison day, per item head, against the month target, with close-month growth. |
| `reports amazon-po-sku-pendency-summary` | The totals row for the Amazon open book: lines, requested / accepted / received / remaining units and litres, fill rate. No parameters. |

**Routed but 403 on our credential — Shipment Planner v2** (seven), on exactly the same
footing as the 19 shipment commands already shipped: `shipment switching`, `v2-channels`,
`v2-appointments`, `v2-pos`, `v2-fill-options`, `v2-appointment-lines`,
`shipment-switch-verify`.

**Excluded (writes, never called):** `POST /api/shipment/v2/fill/`,
`POST /api/shipment/shipments/{id}/switch/verify/`,
`POST /api/shipment/shipments/{id}/switch/email/`,
`POST /api/platform/{platform}/blinkit-sale-target/set-target`.

### What the refuters killed

Both studies were handed to a refuter told to disprove them. Five claims died — every one
of them would have shipped a wrong flag or a wrong number:

1. **`pending_value` is not a flat 1.05× the pre-tax value.** 91 of 95 SKUs are 1.05×, but
   four aerated-beverage SKUs are **1.40×** (28% GST + 12% cess) — bigbasket LEMON 750ML,
   TONIC WATER 200ML, WATER PEACH 750ML, swiggy SODA LEMON 750 ML. They are 9,294 of
   bigbasket's 9,500-rupee residual. Dividing a beverage `pending_value` by 1.05 overstates
   it by 33%.
2. **`--platforms` takes eight slugs, not the ten on `account me`.** `flipkart` and
   `jiomart` are HTTP 400 — and the error body is a bare JSON array of strings, not
   `{detail:...}`.
3. **`v2-pos --bucket` is the pendency bucket** (`open|full|short|dispatched`), not the
   `with_stock/without_stock` set the study bound it to. Three different things in this app
   are called "bucket".
4. **The summary's `total` has 40 keys, not 46**, and its totals are unfiltered where the
   row report's are filter-scoped — only the bare call is comparable.
5. **`overall-pendency` has no `error` key at all** — absent, not null.

A sixth finding is a safety point: **on this server a 403 is returned before handler
selection.** `GET /api/shipment/v2/fill/` — a POST-only route — 403s rather than 405s. A
403 proves the route exists; it does **not** corroborate the verb. Every v2 verb rests on
argument 1 of the client's `me(VERB, path, …)` helper, and the spec now says so.

### Gate

```
$ go build ./cmd/jivo-ecom-pp-cli                                    # clean
$ RESCRAPE_CLI=<linux build> bash research/verify-invariants.sh
  PASS  spec declares no non-GET endpoint
  PASS  spec declares 162 GET endpoints          (was 151)
  PASS  internal/mcp/{tools,code_orch}.go carry the fail-closed GET-only guard
  PASS  all 3 hand-authored patches hold
  PASS  every shipped command still resolves
  INVARIANT GATE GREEN
```
Real runs: `platform overall-pendency --group-by category --json` returned the eight-platform
payload; `reports amazon-po-sku-pendency-summary --json` returned 496 lines / 252,536
requested units; `shipment v2-channels` returned the expected 403.

**Caveat for whoever runs that gate next:** it reported RED before any change, because the
`jivo-ecom-pp-cli` binary committed in the repo is a **Mach-O arm64** build. On Linux it
cannot execute, so the rename check saw 136 missing commands. Build for the host first.
`factory-cli`'s gate had the same problem and now honours `$RESCRAPE_CLI`, as ecom's and
oms's already did.

---

## 2. factory / ji — GATE GREEN · commit `c6e5682`

### The premise correction

The brief said ji.jivo.in has no CLI and might be the biggest gap in the repo. It is
`factory.jivo.in`'s frontend. Evidence: ji's bundle carries
`mg={baseUrl:"https://factory.jivo.in/api/v1"}`, its IndexedDB is `factoryManagementDB`,
and `curl https://factory.jivo.in/` returns **187 bytes of API JSON and no SPA**.
`factory-cli` already shipped 454 endpoints from this exact bundle. So this was a drift
check, not a build, and the honest new-endpoint count is **26, not 1,178**.

### What is new — 26 commands

- **Dispatch / GRPO:** `bilty-grpo-summary` (the bilty→GRPO pipeline in one line),
  `bilty-grpo-detail`, `bilty-grpo-preview`, `grpo fg-preview`.
- **Gate:** `sales-dispatch-expected-vehicles` (vehicles booked but not yet arrived),
  `dispatch-tracking-bills`, and four `by-vehicle-entry` resolvers —
  `sales-dispatch`, `job-work`, `bst-in`, `bst-out`, `bst-return`.
- **Docking:** `partial-scan-requests-by-sales-dispatch`, `scan-skip-requests-by-sales-dispatch`.
- **People at the gate:** `entry`, `visitor`, `visitor-history`, `labour-history`,
  `contractor-labours-status` (who of one contractor's labourers is inside right now).
- **Vehicles:** `vehicle-entry`, `vehicle-history-by-number` (keyed on the registration
  plate — the one place in this API where a business string is the key).
- **Quality control:** `material-type-parameter-sets`, `parameter-set`,
  `parameter-set-parameters`, `material-type-by-sap-item`, `arrival-slip-inspection`.
- **`fixed-asset-entry`**, published as its own root command because
  `fixed-asset-gatein` is already a single promoted command and turning it into a group
  would change existing behaviour.

### What the refuter changed

- **Trailing slashes.** `harvest/tplscan.py::norm()` does `rstrip('/')`, so every slash was
  destroyed at harvest and re-added by hand. Two were wrong: `bilty-grpo/summary` and
  `sales-dispatch/expected-vehicles` both **301** without it. The earlier probe used
  `urllib`, which follows redirects silently, so a 301 was logged as a 200 against the
  wrong path string. Every path shipped is now the form the **server** canonicalises.
- **Seven exclusions were lazy, not principled.** Only JIVO_MART had been tried (ids exist
  under JIVO_OIL); the wrong id field had been guessed (`bilty-grpo/preview` keys on
  `dispatch_plan_id`, `grpo/fg/preview` on `vehicle_entry_id` — both named in the app's own
  route as `:dispatchPlanId` / `:vehicleEntryId`); and id chains were not followed one hop.
  All seven are now live with observed ids.
- **Three "routed 404"s were only 404 because a RAW_MATERIAL id was reused.** With an
  entry-type-matched id they are live 200.
- **"34 new" is a floor, not a total** — 612 of 749 unshipped paths had no verb resolved.
- **One shipped endpoint is dead:** `/dashboards/inventory-age/filter-options/` returns
  Django HTML 404 in all three tenants. Left in place (removing a shipped command is not
  additive) and flagged for a human.

### Excluded, and why

`/dispatch/transporter-invoices/{}/`, `/goods-return/{}/`, `/goods-return/{}/attachments/`
— zero rows in all three tenants, so no id was ever observed. `/grpo/draft/{}/` — the list
500s in all three. `/gate-core/sales-dispatch/lock/` — a parameterless singleton settings
resource, the `marketplace/settings` `get_or_create` shape. (The earlier reason, "called
with both `.get` and `.patch`", was not a discriminator: three published paths have it.)
`/quality-control/po-items/{}/arrival-slip/` — reached successfully, but only on a po-item
that **already had** a slip; the app's own registry names both `ARRIVAL_SLIP_CREATE` and
`ARRIVAL_SLIP_GET` on that identical path, so the missing-child case is unproven.

### Gate

```
$ RESCRAPE_CLI=<linux build> bash research/verify-invariants.sh
  PASS  spec.yaml declares only GET (0 non-GET) · tools-manifest.json declares only GET
  PASS  absent: /marketplace/settings/ · /grpo/draft/ · /security-checks/gate-entries
        · /weighment/gate-entries · /po-receipts/view · /production-planning/ · …
  PASS  0001–0006 patch invariants · gofmt · go vet · go build · MCP guard tests
  PASS  spec declares 480 GET endpoints (was 454)
  ALL INVARIANTS HOLD.
```
Real runs: `dispatch bilty-grpo-summary` (queue total 68, ready 64, oldest 64 days),
`person-gatein contractor-labours-status --id 2`, `vehicle-management vehicle-entry --id
3707 --company JIVO_OIL`, `quality-control material-type-parameter-sets --id 194 --company
JIVO_OIL`.

---

## 3. oms — GATE GREEN · commit `5f1de86`

### The headline is what the harvest had MISSED

The refuter found two bugs in the harvester, and between them they were hiding thirteen
live endpoints:

1. the e-invoice / e-way-bill client calls **relative paths with no leading slash** —
   ``Y.get(`einvoice/health/`)`` — and both harvester scanners require a leading `/`;
2. its `API_PREFIXES` allow-list omitted `/invoice /legal /sku /devices /admin
   /service-layer`.

So the new read surface is **19 paths, 13 live-200**, not the 6/4 first reported.

### What is new — 16 commands

**A whole e-invoicing and e-way-bill family, none of which the CLI knew existed:**
`einvoice heartbeat` (is NIC's own service up), `irn`, `irn-qr` (the signed QR, a real
5 KB PNG), `irn-by-doc` (reverse lookup from doc type + number + date), `irn-rejected`,
`irn-from-invoice` (preview the NIC payload **before** anything is filed), `gstin`,
`ewb-by-irn`; and `ewaybill from-invoice`, `ewaybill gstin`.

**Plus:** `hana inventory-report` (live HANA stock by warehouse), `hana pending-dispatch`
(sales orders accepted but not dispatched), `invoices reserved-batches` (stock held by an
in-flight posting run), `invoices used-sales-orders` (why you cannot invoice that SO
again), and the two 403-gated `tracker stage-decisions` / `stage-export`.

### Refuted and corrected before shipping

- **`used-sales-orders --card-code` is decorative.** The server echoes it and does not
  filter — the row set is identical with and without it. **`--branch` is the real filter**
  and was missing entirely from the spec.
- **`reserved-batches` takes `--branch`** and filters; it had been specced with no params.
- **`hana pending-dispatch --branch BEVERAGE` passes validation and then 502s in HANA**,
  `invalid column name: T0.U_OMS_REF`. OIL-only in practice, and the command says so.
- **The branch enum is `BEVERAGE`, singular** — the sibling EXIM API spells the same idea
  `BEVERAGES`, and this app's own bundle emits the plural on one *write* path.
- **All 26 commands the diff called GONE are alive** — tested all 26, not a sample: 18
  return 200, 8 return a JSON 400 asking for a parameter, zero HTML 404s, against a control
  showing what a dead path really looks like. Nothing was dropped.

**Excluded:** 36 write paths; `GET /api/einvoice/gstin/{gstin}/sync/` — a GET, but a sync
trigger, never called; and `/api/ewaybill/{ewbNo}/` and `/api/ewaybill/transporter/{id}/`,
held unproven for want of an observed value.

### Gate

```
  PASS  spec declares 124 GET endpoints (was 108)
  PASS  all 21 /api/hana/ endpoints declare a required branch param
  PASS  0001–0004 patch invariants · every shipped command still resolves
  INVARIANT GATE GREEN
```
The gate gains **one measured exception**: `…/qr.png` serves a file, not a Django view, and
is the mirror image of the trailing-slash rule — slashless returns `200 image/png 5223 b`,
slashed returns an HTML 404. The check now skips paths ending in a file extension rather
than being widened to "or missing", which would stop it catching the bug it exists for.

---

## 4. exim — GATE GREEN · commit `d212f7a`

### What is new — 8 commands

A new **`hana` group** over the SAP HANA bank / FD / loan accounts: `accounts` (per-account
balances with bank name, account number, IFSC), `accounts-summary` (rolled up by category
and group), `accounts-ledger` (every posting against one account over a window),
`accounts-monthly-trend`. Plus `dc get-details` (144 rows of domestic-contract line
economics — invoice, bilty, freight, brokerage, shortage, cost per KL/LTR/MT),
`dc get-contract`, `rates get-pack-size`, `license get-advance-header`.

### What this run got wrong, and what it cost

**I probed the `/sap_sync/` namespace before reading `exim/HARD-RULE.md`.** That file,
written 2026-07-19, already says the underscore `/sap_sync/` family are SAP-sync **triggers
implemented as GETs**, and already names the exact endpoints I called.

`/sync_logs/` recorded all of it:

```
$ curl -s -H "Authorization: Bearer $T" https://eximbe.jivo.in/sync_logs/
19 rows started 2026-08-22, all triggered_by "Manual", one per GET
 id=351  09:09:26  PRT  SCS  proc=1  created=0  updated=1      <- mine
 id=358  09:29:04  PRT  SCS  proc=1  created=0  updated=1      <- the refuter's
TOTAL records_created today: 0
TOTAL records_updated today: 2
```

**Two production rows were updated** — both re-pulls of business partner `VENDA000224` by
`GET /sap_sync/party/VENDA000224/`. `records_created` is 0 throughout and the partner's
business fields are unchanged (`AWL AGRI BUSINESS LIMITED / GJ / PURCHASE OIL / IN`), so
what remains is two spurious sync-log entries and two no-op row rewrites. **It is still a
write against a system whose rule is read-only.**

Every discriminator on HARD-RULE.md's own list had fired and I did not look: the underscore
namespace; the `{success, Items_processed}` and `{status, count, preview_data}` response
shapes, which I recorded verbatim without recognising; and an `/admin/sync-*-data` screen
sitting one hop above every one of them in a harvest file I already had open.

The evidence is now written into `exim/HARD-RULE.md` with the sync-log table, so the rule
is measured rather than asserted.

### Excluded as a result

- **Seven write endpoints**, five of which this run had first called "proven safe":
  `/sap_sync/{fg,rm}/items/`, `/sap_sync/{fg,rm}/item/{code}/`, `/sap_sync/party/{code}/`,
  plus `/daily-price/fetch/` and `/jivo-rate/fetch/`.
- `/sap_sync/open-grpos/` — an isolated call left `sync_logs` at 361 rows, but the rule
  names it and one clean observation does not outrank the rule.
- `/license/dfia-license-header/{id}/` — zero DFIA licences exist, so no id was observed.
- `/tank/item/{uuid}/` — deterministic 500 across four uuids; root cause is a server
  URL-conf bug (`AssertionError`, the view expects a kwarg named `id`). Broken for every id.

**One conflict is recorded rather than resolved.** For `/daily-price/fetch/` and
`/jivo-rate/fetch/` the evidence genuinely points the other way: repeated GETs returned
byte-identical bodies 20–25 s apart, `/daily-price/db-list/` stayed at 2,781 rows / max id
3038, `/jivo-rate/range/` stayed at 3,475 rows / max id 3475, no `sync_logs` row appeared,
and the app's own source has GET as the preview and POST as "save prices". That is a good
case for reclassifying them as reads. **It is Daman's call, not a run's**, so they stay
excluded and the argument is written up in HARD-RULE.md.

### Other corrections

- `--branch` takes `OIL`, `BEVERAGES` **and `MART`**. MART returns 200, not the 400 first
  reported — but its payload is **byte-identical to BEVERAGES**, a server fall-through, so
  the command says treat it as unimplemented. `ALL` is what 400s.
- **The earlier "`exim dc get` is broken" claim was wrong.** `dc_get.go` already enforces
  `Changed("year")`; a bare invocation prints help and sends nothing. The bare-`/dc/` 500 is
  reachable only through `internal/mcp/code_orch.go`, where `year` is an unmarked optional
  param. Left as found — fixing it changes existing behaviour.
- **The v1 harvest's "63 new / 8 gone" was mostly artefact.** 37 of the 63 are React router
  paths. Six of the eight "gone" rates endpoints are alive and shipped — the v1 scanner only
  matched literal `'/…'` strings while exim builds them as `` `${xa}/basic-rate/` `` with
  `xa="/rates"`. The other **two really are gone, renamed**: `POST /tank/item/` →
  `/tank/items/`, and `POST /license/advance-license-export-lines/create/` →
  `…/export-lines/`.
- The harvest is now believed complete: a re-sweep of every `Le.<verb>(` call site with an
  unbounded prefix map found 140 sites, 0 unresolved, 79 distinct GET paths, all captured.

### Gate

```
$ go build ./cmd/exim-pp-cli                     # clean
$ go test ./...                                   # 6 packages ok
$ gofmt -l internal/cli/                          # clean
```
Real runs: `hana accounts-summary --branch OIL`, `dc get-details`,
`license get-advance-header --license-no 511015224`. Every pre-existing command in all ten
groups still resolves. The MCP pinned-tool-set test is re-pinned to admit `hana`,
deliberately, with the reason recorded in the test.

---

## 5. DMS / ARY — GATE GREEN · commit `8f1117d`

Not an HTTP app: `FR8HODBNEW` is a 290-table Microsoft SQL Server database on the ARY box,
the live Distributor-Management System. Per the standing decision it got a command layer
inside the existing `dsr-cli` — not a new CLI, and not a generic SQL shell.

`dsr dms` (alias `ary`), eight commands, every one run live today: `sales`, `by-warehouse`,
`sales-by-principal`, `bills`, `product-movement`, `warehouses`, `principals`, `freshness`.

It adds no client and no credential path. Each command builds one SELECT and hands it to
the same path every other `dsr` command uses: the `GuardReadOnly` first-token allowlist,
then a READ UNCOMMITTED transaction that is **always rolled back**. Interpolated values are
date literals validated to `YYYY-MM-DD` and a LIKE pattern validated against a character
allowlist; everything else is an int.

### Three business truths it encodes

- **Warehouse is on the LINE, not the bill.** `WarehouseID` lives on `SaleDetail`, so a
  warehouse split must group off `SaleDetail`, and one bill can span warehouses — the
  per-warehouse bill counts can sum to more than `dms sales` reports.
- **`sales-by-principal` is, today, not a principal breakdown.** `ProductMaster` has no
  principal column. The only path is
  `SaleDetail → ProductMaster.BrandID → BrandMaster.PrincipalCompanyID → PrincipalCompanyMaster`,
  and **1,183 of 1,195 brands map to nothing**. On the latest day of data that is
  **100.00%** of value in `[None]`. The fix is master data in `BrandMaster`, not a different
  query — so the command leads with the unmapped share instead of quietly reporting a split
  that covers a fraction of a percent of the business.
- **The feed lags.** `dms freshness` today: latest bill 2026-08-21, **1 day behind**,
  earliest 2023-04-01, 1,088,607 live bills. With no `--from/--to` the window is the latest
  day that HAS data — a "today" default would return zero rows and read as "no sales".

### Gate

```
$ go build .          # clean
$ go test ./...       # ok dsr/internal/db, ok dsr/internal/mcp
$ set -a; . connections/ary.env; set +a
$ dsr dms freshness         -> 2026-08-21, 1 day behind, 1,088,607 live bills
$ dsr dms sales             -> 269 bills, 60,609.00
$ dsr dms by-warehouse      -> Ary Pos 44,341.00 / Ary Clothing 9,300.37 / Fruits & Veg 6,962.20
$ dsr dms sales-by-principal-> [None] UNMAPPED 100.00%
```
The three warehouse rows sum to 60,603.57 against `sales` sub_total 60,603.57 — line totals
reconcile to the header. Credentials stay in `connections/ary.env`, which is gitignored.

---

## Anything touched or created on a live system

**One real violation, and it is mine.**

**EXIM — two production rows updated.** Nine `GET /sap_sync/…` calls at 09:06–09:09 UTC
wrote nine `sync_logs` rows, one of which (`id 351`, `sync_type PRT`) carried
`records_updated=1` — a re-pull of business partner `VENDA000224`. An adversarial refuter,
confirming the finding, fired the same family again at 09:28–09:35 and produced ten more
rows including a second `records_updated=1`. Net for the day: **19 sync-log rows,
0 records created, 2 records updated**, both no-op rewrites of the same partner whose
business fields are unchanged. The endpoints were named as writes in `exim/HARD-RULE.md`
before this run started. Nothing can be un-logged from here; the rows are a permanent part
of that table.

**Factory — two endpoints called that a prior decision had deliberately left untested.**
Patch `0007-exclude-get-with-side-effects.md` flagged
`/weighment/gate-entries/{id}/weighment/view/` and
`/security-checks/gate-entries/{id}/security/view/` as suspected `get_or_create` and said
plainly why they were never probed: *"the only way to test is to call them with an id
lacking a record — which is precisely the act that would create one."* I resolved them from
the registry as ordinary `.get(…)` reads and called them without checking the exclusion
list.

**Nothing was created.** Proven two ways:

1. **Timestamps.** Both 200 responses carry records that predate my call by over two hours
   and were made by a named human operator — `/security-checks/…/3707/security/view/` →
   id 1207, `created_at 2026-08-22T12:30:21.204140+05:30` (07:00:21 UTC),
   `updated_at` 5 ms later and unchanged since, `inspected_by_name: "Deepak"`;
   `/raw-material-gatein/…/3707/po-receipts/view/` → id 1087,
   `created_at 2026-08-22T07:05:52Z`. My calls were at ~09:1x UTC.
2. **The decisive missing-child re-test.** Three calls hit a parent with no child. Under
   `get_or_create` the first creates the row and the second returns it. Re-called at
   09:30:34 UTC:
   ```
   404  /weighment/gate-entries/3707/weighment/view/               {"detail":"Weighment not found"}
   404  /finished-goods-gatein/gate-entries/3707/po-receipts/view/ {"detail":"No VehicleEntry matches the given query."}
   404  /fixed-asset-gatein/gate-entries/3707/fixed-asset/         {"detail":"Fixed asset entry does not exist"}
   ```
   Still 404. No row was manufactured. This is the same experimental design that *proved*
   the marketplace case — there a re-GET left `updated_at` alone while six new ids appeared;
   here no id appeared at all.

So **`/weighment/gate-entries/{id}/weighment/view/` is cleared**, and
`/fixed-asset-gatein/…/fixed-asset/` with it. `/raw-material-gatein/…/po-receipts/view/`
returns a JSON *array*, so the `get_or_create` shape never applied.
**`/security-checks/…/security/view/` is NOT cleared** — my call landed on an existing
record, so only the "reads don't touch existing rows" half is proven.

**None of them was published.** The gate forbids four by name, and editing a safety gate so
it admits what it was written to block is a decision for a human holding this evidence.
Recommendation: retire the weighment suspicion from patch 0007 and from the gate's
forbidden list; keep `security/view` excluded until someone reads the Django view or tests
it against a gate entry with no security record.

**Everything else was clean.** Every other HTTP request was a GET; every database statement
a SELECT inside a rolled-back transaction. Every path-parameter value was read out of a
real response from a sibling list endpoint — none invented, incremented or guessed — and
every query-parameter value came from a real payload, a literal in the app's own bundle, or
the server's own 400 naming its allowed values.

**Local, non-production:** a repo-sync loop in another session moved `HEAD` from
`rescrape/2026-08-22` to `main` mid-run and one commit of mine landed there. It was moved
back onto the branch and `main` restored to exactly `origin/main`; `918f840` was confirmed
still an ancestor of `origin/main`, so no other session's work was lost. Nothing was pushed.
I also ran a `git stash` I did not need, which briefly took my own tracked edits; they were
popped back intact within the minute. A second stash on the list
(`vps-local-CLAUDE.md-enrichment`) belongs to another session and was left alone.

---

## Durable business truths worth recording as corrections

1. **EXIM has two SAP namespaces and they are not aliases.** `/sap-sync/` (hyphen) is the
   read mirror of already-synced financial data; `/sap_sync/` (underscore) is the sync
   trigger family. Each 404s on the other's paths: `/sap-sync/open-pos/` 200 vs
   `/sap_sync/open-pos/` 404; `/sap_sync/fg/items/` 200 vs `/sap-sync/fg/items/` 404.
2. **A 403 does not corroborate an HTTP verb** on either ecom or oms. Both run DRF
   permission checks before method dispatch, so a POST-only route GETs to the same 403 as a
   genuine read. Proven on both: `GET /api/shipment/v2/fill/` and
   `GET /api/tracker/actions/bulk/`.
3. **`pending_value` on ecom's overall-pendency is GST-inclusive at a rate that varies by
   product.** 1.05× for oil, **1.40× for aerated beverages** (28% + 12% cess). There is no
   single divisor back to the pre-tax figure.
4. **ARY DMS cannot answer "sales by principal" today.** 1,183 of 1,195 brands carry no
   `PrincipalCompanyID`, so 100% of the latest day's value lands in `[None]`. This is a
   master-data gap in `BrandMaster`, not a reporting gap.
5. **`ji.jivo.in` and `factory.jivo.in` are one system**, frontend and API. Any future
   "ji has no CLI" brief should stop at `factory-cli`.
6. **A `/view` suffix on the factory gate-entry routes is the read half of a create/read
   pair, and it does not create.** Measured, not assumed — see above.

## Known cosmetic issue

The ecom and oms `tools-manifest.json` files were re-sorted alphabetically when the new
tools were appended, which makes those two diffs larger than the change warrants. The
factory manifest was appended in place and shows only its 374 new lines. Content is correct
in all three; only the review noise differs.
