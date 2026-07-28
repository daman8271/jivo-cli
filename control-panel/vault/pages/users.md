---
title: User Management
route: /users/
type: page
endpoints: [users, verify-pin]
tags: [jivo, control-panel, admin]
---
# User Management

## Purpose
The **Admin** console for creating and managing Control-Panel logins and, crucially, **granting per-report access** — all without touching Django admin. An admin (staff / superuser) uses this page to add a user, set their password, pick a **Realise role**, and tick exactly which report pages and modules that user may see. Changes take effect on the user's next page load. This is the app's home-grown RBAC surface; the permission groups it toggles are the same `*_viewer` groups that gate every other page in the Control Panel.

Sidebar location: **Admin → Users**. Only visible/usable to staff or superusers.

## What it shows
- **Hero header** — "User Management", subtitle "Create users and grant access per report — no Django admin needed."
- **Create-new-user card** (`#umCreate`) — dashed card with a blank editable body + **Create user** button.
- **User list** (`#umList`) — one card per existing user, each with:
  - Username + optional full name in the title row.
  - **Badges**: `Superuser` (red), `Staff` (blue), `Inactive` (grey), `You` (green, on the logged-in admin's own card).
  - The same editable body (name / email / password / realise role / active flag / permission checkboxes) — for users the current admin is allowed to edit.
  - **Save** and, for anyone but yourself, **Delete** buttons with an inline status line.

Editable body fields (shared by create + edit, built by `bodyHTML()`):
- **Username** (create only), **Full name** (`first_name`), **Email**, **Password** (`New password (blank = keep)` when editing, required when creating).
- **Realise role** — dropdown from the catalog (see below).
- **Active (can log in)** checkbox (`is_active`).
- **Staff / Superuser** checkboxes — rendered **only if the current admin is a superuser** (`IS_SUPER`); the logged-in `preshit` is staff-but-not-superuser, so these are hidden and staff cannot edit superuser accounts (read-only notice shown instead).
- **Report pages** grid — one checkbox per page permission group.
- **Modules** grid — one checkbox per module permission group.

## Data sources
- The page is **server-rendered with data embedded**, not fetched: two inline JSON `<script>` blobs seed the UI:
  - `#um-users` — array of existing users (id, username, first_name, email, is_active, is_staff, is_superuser, realise_role, groups[]).
  - `#um-catalog` — the option catalog: `realise_roles`, `page_perms`, `module_perms`.
- [[users]] — `POST /api/users/save/` — create/update a user (WRITE — document only, never called).
- [[users]] — `POST /api/users/delete/` — delete a user (WRITE — document only, never called).
- [[verify-pin]] — `POST /realise/api/verify-pin/` — admin password re-auth gate (used on the Sales page before editing targets, not on this page directly, but part of the same admin-write flow; WRITE/OTP — document only).

## Key fields & columns
**Realise roles** (`realise_role`, single-select — the customer's tier of Realise access):
| value | label |
|---|---|
| `` (empty) | No Realise access |
| `realise_premium` | Realise — Premium (viewer) |
| `realise_commodity` | Realise — Commodity (viewer) |
| `realise_admin` | Realise — Admin (full + can edit targets) |

**Report-page permissions** (`page_perms` → `groups[]`, multi-select). Each maps a `*_viewer` group to a report page:
`customer_aging_viewer` → Customer Aging · `oih_vs_stock_viewer` → OIH vs Stock · `compare_sales_viewer` → Compare Sales · `sales_cn_viewer` → Sales vs Credit Notes · `hidden_sales_viewer` → Hidden Customer Sales · `customer_master_viewer` → Customer Master · `sales_flow_viewer` → Sales Document Flow · `claims_viewer` → Claims · `required_credit_viewer` → Required Credit Limit · `open_payments_viewer` → Open Payments · `dispatch_details_viewer` → Dispatch Details · `realise_calculator_viewer` → Realise Calculator · `reconciliation_viewer` → Wellness–Mart Reconciliation · `stock_viewer` → Stock Available · `production_viewer` → Production Plan · `daily_production_viewer` → Daily Production Transaction.

**Module permissions** (`module_perms` → `groups[]`, coarser than pages):
`inventory_viewer` → Inventory · `sales_viewer` → Sales · `expenses_viewer` → Expenses · `salaries_viewer` → Salaries · `cogs_viewer` → COGS (the OTP-gated COGS module — see [[cogs]]).

**Account flags**: `is_active` (can log in), `is_staff` (can manage users), `is_superuser` (full access, edits other superusers). The logged-in admin `preshit` = staff, not superuser.

## Notes / gotchas
- **Client-side authorisation is advisory** — the JS hides Staff/Superuser toggles and blocks editing superusers when `IS_SUPER` is false, but the real enforcement is server-side in the save/delete endpoints (which are not probed here).
- **`groups` is the union** of ticked page-perms + module-perms; the payload sends the full desired `groups[]` list, so unticking removes a group.
- **You can't delete yourself** — the Delete button is suppressed on the card whose `id === SELF_ID` (12).
- **CSRF** — save/delete read the token from `<meta name="csrf-token">` and send it as `X-CSRFToken`; body is JSON.
- **verify-pin is a password re-auth, not a numeric PIN** — despite the name and the `{pin:...}` body, the value submitted is the admin's account **password**; the server responds `{status:'ok', verified:true|false}`. It gates the "Update Targets" admin action on the Sales dashboard. See [[verify-pin]].
- All save/delete/verify-pin calls are **mutating / auth-sensitive and were NOT executed** — documented from page JS only.

## Related
- [[users]] (API) · [[verify-pin]] · [[customer-master]] · [[cogs]]
