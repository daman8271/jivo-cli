# oms-cli v0.1.0 → v0.2.0 — migration

**73 → 108 endpoints. Nothing was removed and nothing was renamed.**

If you have scripts or agent workflows built on v0.1.0, they keep working
unchanged. This document exists mainly to tell you about the one thing that was
badly broken and is now fixed.

---

## The headline: every `hana` command was broken, and now works

In v0.1.0 all **14** `oms-pp-cli hana …` commands failed, 100% of the time:

```
$ oms-pp-cli hana fg-items                       # v0.1.0
Error: GET /api/hana/fg-items/ returned HTTP 400:
       {"error":"branch is required and must be one of: OIL, BEVERAGE"}
```

The server requires a `branch` parameter on every `/api/hana/` endpoint. The
v0.1.0 spec declared it on none of them, and the CLI had no flag to send it, so
no invocation could succeed. That is 19% of the CLI dead on arrival.

**v0.2.0 adds a required `--branch` to all 19 hana commands:**

```
$ oms-pp-cli hana fg-items --branch OIL          # v0.2.0
443 rows
```

### `--branch` is not cosmetic — it picks a different SAP company

`OIL` and `BEVERAGE` are separate SAP company databases. Same endpoint, same
second:

| command | `--branch OIL` | `--branch BEVERAGE` |
|---|---|---|
| `hana all-customers` | 1,172 rows | 1,247 rows |
| `hana fg-items` | 443 (CHAI, COLD PRESS) | 336 (MINERAL WATER) |
| `hana open-parties` | 58 | 31 |

A card code can exist in **both with different data** — `CUSTA000636` has 55
open sales orders under OIL and 41 under BEVERAGE, and 298 of 1,165 shared card
codes are a *different party* in each. **Never quote a HANA figure without
saying which branch it came from, and never join across branches.**

There is no `MART` branch. OMS's HANA layer reaches Oil and Beverages only.

---

## New commands (35)

| resource | new commands |
|---|---|
| `account` | `devices`, `device`, `device-analytics`, `my-devices`, `ui-labels`, `ui-label-config` |
| `orders` | `dashboard`, `dashboard-charts`, `product-filters`, `template-parties`, `template-orders`, `by-item`, `schemes-manage`, `notifications-history`, `web-push-key` |
| `sap` | `sync-status`, `schedules` |
| `hana` | `series`, `warehouse-details`, `vendor-states`, `state-chain`, `invoice-drafts` |
| `invoices` | `logs`, `credit-limit-cards`, `credit-limit-flow`, `crystal` |
| `legal` (new resource) | `items`, `uoms`, `nutrition`, `item-nutrition` |
| `einvoice` (new resource) | `health`, `companies`, `invoices`, `logs` |
| `tracker` | `invoice-jsap` |

Two new resources are worth knowing about:

- **`legal`** — FSSAI food-label compliance. Upload a pack's artwork PDF against
  an item and the backend reads the label and reports each statutory
  declaration as ok / missing / mismatch. One product set up so far.
- **`einvoice`** — GST e-invoicing. Only the **reads** are wrapped: health,
  enrolled companies, invoices with IRN status, and the generation log. Every
  IRN write (generate, cancel, retry, e-way bill) is deliberately absent.

---

## Behaviour changes you should know about

### `orders list` does not return the order book

Bare `orders list` returns **263 of 2,163 orders**. The shipped description
("All orders") was wrong by about 7×. Three traps, all now in `--help`:

- `--status` accepts a **comma-separated list** and unions the results.
  There are **11** valid values: `ORDER_CREATED`, `RATE_APPROVAL`, `BILLING`,
  `NEED_APPROVAL`, `BILLING_PENDING`, `APPROVED`, `REJECTED`,
  `BILLING_REJECTED`, `COMPLETED`, `AUDITOR_APPROVAL`, `DRAFT`.
- `--billing` **discards** any `--status` you also pass.
- `--approval-pending` on its own is a no-op.

### Response types were wrong on most commands

v0.1.0 declared `response: object` for all 73 endpoints. Many are arrays. Fixed
from what the server actually returned.

### Three commands are broken upstream, and say so

Kept (so they start working the day OMS fixes them) with the reason in
`--help`:

| command | what happens |
|---|---|
| `hana product-stock` | HTTP 502 — `name 'unique_schemas' is not defined` |
| `hana product-so` | HTTP 500 — `get_sales_orders_for_product()` arity error |
| `invoices all` | HTTP 400 — needs a "Warehouse Code" param no name satisfies |

`invoices skus-pending` (`/api/sku/pending/`) has the same class of backend
crash. All four are written up in
`research/FINDINGS-FOR-OMS-TEAM-2026-08-04.md`.

### `tracker` still needs a grant your admin role does not give you

All 15 tracker commands return HTTP 403 for a normal OMS admin:

```
{"detail":"You do not have access to this tracker page."}
{"detail":"Tracker administration is restricted to tracker admins."}
```

They are published anyway — the endpoints exist, and a 403 is a permission
wall, not a dead route. Their response shapes are marked UNVERIFIED because no
credential we have could see a payload. Ask for a `tracker_user` /
`tracker_admin` grant if you need them.

---

## Removed

**Nothing.** Every v0.1.0 command still resolves, under its original name.
`invoices history` remains unregistered, as it was in v0.1.0 — although note
that the backend route **now exists** (it was absent in July and returns 200
today), so patch 0003 is a candidate to lift on the next pass.

---

## Security — read `research/FINDINGS-FOR-OMS-TEAM-2026-08-04.md`

While rescraping we found that **29 OMS API endpoints serve production data
with no authentication at all**, including all 54 staff accounts *with their
password hashes*, 35,722 customer addresses with GST numbers, and per-customer
credit limits. `DEBUG = True` is also on in production. Neither is a CLI issue,
but both are urgent and are documented with reproductions.
