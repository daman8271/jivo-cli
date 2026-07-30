---
title: Auth and Access
portal: Flipkart (Seller Hub + Vendor Hub)
type: meta
read_only: true
created: 2026-07-30
updated: 2026-07-30
---

# Flipkart — Auth & Access map

No token, cookie, JWT, or CSRF **value** appears anywhere in this study (G6). This note records
only mechanisms, key names, and non-secret identity facts.

## Four surfaces, three live auth models

| Surface | Host | Auth mechanism | Refresh | Notes |
|---|---|---|---|---|
| Seller Hub | `seller.flipkart.com` | session **cookie jar** (`T`, `connect.sid`, `sellerId`, `is_login`, `DID`, `nonce`, + `XyZ7pQ9rS2T1uV8wA3bC6dE4fG0h` = CSRF cookie) | fresh login most days (session does not persist) | `GET` needs no CSRF; POSTs need header **`fk-csrf-token`** = the CSRF-cookie value |
| Flipkart Ads / FSN | `seller.flipkart.com/fed-ads` | same jar + CSRF, plus `x-aaccount`/`x-baccount` = sellerId, `x-tenant: SELLER` | same as Seller Hub | FSN download also needs `x-pagecontext: …#csv` |
| Vendor Hub | `vendorhub.flipkart.com` | **`access_token` JWT** cookie (HS256, **24 h** iat→exp) + `_csrf` cookie ↔ `x-csrf-token` header | 24 h; refreshed by the production keepalive on `HO-IT-PC10` | `GET` reads need only the cookie; POSTs need `x-csrf-token`. reCAPTCHA-v2 checkbox on login → pure-curl login impossible |
| Marketplace Seller API | `api.flipkart.net/sellers` | OAuth2 `client_credentials` → `Authorization: Bearer` | per token | **no client id/secret on disk — never used by JIVO** |

## CSRF — solved on both live surfaces

- **Seller Hub:** header `fk-csrf-token` (XHR lowercase) = the `XyZ7pQ9rS2T1uV8wA3bC6dE4fG0h`
  cookie value (mirrors `#seller_session_unique_token` in the authenticated `index.html`).
  Wrong header → `403 EBADCSRFTOKEN`. `GET` bypasses CSRF entirely. (Only matters for writes, which
  this study never fires.)
- **Vendor Hub:** header `x-csrf-token` pairs with the `_csrf` cookie; with it → 200, without → 403.

## G9 — consume a session, never mint one

Flipkart Vendor Hub can enforce single-concurrent-session and its login is reCAPTCHA-gated, so a
fresh login would (a) risk kicking JIVO's e-com team out and (b) be impossible headlessly. This
study therefore **consumed the existing production session** on `HO-IT-PC10` read-only and never
logged in. The two kept-blocks from Amendment-04 — **`/login`/logout** and **`/v1/token/refresh`
(and any rotation endpoint)** — were never touched, as they would break the live session and the
production keepalive cron.

## Session material this session (status only — no values)

| Jar file (on `HO-IT-PC10`) | Surface | State when used |
|---|---|---|
| `C:\jivo\ecom-pipeline\auth\login\out\flipkart-vendor.curl` | Vendor Hub (gurvinder) | **LIVE** — JWT valid to 2026-07-30 06:22 IST; used read-only |
| `…\flipkart-seller.curl` | Seller Hub (ecom8) | **LIVE** — used to seed the read-only browser WALK of Seller Hub (24 pages) + confirmed via `GET reportCategories` 200; POST data-reads fired by the app during the walk, not constructed |
| `…\flipkart-infinite.curl` (ecomcliauto) | Vendor Hub (infinite) | **EXPIRED** ~9 h before use → infinite's 3 vendors documented, not live |
| local Mac `~/ecomcliauto/.../out/*.curl` | all | **EXPIRED** 7–12 days |

Chrome's own cookie DB on that box (`Default\Network\Cookies`) is DPAPI+AES-GCM encrypted; the key
was recoverable but the DB was exclusively locked by 22 running Chrome processes, so the jar files
above (already-decrypted, produced by the production login flow) were used instead. No browser
profile was modified.

## Non-secret identity facts

- **Seller Hub:** `ecom8@jivo.in`, `sellerId=e56b4e65e27e4162`, display "JIVOMART".
- **Vendor Hub gurvinder@jivo.in:** `accountId=ACC20F60245910749BB813F22872E5714426`, tenant `FKI`,
  `retailer=fki`, `iss=retail-vendor-portal`, role Operations Head, 6 vendors (see
  [[Vendor-Users-and-Access]] / [[Flipkart-Data-Inventory]]).
- **Vendor Hub infinite@jivo.in:** `accountId=ACCC6AF17C1930A4F65855A0992EACF02C6`, 3 vendors, roles
  Operations Head + Brand Operations Head.

## Credential key names (names only — G6)
`.env`: `FLIPKART_ECOM8_PASSWORD` (Seller), `FLIPKART_GURVINDER_PASSWORD`,
`FLIPKART_INFINITE_EMAIL`, `FLIPKART_INFINITE_PASSWORD` (Vendor). `pass` store:
`flipkart/gurvinder-password`, `flipkart/ecom8-password`. Absent: `FLIPKART_CLIENT_ID`/`_SECRET`
(confirms the public Seller API is unused).

## Connections
[[00-Flipkart-Atlas]] · [[Read-Only-Guardrails]] · [[Flipkart-Endpoints]] · [[Flipkart-Data-Inventory]]
