---
title: Jivo Factory API Facts
created: 2026-07-19
updated: 2026-08-03
project: jivogpt
type: reference
tags: [jivogpt, factory, api, research]
---

# jivo-factory — API facts (for printing-press)

> **Re-verified live 2026-08-03.** Everything marked ✅ was confirmed against
> `https://factory.jivo.in/api/v1` on that date by direct GET probe of 338
> candidate paths across all three company codes. The previous revision carried
> a 2026-06-30 snapshot imported from the JIVO_MART-only `jivo-factory-intel`
> baseline; where the two disagree, this file wins.

- **Name:** jivo-factory (Jivo "JI" factory management system; frontend https://ji.jivo.in)
- **Base URL:** `https://factory.jivo.in/api/v1` ✅
- **Backend:** Django REST Framework + SimpleJWT ✅
- **Health check:** `GET /accounts/me/` (200 when authed) ✅

## Auth (bearer JWT) ✅

- Login: `POST /accounts/login/` body `{"email","password"}` →
  `{"access","refresh","token":{access_expires_in:90000, refresh_expires_in:604800},"user":{...}}`
- Refresh: `POST /accounts/token/refresh/` body `{"refresh"}` → `{"access"}` (rotates)
- Header: `Authorization: Bearer <access>`
- access ≈ 25 h, refresh ≈ 7 d. Tokens stored 0600 at `~/.config/jivo-factory/`.
- Env for login: `JIVO_FACTORY_EMAIL` / `JIVO_FACTORY_PASSWORD` (or
  `--password-stdin`). **Never store the password.**

## Company scope ✅

- Header: `Company-Code: <CODE>` — omitting it yields
  `403 {"detail":"Company-Code header is missing."}`
- Companies: `JIVO_MART` (id 2), `JIVO_OIL` (id 1), `JIVO_BEVERAGES` (id 3).
  CLI default = `JIVO_MART`.
- **220 of 238 live endpoints behave identically across all three companies.**
  There are exactly two exceptions, and both matter:

| Exception | Behaviour | Cause |
|---|---|---|
| `marketplace/*` (32 endpoints) | 200 on MART, **403 on OIL and BEVERAGES** | Module gating. Body: `{"code":"WRONG_COMPANY","error":"The marketplace module is not enabled for this company unit."}` — not an account-permission fault and not missing data. The module is switched off for those units and could be switched on later. |
| `/barcode/production-release-oil/` | 200 on OIL, **503 on MART and BEVERAGES** | Upstream schema: the HANA view `PRODUCTION_RELEASE_OIL` exists only in `JIVO_OIL_HANADB`. See patch 0005 — the July diagnosis blamed missing pagination and was wrong. |

## Channel scope (marketplace only) ✅

`marketplace/*` endpoints are additionally scoped by a `channel` query param;
omitting it yields `400 {"code":"MARKETPLACE_ERROR","error":"channel is required."}`.
Channel values observed in live payloads: `FLIPKART`, `AMAZON`.
**Do not enumerate channel values against the API** — see the hazard below.

## ⛔ GET IS NOT PROVEN SAFE ON THIS API ✅

`GET /marketplace/settings/?channel=<X>` is a Django `get_or_create`: reading it
with a channel that has no row **creates the row**. On 2026-08-03 six production
rows (ids 2–7) were created this way, including a junk `INVALID_XYZ`, while the
pre-existing `FLIPKART` row kept its old `updated_at` — proving reads do not
touch existing rows and the six were genuinely new.

Consequences, all binding:

1. A GET-only filter does **not** produce a read-only surface. Safety is a
   property of the endpoint, not of the verb.
2. `/marketplace/settings/` must never be published as a CLI command or MCP tool.
3. Any endpoint taking a lookup key and returning a single object with
   `id`/`created_at`/`updated_at` is **suspected `get_or_create`** until cleared.
4. Never send an invented parameter value to this API. Only replay values
   observed in a real payload or in the frontend bundle.

Recorded as correction **C-0007**; enforced by patch **0007**.

## Response shapes ✅ (counted over the 238 live JIVO_MART endpoints)

| Count | Shape |
|---|---|
| 168 | bare JSON array, **no pagination envelope** |
| 54 | bare JSON object |
| 12 | DRF envelope: `results` + `count` + `page` + `page_size` + `total_pages` + `next`/`previous` |
| 3 | DRF envelope: `results` + `count` + `next`/`previous` |

**Do not assume DRF pagination.** About 70 % of this API returns an unwrapped
array, so generated `--page`/`--page-size` flags are meaningless on most
endpoints. Declare the envelope per endpoint.

## Error envelopes ✅ — four incompatible styles in use

```
{"error":  "Search value is required."}
{"detail": "Query params 'entity_type' and 'entity_id' are required."}
{"code":"MARKETPLACE_ERROR", "error": "channel is required."}
{"whs": ["This field is required."]}          # DRF field-level errors
```

A command must surface whichever style its endpoint emits; there is no single
error contract.

## Read-only

This CLI is **READ-ONLY**. Only GET endpoints are published, and only those
cleared of side effects (see the hazard above). No POST/PUT/PATCH/DELETE command
exists except the internal login/refresh exchange.

## Surface size ✅ (2026-08-03 probe, JIVO_MART unless noted)

| Result | Count | Meaning |
|---|---|---|
| 200 | **238** | live and readable (152 in the July baseline — **+86**) |
| 400 | 30 | real endpoint; a required query param was missing |
| 405 | 48 | exists but write-only — excluded from the CLI |
| 404 | 20 | not routed |
| 503 | 1 | `production-release-oil` under a non-Oil company |
| 500 | 1 | `/grpo/draft/` — server error; investigate before publishing |

Frontend bundle re-scrape: 575 JS chunks / 6.8 MB, 754 distinct path-like
strings. Endpoint extraction requires multiple lenses — a single call-site regex
recovers well under a third of the surface.

## Domains

New since the July baseline: `marketplace` (e-commerce fulfilment — orders,
dispatches, packing, returns, SKU mappings, combos, portal-vs-physical
reconciliation), `blowing` (bottle blowing — runs, preform specs, cost rates,
make-vs-buy), `returnable-items`, `person-gatein`, `attendance`,
`security-checks`, `weighment`, and the `construction-` / `fixed-asset-` /
`maintenance-` / `raw-material-gatein` family.

Restructured: the `warehouse/wms/*` sub-tree — eight endpoints live in July now
404, replaced by `warehouse/bst/` (branch stock transfer),
`warehouse/bom-requests/` and `warehouse/fg-receipts/`.

Prior inventory (35 Django apps / ~160 models — see `model-inventory.txt`):
production_execution, gate_core, maintenance, barcode, quality_control, wms,
person_gatein, grpo, dispatch_plans, notifications, labour_count,
raw_material_gatein, fixed_asset_gatein, docking_admin, daily_needs_gatein,
warehouse, vehicle_management, company, sales_planning_requirement,
maintenance_gatein, construction_gatein, accounts, driver_management,
stock_dashboard, ai_assistant, sap_plan_dashboard, non_moving_rm, inventory_age,
weighment, security_checks.

## Research artefacts

- `research/endpoints.txt` — candidate collection endpoints (July baseline, 210)
- `research/get200.txt` — endpoints live in July (152)
- `research/company-matrix-2026-08.tsv` — endpoint × company HTTP status, all three
- `research/sweep.tsv` — July status sweep

Linked: [[CLI/factory-cli/.printing-press-patches/README|Factory patch ledger]] · [[docs/factory/FACTORY_MAP|FACTORY_MAP]] · [[docs/FACTORY_CLI_PLAN|FACTORY_CLI_PLAN]] · [[docs/READ_ONLY_LAW|READ_ONLY_LAW]]
