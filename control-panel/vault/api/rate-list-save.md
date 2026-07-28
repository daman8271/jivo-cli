---
endpoint: /realise/api/rate-list/save/
method: POST
auth: session + X-CSRFToken (JSON body)
readonly: false
used_by: [realise-calculator, rate-list]
tags: [jivo, api, calculator-ratelist]
---

# `POST /realise/api/rate-list/save/`

## Purpose
Persists a [[realise-calculator]] plan (or comparison of plans) to the saved [[rate-list]], tagged by state and scope. Invoked from the calculator's **Save Result** dialog. **WRITE — not executed during recon; signature captured from page JS only.**

## Request
`Content-Type: application/json`, `X-CSRFToken: <csrftoken>`. Body:

| Field | Type | Meaning |
|---|---|---|
| `name` | str | User-given result name (required) |
| `state` | str | Indian state tag from the fixed 24-state list, or `""` |
| `scope` | str | `GRID` (Planning Grid), `ORDER` (Old+New Order), `A` (Existing only), `B` (New only), `BOTH` (Existing + New) |
| `payload` | object | `{ plans: [...], compare: {...}|null }` |
| `payload.plans[]` | array | 1–2 plans, each `{name, rows[], totals:{totSell,revSum,blend}}` |
| `payload.plans[].rows[]` | array | Per-SKU line: `item, code, retailer, ss, dm, gst, pcsbox, disc, boxltr, scheme, sell` + derived `realise, revenue, ssRate, dmRate, exgst, boxVal, netBox, totLtr` |
| `payload.compare` | object\|null | `{blendA, blendB, diffRealise, diffRevenue, aMinusBxBvol}` (set for `BOTH`/`ORDER`) |

Example (structure only, NOT sent):
```json
{"name":"Punjab Q3","state":"Punjab","scope":"BOTH",
 "payload":{"plans":[{"name":"Existing Plan","rows":[...],"totals":{"totSell":0,"revSum":0,"blend":0}}],
            "compare":{"blendA":0,"blendB":0,"diffRealise":0,"diffRevenue":0,"aMinusBxBvol":0}}}
```

## Response
Not probed. Page JS expects JSON `{"status":"ok"}` on success, else `{"status":"error","error":"…"}`.

## Used by
[[realise-calculator]] (Save Result dialog) — results then appear on [[rate-list]].

## Notes
- **WRITE endpoint — mutating.** Listed in the recipe's read-only skip list; documented from `realise__realise-calculator.html` only, never called.
- Delete counterpart: [[rate-list-delete]]. Read/list: [[rate-list]].
