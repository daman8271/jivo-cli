---
title: Users & Access Management
created: 2026-07-24
updated: 2026-07-24
project: jivo-cli
type: reference
tags: [zepto, platform, users-access]
status: studied
---

# Users & Access Management

The **Users & Access Management** section is Zepto's **identity / RBAC surface** for the seller
portal — who inside JIVO can log in, which **role** each user holds, what **modules / actions** a
role unlocks, and the **approval queue** that gates newly-invited or newly-created users before
they get access. For JIVO this is Jivo Wellness Pvt. Ltd. (`manufacturer_id
946950b7-1ce2-4bdf-a7c4-37499e3f5f34`, Manufacturer / STANDARD tier); the captured JWT belongs to
`ecom1@jivo.in` with role **"External Super Ads Admin"** (`roleId
fb6306b3-cbc1-4181-bf21-e4c4cf005385`) — the super-admin who administers other users. It is the
cross-cutting access layer under every other surface: a role here decides whether a user can see
[[Payments]], run [[Vendor-Reports-Queue]], or manage [[Ads-Campaigns-Booking-Keywords]].

The section spans **two parallel RBAC systems** that the micro-frontend stitches together:
- an **auth-backend** access-management system (`auth-backend.zepto.co.in/api/v1/access-management/*`)
  used by the **root-shell / vendor** side — normal-user / super-user / vendor administration and a
  `roles`/`users`/`vendors` triad; and
- an **ads-BFF / vendor-authorize** system on `fcc.zepto.co.in` — the ads remote's
  `ads-bff/api/v1/users*` + `ads-bff/api/v2/user-approvals*` user/approval flows and the vendor
  remote's `vendor/api/v{1,2}/authorize/*` role-config flows (create role, fetch modules per role,
  modify access).

Endpoint contracts below were extracted from the code-split chunks
**`captures/js/vendor/3539.64ab07c46b8741b5.js`** (auth-backend access-management + vendor authorize
const maps), **`captures/js/ads/1183.8940422c8268d8dc.js`** (ads-BFF `_={GET_USERS…}` user +
`user-approvals` maps), and the root-shell **`remoteEntry.js` / `root-shell-main.*.js`**
(super-user, manage-vendors, brand-analytics entity-data, and the vendor-authorize enum) — they are
API-constant + method bindings, **not** live captures except the one probe noted below. One JWT
(header `authorization: <jwt>`, **no** `Bearer` prefix) authenticates both hosts; WAF headers were
not enforced at last capture.

## SPA route(s)

Thirteen routes across the ads, vendor and shell trees mount this access surface:

- `/users` · `/user-management` — user list / management (root-shell).
- `/role-management` — role list / role-config management (root-shell).
- `/vendor/user-management` · `/vendor/role-management` — vendor-lane user & role management.
- `/ads/access-management` · `/ads/access-management/users` · `/ads/access-management/approvers` —
  ads-lane access management (users tab + approver/approvals tab).
- `/ads/user-role-management` — ads-lane user↔role assignment.
- `/sdk/users` — SDK / programmatic user list surface.
- `/notifications/users` — notification-recipient user picker.
- `/verify-user` — invited-user verification landing.
- `/unauthorized-access` — access-denied fallback route.

These pages are rendered by the vendor remote (635), ads remote (632) and the root-shell (631)
against the two backends above.

## Backend host(s)

- **`auth-backend.zepto.co.in`** — identity / access-management system. Path family
  `api/v1/access-management/*` (roles, users, vendors listing reads; normal-user / super-user /
  activate / assign-role / update-vendor writes).
- **`fcc.zepto.co.in`** — two families: `ads-bff/api/v1/users*` + `ads-bff/api/v2/user-approvals*`
  (ads user & approval flows; some paths surface stripped of the `ads-bff` prefix in the const map),
  `brand-analytics-web/api/v1/access-management/user` (entity-data read), and
  `vendor/api/v{1,2}/authorize/*` (role config: get-roles, fetch-modules-per-role, create/modify).

## API endpoints (READ)

`${e}` = a user / role id (path param). Method shown as wired in the chunks: `GET` = confirmed
constant binding; `UNKNOWN` = constant present in the map but the verb was not directly observed in
this chunk — every UNKNOWN row below is a listing / detail / role-config **read** used by a read
view (get-users, fetch-modules, approvals-table, permissions/is-approver, entity-data), so its
effect is a read; verb to confirm on a live capture. Ads-BFF paths are stored in the const map both
with and without the `ads-bff/` prefix (e.g. `GET_USER_ROLES` appears as both
`ads-bff/api/v1/users/child-roles` and `/api/v1/users/child-roles`) — the host-relative path is
shown.

| METHOD | Path | Purpose | Read/Write |
|---|---|---|---|
| GET | `auth-backend · /api/v1/access-management/roles` | Access-management role list — `GET_ROLES_LIST`; probed → **401 Token expired** (documented, expired-token) | READ |
| GET | `auth-backend · /api/v1/access-management/users` | Access-management user list (user-management grid) — `GET_USERS_LIST` | READ |
| GET | `auth-backend · /api/v1/access-management/vendors` | Manage-vendors list (root-shell) — `GET_MANAGE_VENDORS_LIST` | READ |
| UNKNOWN | `fcc · /brand-analytics-web/api/v1/access-management/user` | Current-entity / user context data — `GET_ENTITY_DATA` (brand-analytics-web) | READ (verb to confirm) |
| UNKNOWN | `fcc · /api/v1/access-management/user` | User / entity context read (same `GET_ENTITY_DATA` const, host-relative fragment) | READ (verb to confirm) |
| GET | `fcc · /api/v1/users/child-roles` | Child roles assignable to a user — `GET_USER_ROLES` (ads-bff) | READ |
| UNKNOWN | `fcc · /api/v1/users` | Ads user list — `GET_USERS` (ads-bff) | READ (verb to confirm) |
| UNKNOWN | `fcc · /api/v1/users/permissions` | Is-user-approver / permission check — `GET_IS_USER_APPROVER` (ads-bff) | READ (verb to confirm) |
| UNKNOWN | `fcc · /api/v2/user-approvals` | User-approvals table data (approvers tab) — `APPROVERS_TABLE_DATA` (ads-bff) | READ (verb to confirm) |
| UNKNOWN | `fcc · /api/v2/user-approvals/${e}/details` | Single user-approval overview / detail — `getOverviewApi` (ads-bff) | READ (verb to confirm) |
| UNKNOWN | `fcc · /api/v1/authorize/get-roles` | Vendor-authorize role list (host-relative fragment) — `GET_ALL_ROLES` | READ (verb to confirm) |
| GET | `fcc · /vendor/api/v1/authorize/get-roles` | Vendor-authorize role list — `GET_ALL_ROLES` | READ |
| UNKNOWN | `fcc · /api/v1/authorize/fetch-all-modules-for-an-application-and-role` | Modules/actions unlocked by a role (host-relative fragment) — `GET_ALL_MODULES_BASED_ON_ROLE` | READ (verb to confirm) |
| GET | `fcc · /vendor/api/v1/authorize/fetch-all-modules-for-an-application-and-role` | Modules/actions unlocked by a role — `GET_ALL_MODULES_BASED_ON_ROLE` | READ |
| UNKNOWN | `fcc · /api/v2/authorize/fetch-all-modules-for-an-application` | Full role-config module tree for the application (host-relative fragment) — `GET_ROLE_CONFIG` | READ (verb to confirm) |
| GET | `fcc · /vendor/api/v2/authorize/fetch-all-modules-for-an-application` | Full role-config module tree for the application — `GET_ROLE_CONFIG` | READ |

## Out of scope (writes) — never expose in a read-only CLI

| METHOD | Path | Purpose | Why held out |
|---|---|---|---|
| UNKNOWN (write) | `auth-backend · /api/v1/access-management/activate-vendor` | **Activate** a user/vendor — `ACTIVATE_USER` | Mutates user/vendor state. WRITE. |
| PUT | `auth-backend · /api/v1/access-management/assign-role` | **Edit user** / assign a role — `EDIT_USER` | Changes a user's role. WRITE. |
| POST | `auth-backend · /api/v1/access-management/normal-user` | **Add** a normal user — `ADD_NEW_USER` (also referenced as `W_USER`) | Creates a user. WRITE. |
| POST | `auth-backend · /api/v1/access-management/super-user` | **Create** a super-user — `CREATE_SUPER_USER` (root-shell) | Creates a privileged user. WRITE. |
| PUT | `auth-backend · /api/v1/access-management/update-vendor` | **Update** vendor record — `UPDATE_VENDOR` | Mutates vendor record. WRITE. |
| POST | `fcc · /api/v1/authorize/create/role` | **Create** a role (host-relative fragment) — `CREATE_ROLE` | Creates a role. WRITE. |
| POST | `fcc · /vendor/api/v1/authorize/create/role` | **Create** a role — `CREATE_ROLE` | Creates a role. WRITE. |
| UNKNOWN (write) | `fcc · /api/v1/authorize/modify-access-for-modules-and-actions` | **Modify** module/action access (host-relative fragment) — `MODIFY_ACCESS_FOR_MODULES_AND_ACTIONS` | Changes role permissions. WRITE. |
| POST | `fcc · /vendor/api/v1/authorize/modify-access-for-modules-and-actions` | **Modify** module/action access — `MODIFY_ACCESS_FOR_MODULES_AND_ACTIONS` | Changes role permissions. WRITE. |
| UNKNOWN (write) | `fcc · /api/v1/users/access` | **Grant access** to a user — `GRANT_ACCESS` (ads-bff) | Grants access. WRITE. |
| UNKNOWN (write) | `fcc · /api/v1/users/${e}/access` | **Update access** for a user — `UPDATE_ACCESS` (ads-bff) | Mutates user access. WRITE. |
| POST | `fcc · /api/v1/users/${e}/approve` | **Approve** a user — `APPROVE_USER` (ads-bff) | Approves/grants a user. WRITE. |
| POST | `fcc · /api/v1/users/${e}/reinvite` | **Re-invite** a user — `RE_INVITE_USER` (ads-bff) | Sends invite / mutates state. WRITE. |
| UNKNOWN (write) | `fcc · /api/v2/users/access` | **Create** a user — `CREATE_USER` (ads-bff v2) | Creates a user. WRITE. |
| POST | `fcc · /api/v2/users/${e}/sync` | **Sync** a user — `getSyncApi` (ads-bff v2) | Triggers a sync side-effect. WRITE. |
| POST | `fcc · /api/v2/user-approvals/${e}/approve` | **Approve** a user-approval — `getApproverApi` (ads-bff v2) | Approves a pending user. WRITE. |
| POST | `fcc · /api/v2/user-approvals/${e}/reject` | **Reject** a user-approval — `getRejectedApi` (ads-bff v2) | Rejects a pending user. WRITE. |

DOCUMENTED-FROM-BUNDLE ONLY. A strict read-only CLI must never call any of these. Sibling
disable/sign-out consts seen in the *same* maps but owned by [[Auth-Identity]] (held out here, noted
for trace-back): `DISABLE_USER` (`vendor/api/v1/auth/remove-user-application-access`),
`SET_IMPERSONATION` (`api/v1/commons/impersonation`), and `sign-out`
(`vendor/api/v1/auth/sign-out`) — all mutating / session verbs.

## Live probe (evidence)

- **1 probe fired, read-only GET, then halted** (per the guardrails, stop on first 401/403/429).
  `GET https://auth-backend.zepto.co.in/api/v1/access-management/roles` (const `GET_ROLES_LIST`, an
  unambiguous pure-GET role-list read) with the captured JWT returned
  **`HTTP 401 {"code":401,"message":"Token expired"}`** — the token (`sub
  5116e7a0-cc01-4b7d-b098-810cb32dee02`, `emailId ecom1@jivo.in`, `iat 1783887610`, `exp 1783967399`
  = 2026-07-13 18:29:59 UTC) had lapsed ~11 days before this run (2026-07-24). No 2xx, so **nothing
  was upgraded to PROVEN**; all endpoints remain **documented (not probed)**. Transcript:
  `captures/platform/users-access-probes.txt`.
- **Auth/base confirmed** by the proven sibling flows on `fcc.zepto.co.in`: SALES/INVENTORY
  (`fcc /api/v1/reports*`) and ads (`fcc /ads-bff/api/v1`) work with the identical
  `authorization: <jwt>` header (no `Bearer`), `origin/referer https://brands.zepto.co.in`.
  `auth-backend.zepto.co.in` accepts the same JWT (it 401'd on *expiry*, not on a WAF/challenge).
  Re-run these probes with a fresh token to lock down response shapes.
- **Response shapes:** to confirm via live read-only capture. Expected top-level keys (from grid /
  role-config usage): `access-management/roles` → role array; `access-management/users` /
  `access-management/vendors` → paged user/vendor rows + total; `users/child-roles` → assignable
  role list; `authorize/get-roles` → role list; `authorize/fetch-all-modules-*` → module/action
  tree per role; `user-approvals` → paged approval rows; `users/permissions` → is-approver boolean;
  `access-management/user` (`GET_ENTITY_DATA`) → entity/user context object.

## What a READ-ONLY CLI would expose (candidate commands)

Strictly consuming existing data (no create / approve / assign / grant / modify / sync / reinvite):

- `zepto users list` → `GET /api/v1/access-management/users` (auth-backend);
  `zepto users ads-list` → `GET /api/v1/users` (ads-bff). Pure READ.
- `zepto roles list` → `GET /api/v1/access-management/roles`;
  `zepto roles authorize-list` → `/vendor/api/v1/authorize/get-roles`;
  `zepto users child-roles` → `/api/v1/users/child-roles`. Pure READ.
- `zepto roles modules --role <id>` → `/vendor/api/v1/authorize/fetch-all-modules-for-an-application-and-role`;
  `zepto roles config` → `/vendor/api/v2/authorize/fetch-all-modules-for-an-application`. Pure READ.
- `zepto vendors list` → `GET /api/v1/access-management/vendors`;
  `zepto users entity` → `/brand-analytics-web/api/v1/access-management/user`. Pure READ.
- `zepto users approvals [--details <id>]` → `/api/v2/user-approvals` (+ `/${id}/details`);
  `zepto users is-approver` → `/api/v1/users/permissions`. Pure READ.
- **Excluded:** every create / activate / assign-role / grant-access / update-access / approve /
  reject / reinvite / sync / modify-access verb, plus disable-user / impersonation / sign-out — all
  writes / session mutations.

## Connections

- Index & guardrails: [[00-Zepto-Atlas]] · [[Zepto-Endpoints]] · [[Auth-and-Access]] ·
  [[Read-Only-Guardrails]]
- **Tightest siblings** — the identity lane: [[Auth-Identity]] (login / MFA / sign-out / get-user-by-token
  session layer this RBAC sits on) and [[KYC-Onboarding]] (VMS vendor onboarding that provisions the
  vendors listed here).
- Access controls every other surface: a role here gates [[Payments]] · [[Vendor-Reports-Queue]] ·
  [[Subscription-Billing]] on the platform/vendor side and [[Ads-Campaigns-Booking-Keywords]] · [[Ads-Billing-Wallet]]
  on the ads side (the ads-BFF user-approvals flow is the ads-lane half of this section).
- Shared commons (impersonation, vendor search) it references live in [[Platform-Common]].
