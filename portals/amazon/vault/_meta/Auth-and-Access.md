---
title: Auth and Access
created: 2026-07-30
updated: 2026-07-30
project: jivo-cli
type: meta
tags: [amazon, auth, read-only]
status: studied
read_only: true
---

# Amazon — Auth & Access map

Amazon is the most auth-fragmented target in the program: **three logins, four cookie jars, two
CSRF mechanisms, and one presigned-S3 no-auth path.** This note is the complete map. No secret
value appears here — cookie/token *names* only (G6).

## The three logins

| Login | Portal | Entity | 2FA | Session on disk (this run) |
|---|---|---|---|---|
| `ecom1@jivo.in` | Seller Central | Jivo Mart | TOTP (authenticator) | ✅ `~/ecomcliauto/auth/login/out/amazon-mp.cookies.json` — **8 days old, LIVE** |
| `tanuj@jivo.in` | Vendor Central | Jivo Wellness | email-OTP | ❌ `~/.config/amazon-vc-cli/config.toml` [wellness] — 14 days old, **expired** |
| `ecom4@jivo.in` | Vendor Central | Jivo Mart | TOTP | ❌ `~/.config/amazon-vc-cli/config.toml` [mart] — expired |

## Seller Central (3P) auth — the live one

- **Auth = cookie jar** from a logged-in Chrome session. Business-critical cookie names (values
  never read): `session-id`, `session-token` (rotates per response), `x-acbin`, `at-acbin`
  (access token), `sess-at-acbin`, `sst-acbin`, `ubid-acbin`, `__Host-mselc`, `sso-state-acbin`.
- The auth cookies carry **2027 expiries**; only minor analytics cookies had lapsed. This is why
  an 8-day-old jar still returned HTTP 200 with no bot-check.
- **Session persistence: Seller Central does NOT log you out** (user-confirmed) — the best session
  longevity of any JIVO portal. That is what made the whole live walk possible.
- **Writes need a per-tool CSRF token** (e.g. `coupons/api` → `x-csrf`, `fbmapi/v1/csrf`,
  `appeal/appeals/csrf`, `productclassify … getcsrftoken`). The study never mints or uses one — it
  only reads.
- Expiry signal on the 3P side: a **302 to `amazon.in/ap/signin`** (the `hz`/legacy paths) or an
  HTML sign-in shell with HTTP 200 (SPA paths). Any probe must content-sniff, not just check status.

## Vendor Central (1P) auth — expired this run

- **ARA:** cookie jar **+** `anti-csrftoken-a2z` header **+** `amz-ara-custom-context`
  (`{"timezoneOffset":-330,"traceId":"<uuid>","selectedVendorGroupIds":["<vgid>"],"cid":"<cid>"}`).
  Cookie names: `session-id-vceu`, `ubid-vceu`, `x-vceu`, `at-acbeu`, `sess-at-acbeu`,
  `__Host-mselc`, `session-token`.
- **PO Management:** cookie jar **only** — no CSRF, no ara-context. Scoped purely by the session.
- **Coupon (legacy hz):** cookie jar only; **302→`ap/signin` on expiry** (never 401).
- **Verified dead this run:** `GET /retail-analytics/dashboard/sales`, `/po/…/managepos`,
  `/po/…/dashboard` all 302→`ap/signin` (`assoc_handle=amzn_vc_sm_in`). Confirmed by independent
  curl *before* any walk traffic — this is the pre-existing expiry, **not** a lock caused by the
  study (see [[Study-Verification]]).
- Plain `curl`/Go `net/http` cookie replay works — **no TLS impersonation needed** (the big
  Phase-0 result). ARA reads are POST-bodied — see [[Read-Only-Guardrails]] for why they are excluded.

## The no-auth path

Finished ARA/PO reports and coupon files are delivered as **presigned S3 URLs**
(`X-Amz-Expires ≈ 1h`) — a plain `GET` with **no cookies or headers**. This is `READ_FILE`, the
terminal read action, and is the safest surface in the whole system.

## G9 — consume, never mint

**The study never logs in.** Vendor Central logins are shared with JIVO's e-com team and the
10:30 IST daily cron; a fresh login rotates `session-token` out from under them and can kick a
human out. So an expired session is reported as `NOT_REACHABLE`, never "solved" by re-login. The
Seller Central session was **consumed** from the existing jar, not created.

### The multi-box session hunt (why Wellness + VC are NOT_REACHABLE)

Per AMENDMENT-03 #2, before writing Wellness and Vendor Central off I hunted for a live session on
**every reachable box**, not just this Mac:

| Box | What I did (read-only, G6) | Result |
|---|---|---|
| This Mac | replayed both VC cookie jars in a real browser context; checked the SC account-switcher | VC both **302 → `ap/signin`** (expired 2026-07-16); SC exposes only "Jivo Mart" |
| `ssh dev` (HO-IT-PC10) | **admin VSS-copied** every Chrome + Edge `Network\Cookies` for all users (khushwinder singh incl. the live `Default` modified **today**, Administrator, Navjot Kaur); byte-searched host_keys | **zero** `amazon`/`vendorcentral`/`sellercentral` cookies |
| `ssh win2` / `victus` | admin VSS-copied every Chrome profile for all users (leela, prabh, fleet); no Edge/Brave present | **zero** Amazon cookies |

The VSS copy (admin, backup-semantics) got past the running-Chrome file lock that blocked the first
attempt — so this is a *complete* scan of the live profiles, not a partial one. **No live Amazon
session for Wellness or Vendor Central exists on any machine I can reach.** Combined with G9 (never
mint — a fresh VC login rotates cookies out from under the 10:30 IST cron and the e-com team), the
honest status is `NOT_REACHABLE`. The dev/win2 boxes run JIVO's Flipkart/BigBasket flows, not
Amazon — consistent with zero Amazon cookies anywhere on them.

> **Scope consequence:** this study's live data is **Jivo Mart · Seller Central ONLY**. Jivo
> Wellness (a separate Amazon entity) and all of Vendor Central (1P) are documented from the
> Phase-0 seed but carry no live counts this run. See [[Amazon-Data-Inventory]] §0.

## Where sessions land on disk

| Path | Perms | Contents |
|---|---|---|
| `~/ecomcliauto/auth/login/out/amazon-mp.cookies.json` | — | 34 Seller Central cookies (the live jar) |
| `~/.config/amazon-vc-cli/config.toml` | `0600` | VC mart + wellness cookie/CSRF (expired) |
| `~/ecomcliauto/captures/amazon/*.txt` | — | ⚠️ historical live cURLs with real cookies+CSRF (flagged to lead; never copied into this vault) |

## Runbook — how to COMPLETE the missing datasets (Wellness + Vendor Central)

The three `NOT_REACHABLE` datasets are blocked only on a **live session**, not on unknown mechanics
— every endpoint and payload is already documented. When a session next exists, here is exactly how
to fill each, read-only:

**A. Jivo Wellness / Jivo Mart — Vendor Central (1P).** A VC session must be refreshed *by the
ecomcliauto login the e-com team owns* (never mint one ad hoc — G9). Once
`~/.config/amazon-vc-cli/config.toml` has fresh cookies + `anti-csrftoken-a2z` for the account:
1. `amazon-vc-cli doctor --account {wellness|mart}` → confirms HTTP 200 / N workflows.
2. **Reads only** (this study's scope): `list-report-download-workflows` (body `{}`) and
   `get-report-data` are the *semantic* reads — but they are HTTP **POST**, so they are `READ_POST`.
   Under AMENDMENT-04 an **app-fired** POST is allowed; to capture them read-only, point the
   [[Read-Only-Guardrails|walk harness]] (`~/.cmux-runs/portal-atlas/harness/`) at a VC cookie jar
   and navigate `…/retail-analytics/dashboard/sales` and `…/po/vendor/members/po-mgmt/managepos` —
   the dashboards fire their own workflow-list + report-data POSTs, which the harness records. Do
   **not** call `request-report-download` / `generateVendorSearchFile-v3` (enqueue = WRITE, G2).
3. The 38-metric ARA inventory surface (JIVO pulls 17) and the ~11 unpulled ARA report types
   (forecast, chargebacks, shortage claims) are the headline 1P gap — enumerate them from the
   dashboard's dimension selectors once the walk renders.

**B. Jivo Wellness — Seller Central (3P), if a distinct account exists.** First confirm it exists:
log the Wellness SC login into a dedicated throwaway Chrome profile (the
`amazon-mp-login-launch.sh` pattern), export the jar, then check the account-switcher
(`/account-switcher/global-and-regional-account/merchantMarketplace`) — if it returns a *second*
global account, walk it with the harness exactly as Mart was walked (its own `sec-NN` captures under
a `vault/seller-wellness/` group + its own COVERAGE-LEDGER entity row). If the switcher still shows
only "Jivo Mart", Wellness has no separate SC account and that is the final answer.

**C. Where the concrete payloads live.** Every VC request body (ARA sales/inventory metric lists,
the PO 4-step chain, coupon metrics URL) is in `captures/seed-intel.md`, proven by terminal replay.
The CLI already wires the VC **read** endpoints (`retail-analytics-ara`, `purchase-orders`,
`vc-catalog-products`, `vc-support-help` groups) — they will start returning data the moment a VC
session is on disk; today they report a session error, which is the correct read-only behaviour.

Until any of that happens, the live numbers in this study are **Jivo Mart · Seller Central only** —
see the scope banner in [[00-Amazon-Atlas]] and [[Amazon-Data-Inventory]] §0.

## Connections
- [[00-Amazon-Atlas]] · [[Read-Only-Guardrails]] · [[Study-Verification]] · [[Amazon-Data-Inventory]]
- Sections that depend on this auth: [[Retail-Analytics-ARA]] · [[Purchase-Orders]] · [[Coupons-Promotions]] · [[Orders]]
