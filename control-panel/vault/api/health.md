---
endpoint: /realise/api/health/
method: GET
auth: session + XHR header (X-Requested-With)
readonly: true
used_by: [control-panel, sales]
tags: [jivo, api, realise, health, sap]
---

# `GET /realise/api/health/`

## Purpose
A **liveness / SAP-connectivity probe**. The dashboard calls it on load (and can re-poll) to drive the "SAP Connected" status dot — confirming the Django app can reach the backing **SAP Business One** system that feeds all Realise data. Green dot = SAP reachable; red = SAP error or server offline. Part of the shared `/realise/api/*` backend behind [[control-panel]].

## Request
No query params, no body.
Headers: session cookie + `X-Requested-With: XMLHttpRequest`. (Client also passes `X-CSRFToken`, not required for GET.)

Live JS (realise.html `checkHealth()`):
```
fetch(API + '/api/health/', { headers: { 'X-CSRFToken': getCSRF() } })
// -> sets sDot green/red and sTxt 'SAP Connected' / 'SAP Error'; catch -> 'Server Offline'
```

## Response
HTTP `200`, `application/json`. Top-level keys:
- `sap_connected` — boolean; `true` when the SAP B1 link is live. Drives the status dot colour.
- `message` — string; human status, e.g. `"SAP Connected"`.
- `username` — string; the authenticated user (echoes the session), e.g. `"preshit"`.
- `role` — string; the user's role, e.g. `"admin"`.

Observed live sample:
```json
{"sap_connected": true, "message": "SAP Connected", "username": "preshit", "role": "admin"}
```

## Used by
[[sales-dashboard]] (`checkHealth()` — SAP status dot), [[control-panel]] (same shared backend / app-wide health signal).

## Notes
- **READ-only, safe.** Probed live → `200`, body as above (91 bytes). Idempotent, no side effects.
- Requires `X-Requested-With: XMLHttpRequest`; missing it yields 403/HTML like the other Realise GETs.
- Doubles as a lightweight "who am I" echo (`username`/`role`) alongside the SAP flag.
