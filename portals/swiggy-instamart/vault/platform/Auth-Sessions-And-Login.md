---
title: Auth Sessions And Login
created: 2026-07-30
updated: 2026-07-30
project: jivo-cli
type: reference
tags: [swiggy, instamart, platform, platform]
status: studied
---


# Auth Sessions And Login

> Email-OTP login, the JWT, and the endpoints this study refuses to call.

Authentication runs through Swiggy's **ozone** IdP at
`ozone-idp-brands-im-kba.swiggy.com` for the brand user pool, with
`partner-api.swiggy.com` serving the internal/employee pool. Login is
**passwordless email OTP**; there is no password to hold.

The endpoint family is `createAuthURI` (initiate), `sendVerificationCode` (mails
the OTP), `signInWithOTP`, `signInWithIDP` (SSO), `token/refresh` and `signOut`.
The vendor remote uses `/v2/accounts/sendVerificationCode`.

`GET partner-api.swiggy.com/time` is an unauthenticated server-clock endpoint
that exists because every brand-portal data call is **request-signed** with a
server-synced millisecond timestamp. Full mechanics in [[Auth-and-Access]].

**Endpoints in this section:** 8 (1 read, 7 write/export, 0 unknown/denied).

## API endpoints

### Read surface

| R/W | METHOD | Host · Path | Const | Live status | Purpose evidence |
|---|---|---|---|---|---|
| READ | GET | `partner-api.swiggy.com/time` | `TIME` | **PROVEN LIVE 200** | call site .get() on TIME | live: ['GET'] -> [200], 27B |

### Out of scope (writes / exports) — never exposed in a read-only CLI

| METHOD | Host · Path | Const | Why excluded |
|---|---|---|---|
| POST | `ozone-idp-brands-im-kba.swiggy.com/v1/accounts/createAuthURI` | `initiateLogin` | WRITE — call site .post() on initiateLogin |
| POST | `ozone-idp-brands-im-kba.swiggy.com/v1/accounts/sendVerificationCode` | `sendVerificationCode` | WRITE — call site .post() on sendVerificationCode |
| POST | `ozone-idp-brands-im-kba.swiggy.com/v1/accounts/signInWithIDP` | `signInWithIDP` | WRITE — call site .post() on signInWithIDP |
| POST | `ozone-idp-brands-im-kba.swiggy.com/v1/accounts/signInWithOTP` | `signInWithOTP` | WRITE — call site .post() on signInWithOTP |
| POST | `ozone-idp-brands-im-kba.swiggy.com/v1/accounts/signOut` | `signOut` | WRITE — call site .post() on signOut |
| POST | `ozone-idp-brands-im-kba.swiggy.com/v1/token/refresh` | `refreshToken,vendorRefreshToken` | WRITE — call site .post() on refreshToken |
| POST | `ozone-idp-brands-im-kba.swiggy.com/v2/accounts/sendVerificationCode` | `sendVerificationCode` | WRITE — call site .post() on sendVerificationCode |

### UNKNOWN — documented but DENIED (G1: unknown means denied)

_None in this section._

## Gotchas

- **Every endpoint in this section is a WRITE and none was called.** They mint,
  rotate or destroy a session. `sendVerificationCode` would email a real OTP to a
  real mailbox; `signOut` would log out the human whose session this study
  borrowed; `token/refresh` rotates a **single-use** refresh token and would
  break both JIVO's e-com team's live session and the production keepalive cron.
- `token/refresh` was attempted **123 times by the application itself** during
  the walks and blocked every time, before the socket opened. That block is
  deliberate and was ratified by the lead.
- `/time` is the one read here, and it is the only unauthenticated endpoint in
  the entire study.

## Screenshots (live read-only walk, 2026-07-30)

- `sec-01-login.png`

  ![screenshot](../captures/walk1/sec-01-login.png)
- `sec-03-employee-login.png`

  ![screenshot](../captures/walk1/sec-03-employee-login.png)
- `sec-04-migration-bridge.png`

  ![screenshot](../captures/walk1/sec-04-migration-bridge.png)
- `sec-02-login.png`

  ![screenshot](../captures/walk2/sec-02-login.png)
- `sec-03-employee-login.png`

  ![screenshot](../captures/walk2/sec-03-employee-login.png)
- `sec-04-migration-bridge.png`

  ![screenshot](../captures/walk2/sec-04-migration-bridge.png)

## Connections

- Index & meta: [[00-Swiggy-Instamart-Atlas]] · [[Swiggy-Instamart-Endpoints]] · [[Swiggy-Instamart-Data-Model]] · [[Swiggy-Instamart-Data-Inventory]]
- Auth & scope: [[Auth-and-Access]] · [[Read-Only-Guardrails]] · [[Study-Verification]]
- Routes: [[Swiggy-Instamart-Pages-and-Routes]] · Coverage: [[Swiggy-Instamart-Screenshot-Index]]
- Siblings: [[Purchase-Orders]] · [[PO-Booking-Appointments]] · [[Goods-Received-GRN]] · [[Returns-RTV-and-Purchase-Returns]] · [[Stock-On-Hand-and-Low-Stock]] · [[Availability-and-Fill-Rate]]
