# jivo-ecom-pp-cli — migration, spec v0.1.0 → v0.2.0 (2026-08-03)

138 endpoints → **151**. Two removed, fifteen added, every remaining command
name unchanged.

If you only read one thing: **two commands are gone and one flag changed
name.** Everything else is additive.

---

## Removed — 2 commands

Both carry a positive justification. Nothing was dropped for being untested,
unverifiable or merely unused; a 403 or a "the UI no longer calls it" was never
treated as grounds for removal.

### `platform month-on-month-sale` — proven dead

```
GET /api/platform/{slug}/month-on-month-sale  ->  404 on ALL TEN slugs
amazon · blinkit · zepto · swiggy · bigbasket · flipkart_grocery
zomato · flipkart · citymall · jiomart
```

The 404 body is Django's URL-resolver HTML, not a DRF JSON 404, and the current
SPA contains no call site for it in any of its 152 chunks.

Positive control, so the 404s cannot be blamed on a bad slug:
`GET /api/platform/flipkart/stats` and `/api/platform/citymall/stats` both
return **200** in the same sweep.

**Replacement:** `platform secondary-monthly` for month-on-month secondary
sales, or the new `platform monthly-sales-explorer` (bigbasket, blinkit,
swiggy, zepto).

> Recorded for the app owners in `research/FINDINGS-FOR-ECOM-TEAM-2026-08.md`.
> If the route was removed by accident it can be restored and republished.

### `sap sales-invoice-lines` — proven broken

```
GET /api/sap/sales-invoice-lines/{DocEntry}  ->  500, every DocEntry
{"detail":"SAP HANA error: (260, 'invalid column name: T1.UnitMsr: line 4 col 28 (at pos 115)')"}
```

Fails at SQL parse time, before `DocEntry` is used, which is why all three
tested DocEntries (37594, 37603, 37601 — all taken from a live
`sap sales-invoices` response) fail identically at the same character offset.
The live schema has `INV1.unitMsr` and `OITM.SalUnitMsr`; **no table has a
column `UnitMsr`**. HANA quotes case-sensitively, so this is a one-token casing
bug in the backend's SELECT list.

**Replacement:** none. `sap sales-invoices` returns invoice headers only, so
line-item drill-down is unavailable until the backend is fixed. Excluded as
`KNOWN_BROKEN` with the reason recorded, so it can be republished the day it
is fixed — no rediscovery needed.

---

## Changed — 1 flag

### `dashboard expiry-alerts`: `--platform` → `--table`

The command name is unchanged. The **flag** changed because the shipped one was
semantically wrong.

The path segment holds a **reporting-table name**, not a platform slug. In the
SPA, `useDashboardData` passes the *same array* to `getTableCounts` (indisputably
table names) and to `getExpiryAlerts` per element, then filters the results on
`alert.table`. There is no call site anywhere in the bundle that passes a
platform slug.

This matters because the wrong value fails **silently**:

```bash
# old, wrong - 200 with an empty list, which reads as "no expiry alerts"
GET /api/dashboard/expiry-alerts/amazon            -> {"alerts": []}
# right
GET /api/dashboard/expiry-alerts/amazon_inventory  -> 200 with real alerts
```

```bash
# before
jivo-ecom-pp-cli dashboard expiry-alerts --platform amazon
# after
jivo-ecom-pp-cli dashboard expiry-alerts --table amazon_inventory
```

Valid table names: run `jivo-ecom-pp-cli tables counts`. Its key list is the
server's own allowlist — anything else returns
`400 {"error":"Table not allowed"}`.

---

## Added — 15 commands

| command | what it gives you | status |
|---|---|---|
| `account feature-flags` | which optional features are on for this account | live |
| `dashboard penetration-report` | city × item distribution, 2,492 rows | live |
| `dashboard penetration-report-options` | the filter vocabulary for the above | live |
| `platform bigbasket-sales-explorer` | BigBasket sales explorer (BigBasket only) | live |
| `platform secondary-summary-version` | cache-invalidation stamp for the secondary summary | live |
| `platform blinkit-summary-report` | Blinkit monthly summary (Blinkit only) | live |
| `platform monthly-sales-explorer` | monthly sales explorer (bigbasket, blinkit, swiggy, zepto) | live |
| `reports amazon-po-billing` | Amazon PO billing with line detail | live |
| `reports amazon-po-sku-pendency` | per-SKU PO pendency, 762 rows | live |
| `reports amazon-po-sku-pendency-filter-options` | the filter vocabulary for the above | live |
| `reports live-data` | live report data | **gated** — 403 for this credential |
| `reports live-reports` | live report list | **gated** — 403 for this credential |
| `shipment appointment-families` | ASIN families on an appointment | gated (Shipment Planner) |
| `shipment fc-switch-group` | FC switch group lookup | gated (Shipment Planner) |
| `shipment po-appointments` | appointments for a set of POs | gated (Shipment Planner) |

---

## Corrected descriptions — no command or flag change

These were wrong or dangerously incomplete in v0.1.0. Same commands, better
documentation.

| command | what changed |
|---|---|
| `platform meta` | was "Platform metadata (slugs, labels, config)". It is the **Meta (Facebook/Instagram) advertising dashboard** — 83 campaigns, reach, CPC, CPM, spend. There is no endpoint returning the slug list; use `account me`, field `platforms` |
| `sap distributors` | is the **vendor** master (`OCRD CardType='S'`) — ad agencies and suppliers, not sales distributors. For distributors use `sap platform-distributors` |
| `sap *` (7 commands) | now state the company scope: **JIVO MART** (`JIVO_MART_HANADB`), not Oil and not group-wide |
| `sap sales-invoices` | headers only, **includes cancelled**, `DocTotal` is GST-inclusive, and there is no credit-note endpoint — so JIVO turnover is **not** computable from this domain |
| `sap sales-analysis` | with `--source oil` it defaults to `cardname = JIVO MART PVT LTD`, i.e. it measures Oil→Mart **intercompany** transfers, which JIVO excludes from sales (correction C-0005) |
| `reports raw` / `reports columns` | `--view` is required, and `--platform` on these two takes **UPPERCASE display names with spaces** (`BIG BASKET`), not the lowercase slugs every other endpoint uses |
| 17 `platform` commands | now declare the platforms they are actually served for; the CLI refuses a wrong pairing locally instead of sending it |

---

## New: the CLI now refuses an impossible platform pairing locally

17 platform-scoped routes are served for specific platforms only, and the
server says which. Those lists are now in the spec, so:

```
$ jivo-ecom-pp-cli platform blinkit-ads-dashboard --platform amazon
Error: invalid value "amazon" for --platform: must be one of [blinkit]

$ jivo-ecom-pp-cli platform region-doh --platform blinkit
Error: invalid value "blinkit" for --platform: must be one of [swiggy zepto]
```

Previously this produced a live HTTP 400 whose message read like a broken
command.

---

## Path fix: the shipment family needs a trailing slash

`/api/shipment/…` requires a trailing slash; the rest of the API rejects one.
Verified live with redirects disabled:

```
GET /api/shipment/shipments        -> 301 -> /api/shipment/shipments/
GET /api/dashboard/latest-month/   -> 404
GET /api/sap/distributors/VENDA000526/  -> 404
```

v0.1.0 had zero trailing slashes anywhere, so all 22 shipment commands were
served a 301 before their real response. 21 published shipment paths now carry
the slash. No command or flag changed; the wire path did.

---

## Parameters: 189 → 558

Every shipped parameter and enum was carried forward — a mechanical audit
confirms **zero** shipped parameters were lost (the single exception is the
deliberate `expiry-alerts` flag correction above). The additions come from the
SPA's own request builders and from live 400 bodies in which the server named
its own legal values.

Worth knowing about specifically:

- **`sap sales-analysis --item-head`** (PREMIUM / COMMODITY / OTHERS). JIVO
  correction **C-0003** says to segment the range on this and never by matching
  item names. v0.1.0 did not expose it, which left name-matching as the only
  option. It also gained `--aggregate item_head`, which makes the **server**
  compute the totals — with `--page-size 1` you get a computed `aggregate[]`
  block instead of paging to exhaustion.
- **`sap inventory-overview --status`** (`""` all / `Y` active / `N` frozen).
  The dashboard sends `Y`; a bare CLI call returns **more** rows than the UI
  shows, because it includes frozen items.
- **`--table` on the five `tables` commands** now carries the server's real
  44-name allowlist.

---

## What is NOT verified

**All 25 `shipment` commands return 403 for the credential used here.** The gate
is the permission `amazon.shipment_planning.view`, which this Super-Admin
account does not hold. A 403 proves the endpoint exists and is routed, so all
25 are published — but **their response shapes could not be read and are marked
UNVERIFIED in the spec**. Nobody should treat the shipment section as confirmed
until someone holding that permission runs it. See
`research/FINDINGS-FOR-ECOM-TEAM-2026-08.md` item 3.

Four of those (`shipment shipment-invoices`, `shipment-invoice-file`,
`shipment-po-documents`, `shipment-po-document`) are additionally no longer
called by the current SPA. They are carried forward under the rule that only
positive evidence justifies removal, but they deserve a human's eyes.
