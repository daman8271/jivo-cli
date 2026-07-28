---
endpoint: /realise/api/rate-list/
method: GET
auth: session + XHR header (X-Requested-With / X-CSRFToken)
readonly: true
used_by: [rate-list, realise-calculator]
tags: [jivo, api, calculator-ratelist]
---

# `GET /realise/api/rate-list/`

## Purpose
Returns the saved [[realise-calculator]] results that populate the [[rate-list]] page. With `?id=<n>` it returns just that one saved result, used when the calculator is opened as `?load=<id>` to hydrate the grids for editing.

## Request
Query params:

| Param | Type | Meaning |
|---|---|---|
| `id` | int (optional) | Return only the saved result with this id (wrapped in `rows[0]`). Omit to list all. |

Requires XHR header + session cookie.

## Response
HTTP **200**, `application/json`. Top-level keys:

- `status` — string, `"ok"`.
- `rows` — array of saved results (see shape below). **Empty in the live system at recon time.**
- `count` — int, number of rows.
- `states` — array of distinct state strings present, for the filter dropdown.

Live probe (store currently empty), both `/rate-list/` and `/rate-list/?id=1`:
```json
{"status":"ok","rows":[],"count":0,"states":[]}
```

Each `rows[]` entry (shape reconstructed from the page JS `cardHtml`/`loadSavedResult`):
```json
{
  "id": 1, "name": "…", "state": "Punjab",
  "scope": "BOTH",            // GRID | ORDER | A | B | BOTH
  "created_at": "…", "created_by": "preshit",
  "payload": {
    "plans": [
      { "name": "Existing Plan",
        "rows": [ {"item":"…","code":"FG…","retailer":"…","ss":"…","dm":"…",
                   "gst":"…","pcsbox":"…","disc":"…","boxltr":"…","scheme":"…","sell":"…",
                   "realise":0,"revenue":0,"ssRate":0,"dmRate":0,"exgst":0,
                   "boxVal":0,"netBox":0,"totLtr":0} ],
        "totals": {"totSell":0,"revSum":0,"blend":0} }
    ],
    "compare": {"blendA":0,"blendB":0,"diffRealise":0,"diffRevenue":0,"aMinusBxBvol":0}
  }
}
```
`compare` is present only for `BOTH`/`ORDER` scopes; `blend`/`blendA`/`blendB` are blended [[REALISE]] ₹/L.

## Used by
[[rate-list]] (list + state filter) · [[realise-calculator]] (single-result reload via `?id=`)

## Notes
- Read-only GET; probed live — returns 200 with an empty store.
- The write counterpart is [[rate-list-save]]; deletes go through [[rate-list-delete]].
