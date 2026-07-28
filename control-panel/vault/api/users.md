---
endpoint: /api/users/save/ + /api/users/delete/
method: POST
auth: session + X-CSRFToken
readonly: false
used_by: [users]
tags: [jivo, api, admin]
---
# `POST /api/users/save/` · `POST /api/users/delete/`

> ⚠️ **WRITE endpoints — mutating admin user CRUD. NOT executed.** Documented from the [[users]] page JS only, per read-only discipline on this live production system.

## Purpose
Top-level admin API behind the [[users]] page. `save/` creates a new user or updates an existing one (identity, password, active flag, Realise role, and the full set of report/module permission groups). `delete/` permanently removes a user. Together they are the app's home-grown RBAC write surface — no Django admin required.

## Request
Both are POST with:
- **Headers:** `Content-Type: application/json`, `X-CSRFToken: <token from <meta name="csrf-token">>`. Session cookie required; server-side checks staff/superuser authority.

### `POST /api/users/save/`
JSON body (collected from the card's `[data-k]` inputs + ticked `[data-perms]` checkboxes):
- `id` — integer, **omitted when creating**, present when editing an existing user.
- `username` — string (create only; required, non-blank).
- `first_name` — string, full name.
- `email` — string.
- `password` — string. Required on create; **blank = keep existing** on edit.
- `realise_role` — string, one of `""` (No Realise access) · `realise_premium` · `realise_commodity` · `realise_admin` (see [[users]]).
- `is_active` — boolean (can log in).
- `is_staff` — boolean, **only sent when the acting admin is a superuser** (can manage users).
- `is_superuser` — boolean, superuser-only (full access).
- `groups` — array of group codenames, the **union** of ticked report-page perms and module perms, e.g. `["customer_master_viewer","compare_sales_viewer","stock_viewer"]`. Sent as the complete desired set (unticking removes a group). Full catalog of valid group values is in [[users]].

Example body (create):
```json
{
  "username": "ravi",
  "first_name": "Ravi Kumar",
  "email": "ravi@example.com",
  "password": "<secret>",
  "realise_role": "realise_commodity",
  "is_active": true,
  "groups": ["customer_master_viewer", "compare_sales_viewer"]
}
```

### `POST /api/users/delete/`
JSON body:
- `id` — integer, the user to delete. (The UI forbids deleting your own id, `SELF_ID=12`.)
```json
{ "id": 15 }
```

## Response
Not probed. From the client handling: a JSON body with `status: "ok"` on success (the page then reloads on create/delete, or shows "Saved ✓" on edit). On failure the body carries `error` (a message string) and the HTTP status is non-2xx; the page shows `res.j.error || 'Failed'`.

## Used by
- [[users]] — Create user (`save/` without `id`), Save (`save/` with `id`), Delete (`delete/`).

## Notes
- **NEVER call these** — user create/update/delete on a live prod system. On the RECIPE skip-list.
- Client-side authorisation (hiding staff/superuser toggles, blocking edits of superusers when the acting admin isn't a superuser) is advisory; real enforcement is server-side.
- Related admin re-auth gate: [[verify-pin]].
