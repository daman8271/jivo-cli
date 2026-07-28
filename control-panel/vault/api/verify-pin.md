---
endpoint: /realise/api/verify-pin/
method: POST
auth: session + X-CSRFToken
readonly: false
used_by: [users, realise]
tags: [jivo, api, admin]
---
# `POST /realise/api/verify-pin/`

> ⚠️ **OTP / re-auth gate — NOT executed.** Documented from the Sales page (`realise.html`) JS only, per read-only discipline. It is auth-sensitive (submits the admin's password), so it is treated as a WRITE/OTP endpoint and never probed.

## Purpose
Server-side **re-authentication gate** for admin write actions. Before an admin can open the "Update Targets" editor on the Sales / Realise dashboard, the app pops a modal asking the admin to re-enter their password; this endpoint confirms it. Despite the name and the `{pin:...}` body key, the value is the account **password**, not a numeric PIN. It guards the target-editing flow (`save-targets/` etc.) and is part of the same admin-write surface as [[users]].

## Request
- **Method:** POST
- **Headers:** `Content-Type: application/json`, `X-CSRFToken: <token>` (from `getCSRF()`). Session cookie required.
- **JSON body:**
  - `pin` — string, the current admin user's account password (the modal field is a password input; the label reads "Enter password").
```json
{ "pin": "<admin password>" }
```

## Response
Not probed. From the client (`submitReauth()` in `realise.html`):
- On success: `{ "status": "ok", "verified": true }` → the app sets `updateAuthUser = currentUser`, closes the modal and opens the targets editor.
- On wrong password: `verified` is falsy (`{ "status": "ok", "verified": false }` or similar) → the modal shows "Incorrect password".
- On transport error the client shows "Verification failed".

## Used by
- [[sales-dashboard]] (Sales dashboard) — re-auth before "Update Targets" (`openUpdateTargetsModal` → `submitReauth` → `openTargetsTableModal`).
- Conceptually part of the admin-write surface alongside [[users]].

## Notes
- **NEVER call** — submitting a password to a live prod auth endpoint. On the RECIPE skip-list.
- It only verifies; it does not itself mutate data. The actual mutation is the downstream `save-targets/` call (also skip-listed).
- `API` on the Sales page is set to `/realise`, so the full path is `/realise/api/verify-pin/`.
