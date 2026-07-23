---
title: "EXIM endpoint — GET /sync_logs/"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: endpoint
tags: [jivogpt, exim, api, endpoint]
method: GET
path: /sync_logs/
category: sync_logs
kind: read
resource: synclogs
auth: bearer
---

# `GET /sync_logs/`

> History of SAP sync jobs (type, status, counts).

## Request

| | |
|---|---|
| Method | `GET` |
| URL | `https://eximbe.jivo.in/sync_logs/` |
| Auth | `Authorization: Bearer <access_token>` |
| Query params | — |
| Path params | — |

## Response — real sample (trimmed)

```json
[
  {
    "id": 1,
    "sync_type": "PRT",
    "status": "FLD",
    "triggered_by": "Manual",
    "started_at": "2026-02-24T09:52:04.492097Z",
    "completed_at": null,
    "error_message": "relation \"Party   \" does not exist\nLINE 1: ...rty   \".\"u_main_group\", \"Party   \".\"country\" FROM \"Party   \"...\n                              \u2026",
    "records_procesed": 0,
    "records_created": 0,
    "records_updated": 0
  },
  {
    "id": 2,
    "sync_type": "PRT",
    "status": "SCS",
    "triggered_by": "Manual",
    "started_at": "2026-02-24T09:58:57.073532Z",
    "completed_at": "2026-02-24T09:58:58.193350Z",
    "error_message": null,
    "records_procesed": 1,
    "records_created": 1,
    "records_updated": 0
  },
  "...(+338 more of 340)"
]
```

## Field reference

- `id` — sync-job log ID (sequential).
- `sync_type` — what was pulled from SAP, coded (e.g. `PRT` = parties; other jobs cover items/inventory/accounts).
- `status` — job outcome code: `SCS` = success, `FLD` = failed.
- `triggered_by` — how the job started (e.g. `Manual`).
- `started_at` / `completed_at` — ISO 8601 UTC timestamps; `completed_at` is null when the job failed or never finished.
- `error_message` — raw exception text on failure (e.g. a Postgres "relation does not exist" error), null on success.
- `records_procesed` — rows read from SAP (API typo, single "s").
- `records_created` / `records_updated` — rows inserted vs updated in the EXIM database.

## Used by pages

- [[pages/sync-logs|Sync Logs]]

## Related endpoints

- _(none)_

## Notes

- Kind: **read**. Resource permission group: `synclogs`.
- Read-only GET; safe to call repeatedly.


Linked: [[API-INVENTORY]] · [[INDEX]]
