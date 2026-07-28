---
endpoint: /realise/api/credit-lock/ , /realise/api/credit-unlock/
aliases: [credit-lock, credit-unlock]
method: POST
auth: session + X-CSRFToken (JSON)
readonly: false
used_by: [required-credit-limit]
tags: [jivo, api, accounts]
---
# `POST /realise/api/credit-lock/` & `/realise/api/credit-unlock/` (WRITE — document only)

## Purpose
Freeze / unfreeze the headline figures (**Total Outstanding** & **Required Limit**) on the [[required-credit-limit]] page so they hold their current values for a set number of days while the rest of the row stays live to the As-of date.

## Endpoints
| Path | Body | Role |
|---|---|---|
| `/realise/api/credit-lock/` | `{days: <N>}` (lock duration; page default 30, min 1, max 3650) | Snapshot & freeze Total Outstanding + Required Limit for N days. |
| `/realise/api/credit-unlock/` | `{}` (empty) | Release the active lock immediately. |

## Request
Headers: `Content-Type: application/json`, `X-CSRFToken`. Session cookie required. Posted via a shared `postLock(url, payload, btn)` helper; on success the page does `window.location.reload()` so the server re-renders with frozen/live values.

## Response
Not probed. On success `{status:"ok"}` (page reloads). The reloaded page embeds a `lock` object: `{active:true, days_left, lock_until}` (null when free) which drives the "Locked · N days left · until <date>" status pill.

## Used by
[[required-credit-limit]] (Lock control / Unlock button).

## Notes
- **WRITE — never executed.** Bodies reverse-engineered from page JS (`LOCK_URL`, `UNLOCK_URL`, `postLock`, `rcLockDays`).
- Lock affects only Total Outstanding & Required Limit; Ledger Amt, Payment Done and Outstanding always follow the selected As-of date even while locked.
- Related write on the same page (documented elsewhere): `save-closing-remark/` persists the per-party Delivery Remark.
