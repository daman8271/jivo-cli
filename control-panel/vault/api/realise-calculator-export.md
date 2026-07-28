---
endpoint: /realise/api/realise-calculator/export/
method: POST
auth: session + X-CSRFToken (JSON body)
readonly: false
used_by: [realise-calculator]
tags: [jivo, api, calculator-ratelist]
---

# `POST /realise/api/realise-calculator/export/`

## Purpose
Renders the current [[realise-calculator]] plan(s) into a downloadable, formatted `.xlsx` (with live formulas and a KPI summary block). Used by every "Export Excel" button (Planning Grid, Compare A/B/both, Old vs New Order). **EXPORT/file — not executed during recon; signature captured from page JS only.**

## Request
`Content-Type: application/json`, `X-CSRFToken: <csrftoken>`. Body:

| Field | Type | Meaning |
|---|---|---|
| `filename` | str | Base name for the download (e.g. `Realise_Compare`) → served as `<filename>.xlsx` |
| `layout` | str | `separate` (one plan per sheet-block) or `single` (plans side by side, for compare/order) |
| `plans` | array | Each `{name, items:[...], color, hcolor}` — `items` are grid rows (`item, code, retailer, ss, dm, gst, pcsbox, disc, boxltr, scheme, sell`); `color`/`hcolor` are hex fills for the block/header |
| `summary` | array | KPI rows `{label, value}` — Total To-be-sale (L), Blended Realise (Rs/L), Total Revenue (Rs), plus diff rows for compare/order exports |

Example (structure only, NOT sent):
```json
{"filename":"Realise_Compare","layout":"single",
 "plans":[{"name":"EXISTING PLAN","items":[...],"color":"EEF2FF","hcolor":"4F46E5"},
          {"name":"NEW PLAN","items":[...],"color":"ECFDF5","hcolor":"0D9488"}],
 "summary":[{"label":"Existing Plan · Blended Realise (Rs/L)","value":171.07}]}
```

## Response
Not probed. Returns an `.xlsx` **binary blob** (`r.blob()`), which the page turns into an object-URL download. Errors surface as an "Export failed." alert.

## Used by
[[realise-calculator]] — Export Excel on Planning Grid, Compare (A / B / both), and Order tabs.

## Notes
- **EXPORT / file-download endpoint.** In the recipe's skip list (mutating/heavy file); documented from `realise__realise-calculator.html` only, never called.
- Blended figures in `summary` are [[REALISE]] ₹/L.
- Upload counterparts: [[realise-calculator-upload]], [[realise-calculator-order-upload]].
