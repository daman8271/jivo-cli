# D3 — plain-client (curl) WAF/header matrix + D9 cookie attributes

Live-run 2026-08-21 ~11:55–12:20 UTC (17:25–17:50 IST) against the browse daemon's logged-in
session for **registration 02 — Rajasthan `08AACCJ4223F1ZW`** (GSTIN confirmed in every 200 body).
All requests GET unless marked POST. `-L` never followed. **Cookie values are never written here** —
only cookie *names*. Raw jar stayed in `/tmp` (0600), never under the repo.

Chrome UA string used: `Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36`
HeadlessChrome UA (the browse session's own): `…HeadlessChrome/145.0.7632.6 Safari/537.36`

Header sets:
- **a** cookies only (curl's default `curl/x` UA), no Referer, no Accept
- **b** cookies + HeadlessChrome UA, no Referer
- **c** cookies + UA + Referer(host dashboard)
- **d** cookies + UA + Referer + `Accept: application/json, text/plain, */*`
- **e** = d but the jar with **TS\* cookies removed**
- **f** = d but a **real desktop-Chrome UA** instead of HeadlessChrome
- **g** = d but **all 10 cookies** sent blindly (cross-host)
- **h** = d headers but **no cookies at all**

Per-host jar (names): services `{Lang, TS0134d082, AuthToken, UserName, EntityRefId}` · return `{Lang, TS01d07858, AuthToken, UserName, EntityRefId}` · payment `{Lang, TS01ca3b45, AuthToken, UserName, EntityRefId}` · gstr2b `{AuthToken, UserName, EntityRefId}` (no host TS cookie exists).

## GET matrix (fresh, valid session)

| endpoint (host) | set | status | redirect / note | ctype | bytes | result |
|---|---|---|---|---|---|---|
| services `/services/api/ustatus` | a cookies-only,no-Ref | 200 | — | json | 545 | ✅ authed JSON |
| services `/services/api/ustatus` | b UA,no-Ref | 200 | — | json | 545 | ✅ |
| services `/services/api/ustatus` | c UA+Ref | 200 | — | json | 545 | ✅ |
| services `/services/api/ustatus` | d UA+Ref+Accept | 200 | — | json | 545 | ✅ |
| services `/services/api/ustatus` | e minus-TS | 200 | — | json | 545 | ✅ TS not needed |
| services `/services/api/ustatus` | f **real Chrome UA** | 000 | **TCP RST (curl 56, connection reset)** | — | 0 | ⛔ services RSTs branded Chrome UA |
| services `/services/api/ustatus` | g all-10-cookies | 200 | — | json | 545 | ✅ |
| services `/services/api/ustatus` | h **no cookies** | 200 | — | json | 2 | ⚠️ `{}` (unauthed soft-empty, not 401/403) |
| return `/returns/auth/api/itcbalance` | a cookies-only,no-Ref | 302 | → services…/error/accessdenied | — | 0 | ⛔ no Referer |
| return `/returns/auth/api/itcbalance` | b UA,no-Ref | 302 | → accessdenied | — | 0 | ⛔ no Referer |
| return `/returns/auth/api/itcbalance` | c UA+Ref | 200 | — | json | 136 | ✅ |
| return `/returns/auth/api/itcbalance` | d UA+Ref+Accept | 200 | — | json | 136 | ✅ |
| return `/returns/auth/api/itcbalance` | e minus-TS | 200 | — | json | 136 | ✅ TS not needed |
| return `/returns/auth/api/itcbalance` | f real Chrome UA | 200 | — | json | 136 | ✅ (return host does NOT RST Chrome) |
| return `/returns/auth/api/itcbalance` | g all-10-cookies | 200 | — | json | 136 | ✅ |
| return `/returns/auth/api/itcbalance` | h no cookies | 403 | — | — | 0 | ⛔ no session |
| return `/returns/auth/api/filingsnapshot` | a–h (every set) | 200 | — | text/html | 246–247 | ⛔ **F5 ASM "Request Rejected"** on return host — always |
| payment `/payment/auth/api/cashbalance` | a / b (no Ref) | 302 | → accessdenied | — | 0 | ⛔ no Referer |
| payment `/payment/auth/api/cashbalance` | c / d | 200 | — | json | 312 | ✅ |
| payment `/payment/auth/api/cashbalance` | e minus-TS | 200 | — | json | 312 | ✅ TS not needed |
| payment `/payment/auth/api/cashbalance` | f real Chrome UA | 200 | — | json | 312 | ✅ |
| payment `/payment/auth/api/cashbalance` | h no cookies | 403 | — | — | 0 | ⛔ no session |
| gstr2b `/gstr2b/auth/api/gstr2b/getuserdtls?rtnprd=072026&fy=2026-27` | a / b (no Ref) | 302 | → accessdenied | — | 0 | ⛔ no Referer |
| gstr2b `…/getuserdtls` | c / d | 200 | — | json | 152 | ✅ GSTIN 08…1ZW |
| gstr2b `…/getuserdtls` | e minus-TS | 200 | — | json | 152 | ✅ TS not needed |
| gstr2b `…/getuserdtls` | f real Chrome UA | 200 | — | json | 152 | ✅ |
| gstr2b `…/getuserdtls` | h no cookies | 403 | — | — | 0 | ⛔ no session |

## filingsnapshot — path & host resolution
`filingsnapshot` lives at path **`/returns/auth/api/filingsnapshot` on BOTH hosts**, but only ONE host serves it to a plain client:

| host + path | set d | result |
|---|---|---|
| `return.gst.gov.in/returns/auth/api/filingsnapshot` | 200 | ⛔ ASM "Request Rejected" (246B HTML) — every header combo incl. +XHR/sec-fetch, +Chrome UA, minus-TS |
| `services.gst.gov.in/returns/auth/api/filingsnapshot` | 200 | ✅ real JSON, 1214B, `{"status":1,"data":{"gstin":"08AACCJ4223F1ZW","formNames":[…]}}`, TS not needed |
| `services.gst.gov.in/services/auth/api/filingsnapshot` (wrong path) | 403 | — |

**Rule: call `filingsnapshot` on the `services` host, not `return`.**

## services-host User-Agent rule (verified, fresh session)
Same request (cookies+Referer+Accept), only the UA changed:

| UA | services `/services/api/ustatus` |
|---|---|
| (no UA header — curl default) | 200 ✅ |
| `…HeadlessChrome/145…` | 200 ✅ |
| `gst-portal/1.0 (read-only)` | 200 ✅ |
| `…Chrome/145.0.0.0 Safari…` (branded desktop Chrome) | **000 — TCP RST** ⛔ |
| `…Chrome/120.0.0.0 Safari…` | **000 — TCP RST** ⛔ |
| Chrome UA **+ full sec-ch-ua / sec-fetch** client hints | **000 — TCP RST** ⛔ (hints don't help) |
| bare `Mozilla/5.0` | 200 but **ASM "Request Rejected"** HTML ⛔ |

The RST reproduced 6× and is UA-keyed (only branded-Chrome, only on the `services` host; the return host serves the same Chrome UA fine). **Do not send a real desktop-Chrome UA or a bare `Mozilla/5.0` to `services.gst.gov.in`.** The verified-everywhere UA is the **HeadlessChrome** string (200 live on all four hosts).

## POST (read-shaped) — set d / e / c
| POST | best sets | status | bytes | body head |
|---|---|---|---|---|
| return `/returns/auth/api/efiledReturns` `{"fy":"2026-27","rfp":"Monthly","qtr":null,"mth":null,"rtntp":"GSTR1"}` | d,e,c | 200 | 645 | `[{"rtntype":"GSTR1","fy":"2026-27","taxp":"July","arn":"…","dof":"11/08/2026",…}]` ✅ |
| services `/services/auth/profile/detail` `{}` (Content-Type application/json;charset=utf-8) | d,e,c | 200 | 936 | `{"ntcrbs":"MFT","contacted":{…PII…},…}` ✅ |

Both POSTs need the same recipe as the GETs of their host: cookies + `Referer` (host dashboard) + `Content-Type: application/json;charset=utf-8`. TS\* not required.

## Step 3 — login prerequisites without a session (fresh empty jar)
UA that is NOT on the services reject-list (HeadlessChrome / no-UA / tool-UA — bare `Mozilla/5.0` is blocked):

| request | status | ctype | bytes | Set-Cookie |
|---|---|---|---|---|
| `GET /services/login` (no cookies) | 200 | text/html | ~4847 | **`AuthToken`** (pre-auth placeholder) + **`TS0134d082`** |
| `GET /services/captcha?rnd=0.123456` (jar from /login) | 200 | **image/png** | ~4.5–4.9 KB | **`CaptchaCookie`** + `TS0134d082` (refreshed) |

- The login page is a real ~4.8 KB HTML shell (`<!DOCTYPE html>…`), served to a plain client.
- The captcha **is a real PNG, 182×50** (magic `89504e47`), fresh image (and fresh size) on every GET.
- `/services/captcha` mints a **`CaptchaCookie`** — this is the server-side binding the eventual
  `POST /services/authenticate` validates the 6-digit answer against. A plain client must keep the
  jar from `/login` **and** `/captcha` and send it to `authenticate`. (authenticate NOT posted — read-only task.)

## D9 — cookie attributes (values redacted)
From `browse cookies` (CDP-level; captures httpOnly cookies that `document.cookie` cannot see).

| cookie | domain | path | httpOnly | secure | sameSite | expires | value len |
|---|---|---|---|---|---|---|---|
| AuthToken | `.gst.gov.in` | / | ✅ | ✅ | Lax | session (-1) | 32 |
| UserName | `.gst.gov.in` | / | ✅ | ✅ | Lax | session | 12 |
| EntityRefId | `.gst.gov.in` | / | ✅ | ✅ | Lax | session | 13 |
| TS0134d082 | `.services.gst.gov.in` | / | ✅ | ✅ | Lax | session | 106 |
| TS01d07858 | `.return.gst.gov.in` | / | ✅ | ✅ | Lax | session | 106 |
| TS01ca3b45 | `.payment.gst.gov.in` | / | ✅ | ✅ | Lax | session | 106 |
| TS01255980 | `.www.gst.gov.in` | / | ✅ | ✅ | Lax | session | 106 |
| Lang | services./return./payment. (per host, host-only) | / | ❌ | ❌ | Lax | dated (~hours) | 2 |
| CaptchaCookie | services (login flow) | / | ✅ (obs.) | ✅ | — | session | — |

- **Every auth-bearing cookie is `httpOnly`** → a `document.cookie` exporter misses them. `auth import` must use a CDP/network export (as `browse cookies` does), never `document.cookie`.
- `AuthToken`/`UserName`/`EntityRefId` are on the shared parent `.gst.gov.in` → sent to all four hosts. `gstr2b` rides on these (no gstr2b TS cookie exists).
- TS\* are per-host F5/BIG-IP session cookies; **not required in the request** (every minus-TS set passed on a fresh session).

## D9 note — session lifetime (observed, low-n)
The session was valid through the full matrix + isolation runs, then **expired between 12:19 and 12:20 UTC**:
`services /ustatus` went from **545 B authed → 2 B `{}`** (unauthed soft-empty), and the browser's
`AuthToken` had disappeared from a re-dump. **Ordering seen at session end:** the `return`/`payment`/`gstr2b`
JSON APIs began returning **403 (with a valid Referer)** ~1 min *before* `services` stopped returning
authed data — consistent with per-host authorization lapsing before the services session, but n is tiny
and right at collapse, so treat as a lead for D9, not a settled rule. A plain-client **warm-up GET**
(`/returns/auth/dashboard` → 302) and **`payment keepalive`** (403) did **NOT** revive the expired
return-host access. Precise idle timeout: still D9.

## Error-shape classification for the client (fresh-session, clean)
- **302 → `services.gst.gov.in/services/error/accessdenied`** = valid session but **missing/blank `Referer`** → fix the Referer and retry (do NOT re-login).
- **403** (return/payment/gstr2b) or **services `/ustatus` returning `{}` (2 B)** = **no valid session** (no cookies or expired) → re-login.
- **200 `text/html … "Request Rejected"`** = F5 ASM block (path- or UA-triggered), NOT an auth problem → change host/path (filingsnapshot) or UA (drop bare `Mozilla/5.0`).
- **000 / connection reset** on `services` = branded desktop-Chrome UA → change the UA.
