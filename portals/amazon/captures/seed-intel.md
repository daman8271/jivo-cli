---
title: Amazon — Seed Intel (PHASE 0)
platform: amazon
phase: 0
worker: worker-a
date: 2026-07-30
sources: ~/ecomcliauto (read-only)
status: complete
---

# PHASE 0 — Seed Intel: Amazon Vendor Central + Seller Central

Everything below was mined **read-only** from `~/ecomcliauto/` (live production automation —
never modified, per G7). No network calls were made in this phase. No secret values are
reproduced anywhere in this file (G6).

## 1. Two portals, four distinct API surfaces

Amazon is not one portal. JIVO touches **two portals**, and Vendor Central alone splits into
**three unrelated service surfaces** with three different auth contracts. This split is the
single most important structural fact about the platform.

| # | Surface | Host + prefix | Auth contract | Verified? |
|---|---|---|---|---|
| 1 | **Retail Analytics (ARA)** | `www.vendorcentral.in/api/retail-analytics/v1/` | cookie jar **+** `anti-csrftoken-a2z` **+** `amz-ara-custom-context` | ✅ VERIFIED (terminal curl replay, 2026-07-07) |
| 2 | **PO Management** | `www.vendorcentral.in/po-api/vendor/members/po-mgmt/search/` | cookie jar **ONLY** — no CSRF, no ara-context | ✅ VERIFIED 2026-07-08 |
| 3 | **Coupon campaigns (legacy `hz`)** | `www.vendorcentral.in/hz/vendor/members/coupon-campaigns/` | cookie jar only; **302→signin on expiry, never 401** | ✅ VERIFIED 2026-07-08 |
| 4 | **Seller Central (3P marketplace)** | `sellercentral.amazon.in` | separate login (`ecom1@jivo.in`), separate cookie jar, India marketplace picker | ⚠️ login VERIFIED; endpoints NOT yet captured |

> **Host correction (important).** The brief names `vendorcentral.amazon.in`. The
> **actually-working host proven by terminal replay is `https://www.vendorcentral.in`** — a
> distinct apex domain, not an `amazon.in` subdomain. The Seller Central host in the brief
> (`sellercentral.amazon.in`) is correct. Recorded here so no later phase probes the wrong host.

## 2. Account model — TWO Vendor Central logins, not two entities in one login

Corrected by JIVO's e-com team 2026-07-08 (the earlier "two entities, one login" model was wrong).

| Account | Login email | `vendorGroupId` | `cid` | Business name in file | Flows proven |
|---|---|---|---|---|---|
| **wellness** | `tanuj@jivo.in` | `7691702` | `A2I4CTXZEM9HDK` | `JIVO WELLNESS PVT. LTD.` | Sales, Inventory, PO (vendor code `H06YJ`), Coupon `A3R5OT2YBOK7ZZ` |
| **mart** | `ecom4@jivo.in` | `8592892` | `A2882479L2H86F` | `Jivo Mart Private Limited.` | Sales, Inventory, PO, Coupon |

- `amz-ara-custom-context` header value shape (both fields are **per-account** — they differ):
  `{"timezoneOffset":-330,"traceId":"<uuid4>","selectedVendorGroupIds":["<vgid>"],"cid":"<cid>"}`
- Each account has its **own cookie jar + own CSRF token**. There is no per-call company switch
  inside one session — the account *is* the entity.
- ⚠️ **`ASSPL` (`8026922`) is a DEAD/junk entity** inside the wellness login. It was the source of
  the "0 rows" mystery. It is **not** Mart. Dropped. Do not resurrect it in the vault as a company.
- **Seller Central** is a *third* login: `ecom1@jivo.in`, account label **"Jivo Mart | India"**,
  2SV via TOTP authenticator (SHA1 / 6 digits / 30s).

## 3. Auth mechanics

### Vendor Central (both accounts)
- **Auth = cookie jar** lifted from a logged-in Chrome session. Cookie *names* (no values):
  `session-id-vceu`, `ubid-vceu`, `session-id-time-vceu`, `x-vceu`, `at-acbeu` (access token),
  `sess-at-acbeu`, `__Host-mselc`, `session-token` (**rotates per response**).
- **POST calls additionally need** `anti-csrftoken-a2z`. A captured value kept working on replay
  (it is *not* one-shot). Sourced from the authenticated dashboard's page HTML/JS.
- **TLS impersonation is NOT needed** — plain `curl` / Go `net/http` cookie replay works. This was
  the big 2026-07-07 result and it de-risks the whole lane.
- Expiry signal: the JSON APIs return an **HTML login page with a 200**, not a 401. The seed CLI
  detects this via `IsHTMLLoginResponse`. The `hz` coupon path instead **302s to
  `amazon.in/ap/signin`**.
- Headless auto-login exists: `auth/login/amazon-auto-login.sh {mart|wellness}` →
  `amazon-login-capture.mjs`. mart = authenticator TOTP; wellness = email-OTP to `tanuj@jivo.in`
  via himalaya. **Not to be used by this study — G9 forbids minting a session.**

### Seller Central
- One-time **manual** login into a *dedicated throwaway Chrome profile* on CDP port 9250
  (`auth/login/amazon-mp-login-launch.sh`), then `amazon-mp-manual-capture.mjs` exports the jar.
  The dedicated-profile trick exists precisely because a snapshot of a live everyday profile
  rotates `session-token` and dies in under a day.
- **Session persistence: this portal does NOT log you out** (user-confirmed 2026-07-11) — best of
  any JIVO portal. Sessions survive; do not re-login.

### Where sessions land on disk (state inventory, this machine, 2026-07-30)

| Path | Contents | Age | Usable for PHASE 5? |
|---|---|---|---|
| `~/.config/amazon-vc-cli/config.toml` (`0600`) | VC cookie + CSRF for **mart** and **wellness** | `imported_at` **2026-07-16** → **14 days old** | ❌ almost certainly dead |
| `~/ecomcliauto/auth/login/out/amazon-mp.cookies.json` | **34 Seller Central cookies**; auth cookies (`at-acbin`, `sess-at-acbin`, `sst-acbin`, `x-acbin`, `session-token`, `__Host-mselc`) all carry 2027 expiries; 5 minor analytics cookies already lapsed | captured **2026-07-22** → 8 days old | ⚠️ **best available candidate** |
| `~/ecomcliauto/captures/amazon/*.txt` | full live cURLs **including real cookies + CSRF** | 2026-07-07/08 | ❌ dead, and never to be copied into the vault |

Credential key **names** only (values never read into this study): `AMAZON_WELLNESS_PASSWORD`,
`AMAZON_MART_PASSWORD`, `AMAZON_EMAIL_MART`, `AMAZON_EMAIL_WELLNESS`, `AMAZON_VC_TOTP_WELLNESS`,
`AMAZON_VC_TOTP_MART`, `AMAZON_MP_ECOM1_PASSWORD`, `AMAZON_MP_ECOM1_TOTP`.

> ⚠️ **Secret-hygiene incident noted, not propagated.**
> `~/ecomcliauto/comms/019-amazon-sellercentral-login-GO.md` contains the Seller Central
> **password and TOTP seed in plaintext**, and `~/ecomcliauto/captures/amazon/*.txt` contain live
> cookies and CSRF tokens. Both are outside this study's write scope (G7) so nothing was changed.
> Flagging for the lead as a hygiene finding. Nothing from either file is reproduced here.

## 4. Proven endpoints with proven verbs

Every row below is `VERIFIED` — observed working from the terminal, sourced from
`amazon/VERIFIED-FINDINGS.md` + the hardcoded constants in `clis/amazon-vc-cli/internal/client/`.

| Verb | Host · Path | Purpose | R/W posture |
|---|---|---|---|
| `POST` | `www.vendorcentral.in/api/retail-analytics/v1/request-report-download` | enqueue an ARA report → `{referenceId}` | **WRITE** (G2: enqueue burns live queue budget) |
| `POST` | `www.vendorcentral.in/api/retail-analytics/v1/list-report-download-workflows` | list report workflows (body `{}`) | **READ_POST** — semantic read, HTTP POST (see §6) |
| `POST` | `www.vendorcentral.in/api/retail-analytics/v1/get-report-data` | dashboard table as JSON, `limit`/`offset` paged | **READ_POST** — semantic read, HTTP POST |
| `GET` | `<reportDataUrl>` (presigned S3, `X-Amz-Expires`≈1h) | download a finished report | **READ_FILE** — no auth sent |
| `POST` | `…/po-api/vendor/members/po-mgmt/search/generateVendorSearchFile-v3` | enqueue PO export → `{poleTaskId}` | **WRITE** (enqueue) |
| `POST` | `…/po-api/…/search/getVendorSearchFileStatus` | poll `{poleTaskId}` → `s3Key`, `vendorGroupId`, `isTooManyItems` | **READ_POST** |
| `POST` | `…/po-api/…/search/downloadVendorSearchFile` | `{s3Key,poleTaskId,isPoHeader,zoneId}` → `awsS3Configuration.signedUrl` | **READ_POST** |
| `GET` | `…/hz/vendor/members/coupon-campaigns/download/<campaignId>/download-metrics` | **direct** coupon-metrics xlsx, no async | **READ_FILE / EXPORT** ✅ genuinely GET |
| `GET` | `sellercentral.amazon.in/mytax/gstreports/ondemand` | GST on-demand reports page (45-day cap) | READ (page) |

Known referers (needed to look like the SPA): `…/retail-analytics/dashboard/sales`,
`…/po/vendor/members/po-mgmt/managepos?tabId=all&order-date-range-from=&order-date-range-to=`,
`…/hz/vendor/members/coupon-campaigns/view/<campaignId>/campaign-metrics`.
Other known page routes from the corpus: `…/analytics/dashboard/vendorAnalytics`.

### ARA report request shape (fully parameterised — the whole report spec is client-controlled)
`reportRequest{ reportId, dimensionSelections[], comparisons[], limit, offset, metrics[],
aggregations[], orderBy{metricId,comparison,ascending} } + fileName + fileExtension`

- Time dimension, **daily**: `{rootParentDimensionId:"time-period", dimensionId:"daily-day",
  value:{timePeriod:"DAY", startDate, endDate}}`
- Time dimension, **range**: `dimensionId:"custom-period", value:{timePeriod:"CUSTOM", …}`
- Constant dims: `viewBy:"asin"`, `distributorView:"manufacturing"`, `programView:"retail"`,
  `currencySelector:"INR"`
- `reportId:"sales"` → 9 metrics: `ASIN, ITEM_NAME, BRAND, ORDERED_REVENUE, ORDERED_UNITS,
  SHIPPED_REVENUE, SHIPPED_COGS, SHIPPED_UNITS, CUSTOMER_RETURNS`; `orderBy ORDERED_REVENUE`
- `reportId:"inventory"` → the portal's default **17 of 38** columns: `ASIN, ITEM_NAME, BRAND,
  SOURCEABLE_PRODUCT_OOS_PERCENTAGE, VENDOR_CONFIRMATION_RATE, NET_RECEIVED,
  NET_RECEIVED_UNITS, OPEN_PO_QTY, RECEIVE_FILL_RATE, OVERALL_VENDOR_LEAD_TIME,
  UNFILLED_CUST_ORDERED_UNITS, AGED_90_DAYS_SELLABLE_INVENTORY, AGED_90_DAYS_SELLABLE_UNITS,
  SELLABLE_ON_HAND_INVENTORY, SELLABLE_ON_HAND_UNITS, UNSELLABLE_ON_HAND_INVENTORY,
  UNSELLABLE_ON_HAND_UNITS`; `orderBy NET_RECEIVED`; **daily only, never a range**
- **38 total inventory metrics exist; JIVO pulls 17.** That gap is a PHASE-6b headline.
- Workflow retention ≈ **5 days**; `IN_PROGRESS → COMPLETE` in ~20-25 s.
- `fileName` is client-chosen. ⚠️ Amazon's own naming is **identical across both companies** —
  never disambiguate a file by name alone; match `fileName` + `workflowStartTime`.

### PO export chain (4 steps, epoch-millis dates, `Asia/Calcutta`)
`generateVendorSearchFile-v3` → `getVendorSearchFileStatus` (poll until
`statusTypeTranslationId == "po_app_bulk_status_done"`, ~4-6 s) → `downloadVendorSearchFile` →
plain `GET signedUrl`. `pageSize:1000`, **32 export columns**, `excelFileType:"XLSX"`.
File sheet = `Line Items`, header on **row 1** (no metadata row, unlike ARA files).

## 5. What JIVO's automation actually covers — the 5% baseline

JIVO's live daily cron (`launchd com.jivo.amazon-daily`, 10:30 IST) pulls exactly **four** flows
from Vendor Central and **zero** from Seller Central:

| Flow | Report | Window | Status |
|---|---|---|---|
| 1 | ARA **Sales** (Secondary) | daily T-2 + MTD range | ✅ live, uploads to `amazon_sec_daily` |
| 2 | ARA **Inventory** | daily only | ✅ live |
| 3 | **PO Items** | 1st-of-(month−2) → today | ✅ live (closed 2026-07-14) |
| 4 | **Coupon** metrics | per campaign id | ✅ live |
| 21 | SC **GST MTR B2B** | 1st-of-month → yesterday | ⏸ pull only, upload on hold (.zip) |
| 22 | SC **GST MTR B2C** | same | ⏸ same |

**That is 2 of ~13 ARA report types, and 2 pages of Seller Central.** Everything else Amazon
holds for JIVO — chargebacks, shortage claims, forecast, ASN/ARN, Brand Analytics, settlements,
fees, FBA inventory, listing/ASIN health, Sponsored Ads reporting, user access — is
**unmapped**. That gap is this study's whole reason for existing.

## 6. ⚠️ Structural guardrail conflict — Amazon's read APIs are POST-bodied RPC

**This is the defining constraint on the Amazon deliverable and it must be resolved by the lead.**

`GUARDRAILS.md` **G0** permits exactly two network effects: `GET` pure reads, and one login
`POST`. `METHOD.md` PHASE 8 requires a transport that *"refuses anything that is not GET"* before
a socket opens.

But Amazon Vendor Central has **no GET JSON API**. Every analytics read is an
`XMLHttpRequest`-style POST with a JSON body:

- `list-report-download-workflows` — body `{}`, returns a list. Semantically a pure read. HTTP POST.
- `get-report-data` — returns the dashboard table. Semantically a pure read. HTTP POST.
- `getVendorSearchFileStatus`, `downloadVendorSearchFile` — poll + presign. Reads. HTTP POST.

So on Amazon, **G0-compliant and useful are mutually exclusive** for the ARA surface. I am
treating G0 as binding (it wins over every other instruction) and therefore:

1. A new classification bucket, **`READ_POST`** — *proven semantic read, forbidden by G0 because
   it is an HTTP POST.* Documented in full; **never wired into the CLI**; excluded from the read
   allowlist alongside `WRITE` and `UNKNOWN`.
2. The only genuinely `GET` authenticated read surface on Vendor Central is the **`hz` legacy
   path** (coupon metrics download) plus presigned-S3 downloads. Seller Central, being
   server-rendered, is expected to be **much richer in GETs** — which promotes it from
   "secondary" to the primary source of wireable read commands.
3. `BLOCKED_ASK_LEAD` written to the status file. Per **G10** I keep working on everything that
   is not blocked rather than halting.

**Question for the lead:** does G0 intend to forbid a *proven, body-`{}`, list-only* POST read
such as `list-report-download-workflows`? Until answered, the answer I am acting on is **yes,
forbidden**, and the Amazon CLI will ship GET-only.

## 7. Platform hazards carried into later phases

- **Most bot-hostile target in the program.** Server-rendered, aggressive WAF, CAPTCHA,
  device/session fingerprinting. One gentle attempt per asset path in PHASE 2; a bot-check means
  stop that line of attack immediately and write `BLOCKED_HARVEST`.
- **Report generation is an enqueue = a WRITE (G2).** Never call `request-report-download` or
  `generateVendorSearchFile-v3`. List and download only what humans already generated.
- **Sponsored Ads / AMS campaign state is live spend.** Read-only, no exceptions (G2).
- **Session hijack risk (G9):** Vendor Central logins are shared with JIVO's e-com team and the
  daily cron. A fresh login would rotate cookies out from under the 10:30 IST cron. Consume only.
- Expired VC session presents as **HTTP 200 + HTML login page**, not 401 — any probe must
  content-sniff, not just check status.
- `session-token` rotates on every response; a static jar degrades.
- Coupon campaign ids are **per-account**; the two ids in `coupon_campaigns` config default belong
  to a different account than `wellness` and 302 from it.

## Connections
- [[00-Amazon-Atlas]] · [[Amazon-Endpoints]] · [[Auth-and-Access]] · [[Read-Only-Guardrails]]
- [[Amazon-Data-Inventory]] — the 17-of-38 metric gap and the 4-of-N flow gap start here
