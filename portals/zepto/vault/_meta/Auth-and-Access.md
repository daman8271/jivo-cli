---
title: Zepto Auth & Access
created: 2026-07-24
updated: 2026-07-24
project: jivo-cli
type: reference
tags: [zepto, auth, access, meta]
status: studied
---

# Zepto Auth & Access

The **single source of truth** for how a JIVO operator authenticates to the Zepto
seller portal and which header authorizes which backend. This is the portal-wide auth
map; the section-level login/session mechanics live in [[Auth-Identity]] and the RBAC /
user-administration surface in [[Users-Access]].

## One portal, one micro-frontend, one token

- **Portal:** `brands.zepto.co.in` — a single webpack **module-federation
  micro-frontend**. Three remotes are stitched together at runtime:
  - **root-shell** (build `631`) — the auth gate + host shell (login, MFA,
    forgot/reset, invited-user verify, current-user profile).
  - **vendor** (build `635`) — the vendor money/goods lanes ([[Purchase-Orders]],
    [[Invoicing]], [[Payments]], [[Receivables]], …).
  - **ads** (build `632`) — the ads lanes ([[Ads-Campaigns-Booking-Keywords]],
    [[Ads-Billing-Wallet]], [[Brand-Analytics]], …).
  - Remote manifest at **`/manifest.json`**; each remote loads its own
    `remoteEntry.js`.
- **One JWT authorizes ALL backends.** After login the shell holds a single JWT and
  sends it as the raw **`authorization: <jwt>` header — NO `Bearer` prefix** — to
  every backend below. **WAF headers are NOT enforced** at last capture (the backends
  401'd on token *expiry*, never on a WAF challenge), so no `x-*` WAF/entity headers
  are required beyond `origin`/`referer https://brands.zepto.co.in`.

### Backends the one JWT unlocks

| Host | Role |
|---|---|
| `auth-backend.zepto.co.in` | **Identity provider** — mints the JWT; access-management (roles/users/vendors), subscription, KYC, brands, config |
| `fcc.zepto.co.in` | Vendor reports + `/ads-bff` ads + `vendor/api/v*/auth` session layer + `vendor/api/v*/authorize` role-config |
| `financenew.zepto.co.in` | Finance / receivables / ledger |
| `scpfin.zepto.co.in` | Supply-chain finance |
| `brands-onboarding.zepto.co.in` | Onboarding / KYC |
| `ads-platform.zepto.co.in` | Ads platform |
| `partner.zepto.co.in` | Partner |

## Entity & session facts

- **Entity:** Jivo Wellness Pvt. Ltd. — **Manufacturer, STANDARD** tier.
  `manufacturer_id 946950b7-1ce2-4bdf-a7c4-37499e3f5f34`. Ads
  `brand_id b3550d5d-fc71-47b0-af4f-f221f909b936`.
- **Captured session:** login `ecom1@jivo.in`, JWT `sub`/`userId`
  `5116e7a0-cc01-4b7d-b098-810cb32dee02`, `roleName` **"External Super Ads Admin"**
  (`roleId fb6306b3-cbc1-4181-bf21-e4c4cf005385`), `category External`,
  `applicationId d0cd4873-7cb3-4c7c-9a25-3b109a0d2301`.
- **JWT size:** 731 characters.

## The login flow (email-OTP → JWT)

Two-step **email-OTP** MFA against the identity provider `auth-backend.zepto.co.in`:

1. `POST /api/v1/auth/sign-in?applicationId=d0cd4873-7cb3-4c7c-9a25-3b109a0d2301`
   — validates credentials for `ecom1@jivo.in` and **triggers the OTP email**.
2. `POST /vendor/api/v1/auth/validate-mfa-otp/?applicationId=d0cd4873-7cb3-4c7c-9a25-3b109a0d2301`
   — the `applicationId` is **ALSO required in the request body** (not only the query
   string). On success it returns the **731-char JWT**.

- **NO refresh token.** The session cannot be silently renewed → **re-login daily.**
  The JWT **expires at 23:59:59 IST the same day** it was minted.
- **Single-concurrent-session:** a fresh login **kicks any other human** out of the
  account. But **replaying an already-issued JWT does NOT** invalidate other
  sessions — a read-only crawl that consumes an out-of-band token is safe to run
  alongside a human session as long as it does not re-login.
- **JWT claims** (decoded): `emailId ecom1@jivo.in`, `roleName "External Super Ads
  Admin"`, `sub/userId 5116e7a0-…`, `applicationId d0cd4873-…`, `category External`,
  `iat`/`exp` (same-day IST expiry).

## Unattended login (no browser)

`~/ecomcliauto/orchestrate/zepto-login.sh` runs the whole flow headless: it fires the
`sign-in` call, **reads the OTP out of the `ecom1@jivo.in` mailbox via `himalaya`**,
posts `validate-mfa-otp`, and captures the fresh JWT — no browser, no human. Because
there is no refresh token, this runs **daily** (before the 23:59:59 IST expiry) to keep
a token on hand. A read-only CLI must **consume** the token this script produces; it
must never mint or end a session itself.

## Every auth / identity / access-management endpoint

Extracted from `captures/js/sections.json` + `captures/js/endpoints-raw.json` and the
root-shell / vendor / ads const maps. `READ` rows are pure reads (safe to expose in a
read-only CLI); `WRITE` rows mint/end sessions, mutate users/roles, or fire OTP/email
and are **DOCUMENTED-FROM-BUNDLE ONLY — never call them**. `${e}` = a path-param id.
`METHOD UNKNOWN` = the const is present but the verb was not directly observed in the
chunk (bare-path / trailing-slash duplicate of a sibling row).

### Login / session (identity provider + vendor session layer)

| R/W | METHOD | Host · Path | Const | Purpose |
|---|---|---|---|---|
| WRITE | POST | `auth-backend · /api/v1/auth/sign-in` | `i`/`r` | Password/OTP sign-in — **triggers OTP email**, step 1 of MFA |
| WRITE | POST | `auth-backend · /api/v1/auth/google/sign-in` | `l` | Google SSO sign-in — mints JWT |
| WRITE | POST | `fcc · /vendor/api/v1/auth/validate-mfa-otp` | `p` | Validate MFA OTP — step 2, **mints the JWT** |
| WRITE | UNKNOWN | `fcc · /vendor/api/v1/auth/validate-mfa-otp/` | `p` | MFA validate, trailing-slash variant (contains `otp`) |
| WRITE | UNKNOWN | `fcc · /api/v1/auth/validate-mfa-otp/` | — | MFA validate, bare-path trailing-slash variant |
| WRITE | POST | `fcc · /vendor/api/v1/auth/resend-mfa-otp` | `_` | Resend the MFA OTP |
| WRITE | UNKNOWN | `fcc · /vendor/api/v1/auth/resend-mfa-otp/` | `h` | Resend MFA OTP, trailing-slash variant |
| WRITE | UNKNOWN | `fcc · /api/v1/auth/resend-mfa-otp/` | — | Resend MFA OTP, bare-path variant |
| WRITE | POST | `fcc · /vendor/api/v1/auth/sign-out` | `_`/`f` | End the session |
| WRITE | UNKNOWN | `fcc · /api/v1/auth/sign-out` | — | Sign-out, bare-path variant |
| **READ** | GET | `fcc · /vendor/api/v1/auth/get-user-by-token` | `GET_USER_PROFILE` | **Current user profile from the JWT** — the whoami/doctor read; probed → 401 Token expired |
| READ | UNKNOWN | `fcc · /api/v1/auth/get-user-by-token` | `GET_USER_PROFILE` | Bare-path profile-by-token variant (same const) |

### Invite / password / code (identity provider)

| R/W | METHOD | Host · Path | Const | Purpose |
|---|---|---|---|---|
| WRITE | POST | `auth-backend · /api/v1/auth/verify-invited-user` | `o`/`s` | Verify + activate an invited user |
| WRITE | POST | `auth-backend · /api/v1/auth/forgot-password-invited` | `o`/`s` | Start forgot-password for an invited user |
| WRITE | POST | `auth-backend · /api/v1/auth/reset-password` | `c`/`l` | Set a new password |
| WRITE | POST | `auth-backend · /api/v1/auth/resend-code` | `E`/`u` | Resend the verification code |
| WRITE | POST | `auth-backend · /api/v1/auth/reinvite-user` | `RESEND_INVITE` | Re-invite / resend an invite (email) |
| **READ** | GET | `auth-backend · /api/v1/auth/get-user-by-code` | `c`/`d` | Pre-login lookup of an invited/reset user by one-time code |

### Access-management / RBAC (identity provider + vendor authorize)

| R/W | METHOD | Host · Path | Const | Purpose |
|---|---|---|---|---|
| **READ** | GET | `auth-backend · /api/v1/access-management/roles` | `GET_ROLES_LIST` | Role list; probed → 401 Token expired |
| **READ** | GET | `auth-backend · /api/v1/access-management/users` | `GET_USERS_LIST` | User-management grid |
| **READ** | GET | `auth-backend · /api/v1/access-management/vendors` | `GET_MANAGE_VENDORS_LIST` | Manage-vendors list |
| WRITE | UNKNOWN | `auth-backend · /api/v1/access-management/activate-vendor` | `ACTIVATE_USER` | Activate a user/vendor |
| WRITE | PUT | `auth-backend · /api/v1/access-management/assign-role` | `EDIT_USER` | Edit user / assign a role |
| WRITE | POST | `auth-backend · /api/v1/access-management/normal-user` | `ADD_NEW_USER`/`W_USER` | Add a normal user |
| WRITE | POST | `auth-backend · /api/v1/access-management/super-user` | `CREATE_SUPER_USER` | Create a super-user |
| WRITE | PUT | `auth-backend · /api/v1/access-management/update-vendor` | `UPDATE_VENDOR` | Update a vendor record |
| WRITE | POST | `auth-backend · /api/v1/commons/impersonation` | `SET_IMPERSONATION` | Impersonate another user |
| **READ** | UNKNOWN | `fcc · /brand-analytics-web/api/v1/access-management/user` | `GET_ENTITY_DATA` | Current-entity / user context (web) |
| **READ** | GET | `fcc · /brand-analytics-mobile/api/v1/access-management/user` | `GET_ENTITY_DATA_FOR_MOBILE_APP` | Current-entity context (mobile) |
| **READ** | UNKNOWN | `fcc · /api/v1/access-management/user` | `GET_ENTITY_DATA` | Entity context, host-relative fragment |
| **READ** | GET | `fcc · /api/v1/users/child-roles` | `GET_USER_ROLES` | Child roles assignable to a user (ads-bff) |
| **READ** | UNKNOWN | `fcc · /api/v1/users` | `GET_USERS` | Ads user list (ads-bff) |
| **READ** | UNKNOWN | `fcc · /api/v1/users/permissions` | `GET_IS_USER_APPROVER` | Is-user-approver / permission check |
| **READ** | UNKNOWN | `fcc · /api/v2/user-approvals` | `APPROVERS_TABLE_DATA` | User-approvals table (approvers tab) |
| **READ** | UNKNOWN | `fcc · /api/v2/user-approvals/${e}/details` | `getOverviewApi` | Single user-approval detail |
| **READ** | UNKNOWN | `fcc · /api/v2/users` | `USER_TABLE_DATA` | Ads-BFF v2 user table |
| **READ** | GET | `fcc · /ads-bff/api/v1/users/details` | `GET_BOOKING_USER_DETAILS` | Booking user details (ads) |
| **READ** | GET | `fcc · /ads-bff/api/v1/parent-brand/${e}/users` | — | Users under a parent brand (ads) |
| **READ** | GET | `fcc · /vendor/api/v1/authorize/get-roles` | `GET_ALL_ROLES` | Vendor-authorize role list |
| **READ** | UNKNOWN | `fcc · /api/v1/authorize/get-roles` | `GET_ALL_ROLES` | Role list, host-relative fragment |
| **READ** | GET | `fcc · /vendor/api/v1/authorize/fetch-all-modules-for-an-application-and-role` | `GET_ALL_MODULES_BASED_ON_ROLE` | Modules/actions unlocked by a role |
| **READ** | UNKNOWN | `fcc · /api/v1/authorize/fetch-all-modules-for-an-application-and-role` | `GET_ALL_MODULES_BASED_ON_ROLE` | Same, host-relative fragment |
| **READ** | GET | `fcc · /vendor/api/v2/authorize/fetch-all-modules-for-an-application` | `GET_ROLE_CONFIG` | Full role-config module tree |
| **READ** | UNKNOWN | `fcc · /api/v2/authorize/fetch-all-modules-for-an-application` | `GET_ROLE_CONFIG` | Same, host-relative fragment |
| **READ** | GET | `fcc · /contractservice/api/v1/vendor-contract/users` | `GET_USERS_FOR_ROLE` | Users-for-role (contract service) |
| **READ** | GET | `fcc · /vms/api/v1/admin/lead/get-user-details` | `GET_USER_DETAILS` | Onboarding lead user-details (VMS) |
| WRITE | UNKNOWN | `fcc · /vendor/api/v1/auth/remove-user-application-access` | `DISABLE_USER` | Revoke a user's application access |
| WRITE | POST | `fcc · /vendor/api/v1/authorize/create/role` | `CREATE_ROLE` | Create a role |
| WRITE | POST | `fcc · /api/v1/authorize/create/role` | `CREATE_ROLE` | Create a role, host-relative fragment |
| WRITE | POST | `fcc · /vendor/api/v1/authorize/modify-access-for-modules-and-actions` | `MODIFY_ACCESS_FOR_MODULES_AND_ACTIONS` | Modify module/action access |
| WRITE | UNKNOWN | `fcc · /api/v1/authorize/modify-access-for-modules-and-actions` | `MODIFY_ACCESS_FOR_MODULES_AND_ACTIONS` | Same, host-relative fragment |
| WRITE | UNKNOWN | `fcc · /api/v1/users/access` | `GRANT_ACCESS` | Grant access to a user (ads-bff) |
| WRITE | UNKNOWN | `fcc · /api/v1/users/${e}/access` | `UPDATE_ACCESS` | Update access for a user (ads-bff) |
| WRITE | POST | `fcc · /api/v1/users/${e}/approve` | `APPROVE_USER` | Approve a user (ads-bff) |
| WRITE | POST | `fcc · /api/v1/users/${e}/reinvite` | `RE_INVITE_USER` | Re-invite a user (ads-bff) |
| WRITE | UNKNOWN | `fcc · /api/v2/users/access` | `CREATE_USER` | Create a user (ads-bff v2) |
| WRITE | POST | `fcc · /api/v2/users/${e}/sync` | `getSyncApi` | Sync a user (ads-bff v2) |
| WRITE | POST | `fcc · /ads-bff/api/v2/users/${e}/update` | — | Update an ads user |
| WRITE | POST | `fcc · /ads-bff/api/v2/users/${e}/update/payload` | — | Update-payload for an ads user |
| WRITE | POST | `fcc · /api/v2/user-approvals/${e}/approve` | `getApproverApi` | Approve a pending user-approval |
| WRITE | POST | `fcc · /api/v2/user-approvals/${e}/reject` | `getRejectedApi` | Reject a pending user-approval |

## Live probe (evidence)

- The captured JWT (`iat 1783887610`, `exp 1783967399` = 2026-07-13 18:29:59 UTC) had
  **lapsed ~11 days** before the study run (2026-07-24), so every read-only probe of
  the auth surface returned **`HTTP 401 {"code":401,"message":"Token expired"}`** —
  e.g. `GET fcc /vendor/api/v1/auth/get-user-by-token` and
  `GET auth-backend /api/v1/access-management/roles`. **Nothing was upgraded to
  PROVEN**; all rows remain **documented (not probed)**. Transcripts:
  `captures/platform/auth-identity-probes.txt`,
  `captures/platform/users-access-probes.txt`.
- **The 401 is an expiry, not a WAF/challenge** — the same `authorization: <jwt>`
  header (no `Bearer`) is proven working on the sibling read flows on the same host:
  SALES/INVENTORY (`fcc /api/v1/reports*`) and ads (`fcc /ads-bff/api/v1`). Re-run
  with a fresh token (via `zepto-login.sh`) to lock down every response shape.

## Read-only guardrails (what a CLI may touch)

- **Consume a token, never mint one.** The CLI takes the JWT produced out-of-band by
  `zepto-login.sh`; it must never call `sign-in`, `google/sign-in`, `validate-mfa-otp`,
  `resend-mfa-otp`, or `sign-out`.
- **Safe reads:** `get-user-by-token` (whoami/doctor), `get-user-by-code`, the
  `access-management/{roles,users,vendors,user}` reads, `authorize/get-roles`,
  `authorize/fetch-all-modules-*`, `users/child-roles`, `users/permissions`,
  `user-approvals` (+ `/details`), and the ads/VMS/contract user reads above.
- **Never fire:** any `create`/`add`/`super-user`/`assign-role`/`activate`/
  `update-vendor`/`grant`/`update-access`/`approve`/`reject`/`sync`/`reinvite`/
  `modify-access`/`remove-…-access`/`impersonation` verb, or any login/OTP/sign-out
  verb — all writes / session mutations / OTP-or-email side-effects. See
  [[Read-Only-Guardrails]].

## Connections

- Index & guardrails: [[00-Zepto-Atlas]] · [[Zepto-Endpoints]] · [[Read-Only-Guardrails]]
- **Section detail:** [[Auth-Identity]] (login/MFA/sign-out/get-user-by-token session
  mechanics) · [[Users-Access]] (the full RBAC / user-administration surface).
- The one JWT documented here authenticates every lane: the vendor money/goods surfaces
  ([[Payments]] · [[Invoicing]] · [[Purchase-Orders]] · [[Receivables]]) and the ads
  surfaces ([[Ads-Campaigns-Booking-Keywords]] · [[Ads-Billing-Wallet]] ·
  [[Brand-Analytics]]) all reuse the same `authorization: <jwt>` header.
