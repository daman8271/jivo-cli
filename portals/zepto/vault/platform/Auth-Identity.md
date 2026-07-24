---
title: Auth & Identity
created: 2026-07-24
updated: 2026-07-24
project: jivo-cli
type: reference
tags: [zepto, platform, auth-identity]
status: studied
---

# Auth & Identity

The **Auth & Identity** section is the Zepto seller portal's **login, session and
current-user surface** — how a JIVO operator signs in, resolves their own profile
from the bearer token, verifies an invited user, resets a forgotten password, runs
the MFA (OTP) challenge, and signs out. It is the root-shell gate that every other
lane sits behind: it mints the single JWT (header `authorization: <jwt>`, **no**
`Bearer` prefix) that then authenticates the vendor / ads / finance backends. For
JIVO this is Jivo Wellness Pvt. Ltd. (`manufacturer_id
946950b7-1ce2-4bdf-a7c4-37499e3f5f34`, Manufacturer / STANDARD tier); the captured
session is `ecom1@jivo.in`, role **"External Super Ads Admin"** (JWT `sub`/`userId`
`5116e7a0-cc01-4b7d-b098-810cb32dee02`, `applicationId d0cd4873-…`, `category
External`).

The endpoint contracts below were extracted from the **root-shell** and **vendor**
micro-frontend chunks — the auth-constant maps in
`captures/js/root-shell/root-shell-main.8a3af4e6aebe630f.js`,
`captures/js/vendor/3539.64ab07c46b8741b5.js`, and the shared `remoteEntry.js`
(consts `s`/`r`/`o`/`l`/`E`/`c`/`d` = the `api/v1/auth/*` identity-provider set, and
`f`/`p`/`h`/`_` = the `vendor/api/v1/auth/*` session set) — **not** live captures
except where a probe is noted. Two hosts serve this surface: the identity provider
**`auth-backend.zepto.co.in`** (`api/v1/auth/*` — sign-in, invite, password, code)
and the vendor session layer **`fcc.zepto.co.in`** (`vendor/api/v1/auth/*` —
current-user profile, MFA, sign-out). WAF headers were not enforced at last capture.

**Almost all of this section is WRITE.** Auth is a mutation surface by nature —
signing in mints a session, verifying an invite / resetting a password / running an
OTP challenge / signing out all change server-side state. Only the two
**current-user / by-code lookups** are reads. Everything else is documented from the
bundle and held out of scope.

## SPA route(s)

- `/authentication` — the root-shell authentication container (login form, MFA
  challenge, forgot-password / reset-password, invited-user verification).
- `/login` — the login entry route.

Both are served by the **root-shell** remote (631) before any lane loads; the
current-user profile fetch is then reused across the vendor remote (635) shell.

## Backend host(s)

- **`auth-backend.zepto.co.in`** — identity / access-management provider. Path
  family `api/v1/auth/*`: `sign-in`, `google/sign-in`, `verify-invited-user`,
  `forgot-password-invited`, `reset-password`, `resend-code`, `reinvite-user`,
  `get-user-by-code`. This is where the JWT is minted.
- **`fcc.zepto.co.in`** — vendor session layer (same host the proven SALES /
  INVENTORY / ads pulls use). Path family `vendor/api/v1/auth/*` (plus bare
  `api/v1/auth/*` profile variant): `get-user-by-token` (current-user profile),
  `validate-mfa-otp`, `resend-mfa-otp`, `sign-out`, `remove-user-application-access`.

## API endpoints (READ)

The only pure reads in this section resolve **who the caller is**. Method shown as
wired in the chunk: `GET` = confirmed constant binding; `UNKNOWN` = constant present
but the verb was not directly observed in this chunk (these are current-user/by-code
lookups used by read views, so their effect is a read — verb to confirm on a live
capture).

| METHOD | Path | Purpose | Read/Write |
|---|---|---|---|
| GET | `/vendor/api/v1/auth/get-user-by-token` | Current authenticated user's profile from the bearer JWT — `GET_USER_PROFILE` (userId, emailId, roleName, applicationId, modules/permissions) | READ · probed → **401 Token expired** (documented, expired-token) |
| UNKNOWN | `/api/v1/auth/get-user-by-token` | Bare-path profile-by-token variant on `fcc` — same `GET_USER_PROFILE` const value used by the shell | READ (verb to confirm) |
| GET | `/api/v1/auth/get-user-by-code` | Look up an invited/reset user by a one-time code (pre-login; feeds verify-invited / reset-password screens) — const `c`/`d` on `auth-backend` | READ |

**Host note.** The bare `fcc /api/v1/auth/get-user-by-token` and the
`/vendor/`-prefixed one are the **same** `GET_USER_PROFILE` constant (`"vendor/api/v1/auth/get-user-by-token"`);
the shell resolves it against `fcc.zepto.co.in`. `get-user-by-code` lives on the
identity provider `auth-backend.zepto.co.in`.

## Out of scope (writes) — never expose in a read-only CLI

DOCUMENTED-FROM-BUNDLE ONLY. A strict read-only study must never call any of these —
every one mints/ends a session, mutates a user, or fires an OTP / email.

| METHOD | Path | Purpose | Why held out |
|---|---|---|---|
| POST | `auth-backend /api/v1/auth/sign-in` | Password sign-in — mints the session JWT (const `i`/`r`) | Creates a session. WRITE. |
| POST | `auth-backend /api/v1/auth/google/sign-in` | Google SSO sign-in — mints the session JWT (const `l`) | Creates a session. WRITE. |
| POST | `auth-backend /api/v1/auth/verify-invited-user` | Verify + activate an invited user (const `o`/`s`) | Mutates user state. WRITE. |
| POST | `auth-backend /api/v1/auth/forgot-password-invited` | Start forgot-password for an invited user (const `o`/`s`) | Triggers reset flow / email. WRITE. |
| POST | `auth-backend /api/v1/auth/reset-password` | Set a new password (const `c`/`l`) | Mutates credentials. WRITE. |
| POST | `auth-backend /api/v1/auth/resend-code` | Resend the verification code (const `E`/`u`) | Sends a code. WRITE. |
| POST | `auth-backend /api/v1/auth/reinvite-user` | Re-invite / resend an invite to a user — `RESEND_INVITE` | Sends an invite email. WRITE. |
| POST | `fcc /vendor/api/v1/auth/validate-mfa-otp` | Validate the MFA OTP challenge (const `p`) | OTP verification / session step-up. WRITE. |
| UNKNOWN (write) | `fcc /api/v1/auth/validate-mfa-otp/` | MFA OTP validate, bare-path trailing-slash variant | Contains `otp`. WRITE. |
| UNKNOWN (write) | `fcc /vendor/api/v1/auth/validate-mfa-otp/` | MFA OTP validate, trailing-slash variant (const `p`) | Contains `otp`. WRITE. |
| POST | `fcc /vendor/api/v1/auth/resend-mfa-otp` | Resend the MFA OTP (const `_`) | Sends an OTP. WRITE. |
| UNKNOWN (write) | `fcc /api/v1/auth/resend-mfa-otp/` | Resend MFA OTP, bare-path variant | Contains `otp`. WRITE. |
| UNKNOWN (write) | `fcc /vendor/api/v1/auth/resend-mfa-otp/` | Resend MFA OTP, trailing-slash variant (const `h`) | Contains `otp`. WRITE. |
| POST | `fcc /vendor/api/v1/auth/sign-out` | End the session (const `f`/`_`) | Destroys the session. WRITE. |
| UNKNOWN (write) | `fcc /api/v1/auth/sign-out` | Sign-out, bare-path variant | `sign-out`. WRITE. |
| UNKNOWN (write) | `fcc /vendor/api/v1/auth/remove-user-application-access` | Revoke a user's application access — `DISABLE_USER` | Mutates access grants. WRITE. |

Adjacent access-management verbs seen in the **same** const maps but owned by the
access-management surface (held out of this section, noted for trace-back):
`ADD_NEW_USER` (`api/v1/access-management/normal-user`), `GET_ROLES_LIST`
(`api/v1/access-management/roles`), `UPDATE_VENDOR` (`api/v1/access-management/update-vendor`),
`UPDATE_VENDOR_VMS` (`vms/api/v2/vendor/update`), and the role-config read
`GET_ROLE_CONFIG` (`vendor/api/v2/authorize/fetch-all-modules-for-an-application`) —
all documented under [[Users-Access]] / [[Users-Access]].

## Live probe (evidence)

- **1 probe fired, read-only GET, then halted** (per the guardrails, stop on first
  401/403/429). `GET https://fcc.zepto.co.in/vendor/api/v1/auth/get-user-by-token`
  (const `GET_USER_PROFILE`, the cleanest unambiguous pure-GET current-user read)
  with the captured vendor JWT returned **`HTTP 401 {"code":401,"message":"Token
  expired"}`** — the token (`iat 1783887610`, `exp 1783967399` = 2026-07-13 18:29:59
  UTC) had lapsed ~11 days before this run (2026-07-24). No 2xx, so **nothing was
  upgraded to PROVEN**; all endpoints remain **documented (not probed)**. Transcript:
  `captures/platform/auth-identity-probes.txt`.
- **Auth/base confirmed** by the proven sibling flows on the same host: SALES /
  INVENTORY (`fcc /api/v1/reports*`) and ads (`fcc /ads-bff/api/v1`) work with the
  identical `authorization: <jwt>` header (no `Bearer`), origin/referer
  `https://brands.zepto.co.in`. Re-run this probe with a fresh token to lock down the
  profile response shape.
- **Response shapes:** to confirm via live read-only capture. Expected top-level keys
  (from the decoded JWT + shell usage): `get-user-by-token` → the user profile —
  `userId`, `emailId`, `roleName`/`roleId`, `applicationId`, `category`, and a
  module/permission list; `get-user-by-code` → a minimal invited-user record keyed by
  the one-time code.

## What a READ-ONLY CLI would expose (candidate commands)

Strictly consuming existing data (no sign-in, no sign-out, no OTP, no invite/reset):

- `zepto whoami` → `GET /vendor/api/v1/auth/get-user-by-token` (`GET_USER_PROFILE`) —
  resolve the current session's user/role/application from the configured JWT. Pure
  READ. (This is the natural `doctor`/identity check for the whole stack — every
  other lane depends on the same token.)
- `zepto auth user-by-code <code>` → `GET /api/v1/auth/get-user-by-code` — pre-login
  lookup of an invited/reset user by one-time code. Pure READ (rarely needed; requires
  a valid code).
- **Excluded:** sign-in / google-sign-in (mint session), verify-invited-user,
  forgot-password / reset-password, resend-code, reinvite-user, validate-mfa-otp,
  resend-mfa-otp, sign-out, remove-user-application-access — all writes / OTP / email
  / session verbs. The CLI must **consume** a token obtained out-of-band, never mint
  or end one.

## Connections

- Index & guardrails: [[00-Zepto-Atlas]] · [[Zepto-Endpoints]] · [[Auth-and-Access]] ·
  [[Read-Only-Guardrails]]
- **Tightest siblings** — this note is the login/session gate; the user/role
  administration behind the same const maps lives in [[Users-Access]] and
  [[Users-Access]] (add/disable user, roles list, role-config modules).
- The JWT minted here authenticates every lane: the vendor money/goods surfaces
  ([[Payments]] · [[Invoicing]] · [[Purchase-Orders]]) and the ads surfaces all reuse
  the same `authorization: <jwt>` header documented here.
