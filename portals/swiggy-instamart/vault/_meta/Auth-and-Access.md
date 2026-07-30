---
title: Auth and Access
portal: Swiggy Instamart Brand + Supply Portal
type: meta
created: 2026-07-30
updated: 2026-07-30
project: jivo-cli
tags: [swiggy, instamart, auth, meta]
read_only: true
---

# Auth and Access — Swiggy Instamart

> **No secret value appears in this note or anywhere in `captures/`.** Tokens, refresh
> tokens, the signing pepper, the New Relic key and presigned-S3 signatures are recorded by
> *shape and lifecycle only*. `captures/scrub.py` enforces this over the whole capture tree and
> reported **129 + 14 redactions** on its first two runs. Non-secret session facts (account ids,
> brand ids, login emails, role names) are recorded deliberately — G6 permits those.

This is the most intricate auth model of the three Wave-1 platforms. There are **two portals
behind one login**, **two different auth header schemes**, an **HMAC request signature**, and a
server-side session wall that defeats hand-built requests.

## 1. One login, two portals

`partner.instamart.in` is a single React SPA that is **both** the Brand/Ads portal and the
Supply/Vendor portal. The `/account-select` screen says so in as many words:

> *"Welcome to Swiggy Instamart Partner Portal — Welcome ecom1, You can access both the Brand
> and Supply portal from below."*

⚠️ **Correction to the mission brief.** The brief named `partner.swiggy.com` as the "partner
portal shell". It is not. `partner.swiggy.com` 302-redirects to `/food/` and serves the
**"Swiggy Partner App"** — the restaurant/food partner portal, an unrelated product JIVO has no
account on. VERIFIED live. The brief also named `brands-im-kba.swiggy.com`, which **does not
resolve at all** (NXDOMAIN); the real host is `ozone-idp-brands-im-kba.swiggy.com`, the IdP.

## 2. Login: passwordless email OTP

There is **no password** to hold anywhere.

| Step | Endpoint (on the ozone IdP) | Note |
|---|---|---|
| initiate | `POST /v1/accounts/createAuthURI` | `initiateLogin` |
| send OTP | `POST /v1/accounts/sendVerificationCode` | **mails a real 6-digit OTP.** `/v2/...` for the vendor pool |
| sign in | `POST /v1/accounts/signInWithOTP` | |
| SSO | `POST /v1/accounts/signInWithIDP` | present in the client, unused by JIVO |
| rotate | `POST /v1/token/refresh` | **single-use, rotates on every call** |
| sign out | `POST /v1/accounts/signOut` | would log the human out |

Sender `no-reply@swiggy.in`, subject *"Your Login OTP for Swiggy Instamart Ads Portal"*, 10-minute
validity, no captcha. The login form is `input#email-input` → "Send OTP", then
6 × `input[name=otp1..otp6]` → "Login".

**Every endpoint in this table is a WRITE and this study called none of them.**

## 3. The tokens

- **Access token:** a JWT, sent as `authorization: Bearer <jwt>`. Issuer is the
  `ozone-idp-im-kba` jwks. Claim set observed: `iss, sub, exp, iat, siat, jti, email,
  user_pool, session_id, claims`. `user_pool` = `USER_POOL_BRAND`. Lifetime ≈ **5 hours**.
- **Refresh token:** shape `"<counter>.<session_id>"`. **Single-use** — every refresh rotates
  both `jti` and `session_id`. The portal page burns a fresh one roughly every 2 minutes, which
  is why a captured refresh token is dead on arrival and why JIVO's own supply lane stores
  `supply_refresh_token: ""` deliberately and re-logs-in instead of refreshing.
- **Vendor lane uses a different header.** Calls to `picker.swiggy.com` authenticate with
  **`Abacus-Token: <jwt>`** plus `Content-Type`, *not* `authorization: Bearer`. Same JWT,
  different header name. Missing this is the single easiest way to get a 401 on the supply lane.

### Where the session lives on disk

`~/.config/swiggy-instamart-cli/config.json` (mode `0600`), keys:
`token · refresh_token · user_id · email · refresh_client_id · brand_accounts ·
supply_token · supply_refresh_token · supply_user_id · supply_email · supply_companies`.

Browser sessions live in dedicated Chrome profiles —
`~/.config/swiggy-instamart-cli/chrome-profile` (ads / `tanuj@jivo.in`) and
`chrome-profile-ecom1` (supply / `ecom1@jivo.in`) — with the token in **`localStorage`**, not
cookies. In-browser keys (names only): `__IM_ADS_ACCESS_TOKEN__`, `__IM_ADS_REFRESH_TOKEN__`,
`__IM_ADS_CURRENT_ACCOUNT_ID__`, `__IM_ADS_CURRENT_ACCOUNT_NAME__`, `__IM_VENDOR_BRAND_ID__`,
`__IM_ADS_REDIRECT_URL__`, `__IM_SIDE_PANEL_STATE__`, `__IM_HOST_NOTIFICATION_KEY___`,
`__IM_ADS_UTM_ANALYTICS_PARAMS__`, `_cltk`.

> **Consequence for tooling:** because the session is in `localStorage`, a cookie-jar import
> (`/setup-browser-cookies`) **cannot** authenticate this portal. That is why this study drove a
> copy of a real logged-in Chrome profile instead.

## 4. Request signing — every brand-portal call

Calls to `brand-portal-service-http.swiggy.com` fail with
`403 {"code":7, … "Request Forbidden: Please reload the browser"}` unless two headers are present:

```
x-timestamp : <ms>      = Date.now() + (serverTime - Date.now())
x-signature : <64 hex>  = HMAC_SHA256(
                             key = PEPPER ‖ requestId ‖ sessionId,
                             msg = JSON.stringify(app_version + timestamp + requestId)
                          )
```

- `PEPPER` is a 32-char constant embedded in `media_loader.wasm` (a Rust→WASM module exporting
  `getMediaURL`). **Value deliberately not reproduced here (G6);** it lives in
  `~/ecomcliauto/swiggy/signer/`.
- `requestId` is the `x-client-request-id` header (a per-request UUID).
- `sessionId` is the **current access token's `session_id` claim**, and it must be **fresh** — a
  stale one is exactly what produces "Please reload the browser".
- `app_version` is server-validated. JIVO's prior work proved `1.4.122` accepted and `0.0.28`
  rejected; the **current** shell reports `0.0.34` and a live capture on this account shows
  `app_version: 0.0.32`, so the value has moved and must be read from the live shell rather than
  hardcoded.
- Server clock: `GET https://partner-api.swiggy.com/time` → `{"timestamp": <ms>}`,
  unauthenticated and unsigned. **VERIFIED live this run** (`{"timestamp":1785361562051}`).
- The wasm asset hash rotates: `4ae21eb99f57c402ef8f.wasm` in JIVO's 2026-07-08 capture,
  **`090bc398c70257afc9b6.wasm`** observed loading this run.

### Other required headers on a brand-portal data call

`app_version` · `authorization` · `content-type` · `origin: https://partner.instamart.in` ·
`referer` · `user-agent` · `x-client-account-id` · `x-client-id` · `x-client-request-id` ·
`x-signature` · `x-timestamp`.

⚠️ **`x-client-id` has changed.** JIVO's 2026-07 notes record
`IM_ADS_EXTERNAL_DASHBOARD`; a live capture on this account shows
**`IM_BRAND_PORTAL_EXTERNAL_DASHBOARD`**, and the brandverse remote uses `BRANDVERSE_CLIENT`.
The refresh endpoint takes a *different* `client_id` — an OAuth client UUID, not either of these.

## 5. The session-activation wall (why pure API is blocked)

A **correctly signed** request 403s from all three of: pure curl, a signed `fetch` inside a
Playwright page, and a signed `fetch` typed into the human's own logged-in browser console —
while the app's own requests on that same page succeed. So there is a **server-side
session-activation layer beyond the signature**, which the SPA's own request pipeline satisfies
and a hand-built request does not.

This is why **AMENDMENT-02's "let the app fire its own requests" is not merely safer here — it is
the only method that works at all.** It is also why Phase 5 GET-probing was never going to
upgrade these endpoints and the live walk had to.

## 6. Entities: three accounts, one user

`ecom1@jivo.in` (user id **345**) can select **three** accounts. VERIFIED by clicking each tile
and reading back `__IM_ADS_CURRENT_ACCOUNT_ID__`:

| Selectable account | Account id | brandCompany id | brandAccount id |
|---|---|---|---|
| **Jivo Mart Pvt. Ltd** | `89bafc9c-8a56-4286-94cf-a55ab4e564d3` | `935ac57d898d4c1b3b8ec0001a87d28a44b12928` | `e4d59d18-4a2a-4ccb-a03c-2bbdb4474b79` |
| **Jivo Wellness** | `c9f24655-a984-4b65-a4da-2d5b6461b9ec` | `5ecb3c0025f73c6716097e1a1a6e62390ceb2504` | `260921c1-76e7-48ef-9771-82124ebe1fcc` |
| **Jivo** (brand under Wellness) | `260921c1-76e7-48ef-9771-82124ebe1fcc` | — | brand `1bd421f677aba0b28ef95a6ed80970824cdf83ec` |

`POST /api/v1/account/permissions` → `userType: USER_TYPE_BRAND`, `personas: []`,
`accessibleDomains: ["DOMAIN_ADS","DOMAIN_CATALOG","DOMAIN_PARTNER"]`.

The second login, `tanuj@jivo.in` (user id **344**), is the one JIVO's daily *sales* cron uses.
Its token was expired at every location checked this run.

⚠️ **A naming error in JIVO's own config.** `config.json` maps `brand_accounts.mart →
c9f24655…`, but `c9f24655…` is **Jivo Wellness** live; Jivo Mart is `89bafc9c…`. VERIFIED.
Whether the daily upload therefore mislabels Mart vs Wellness is **INFERRED and needs a human
check** — this study did not trace the upload path.

## 7. Session state at study time, and what this study refused to do

| Location | Login | Token expiry | Valid? |
|---|---|---|---|
| Mac `config.json` | `tanuj@jivo.in` | 2026-07-14T18:14Z | no |
| Mac `chrome-profile` localStorage | `tanuj@jivo.in` | 2026-07-18T19:18Z | no |
| `dev` (HO-IT-PC10) `config.json` `token` | `tanuj@jivo.in` | 2026-07-18T19:08Z | no |
| `dev` `chrome-profile` localStorage | `tanuj@jivo.in` | 2026-07-29T14:29Z | no |
| **`dev` `config.json` `supply_token` + `chrome-profile-ecom1`** | **`ecom1@jivo.in`** | **2026-07-30T01:40Z** | **YES — used** |

Per **G9 this study consumed that session and never minted one.** Concretely:

- It ran against a **copy** of `chrome-profile-ecom1`, never the human's live profile.
- It **blocked `/v1/token/refresh` at the transport layer 123 times.** The app tried to rotate
  the single-use refresh token on almost every page load; letting it through would have
  invalidated the refresh chain held by JIVO's e-com team *and* by the production keepalive cron,
  forcing an OTP re-login. That is a state change, so it was refused. The lead ratified this
  block, and AMENDMENT-04 preserved it explicitly.
- It never ran `browserpull.js autologin`, `swiggy-supply-login.sh`, `auth-ensure.sh` or any
  other script in `~/ecomcliauto/` — those mint sessions and would have collided with the
  4-hourly keepalive and its lane lock.

## Connections

- [[00-Swiggy-Instamart-Atlas]] · [[Read-Only-Guardrails]] · [[Study-Verification]]
- [[Auth-Sessions-And-Login]] — the endpoint table for this section
- [[Accounts-And-Entities]] — the entity graph in detail
- [[Config-And-Feature-Flags]] — what the account is entitled to
- [[Swiggy-Instamart-Endpoints]] · [[Swiggy-Instamart-Data-Inventory]]
