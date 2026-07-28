---
endpoint: /realise/api/save-closing-remark/
method: POST
auth: session + X-CSRFToken + XHR header
readonly: false
used_by: [sales-dashboard]
tags: [jivo, api, sales-dashboard, write]
---
# `POST /realise/api/save-closing-remark/` — ⚠️ WRITE (NOT PROBED)

## Purpose
Persists a free-text **closing remark** / note for a reporting period on the Realise dashboards (a period sign-off comment stored server-side). Part of the shared Realise API's write set.

## Request
Not directly referenced in `realise.html` JS (the save-remark UI lives on a sibling Realise screen, e.g. Compare Sales). Based on the shared-API naming convention and its sibling save endpoints, expected body is a small JSON object identifying the period and the remark text, e.g. `{period/month/year, remark}`, POSTed with `Content-Type: application/json` + `X-CSRFToken`. Exact fields not confirmed from this page.

## Response
Not probed.

## Used by
[[sales-dashboard]] (and other Realise screens — shared API).

## Notes
**WRITE — mutating. Never call.** Listed in the shared Realise write set (`save-targets/ save-closing-remark/ …`). Documented for completeness; request signature not observable from `realise.html` — confirm from the page that actually renders the closing-remark editor before relying on the body shape.
