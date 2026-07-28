---
endpoint: /realise/api/dispatch-details/
method: POST
auth: session + X-CSRFToken
readonly: true
used_by: [dispatch-details]
tags: [jivo, api, sales, flow-dispatch, logistics]
---
# `POST /realise/api/dispatch-details/`

## Purpose
Returns one row per **A/R invoice** in a date range with its **physical dispatch / freight metadata** — dispatch date, bilty (lorry receipt) date & number, transporter, vehicle number, driver mobile. Backs the [[dispatch-details]] page (the logistics tail of the sales flow).

## Request
JSON body (`Content-Type: application/json` + `X-CSRFToken`):

| Field | Type | Meaning |
|---|---|---|
| `start_date` | string `YYYY-MM-DD` | Range start (page defaults to 1st of current month). |
| `end_date` | string `YYYY-MM-DD` | Range end (page defaults to today). |

Example: `{"start_date":"2026-07-22","end_date":"2026-07-22"}`

No `company` field — unlike [[sales-flow]], this endpoint is company-agnostic (single range only).

## Response
HTTP 200. Top-level keys:

| Key | Shape | Meaning |
|---|---|---|
| `status` | string | `"ok"` (or `"error"` + `error`). |
| `rows` | array | One object per invoice (see below). |
| `count` | number | Row count. |
| `start` / `end` | string | Echo of the requested range. |

Each `rows[]` object:
- `inv_date` (string `YYYY-MM-DD`) — invoice posting date.
- `code` (string) — SAP customer card code · `name` (string) — customer name.
- `inv_no` (string) — SAP A/R invoice number.
- `dispatch` (string) — dispatch date (empty if not yet dispatched).
- `biltydate` (string) — bilty date · `bilty` (string) — bilty / LR number.
- `transporter` (string) — freight carrier name.
- `vehicle` (string) — truck registration number.
- `mobile` (string) — driver mobile number.

All logistics fields are empty strings when the invoice has not yet been dispatched.

TRIMMED sample (2026-07-22, a dispatched row):
```json
{
  "status": "ok", "count": 17, "start": "2026-07-22", "end": "2026-07-22",
  "rows": [{
    "inv_date": "2026-07-22", "code": "CUSTA001073",
    "name": "NORTHERN NATURALS PRIVATE LIMITED", "inv_no": "626070454",
    "dispatch": "2026-07-22", "biltydate": "2026-07-22", "bilty": "3698",
    "transporter": "Mahaveer Transport", "vehicle": "HR67C1036",
    "mobile": "6006399745"
  }]
}
```
(Many rows in the same day have empty dispatch/bilty/vehicle — invoiced but not yet dispatched.)

## Used by
[[dispatch-details]]

## Notes
- READ endpoint — safe. Probed live with a single day (17 rows) per read-only discipline.
- `bilty` presence is the app's definition of "Dispatched" (KPI counts non-empty bilty).
- `inv_no` ties each dispatch row back to the Invoice column in [[sales-flow]].
