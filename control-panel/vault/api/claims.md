---
endpoint: /realise/api/claims/
method: GET
auth: session + XHR header (X-Requested-With / X-CSRFToken)
readonly: true
used_by: [claims]
tags: [jivo, api, accounts]
---
# `GET /realise/api/claims/`

## Purpose
Returns the full **claim register** (manually-entered customer claims) plus the customer **master picklist** used by the Add-Claim dialog. Backs the [[claims]] page.

## Request
Headers: `X-Requested-With: XMLHttpRequest` required. Session cookie required. No query params.

## Response
HTTP `200`, `application/json` (~97 KB sample). Top-level keys:
- `status` — `"ok"`.
- `rows` — list of claim records.
- `masters` — `{status, customers}` where `customers` is `[{code, name, main_group}]` (1,167 on sample) — the party autocomplete source.

Claim row shape (all keys): `id`, `claim_date`, `claim_month`, `month_year`, `ym`, `party_code`, `party_name`, `main_group`, `product`, `item`, `claim_type`, `ref_inv_no`, `coop_no`, `claim_amount`, `claim_pass_date`, `claim_hold` (`Yes`/`No`), `claim_passed`, `hold_amount` (= claim_amount − claim_passed), `reason_of_hold`.

Trimmed 1-row sample:
```json
{"id":5,"claim_date":"2026-07-07","month_year":"Jul 2026","party_code":"CUSTA000872",
 "party_name":"SAI TRADERS LUDHIANA","main_group":"MT","claim_type":"NSO CLAIM",
 "ref_inv_no":"1030003568 / 2026","claim_amount":23600.0,"claim_pass_date":"2026-05-20",
 "claim_hold":"Yes","claim_passed":0.0,"hold_amount":23600.0,
 "reason_of_hold":"APPROVAL PENDING FROM PRINCE SIR"}
```

## Used by
[[claims]].

## Notes
- Read-only. Probed live → HTTP 200, 6 rows + 1,167 master customers.
- The register is hand-maintained (not a SAP feed). Mutating siblings share the base `/realise/api/claims/`:
  - `POST /realise/api/claims/save/` — create/update a claim (WRITE).
  - `POST /realise/api/claims/delete/` — `{id}` delete (WRITE).
  - `POST /realise/api/claims/upload/` — bulk Excel import (WRITE).
  These are documented from page JS only, never executed.
