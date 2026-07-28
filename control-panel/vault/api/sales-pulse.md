---
endpoint: /realise/api/sales-pulse/
method: GET
auth: session + XHR header (X-Requested-With)
readonly: true
used_by: [control-panel, sales]
tags: [jivo, api, realise, live-refresh, heartbeat]
---

# `GET /realise/api/sales-pulse/`

## Purpose
A **cheap change-fingerprint / heartbeat** for the shared Realise backend. The [[sales-dashboard]] dashboard's live-refresh loop polls this every ~30s while the tab is visible; when the returned `pulse` string changes versus the last sample, the client knows the underlying SAP data moved and triggers a full (heavy) reload of [[sales-data]] / beverages. If the fingerprint is unchanged, it stays light and does nothing. Belongs to the same `/realise/api/*` backend that fronts the [[control-panel]] home KPIs.

## Request
Query params (all optional; sent by the heartbeat):
- `dataset` — string, `oils` | `beverages`. Selects which segment's fingerprint to compute. Home probe uses `oils`. See [[OILS]] / [[BEVERAGES]].
- `start` — string `YYYY-MM-DD`, start of the active date window (from the dashboard's From picker).
- `end` — string `YYYY-MM-DD`, end of the active date window (To picker).

Headers: session cookie + `X-Requested-With: XMLHttpRequest`. (Client also sends `X-CSRFToken`, though as a GET it is not required.) No request body.

Live JS (realise.html):
```
fetch(API + '/api/sales-pulse/?dataset=' + dataset + '&start=' + start + '&end=' + end,
      { headers: { 'X-CSRFToken': getCSRF() } })
```

## Response
HTTP `200`, `application/json`. Top-level keys:
- `status` — string, `"ok"`.
- `pulse` — string; an opaque fingerprint of the current data window. Empty string `""` when there is nothing to fingerprint (e.g. no `start`/`end` supplied, or no data in range). The client treats an empty `pulse` as "no signal" and skips the refresh.

Observed samples (all params, and with `dataset=oils` / `beverages` / none — same shape):
```json
{"status": "ok", "pulse": ""}
```
When data exists in the window, `pulse` carries a non-empty token that changes as rows move; the client only compares equality, never parses it.

## Used by
[[sales-dashboard]] (live auto-refresh heartbeat, `heartbeatTick()`), [[control-panel]] (same shared `/realise/api/*` backend).

## Notes
- **READ-only, safe.** Probed live: `GET /realise/api/sales-pulse/?dataset=oils` → `200`, body `{"status":"ok","pulse":""}` (empty because no `start`/`end` window was supplied). `dataset=beverages` and no-dataset return the identical shape.
- Requires the `X-Requested-With: XMLHttpRequest` header; without it the app returns 403/HTML like the other Realise GET endpoints.
- Cheap by design — intended to be polled frequently; do not use it to pull data (it carries none), only to detect change.
