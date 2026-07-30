# PHASE 0 — Seed intel: Swiggy Instamart (brand/vendor side)

> Mined **read-only** from JIVO's live daily automation at `~/ecomcliauto/` on 2026-07-30.
> Nothing in `~/ecomcliauto/` was modified. **No secrets in this file** — token values,
> refresh tokens and the signing pepper are referenced by *name and shape only*.
> Source-of-truth documents: `~/ecomcliauto/swiggy/VERIFIED-FINDINGS.md`,
> `SESSION-2026-07-08.md`, `STATE-2026-07-14.md`, `~/ecomcliauto/clis/swiggy-instamart-cli/*.go`,
> `~/ecomcliauto/swiggy/signer/*.js`, `~/ecomcliauto/orchestrate/swiggy-*.sh`.

Every row below is marked **VERIFIED** (JIVO's automation proved it live, or I read it
verbatim out of working code) or **INFERRED** (from the brief / a name / a single bundle
string, not proven).

---

## 1. The single most important structural correction to the brief

The brief names `partner.swiggy.com` as "partner portal shell". **That is not the shell
JIVO uses.** The Instamart brand/ads SPA JIVO actually logs into is:

**`https://partner.instamart.in`** — VERIFIED. It is the `origin`/`referer` on every
proven data call (`swiggy-instamart-cli/sign.go:33-34`), the host `browserpull.js`
navigates (`/login`, `/account-select`, `/instamart/sales`, `/instamart/reports`), and the
host `extract-supply-token.js` reads localStorage from.

`partner.swiggy.com` appears **once** in the whole corpus and never in a proven call path.
`partner-api.swiggy.com` is real but the only proven path on it is the unauthenticated
server-clock endpoint `/time`. Treated as: **two distinct portal families under one brand**
— see §2.

## 2. Host map

| Host | Role | Status |
|---|---|---|
| `partner.instamart.in` | **The SPA shell** JIVO logs into (React + webpack). Instamart Ads / Brand Portal. `origin`/`referer` for all data calls. | **VERIFIED** |
| `brand-portal-service-http.swiggy.com` | Brand-portal data API. Proven paths `POST /api/v1/sales/report`, `POST /api/v1/sales/reports`. All calls **request-signed**. | **VERIFIED** |
| `ozone-idp-brands-im-kba.swiggy.com` | Identity provider for the `BRAND` user pool. `POST /v1/token/refresh` (unsigned). JWT `iss` = `…/ozone-idp-im-kba.json` jwks. | **VERIFIED** |
| `partner-api.swiggy.com` | Server clock: `GET /time` → `{"timestamp": <ms>}`. Unauthenticated, unsigned. Needed because signing embeds a server-synced ms timestamp. | **VERIFIED** |
| `instamart-media-assets.swiggy.com` | Static-asset CDN for `brand-portal-client` — webpack chunks + `media_loader.wasm`. **This is the Phase-2 corpus source.** | **VERIFIED** |
| `im-brand-reports-in-west.s3.ap-south-1.amazonaws.com` | Report delivery bucket. `downloadUrl` on a completed report row is a **presigned S3 URL** — auth-free plain `GET`, the presign *is* the auth. | **VERIFIED** (a real 1.4 MB / 20,384-row xlsx was downloaded from it) |
| `brands-im-kba.swiggy.com` | Instamart KBA / brand analytics. Named in the brief; the sibling `ozone-idp-brands-im-kba` is proven, so the family is real. | **INFERRED** |
| `partner.swiggy.com` | Swiggy partner portal shell — a *different* portal family (restaurant/partner side), not the Instamart brand SPA. | **INFERRED** |
| `vendor-media-assets.swiggy.com` | Vendor media assets CDN. One corpus hit. | **INFERRED** |
| `media-assets.swiggy.com` / `dineout-media-assets.swiggy.com` | Generic Swiggy image CDNs referenced by the shared UI layer. | **INFERRED** |
| `brand-svc-bucket.s3.ap-south-1.amazonaws.com` | Brand-service S3 bucket (per brief). Not seen in the seed corpus. | **INFERRED** |
| `npi.swiggy.com` | Unknown Swiggy service, one corpus hit. | **INFERRED** |
| `partner-staging.swiggy.com` | **Staging. Documented, never called.** | **INFERRED** |
| `*.imads.in-west.swig.gy` (internal) | Internal/preprod host variants found in the bundles: `partner-service.imads.in-west.swig.gy`, `brand-portal-service-http.imads.in-west.swig.gy`, `ozone-idp-brands-http.imads.in-west.swig.gy`, `ozone-idp-employees-http.imads.in-west.swig.gy` | **VERIFIED as strings in the bundle**, never called |
| `uat-pimcore.poc.in-west.swig.gy` | UAT Pimcore (catalog/PIM) reference in the bundle. Never called. | **VERIFIED as string** |

⚠️ **Brief drift:** the brief lists the report bucket as `brand-reports-in-west.s3…`. The
bucket actually observed in a live `downloadUrl` is **`im-brand-reports-in-west.s3…`**.
Both are recorded; the `im-` prefixed one is the proven one.

## 3. Known-good endpoints with proven verbs

| Verb | Host · Path | What it does | Read/Write | Status |
|---|---|---|---|---|
| `POST` | `brand-portal-service-http.swiggy.com/api/v1/sales/report` | **GENERATE / enqueue** a sales report. Returns `{operation:{name:"InitiateSalesReport#<acct>#<user>$<ts>",done:false}}` — an ack, *not data*. | **WRITE** (creates a queue row — G2) | VERIFIED |
| `POST` | `brand-portal-service-http.swiggy.com/api/v1/sales/reports` | **LIST/POLL** available reports: `{reports:[{name,downloadUrl,reportStatus,requestedTime,dateRange,brandId,brandIds}],nextPageOffset}`. `downloadUrl` empty until `reportStatus==STATUS_COMPLETED`. | **READ** (POST-to-read) | VERIFIED |
| `GET` | `<downloadUrl>` (presigned S3) | Download an **already-completed** xlsx. No auth, no signature. | **READ_FILE** — the terminal safe action | VERIFIED |
| `POST` | `ozone-idp-brands-im-kba.swiggy.com/v1/token/refresh` | Rotate the access JWT. Body `{user_id, refresh_token:"<counter>.<session_id>", client_id}`. Unsigned. Refresh token is **single-use and rotates**. | **WRITE** (mints/rotates session state — G9 forbids) | VERIFIED |
| `GET` | `partner-api.swiggy.com/time` | `{"timestamp": <ms>}` server clock. Unauthenticated. | **READ** | VERIFIED |
| `POST` | `…/api/v1/advertiser/metrics/report` | Ads metrics report **generate**. | **WRITE** (enqueue) | INFERRED (path string only, host not pinned) |
| `POST` | `…/api/v1/advertiser/metrics/report/list` | Ads metrics report list. | READ (POST-to-read) | INFERRED (path string only) |
| — | `…/api/auth/login` | Login. | **WRITE** — G9: never called | INFERRED |
| — | `…/api/dashboard/table-count/<n>` | Dashboard table count. | READ | INFERRED |
| — | `…/im-vendor/downloads` | Vendor downloads list (stock-on-hand bulk). Named in the brief and in the flow-11 gap note. | READ (probable) | **INFERRED — never captured** |

**Per G2 the report-generate call is a WRITE and is never fired by this study.** JIVO's own
daily automation *does* fire it (that is its job); this study does not.

## 4. The auth mechanism — the most intricate in this wave

**Shape:** `authorization: Bearer <JWT>`. **No cookies** on data calls.

- **JWT issuer:** `ozone-idp-im-kba` (jwks on an `s3.ap-southeast-1` well-known path).
  Claim set observed: `claims, email, exp, iat, iss, jti, session_id, siat, sub, user_pool`.
  `sub` = numeric user id, `user_pool` = `BRAND`. Lifetime ≈ **iat + 5 h**.
- **Login is passwordless email OTP** — sender `no-reply@swiggy.in`, subject
  "Your Login OTP for Swiggy Instamart Ads Portal", 6-digit, 10-minute validity. No captcha.
  "Login via SSO" exists on the form but is unused by JIVO.
- **Refresh** rotates *both* `jti` **and** `session_id` on every call, and the refresh token
  itself is **single-use**. `extract-supply-token.js` documents that the portal page burns a
  new refresh token every ~2 min, so a captured refresh token is dead on arrival — the
  durable path JIVO chose is **re-login**, not refresh.
- **Every `brand-portal-service` data call is request-signed** with two extra headers, or the
  server returns `403 {"code":7,…"Request Forbidden: Please reload the browser"}`:
  - `x-timestamp: <ms>` = server clock from `/time` (`t = Date.now() + timeOffset`)
  - `x-signature: <64 hex>` = `HMAC_SHA256(key = PEPPER ‖ requestId ‖ sessionId,
    msg = JSON.stringify(app_version + timestamp + requestId))`
    - `PEPPER` = a 32-char constant **embedded in `media_loader.wasm`** (a Rust→WASM module
      exporting `getMediaURL`). **Value deliberately not reproduced here (G6);** it lives in
      `~/ecomcliauto/swiggy/signer/`.
    - `requestId` = the `x-client-request-id` header (a UUID minted per request).
    - `sessionId` = the **current access token's `session_id` claim** — and it must be
      **fresh**. A stale `session_id` is exactly what produces "Please reload the browser".
    - `app_version` = `1.4.122` (server-validated: `0.0.28` → `403 App version update required`).
  - JIVO reproduced the app's own live signatures byte-for-byte, so **the wasm is not needed** —
    the signer is pure HMAC in Go/Node/Python.
- **Other required headers on a data call** (verbatim from `client.go`):
  `app_version`, `authorization`, `content-type: application/json`, `origin`,
  `referer`, `user-agent`, `x-client-account-id`, `x-client-id: IM_ADS_EXTERNAL_DASHBOARD`,
  `x-client-request-id`, `x-signature`, `x-timestamp`.
- **`x-client-id` vs refresh `client_id` are different values** — `IM_ADS_EXTERNAL_DASHBOARD`
  for data calls, a UUID oauth client id for `/v1/token/refresh`.

### ⛔ The wall — and why it matters to this study

A **correctly-signed** request 403s with "Please reload the browser" from **all three** of:
pure curl, a signed `fetch` inside a Playwright Chrome page, and **a signed `fetch` typed
into the user's own logged-in browser console** — while the app's own requests on that same
page succeed. So there is a **server-side session-activation layer beyond the signature**.
JIVO's conclusion (2026-07-08, re-affirmed 07-14): Swiggy is the one platform where
anti-automation defeats pure-API, so the daily lane drives the real SPA.

**Consequence for Phase 5 of this study:** even *with* a fresh token, a hand-built signed
`GET`/`POST-to-read` against `brand-portal-service-http` is expected to 403. That is a
documented property of the platform, not a study failure. And per **G4** the answer is *not*
to drive a browser and click — endpoint discovery here is static analysis of the bundles.

### Where the token lands on disk

`~/.config/swiggy-instamart-cli/config.json`, mode `0600`. Keys (names only):
`token`, `refresh_token`, `user_id`, `email`, `refresh_client_id`, `brand_accounts`.
The supply lane adds `supply_token`, `supply_user_id`, `supply_email`,
`supply_refresh_token` (deliberately left empty — renewed by re-login, not refresh).
Browser sessions live in Chrome profiles: `~/.config/swiggy-instamart-cli/chrome-profile`
(sales/tanuj) and `…/chrome-profile-ecom1` (supply/ecom1).

**Live token state, checked 2026-07-30 (value never printed):** the only JWT on disk has
`exp = 2026-07-14T18:14:03Z` — **expired 16 days ago**. There is no valid token.
Per **G9 I do not mint one** → Phase 5 is `BLOCKED_NEEDS_TOKEN`.

In-browser storage keys (non-secret names): `__IM_ADS_ACCESS_TOKEN__`,
`__IM_ADS_REFRESH_TOKEN__`, `__IM_ADS_CURRENT_ACCOUNT_ID__`, `_cltk`.

## 5. Entity / account ids (non-secret session facts, G6-permitted)

Two logins, four brand account ids, one portal.

| Fact | Value | Status |
|---|---|---|
| Login A | `tanuj@jivo.in`, `user_id` **344** — the one the daily lane uses; holds **both** brands via the in-app brand switcher | VERIFIED |
| Login B | `ecom1@jivo.in`, `user_id` **345** — used for the *supply* lane (PO/GRN/SoH); its JWT carries **4** brand account ids with personas `mis_analyst` + `ads_admin` | VERIFIED |
| Parent / `x-client-account-id` (tanuj) | `c9f24655-a984-4b65-a4da-2d5b6461b9ec` | VERIFIED |
| Parent / `x-client-account-id` (ecom1) | `89bafc9c-8a56-4286-94cf-a55ab4e564d3` | VERIFIED |
| **Jivo Wellness** brand (`FILTER_BRAND_ACCOUNT_ID`) | `260921c1-76e7-48ef-9771-82124ebe1fcc` | VERIFIED |
| **Jivo Mart** brand (`FILTER_BRAND_ACCOUNT_ID`) | `e4d59d18-4a2a-4ccb-a03c-2bbdb4474b79` | VERIFIED |
| 4th account id on the ecom1 JWT | `c9f24655-…` (= tanuj's parent) — so the two logins overlap | VERIFIED |

⚠️ **Naming trap:** the on-disk config maps `brand_accounts.mart = c9f24655…`, but
`VERIFIED-FINDINGS` records `c9f24655…` as tanuj's **parent/account** id and Jivo Mart's
brand id as `e4d59d18…`. `brand-check.js` also treats `c9f24655…` as *Wellness*. The three
sources disagree. **Do not trust the `mart`/`wellness` labels in `config.json`** — resolve
by the ids above and re-confirm from a live account list when a token exists.

An earlier note claiming "Mart needs the `ecom1` login" was **explicitly corrected** in the
2026-07-08 session log: both brands live under `tanuj@jivo.in`.

## 6. What JIVO's automation actually pulls today (the 5% baseline)

| Flow | Lane | What | Mechanism |
|---|---|---|---|
| 9 | Sales — **Jivo Mart** | daily sales xlsx → `secondary`/`swiggy` → table `swiggySec` | browser-driven generate → poll → presigned download |
| 10 | Sales — **Jivo Wellness** | same table, brand switched in-app | same |
| 11 | Inventory / Stock-on-Hand | **NOT BUILT** — endpoints never captured | — |
| 12 | Ads summary (2 CSVs) | **NOT BUILT** — endpoints never captured | — |
| 31 / 32 | Supply PO / GRN (`ecom1` login) | supply-lane login + token extract exist; pulls not built | — |

So the whole live automation is **two report downloads a day**, both of the *same* sales
report, into one table. Everything else in the portal is unmapped. Date range = "This Month"
preset; reports auto-expire (24 h per one note, 7 days per another — the 7-day figure is the
later and more tested one); IST day → UTC window `T-1 18:30:00.000Z` → `T 18:29:59.999Z`.

Orchestration (all read-only to me, never executed):
`orchestrate/swiggy-daily.sh` (launchd `com.jivo.swiggy-daily`, 10:20 IST) →
`auth-ensure.sh swiggy` → `swiggy-wire.sh all --real`;
`swiggy-keepalive.sh` every ~4 h (Windows `schtasks`) keeps the Chrome profile session warm
and heals a jammed report queue; `swiggy-supply-login.sh` re-logs the supply lane.
**A lane lock (`.swiggy-lane.lock`) serialises them on one shared Chrome profile.**

### 🚨 G9 operational note

Because a **keepalive** owns that session on a ~4 h cadence and a **lane lock** guards it, I
must not run `browserpull.js autologin`, `swiggy-supply-login.sh`, `check`, or any
`swiggy-*.sh`. Doing so would (a) mint/rotate a session the e-com team and the cron are
sharing, (b) fight the keepalive, and (c) burn a real OTP. **Consume only. This study runs
zero scripts from `~/ecomcliauto/`.**

## 7. Corpus already on disk (Phase-2 head start)

`~/ecomcliauto/swiggy/signer/_assets/` holds a **partial** 2026-07-08 harvest of the
`brand-portal-client` bundle: 5 `bundle_*.js` (~680 KB), 6 `chunk_*.js` (~700 KB, incl.
chunk 993 = the signing orchestrator and chunk 194 = the wasm glue), `media_loader.wasm`
+ its 300 KB `.wat` disassembly, and `sales_page.html` / `now_shell.html` page shells.

That is a *sales-page-only* slice — enough to crack signing, nowhere near the whole SPA.
Phase 2 must harvest the **full** chunk manifest from `instamart-media-assets.swiggy.com`.
Asset hashes rotate; the 07-08 URLs (`4ae21eb99f57c402ef8f.wasm`,
`194.08a5e22e26be79279e5e.js`, `993.f033252d86dd88a70210.js`) are likely stale — re-derive
from the live page shell.

## 8. SPA routes known from the seed (Phase-3 seeds)

`/login` · `/account-select` · `/instamart/sales` · `/instamart/reports` — VERIFIED
(navigated by `browserpull.js` / `brand-check.js`). Four routes out of an unknown total;
Phase 3 must enumerate the router exhaustively from the bundles.

UI facts worth keeping: the login form is `input#email-input` + "Send OTP", then
6× `input[name=otp1..otp6]` + "Login". The reports page has a "Generate Report" `<button>`
whose accessible name is broken (Playwright's `getByRole`/`getByText` both miss it).
**Recorded as documentation only — G4 forbids clicking it, and G2 forbids generating.**

## 9. Credential key names present in the automation env (names only, per METHOD)

`~/ecomcliauto/.env` was **not** read for values. The Swiggy-relevant env names that appear
in the scripts are: `SWIGGY_LOGIN_EMAIL`, `SWIGGY_IMAP_ACCOUNT`, `SWIGGY_PROFILE_DIR`,
`SWIGGY_SIGNER_DIR`, `SWIGGY_SUPPLY_SIGNER_DIR`, `SWIGGY_SUPPLY_PROFILE`, `CHROME_PATH`,
`SWIGGY_TOKEN`, `SWIGGY_REFRESH_TOKEN`, `SWIGGY_USER_ID`, `SWIGGY_EMAIL`,
`SWIGGY_REFRESH_CLIENT_ID`, `SWIGGY_SKIP_GENERATE`, `SWIGGY_NO_HEAL`,
`SWIGGY_LANE_LOCK_HELD`, `SWIGGY_LOCK_WAIT_S`.

## 10. Open questions Phase 2–4 must answer

1. Is the SPA one webpack app or module-federated (like Zepto's 3 remotes)? — the presence of
   a `module-federation.io` string in the corpus is suggestive but unproven.
2. Does the **supply/vendor** surface (POs, GRN, ASN, stock-on-hand, `im-vendor/downloads`)
   live in the *same* SPA under a different route tree, or in a separate app on
   `partner.swiggy.com`? This decides whether the study covers one shell or two.
3. What is `brands-im-kba.swiggy.com` actually serving — the KBA/brand-analytics API?
4. The full report catalogue: JIVO pulls 1 report type (IM sales). How many exist?
5. Are the ads surfaces (`/api/v1/advertiser/metrics/*`) on `brand-portal-service-http` or a
   separate ads host?
