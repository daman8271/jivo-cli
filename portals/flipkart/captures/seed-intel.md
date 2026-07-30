---
title: Flipkart — Phase 0 Seed Intel
created: 2026-07-30
project: jivo-cli
type: reference
tags: [flipkart, portal-study, seed, read-only]
phase: 0
---

# PHASE 0 — Flipkart seed intel (mined from `~/ecomcliauto`, read-only)

Everything below was read out of JIVO's **existing live daily automation** at `~/ecomcliauto/`
(never modified — G7). No network call was made in this phase. Each row is marked with how it is
known: **PROVEN-BY-JIVO** = a JIVO engineer replayed it live against the real account and recorded
the result; **DOCUMENTED** = written in a seed doc but not shown replaying; **INFERRED** = my own
reading of the source.

Secrets: no cookie, JWT, password or CSRF value appears in this file or anywhere in this study
(G6). Only key *names*, and non-secret session facts (emails, entity ids, roles, permissions).

---

## 1. The four portals/API surfaces (not two)

The brief names two hostnames. Phase 0 shows Flipkart is actually **four distinct surfaces**, and
the "two API generations" the brief asks about are surfaces 1 and 2 — they are not two generations
of the same API at all, they are a public partner API and an internal SPA API.

| # | Surface | Host | Auth | JIVO login | Status |
|---|---|---|---|---|---|
| 1 | **Seller Hub (internal SPA XHR)** | `seller.flipkart.com` (`/napi/*`, `/fed-ads/*`) | session cookie jar + `fk-csrf-token` on POST | `ecom8@jivo.in` | **CURRENT — this is what JIVO actually uses daily** |
| 2 | **Marketplace Seller API (public partner API)** | `api.flipkart.net/sellers` | OAuth2 `client_credentials` → Bearer | — (no client id/secret on disk) | modelled in `flipkart-seller-api-cli`, **never exercised by JIVO** |
| 3 | **Vendor Hub (1P / Flipkart Grocery)** | `vendorhub.flipkart.com` (`/vendor/*`, `/vendor-p/*`) | `access_token` JWT cookie (24 h) + `_csrf` cookie ↔ `x-csrf-token` header | `gurvinder@jivo.in`, `infinite@jivo.in` | **CURRENT — daily PO + sales/inventory automation** |
| 4 | Flipkart Ads (`fed-ads`) | `seller.flipkart.com/fed-ads/*` | same Seller Hub cookie jar + CSRF, plus `x-aaccount`/`x-baccount`/`x-tenant` | `ecom8@jivo.in` | **CURRENT — daily ads + FSN pulls** |

**Answer to the brief's question "which API generation is current":** the *internal* Seller Hub XHR
API (surface 1 + 4) is what JIVO runs on today; `flipkart-seller-api-cli` (surface 2) is a
speculative build against Flipkart's *published* Marketplace Seller API and has **no credentials on
disk** (`FLIPKART_CLIENT_ID` / `FLIPKART_CLIENT_SECRET` are absent from `~/ecomcliauto/.env`). It is
not a newer generation of the internal API — it is a **different, unused product**. Recorded as
such rather than guessed. (INFERRED from spec + env key inventory; see §7.)

---

## 2. Seller Hub — proven endpoints (`seller.flipkart.com`)

Express app. Unknown routes return `404 text/html` `Cannot GET /<route>` with the `napi` prefix
stripped → **GET is a safe route-existence probe** (PROVEN-BY-JIVO,
`flipkart/auth/VERIFIED-FINDINGS.md`).

### 2a. Report Centre / business reports (`/napi/metrics/bizReport/*`)

| Verb | Path | Params / body | Evidence |
|---|---|---|---|
| GET | `/napi/metrics/bizReport/reportCategories` | — | **PROVEN-BY-JIVO** 200, no CSRF. Live values: `5=Fulfilment Reports`, `10=Invoices`, `9=Listings reports`, `4=Payment Reports`, `11=Tax Reports` |
| GET | `/napi/metrics/bizReport/report/checkReports` | `fileName, from_date, to_date, emailId, sellerId` | **PROVEN-BY-JIVO** 200 (Flow 13 step 2). Returns `{request_id, created_at, downloadLink:{isCSV, link:{url}}}` |
| GET | `/napi/metrics/bizReport/report/generateReport` | same params | **PROVEN-BY-JIVO** 200 — but this is an **ENQUEUE. G2 forbids firing it.** Catalogued only. |
| GET | `/napi/metrics/bizReport/downloadReport/earn_more_report.xlsx` | `token=<request_id>, sellerId` | **PROVEN-BY-JIVO** 200, real 124,669-byte xlsx, 1,553 rows × 16 cols |
| POST | `/napi/metrics/bizReport/report/getReportsV2` | `{reportGroup,reportName,enable,status,page_size,starting_page}` | **PROVEN-BY-JIVO** 200, 4,990 bytes. CSRF required. |
| POST | `/napi/metrics/bizReport/getReportsCount` | `{reportGroup,reportName,enable,status,repeat_*}` | **PROVEN-BY-JIVO** 200 → `{"one_time_reports_count":69,"repeat_report_request_count":3}` |

⚠️ **`generateReport` is a WRITE by G2** ("requesting a report creates a row and burns queue budget").
It is a `GET` in Flipkart's design, which is exactly the G1 trap: *the verb does not tell you the
posture.* Classified `WRITE` and excluded from the CLI.

⚠️ The `downloadLink.link.url` in `checkReports` points at `storage.googleapis.com` and **403s with
`SecurityPolicyViolated — VPC Service Controls`** from any IP outside Flipkart's perimeter — even
JIVO's own. Always use the `/napi/metrics/bizReport/downloadReport/...` proxy. (PROVEN-BY-JIVO,
lesson P1.)

### 2b. GraphQL gateway — the real data core

| Verb | Path | Evidence |
|---|---|---|
| POST | `/napi/graphql` | **PROVEN-BY-JIVO** 200. Headers `content-type: application/json`, `fk-csrf-token`, `operation: query`, `operation-name: <OpName>`. Confirmed op `GetSellerBannerDetails($sellerId,$version)` → `{data:{getSellerBannerDetails:{seller_id,metadata,documents,checklist}}}` |

Every Seller Hub dashboard widget is a GraphQL operation behind this single POST. It is a `POST`,
so **G0 forbids calling it** even though `operation: query` declares it a read — a POST is a POST.
Documented as the extension point; not wired.

### 2c. Other proven Seller Hub routes

| Verb | Path | Evidence |
|---|---|---|
| GET | `/napi/printing/certificate` | **PROVEN-BY-JIVO** 200, real PEM. Good health-check path. |
| GET | `/napi/printing/signature` | DOCUMENTED — found as a bundle literal, sibling of `certificate`; not probed |
| GET | `/napi/sellerBuyerCommunications/getChatKey` | **PROVEN-BY-JIVO** auth accepted (app-level 500 `KEYMAKER_GET_CHAT_KEY`) |
| GET | `/index.html` | **PROVEN-BY-JIVO** — authenticated SPA shell; carries `<input id="seller_session_unique_token">` (the CSRF token) |

### 2d. DISPROVEN — do not re-model these

- `POST /napi/sellerInsights/fetch` → 404 `Cannot POST` (route does not exist)
- `POST /napi/insights/getData` → 404 `Cannot POST`

Growth / "earn more" seller insights are **not** a live JSON API — they are delivered as
downloadable **Analytics Reports** through Report Centre. (PROVEN-BY-JIVO.)

### 2e. Feature surface named in the Seller Hub SPA bundle

From JIVO's bundle inventory (DOCUMENTED, `VERIFIED-FINDINGS.md` §"Feature surface"):
`orders · listings · pricing/PriceManagement · unifiedInventory · inventoryHealth · payments ·
returns · report-centre · promotions · rateCard · lending · sellerBuyerCommunications ·
sellerQnA · multisellerselect · partnerServices · gamification · spf · sir · metrics ·
guidedassistance · printing`

This is the Phase-2/3 target list: 21 named subsystems, of which JIVO's automation touches **3**
(report-centre, fed-ads reports, printing health check).

---

## 3. Flipkart Ads (`seller.flipkart.com/fed-ads/*`)

A *different service* from `/napi`, same cookie jar. Both endpoints below are **POSTs that return a
CSV synchronously** — no generate/poll.

| Verb | Path | Body shape | Evidence |
|---|---|---|---|
| POST | `/fed-ads/downloadV2` | `{dateRange:{startDate,endDate RFC1123-GMT}, timeGranularity:"DAY", requestId:"consolidated-table", isRealTime:true, search:"", filters:{type:["PLA","SELLER_PCA"], marketplace:["FLIPKART","SHOPSY"], budgetType:["DAILY_BUDGET","TOTAL_BUDGET"], budgetRecommended:false, status:null, campaignTags:null}, pagination:{size,number}, sortBy:{}, hashId, fields:[…17…]}` | **PROVEN-BY-JIVO** 200, 23,301-byte CSV, **260 campaign rows** (Flow 14, 2026-07-08) |
| POST | `/fed-ads/download/table` | `{dateRange:{startDate,endDate YYYY-MM-DD}, pageLevelFilter:[], queries:[{query:{filters,group_by,metrics,order_by,type:"TABULAR",view_id:"612"},queryId}], requestId, timeGranularity:"DAY", reportId:"sellerPlaConsolidatedFSNReport"}` | **PROVEN-BY-JIVO** 200, 46,140-byte CSV, **269 product rows** (Flow 15) |

Required headers on both: `Content-Type: application/json`, `fk-csrf-token`, `x-aaccount: <sellerId>`,
`x-baccount: <sellerId>`, `x-tenant: SELLER`, `Origin`, `Referer`. `/download/table` additionally
needs `x-pagecontext: other-reports#PLA#sellerPlaConsolidatedFSNReport#csv` (the `#csv` suffix is
what makes the server return CSV).

Ads report fields available (`downloadV2.fields`, PROVEN-BY-JIVO): `id, name, status, type,
marketplace, startAndEndDate, budget, budgetType, cost, remainingBudget, views, clicks,
totalConvertedUnits, totalConvertedRevenue, roi, ctr, cvr`.
FSN report metrics (`download/table`): `views, engagements, direct_units, indirect_units,
total_revenue, cvr, roi, cost`, grouped by `campaign_id, campaign_name, ad_group_id, ad_group_name,
sku_id, listing_name`.

`view_id: "612"` and `reportId: "sellerPlaConsolidatedFSNReport"` are the discoverable keys into the
wider `fed-ads` report catalogue — there are almost certainly more `reportId`s than the one JIVO
pulls. Phase 3 target.

**These are POSTs → G0 forbids firing them.** Catalogued as `EXPORT`.

---

## 4. Vendor Hub — proven endpoints (`vendorhub.flipkart.com`)

SPA with hash routes (`#/vendor-portal/...`, `#/operations/...`, `#/welcome/...`).

| Verb | Path | Body / params | Evidence |
|---|---|---|---|
| POST | `/login` | `{username,password,captchaResponse,app,context}` | **PROVEN-BY-JIVO**. reCAPTCHA v2 **checkbox**, server-validated → pure-curl login is impossible. **G9: never mint.** |
| POST | `/select-vendor` | `{…vendor id…}`, `x-csrf-token` | **PROVEN-BY-JIVO** — required before dashboard XHRs return a CSRF token |
| GET | `/vendor/user-management/vendor-list` | — | **PROVEN-BY-JIVO** — the vendor picker; the SPA calls it right after login |
| GET | `/vendor/purchase-orders` | `page_number, page_size, status, order=desc, from_date, thru_date, sort_column=order_date` | **PROVEN-BY-JIVO** — the PO list grid (Flow 35) |
| GET | `/vendor/purchase-order-download?id=<PO>` | — | **PROVEN-BY-JIVO** — per-PO Excel workbook. *This* is the real PO source; the page's "Download List" button only exports the table, not the workbook. |
| POST | `/vendor/analytics/report` | `{"filter":{},"dateTime":"<display ts>"}` | **PROVEN-BY-JIVO** 200 → `{}` — **ENQUEUE (inventory report), emails a link. G2 forbids firing.** |
| POST | `/vendor/analytics/sales-report` | `{"filter":{}}` | **PROVEN-BY-JIVO** 200 → either `{}` (async/email) or `{"sync":true,"document_id":"CONA…"}`. **ENQUEUE. G2 forbids firing.** |
| GET | `/vendor-p/getFile/v1/retail/documents/<document_id>/download` | cookie only, **no CSRF** | **PROVEN-BY-JIVO** 200 `application/xlsx` — the synchronous direct download once a `document_id` exists |
| GET | `/vendor-p/getDocument/<token>` | cookie | **PROVEN-BY-JIVO** 200 `application/xlsx` (251 KB inventory, 2,446 rows) — the emailed-link download path |

CSRF is **enforced** on Vendor Hub POSTs: with `x-csrf-token` → 200, without → 403 (PROVEN-BY-JIVO).
Reads (`purchase-orders`, `purchase-order-download`, `getFile`, `getDocument`) need only the cookie.

### Vendor Hub app surface, from the JWT `permissions` claim (PROVEN — decoded from a real token)

`VIEW_MATERIAL_MOVEMENT · MODIFY_MATERIAL_MOVEMENT · VIEW_PRODUCT_STOCK · MODIFY_PRODUCT_STOCK ·
VIEW_AGREEMENTS_APP · MODIFY_AGREEMENTS_APP · VIEW_PAYMENT · VIEW_PRODUCT_COMPLIANCE ·
MODIFY_PRODUCT_COMPLIANCE · VIEW_INVENTORY_PRODUCTS · VIEW_FINANCE · VIEW_CATALOGUE ·
MODIFY_CATALOGUE · VIEW_MANAGE_USERS · VIEW_REPORTS · VIEW_INVENTORY_SUMMARY ·
VIEW_AGREEMENTS_CLAIMS · MODIFY_AGREEMENTS_CLAIMS`

That is 12 distinct app areas. JIVO's automation touches **3** (reports/analytics, purchase orders,
inventory summary). The other 9 — material movement, product stock, agreements, payment, product
compliance, finance, catalogue, manage users, claims — are unmapped. Phase 3/6b target.

### Vendor Hub known routes (SPA hash routes, DOCUMENTED from seed docs)

- `#/welcome/select-account?app&context` — vendor account picker
- `#/vendor-portal/inventory/landing/analytics/product-details/list` — Sales & Inventory Analytics → Product Details
- `#/operations/po/list?status=new` — Primary PO list

---

## 5. Entity + identity facts (non-secret, PROVEN)

### Seller Hub (3P marketplace)
- login `ecom8@jivo.in` · `sellerId = e56b4e65e27e4162` · display "JIVOMART"
- one-time reports on the account: **69** · repeat report requests: **3** (live `getReportsCount`, 2026-07-06 era)

### Vendor Hub (1P grocery) — decoded from real JWTs, 2026-07-22
| Login | Name | Role(s) | accountId | Selected vendor | # vendors |
|---|---|---|---|---|---|
| `gurvinder@jivo.in` | Gurvinder Jivo | Operations Head | `ACC20F60245910749BB813F22872E5714426` | `VEN23097` JIVO MART PRIVATE LIMITED | **6** |
| `infinite@jivo.in` | Piyush Kamwal | Operations Head, Brand Operations Head | `ACCC6AF17C1930A4F65855A0992EACF02C6` | `VEN20104` BABA LOKENATH TRADERS | **3** |

Both: `tenant = FKI`, `retailer = fki`, `iss = retail-vendor-portal`, `is_external = true`,
`vendor_level_access = true`, `number_of_retailers = 1`.

**9 vendor entities total** across the two logins. Named in the seed docs:
- gurvinder: JIVO MART PRIVATE LIMITED · KNOWTABLE ONLINE SERVICES PRIVATE LIMITED · CHIRAG
  ENTERPRISES · FAIRDEAL MARKETING · Jivo wellness private limited · M/S SHIV SHAKTI ENTERPRISES
- infinite: BABA LOKENATH TRADERS · Evara Enterprises · SUSTAINQUEST PRIVATE LIMITED

(6 + 3 = 9, matching the `number_of_vendors` claims exactly — VERIFIED cross-check.)

---

## 6. Auth mechanics + where tokens land on disk

| Surface | Mechanism | Lifetime | Refresh recipe |
|---|---|---|---|
| Seller Hub | opaque cookie jar: `T` (.flipkart.com, httpOnly), `connect.sid` (Express), `sellerId`, `is_login`, `DID`, `nonce`, `XyZ7pQ9rS2T1uV8wA3bC6dE4fG0h` (= the CSRF value) | **needs a fresh login most days** — session does not persist | `~/ecomcliauto/auth/login/flipkart-seller-cdp.sh` → CDP-rides Chrome **Profile 16** (`ecom8@jivo.in`) → writes `out/flipkart-seller.curl` → `flipkart-cli auth import` |
| Vendor Hub | `access_token` JWT (HS256, **exactly 24 h** iat→exp) + `_csrf` cookie ↔ `x-csrf-token` header | 24 h | `~/ecomcliauto/auth/login/flipkart-vendor-cdp.sh` → CDP-rides Chrome **Profile 15** → `out/flipkart-vendor-fresh.curl` → `flipkart-grocery-cli auth import` |
| Marketplace Seller API | OAuth2 client_credentials → `https://api.flipkart.net/oauth-service/oauth/token`, scopes `Seller_Api`, `Default` | per token | **no credentials exist** — never used |

**CSRF, both portals:** the token is readable straight out of the cookie jar — Seller Hub
`fk-csrf-token` = the `XyZ7pQ9rS2T1uV8wA3bC6dE4fG0h` cookie value; Vendor Hub `x-csrf-token` pairs
with the `_csrf` cookie. No `index.html` scrape is needed in practice (PROVEN-BY-JIVO, lesson P3),
though the SPA itself reads `#seller_session_unique_token` from `index.html`.

**Chrome profile map** (PROVEN-BY-JIVO): Profile **15** = Vendor Hub session (Google-trusted
`tanuj@jivo.in`, holds gurvinder's cookies) · Profile **16** = `ecom8@jivo.in` Seller Hub ·
Profile 17 = `ecom1@jivo.in` (BigBasket/Amazon/Zepto).

### Token status on disk RIGHT NOW (checked 2026-07-30, VERIFIED)

| File | Surface | iat | exp | Verdict |
|---|---|---|---|---|
| `~/ecomcliauto/auth/login/out/flipkart-vendor-fresh.curl` | Vendor Hub (gurvinder) | 2026-07-22 19:35 | 2026-07-23 19:35 | **EXPIRED 7 days** |
| `…/flipkart-vendor.curl` | Vendor Hub (gurvinder) | 2026-07-18 15:46 | 2026-07-19 15:46 | **EXPIRED 11 days** |
| `…/flipkart-infinite.curl` | Vendor Hub (infinite) | 2026-07-22 20:00 | 2026-07-23 20:00 | **EXPIRED 7 days** |
| `…/flipkart-seller.curl` | Seller Hub | captured 2026-07-18 | opaque cookies, no exp claim | **12 days old; Seller Hub needs a same-day login → treat as dead** |

No `~/.config/flipkart-cli/` or `~/.config/flipkart-grocery-cli/` config exists on this machine
either. **→ Phase 5 is `BLOCKED_NEEDS_TOKEN`.** Per G9 I will not mint a session: Vendor Hub login
requires solving a server-validated reCAPTCHA v2 checkbox, and both refresh recipes drive a real
Chrome profile — either would risk kicking a live JIVO user out of the account. Phases 0–4 and 6–8
proceed unaffected; every endpoint ships marked `documented (not probed)`.

---

## 7. Credential key names present in `~/ecomcliauto/.env` (names only — G6)

`FLIPKART_ECOM8_PASSWORD` → Seller Hub (`ecom8@jivo.in`)
`FLIPKART_GURVINDER_PASSWORD` → Vendor Hub (`gurvinder@jivo.in`)
`FLIPKART_INFINITE_EMAIL` + `FLIPKART_INFINITE_PASSWORD` → Vendor Hub (`infinite@jivo.in`)

Also referenced by the seed docs but **absent** from `.env`: `FLIPKART_VENDOR_PASSWORD`
(the vendor CDP re-login script's variable name — supplied from `pass show
flipkart/gurvinder-password`, i.e. the macOS password store, not `.env`).
**Absent entirely:** `FLIPKART_CLIENT_ID`, `FLIPKART_CLIENT_SECRET` — confirming the public
Marketplace Seller API has never been used.

**Login → portal map is unambiguous** (no ambiguity to record): the seed docs state it explicitly
and the decoded JWTs confirm it — `ecom8` is Seller Hub only, `gurvinder` and `infinite` are Vendor
Hub only.

---

## 8. Hard-won gotchas to carry into Phases 2–8 (all PROVEN-BY-JIVO)

1. **GCS presigned links are VPC-blocked.** Any `storage.googleapis.com` download link Flipkart
   hands out 403s `SecurityPolicyViolated` from outside its perimeter. Use the Flipkart proxy path.
2. **`generateReport` 400s "already been requested"** when a window already has a live link — which
   is *good news* for a read-only study: `checkReports` alone surfaces existing reports.
3. **The FSN "Download" button fires no data request** — only mixpanel/GA analytics. The
   `download/table` POST that renders the report *is* the download.
4. **`queryId`/`requestId` in the FSN body are not cache keys** — proven by a two-date replay
   (2026-07-08 → 271 rows vs 2026-06-15 → 129 rows). The server keys off `dateRange`.
5. **Vendor Hub throttles report generation.** After ~8 triggers in ~2 h, triggers still return 200
   but no report is ever produced. Operational rule already baked into JIVO's CLI: ≤1 trigger per
   type per run, never auto-retry. **For this study: zero triggers.**
6. **Never infer a destination or a schema — capture it.** JIVO's costliest near-miss (lesson U4)
   was a documented-but-wrong mapping that would have silently collapsed 313 rows to ~62. This is
   the same discipline as G1.
7. **`looksLikeLogin` must key on `Content-Type: text/html` only.** Any `<`-prefixed body (e.g. a
   GCS XML error) was previously misreported as "session expired".

---

## 9. What Phase 0 did NOT establish (honest gaps)

- **No JS corpus yet** — Phase 0 is document mining only. Every endpoint above came from JIVO's
  automation, which covers ~3 of 21 Seller Hub subsystems and ~3 of 12 Vendor Hub areas. The
  bird's-eye view still has to come from the bundles (Phase 2/3).
- **No page/route inventory** — only 3 Vendor Hub hash routes and 0 Seller Hub routes are known so
  far.
- **No live number is current.** The 260 campaigns / 269 FSN rows / 69 reports / 2,446 inventory
  rows above are JIVO's July-8→14 figures, not today's. They are recorded as **UNVERIFIED for
  today** in the data inventory.
- **Nothing was probed this run** — no token (§6).

## Files read (all read-only, none modified)

```
~/ecomcliauto/flipkart/FLIPKART-LESSONS.md
~/ecomcliauto/flipkart/VENDORHUB-LOGIN-CONTRACT.md
~/ecomcliauto/flipkart/auth/{VERIFIED-FINDINGS,REAL-ENDPOINTS,FLOW-13-VERIFIED,FLOW-14-VERIFIED,FLOW-15-VERIFIED}.md
~/ecomcliauto/flipkart/specs/{flipkart-seller-hub-spec,flipkart-seller-api-spec}.yaml
~/ecomcliauto/flipkart-grocery/{FLOWS,BUILD-PLAN,STATE-2026-07-14,UPLOAD-CONTRACT}.md
~/ecomcliauto/clis/flipkart-cli/*.go
~/ecomcliauto/clis/flipkart-grocery-cli/*.go
~/ecomcliauto/clis/flipkart-seller-api-cli/spec.yaml
~/ecomcliauto/clis/flipkart-seller-hub-cli/spec.yaml
~/ecomcliauto/captures/flipkart/{13-*,14-download,15-table}.txt          (header names only)
~/ecomcliauto/captures/flipkart-vendorhub/16-*.txt                        (header names only)
~/ecomcliauto/orchestrate/flipkart-*.{sh,ps1}
~/ecomcliauto/auth/login/flipkart-*.{sh,mjs}
~/ecomcliauto/auth/login/out/flipkart-*.curl                              (JWT exp/claims only)
~/ecomcliauto/.env                                                        (key NAMES only)
```
