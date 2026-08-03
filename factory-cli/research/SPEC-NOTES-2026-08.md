# spec.yaml v0.4.0 — decisions established before writing it

Everything here is live-verified 2026-08-03 unless marked otherwise. These are
the things a naive regeneration from an endpoint list would get wrong.

## 1. Endpoint set

| | |
|---|---|
| July baseline live (get200.txt) | 152 |
| Live now (JIVO_MART, GET 200) | **238** |
| Net new | +86, plus ~30 more that are real but need query params |
| Write-only (405) — excluded | 48 |
| Dead (404) | 20 |

Restructured, not lost: `warehouse/wms/*` — eight July endpoints now hard-404
(`dashboard`, `stock/overview`, `warehouses/summary`, `batches/expiry`,
`billing/overview`, `sales-orders/backlog`, `stock/movements`,
`transfers/overview`). Replaced by `warehouse/bst/` (branch stock transfer),
`warehouse/bom-requests/`, `warehouse/fg-receipts/`. Only `wms/item-groups/`
and `wms/warehouses/` survive. **Drop the eight dead commands** — leaving them
ships eight commands that always 404.

## 2. Parameters — a COVERAGE gap, not a quality gap

The existing pattern is good and must be copied, not redesigned. 19 of the 183
endpoints declare params today, and all 19 do it correctly — in both `spec.yaml`
and `tools-manifest.json`:

```yaml
        params:
        - name: search
          type: string
          required: true
          description: Barcode / search term (required; 400 without it)
```

with the tool description ending `"... Required: search."` so an agent reading
only the description still learns the requirement. Keep exactly this shape.

The gap is **coverage**: of 15 sampled param-requiring endpoints, 7 are already
declared properly and 8 are absent from the spec altogether because they are new
since July (`/blowing/audit/`, `/blowing/reports/daily/`, `/oms/invoices/`,
`/po/open-pos/`, `/person-gatein/check-status/`, `/barcode/items/oitm/detail/`,
`/marketplace/settings/` — the last of which must stay unpublished, see §6).

The live 400 bodies name the required param verbatim — use them as the source of
truth. Endpoints known to require params (from the probe):

```
entity_type+entity_id  /blowing/audit/
date                   /blowing/reports/daily/ · /production-execution/reports/daily-production/
date_from+date_to      /blowing/reports/make-vs-buy/ · /blowing/reports/variances/ · /dispatch-plans/bills/
year+month             /blowing/reports/monthly/
channel                7x /marketplace/* (settings, gate/queue, delivery-notes/*, dispatches/*)
channel+order_id       /marketplace/orders/resolve/
as_of_date             /dashboards/stock/as-of/
age                    /non-moving-rm/report/
whs                    /oms/invoices/ · /oms/invoices/pending-count/
vehicle_id             /gate-core/arrivals/expected/
supplier_code          /po/open-pos/
line_id                /production-execution/line-configs/auto-fill/
sap_doc_entry          /production-execution/reports/analytics/procurement-vs-planned/
item_code              /production-execution/sap/bom/ · /barcode/items/oitm/detail/
entry_type             /vehicle-management/vehicle-entries/ · .../count/
status                 /vehicle-management/vehicle-entries/list-by-status/
q                      /person-gatein/entries/search/
visitor|labour         /person-gatein/check-status/ (either-or, not both)
search value           /barcode/intercompany/trace/
```

Required params must be declared as required in the spec AND named in the
agent-facing description, so the MCP surface can fail before the network call.

## 1b. Two systematic errors the adversarial pass caught — guard against both

**(a) "companies" means ROUTED, not POPULATED.** Study agents repeatedly filled
the per-endpoint `companies` field from where rows happened to exist today, e.g.
marking all 14 blowing endpoints `[JIVO_OIL]` because Mart returns `200 []`.
The company matrix shows those paths at 200/200/200. A generator keying on that
field would emit company-restricted commands that silently return nothing in the
other two companies — and would break the moment Mart gets its first row.

Rule: an endpoint is available in every company unless the probe proves
otherwise. Only two things are genuinely company-scoped (§5): marketplace
(403 module gating) and production-release-oil (503 missing HANA view).
Where data exists is a *note for the operator*, never a restriction on the
command.

**(b) Harvested methods are what the CLIENT calls, not what the SERVER allows.**
`/returnable-items/returnable-attachments/{id}/` was excluded as DELETE-only
because the React app only ever calls delete on it — but a live GET with a real
attachment id returns the object. DRF ViewSets routinely accept GET on paths the
UI never reads.

Consequence: the GET-capable count derived from the bundle is a **floor, not a
ceiling**. Under-publishing is the safe direction under READ_ONLY_LAW, so the
default stays "exclude", but a recovered read should be published whenever a
live GET with a REAL (observed) id proves it. Never fabricate an id to test this
— see §6b.

## 3a. Response TYPE is misdeclared on 68% of the shipped spec — fix it

Of the 154 endpoints present in BOTH the July `spec.yaml` and the 2026-08-03
live probe:

| 104 | declared `type: object`, actually return a **bare JSON array** |
| 50 | declared `type: object`, actually object — correct |
| 0 | declared `array` anywhere in the file |

The spec declares `object` universally, so two thirds of it is wrong. This is
not cosmetic: the declared response type drives how the generated CLI and MCP
parse and render the payload. Every endpoint in v0.4.0 must carry the type the
live probe actually observed — `probe-mart.jsonl` records the shape per path,
so this is mechanical, not a judgement call.

(Found by the gatein-family agent on one endpoint; measured across the whole
spec afterwards.)

## 3. Pagination — do NOT assume DRF

Counted over the 238 live JIVO_MART endpoints:

| 168 | bare JSON array, no envelope |
| 54 | bare JSON object |
| 12 | DRF: results+count+page+page_size+total_pages+next/previous |
| 3 | DRF: results+count+next/previous |

Only **15** endpoints paginate. Emitting `--page`/`--page-size` on the other 223
produces flags that do nothing. Declare the envelope per endpoint.

## 3b. Emit paths VERBATIM — do not normalise the trailing slash

Django `APPEND_SLASH` is on: `GET /accounts/users` → **301** to
`/accounts/users/`. A missing slash therefore costs a redirect, not a failure,
so this is not a correctness risk for the 400-odd paths that have one.

The risk runs the other way. Exactly **7 GET-capable paths legitimately have no
trailing slash**, and a generator that appends one uniformly would break four of
them:

```
/marketplace/batches/{id}/issuance.csv          <- file extension, no slash
/marketplace/delivery-notes/{id}/export.csv     <- file extension, no slash
/marketplace/reports/{id}/export.csv            <- file extension, no slash
/marketplace/reports/{slug}/export.csv          <- file extension, no slash
/raw-material-gatein/gate-entries/{id}/po-receipts/view
/security-checks/gate-entries/{id}/security/view      <- suspected get_or_create, excluded
/weighment/gate-entries/{id}/weighment/view           <- suspected get_or_create, excluded
```

Rule: take the path exactly as the app's own ENDPOINTS registry declares it.
Never add or strip a trailing slash in the spec or the generator.

## 4. Four incompatible error envelopes

```
{"error":  "..."}                                   plain
{"detail": "..."}                                   DRF standard
{"code":"MARKETPLACE_ERROR", "error":"..."}          marketplace
{"whs": ["This field is required."]}                 DRF field-level
```
There is no single error contract; the client must handle all four.

## 5. Scoping — two orthogonal axes

- **Company** (`Company-Code` header): 220 of 238 endpoints behave identically
  across all three. Two exceptions only:
  - `marketplace/*` (32) → 403 `WRONG_COMPANY` on OIL/BEVERAGES: *"The
    marketplace module is not enabled for this company unit."* Module gating,
    not permissions, not missing data. Effectively JIVO_MART-only today.
  - `/barcode/production-release-oil/` → 503 on MART/BEVERAGES; the HANA view
    `PRODUCTION_RELEASE_OIL` exists only in `JIVO_OIL_HANADB`. **OIL-only.**
    (Patch 0005 revised — pagination was never the cause.)
- **Channel** (`?channel=` query param, marketplace only): needs a first-class
  `--channel` flag mirroring `--company`. Observed values: `FLIPKART`, `AMAZON`.
  Do NOT enumerate to discover more — see §6.

## 6. ⛔ Endpoints that must never be published

`/marketplace/settings/` — `GET` is a Django `get_or_create`. Reading it with a
channel that has no row **creates the row**. Six production rows were created
this way on 2026-08-03 (ids 2–7, including a junk `INVALID_XYZ`). See patch 0007
and correction C-0007. A GET-only filter does not make a surface read-only;
safety is a property of the endpoint, not the verb.

Any endpoint taking a lookup key and returning a single object with
`id`/`created_at`/`updated_at` is suspected `get_or_create` until cleared.

**Do not let exclusion depend on a magic string.** The domain study placed
`/marketplace/settings/` inside its `endpoints[]` array carrying
`command_name: "DO-NOT-PUBLISH"` and `side_effect_risk:
"confirmed-mutates-on-get"` — safe only if every downstream tool remembers to
read those fields. Excluded endpoints belong in `excluded_writes[]`, out of the
list a generator iterates. The assembler additionally hard-denies this path in
code; both layers stay.

**Enforce the channel enum domain-wide, not just where channel is required.**
`channel` is the key that triggered the get_or_create. `--channel` must be
restricted to the observed enum (`FLIPKART`, `AMAZON` — the only two values in
the UI's channel selector and its stored default) on EVERY marketplace command,
including `/marketplace/warehouse-insights/` and `/marketplace/reconciliation/`,
which also accept it. Those two are aggregates with no id and cannot plausibly
create a row, but a free-typed channel anywhere in this domain is the same class
of mistake.

**Discriminator for the suspect list — surrogate key vs natural key.** The
"any key-lookup returning a single object" rule is deliberately over-broad and
flagged 19 endpoints. Resolve them on this principle rather than by taste:

> A `get_or_create` can only fire if the key carries enough information to
> CONSTRUCT the row.

- **Surrogate key (autoincrement pk) → safe.** `id=999` carries nothing; Django
  cannot build a batch row without filename/channel/row_count/uploaded_by. Every
  `{id}` detail route in the suspect list resolves this way — publish them, with
  the id sourced from a listing (below).
- **Natural key → suspect.** `?channel=FLIPKART` IS sufficient to construct a
  settings row, which is exactly how the incident happened. Treat any lookup on
  a name/code/channel/slug as unproven until read server-side.

Applying it to the 19 flagged: the `{id}` routes across person-gatein, grpo,
marketplace-orders, production-planning and gatein-family are surrogate-key
lookups and clear. The one that does NOT clear is
**`/marketplace/orders/resolve/`** — it takes `channel` + `order_id`, both
natural keys, and "resolve" is a verb that plausibly writes a resolution.
Exclude it until someone reads the Django view.

**Require ids to come from a listing.** `/marketplace/batches/{id}/` is a plain
DRF retrieve on an autoincrement pk (judged safe: a pk-only get_or_create could
not construct the filename/channel/row_count the model needs, and observed ids
stayed contiguous 29–51 all session). It remains unproven against an unknown id,
so the command should require an id taken from `batches` output rather than
accepting an arbitrary integer.

## 6b. ⛔ CONSTRAINT ON THE GENERATOR'S OWN DOGFOOD STEP

`/printing-press` requires behavioural testing: its shipcheck runs every
subcommand, with `--json` and error paths, against the real target. The current
CLI's generated examples look like `--entry-type example-value`. Combining those
two facts on THIS API would reproduce the 2026-08-03 incident at ~400x scale:
a fabricated parameter value sent to an undiscovered `get_or_create` endpoint
creates production rows, and only 3 such endpoints are known so far.

Binding rules for the dogfood/live-smoke step:

1. **Never send a fabricated parameter value.** Not `example-value`, not
   `test`, not `1`. Every value must be one observed in a real payload, in the
   frontend bundle, or supplied by the operator.
2. **Prefer `--dry-run`** for the mechanical every-subcommand matrix; it proves
   flag wiring and URL construction without issuing a request.
3. **Restrict live calls to the 238 endpoints already proven safe** by the
   2026-08-03 probe — they were called bare (no params) and provably created
   nothing (checked: zero 200-payloads carried a timestamp inside the probe
   window).
4. **Never live-test an endpoint that requires a param** unless a real value for
   it is in hand. A 400 from a bare call is a SAFE result and is sufficient
   evidence that the command reaches the right URL.

This constraint is not negotiable for a "thorough" run. Thoroughness here means
more dry-run coverage, not more live writes.

## 7. Known-broken upstream — decide before publishing

- `/grpo/draft/` → HTTP 500 (Django error page) on all three companies.
  Either exclude it or publish it with an explicit "known broken upstream" note.
  Do not ship a command that only ever 500s without saying so.

- `/marketplace/reconciliation/` → HTTP 500 when given `from_date` or `to_date`.
  Works without them. New-and-broken rather than regressed (the module did not
  exist in July). Publish without the date params, or document the trap.

- **`/production-planning/*` — a UI module with no backend.** Every
  non-parameterised path 404s on all three companies, *including the module
  root*, returning Django's bare "Not Found" page — an unrouted URL, not a
  permissions or empty-data condition:

  ```
  /production-planning/            /production-planning/summary/
  /production-planning/daily-entries/
  /production-planning/dropdown/{items,uom,warehouses,bom}/
  ```

  The app's July route map advertises it as a live section ("Production ·
  UI /production · API /production-execution, /production-planning"), and the
  paths are present in the current bundle with real call sites — so the frontend
  ships screens whose API is not deployed. No alternate prefix serves it
  (`/sap/plan-dashboard/*` is a different feature). Correctly excluded here, but
  **worth reporting to whoever owns the factory app** — those screens are broken
  for users today, and the CLI cannot cover the gap.

  Unprobed caveat: the `{id}` sub-routes could not be tested without a real id.
  Given the root is unrouted, the module is almost certainly not deployed at all.

## 8. MCP surface shape

The deployed MCP is **not** 183 individual tools — it is 17: a
code-orchestration surface (`jivo-factory_execute` + `jivo-factory_search`,
plus `sql`, `search`, `sync`, `analytics`, `context`, `tail`, `workflow*`,
`product*`). New endpoints extend the executor's catalog rather than adding
tools. Keep this shape; do not regress to per-endpoint tools at this size.

Patch 0003's GET-only guards must be re-asserted in **both** execution paths
(`tools.go` and `code_orch.go`) — guarding only the direct path leaves the
code-orchestration executor as a write bypass.

## 9. Patches that must survive (7)

0001 native login · 0002 multi-company scope (flag + header + cache partition) ·
0003 MCP GET-only guards, both paths · 0004 no generic `import` command ·
0005 Oil release: company scope (revised) · 0006 product-identity consumer ·
0007 exclude GETs with side effects (new)
