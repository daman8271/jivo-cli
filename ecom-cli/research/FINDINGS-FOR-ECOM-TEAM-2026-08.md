# Findings for the ecom.jivo.in team — 2026-08-03

Surfaced while re-surveying the API to regenerate the read-only CLI. Every
item below was observed live on 2026-08-03 with a read-only GET sweep from
the account `dp605702@jivo.in`. **No writes of any kind were issued** and no
data was created or changed.

Ordered by how much they cost someone.

---

## 1. `GET /api/sap/sales-invoice-lines/{DocEntry}` returns 500 for every invoice

**Severity: broken feature, silent.** The endpoint is routed and reachable; it
just always fails.

**Reproduction**

```bash
# any DocEntry taken from a live /api/sap/sales-invoices response
curl -s -H "Authorization: Bearer $TOKEN" \
  https://ecom.jivo.in/api/sap/sales-invoice-lines/37594
```

**Response — HTTP 500, identical for 37594, 37603 and 37601:**

```json
{"detail":"SAP HANA error: (260, 'invalid column name: T1.UnitMsr: line 4 col 28 (at pos 115)')"}
```

**Diagnosis.** The query behind this view selects `T1.UnitMsr`, and that column
does not exist on the aliased table. It is not data-dependent — all three
DocEntries tested came from a successful `/api/sap/sales-invoices` call, and all
three fail identically at the same character offset. This looks like a column
that was renamed or that belongs to a different table alias in the join.

**Impact.** Invoice line-item drill-down is unavailable. The failure is a 500
rather than a user-facing message, so the UI shows a generic error and nobody
files it.

**Status in the CLI.** Excluded as `KNOWN_BROKEN` with this reason recorded, so
it can be published again the day it is fixed — no rediscovery needed.

---

## 2. `GET /api/platform/{slug}/month-on-month-sale` is gone but still published

**Severity: dead route still on a public contract.**

Returns Django's URL-resolver 404 (plain HTML, not a DRF JSON 404) on **every**
platform tried — amazon, blinkit, zepto, swiggy, bigbasket, flipkart_grocery,
zomato. A resolver 404 is slug-independent, so the route no longer exists at
all.

It is still published in CLI spec v0.1.0 as the command
`platform month-on-month-sale`, and the current SPA no longer calls it. Most
likely it was removed from `urls.py` without anything downstream noticing.

**Action taken.** Removed from the regenerated spec, recorded in
`MIGRATION-2026-08.md` as proven dead. **If this removal was not intentional,
the route needs restoring** — please say so and it goes straight back.

---

## 3. `amazon.shipment_planning.view` is not grantable through the normal admin path

**Severity: blocks verification, and probably blocks real users.**

All 19 Amazon Shipment Planner endpoints return:

```json
{"detail":"You do not have access to the Amazon Shipment Planner."}
```

The account holds **144 permissions**, including every one that looks like it
should be sufficient — `view_shipment`, `view_shipmentitem`,
`view_shipmentauditlog`, `dispatch.view`, `dispatch.edit`,
`admin.dispatch.manage`, `platform.amazon.access` — and belongs to the groups
*Super Admin*, *Platform Admin*, *Operations Manager* and *Dispatch Operator*.

It still fails, because the gate is a single distinct permission string,
`amazon.shipment_planning.view` (visible in the SPA's own permission map), and
`is_superuser` is `false` so the bypass in that same module does not apply.

**Two questions for the team:**

1. Is `amazon.shipment_planning.view` attached to any group at all? If a user in
   *Super Admin* + *Dispatch Operator* cannot open the Shipment Planner, either
   the permission is unassigned or the group mapping is stale.
2. Should `admin.dispatch.manage` imply it? A permission that only exists
   standalone and is not implied by the obvious role is the kind that gets
   forgotten on every new hire.

**Consequence for the CLI.** All 34 shipment endpoints are published (a 403
proves the endpoint exists), but their **response shapes could not be
verified** and are marked as such. Nobody should treat the shipment section of
the CLI docs as confirmed until someone with that permission runs it.

---

## 4. `/api/reports/live/data` and `/api/reports/live/reports` are gated by something unnamed

**Severity: minor, but it costs an afternoon to diagnose.**

Both return 403 with DRF's generic message:

```json
{"detail":"You do not have permission to perform this action."}
```

Unlike the Shipment Planner, this gate is **not** named in the SPA's permission
map, so there is no way to work out from the client what permission is
required. A named message (as the Shipment Planner does) would make this
self-diagnosing.

---

## 5. `GET /api/platform/{slug}/region-doh-dashboard` exists for only two platforms, and fails opaquely for the rest

**Severity: cosmetic, but it reads as a bug.**

| platform | result |
|---|---|
| swiggy, zepto | 200 |
| amazon, blinkit, bigbasket, flipkart_grocery, zomato | 404 |

The 404 is raised inside the view, so the endpoint is alive — it simply is not
enabled for those platforms. Every other platform-restricted route in this API
returns a **400 with a clear message** instead:

```json
["Blinkit Ads Dashboard is available only for Blinkit."]
["Monthly landing rate is only available for blinkit, zepto, swiggy, bigbasket, flipkart_grocery."]
```

Those messages are genuinely excellent — they made it possible to verify 17
platform-scoped endpoints safely, because the server named its own legal
values instead of us guessing them. `region-doh-dashboard` is the one that
does not follow the pattern, and a bare 404 is indistinguishable from a dead
route. Suggest matching the others.

---

## 6. Typo in the platform registry makes Zepto's secondary-sales table unreachable

**Severity: real bug, one character.**

In `assets/api-<hash>.js`, the platform registry spells Zepto's secondary
table `zeptSec`:

```js
zepto:{slug:`zepto`, name:`Zepto`, …,
       tables:{inventory:`zepto_inventory`, secondarySells:`zeptSec`, …}}
```

Every other platform uses the full form (`blinkitSec`, `swiggySec`,
`bigbasketSec`, `zomatoSec`, …). The server only accepts the full form:

```bash
GET /api/dashboard/table-count/zeptoSec   -> 200 {"table":"zeptoSec","count":51458}
GET /api/dashboard/table-count/zeptSec    -> 400 {"error":"Table not allowed","count":0}
```

`zeptSec` appears in **exactly one file** — the API module. Every other chunk
(`Dashboard`, `UploadHub`, `SecondaryUploader`, `UploadPage`,
`FkGroceryUploader`, `FolderLandingPage`) spells it `zeptoSec`. So any feature
that reads `platform.tables.secondarySells` for Zepto sends the bad value and
gets a 400, while the same screen for Blinkit works. 51,458 rows are behind it.

One-character fix. Worth checking which screens actually route through the
registry field rather than a hardcoded string, since those are the ones
currently silently empty for Zepto only.

---

## 7. `/api/shipment/` requires a trailing slash; the rest of the API rejects one

**Severity: cosmetic inconsistency, but it has already caused a wrong spec.**

Verified live with redirects disabled:

```
GET /api/shipment/shipments        -> 301  Location: /api/shipment/shipments/
GET /api/shipment/shipments/       -> 403  (the real response, behind its gate)
GET /api/dashboard/latest-month    -> 200
GET /api/dashboard/latest-month/   -> 404
GET /api/sap/distributors/VENDA000526   -> 200
GET /api/sap/distributors/VENDA000526/  -> 404
```

So the two families have **opposite** conventions. The SPA gets this right —
every `/api/shipment/` call it makes is slash-terminated. CLI spec v0.1.0 got
it wrong: it has zero trailing slashes anywhere, so all 22 shipment commands
were served a 301 before their real response. Harmless for a redirect-following
GET client, but it is a round trip per call and it is a reliable sign those
paths were published without ever being exercised.

Not asking for a change — just recording it, because anything written against
this API needs to know the rule is per-module rather than global. The
regenerated CLI now emits the slash for the shipment family only.

---

## 8. An undocumented destructive endpoint sits in a widely-imported module

**Severity: worth a second look, not necessarily a bug.**

`POST /api/upload/delete-by-date` bulk-deletes rows from a named table over a
date range. It lives in `uploaderUtils`, which is imported by 17 chunks, and it
appears in no spec, no CLI and no prior inventory of this API.

Flagging it only because a destructive bulk operation reachable from a shared
utility module is easy to call by accident from new UI code. It is excluded
from the CLI permanently under the read-only rule and was never invoked.

---

## Notes on method

- Read-only throughout: GET only, no query parameters on the first sweep, and
  every value substituted afterwards was one the server itself had already
  returned — either in a live 200 payload or named verbatim in a 400 body.
- The 46 client-side write endpoints were never called at all.
- Six collections were size-checked before and after the sweep and none
  changed; responses were scanned for same-day `created_at`/`updated_at` and
  the only hits predate the sweep by hours.
- Full evidence: `ecom-cli/research/evidence/`, scripts in
  `ecom-cli/research/scripts/`.
