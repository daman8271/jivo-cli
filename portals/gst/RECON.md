# GST portal — recon notes (live, 2026-08-21, Haryana + Rajasthan sessions)

Portal: https://services.gst.gov.in/services/login — JWPL = JIVO WELLNESS PRIVATE LIMITED (PAN AACCJ4223F, the Oil books).
8 registrations; creds in `.env` (gitignored). Everything below was observed with gstack `browse` (headless Chromium).

## Login flow (verified twice, no OTP shown)
1. `GET /services/login` — AngularJS 1.5 SPA. Inputs: `#username` (name user_name), `#user_pass`, `#captcha`.
2. Captcha appears after username is entered: `<img id="imgCaptcha" src="/services/captcha?rnd=0.xxx">` 182x50 PNG, 6 digits, grid background + red line. Refresh button beside it. Audio button exists.
3. `POST https://services.gst.gov.in/services/authenticate` → 200 (80 B body) — then app navigates to `/services/auth/fowelcome`. (POST body shape NOT yet captured — discovery item D1.)
4. After login: `POST /services2/auth/web/alerts/count`.
5. No 2FA/OTP prompt on either login (Haryana 06…, Rajasthan 08…). Dashboard shows "Last logged in" + "Currently logged in from IP".
6. Logout: a link with text "Logout" in the user dropdown (href not recorded — D2).

## Session / cookies
Cookie names after login: `AuthToken`, `UserName`, `EntityRefId`, `Lang`, `TS0134d082`, `TS01255980` (TS* = F5 BIG-IP / ASM WAF).
Cookies are shared across `services.gst.gov.in`, `return.gst.gov.in`, `payment.gst.gov.in` (in-app navigation between them carries the session).

## WAF behaviour (important for an HTTP client)
- Direct `GET https://return.gst.gov.in/returns/auth/dashboard` typed into a fresh tab → 302 → `/services/error/accessdenied`.
- Direct `GET …/returns/auth/viewfiled` → "Request Rejected" page (F5 ASM block).
- The SAME URLs reached by clicking the in-app menu link → 200. Difference is the request context (Referer from a gst.gov.in page and/or the TS* cookies being fresh). CLI must send a proper `Referer` and reuse the full cookie jar; verify in D3.

## JSON endpoints seen (all GET unless noted, all cookie-authenticated, all READ)
| Endpoint | Returns |
|---|---|
| `services.gst.gov.in/services/api/ustatus` | `{gstin, bname, stcd, einvStatus, utype, Llogin, appStatus, cob, regType, isManufacturer, …}` — who am I |
| `services.gst.gov.in/returns/auth/api/filingsnapshot` (also on return.) | `{data:{gstin, formNames:[{formName:"GSTR-1 / IFF", retPrds:[{monthYearName,"filingStatus","filingDate","status"}]}, {formName:"GSTR-3B",…}]}}` — last 5 periods |
| `return.gst.gov.in/returns/auth/api/dropdown` | `{data:{Years:[{year:"2026-27", months:[{month:"July", value:"072026"}…]}…]}}` — period codes are `MMYYYY` |
| `return.gst.gov.in/returns/auth/api/rolestatus?rtn_prd=072026` | per-form tile status for a period: `return_ty` GSTR1/GSTR1A/GSTR2B/GSTR3B/GSTR2A, `status` FIL/NF, `due_dt` |
| `return.gst.gov.in/returns/auth/api/itcbalance` | Electronic CREDIT ledger balance: `{op_tot, sgstTaxBal, cgstTaxBal, igstTaxBal, cessTaxBal, blockTotBal, dt}` |
| `payment.gst.gov.in/payment/auth/api/cashbalance` | Electronic CASH ledger balance by head: `{tot_rng_bal, igst:{tx,intr,pen,fee,oth,tot}, cgst:{…}, sgst:{…}, cess:{…}}` |
| `return.gst.gov.in/master/gstrs/A`, `/master/fy`, `/master/allstates`, `/master/ut/12` | dropdown masters |

## Pages (HTML shells; data comes from the APIs above or from APIs not yet captured)
- Returns dashboard: `return.gst.gov.in/returns/auth/dashboard` — selects FY (`select[name=fin]`), quarter, month; SEARCH → tiles: GSTR-1 (VIEW/DOWNLOAD), GSTR-1A, GSTR-2B (VIEW/DOWNLOAD), GSTR-3B (VIEW GSTR3B/DOWNLOAD), GSTR-2A (VIEW/DOWNLOAD).
- View Filed Returns: `return.gst.gov.in/returns/auth/efiledReturns` — selects FY / frequency (Annual, Half Yearly, Quarterly, Monthly) / form (GSTR1, GSTR3B, GSTR9, 9C, 10, TDS/TCS, TRAN1…). Selects have NO name attr (use nth-of-type). Search API not yet captured (D4).
- Ledgers: cash `payment.gst.gov.in/payment/auth/ledger/cashledger` (detail at `/payment/auth/ledger/detailedledger`), credit `return.gst.gov.in/returns/auth/ledger/itcledger`, liability `return.gst.gov.in/returns/auth/ledger/taxledger`. Date-range statement APIs not yet captured (D5).
- Profile: `services.gst.gov.in/services/auth/dashboard/profile` (API not captured, D6). Quick links: Ledgers `services.gst.gov.in/services/auth/quicklinks/ledgers`.
- Tax liabilities & ITC comparison: `return.gst.gov.in/returns/auth/comparison` (D7 — the best SAP-comparison source).
- IMS dashboard: `return.gst.gov.in/imsweb/auth/imsDashboard`.

## Live numbers captured (Haryana 06AACCJ4223F1Z0, 2026-08-21 ~17:05 IST)
- Credit ledger: total ₹4,33,72,582 (SGST 1,92,62,335 · CGST 1,31,74,558 · IGST 1,08,67,113 · Cess 71,937). `dt` field came back as "16/02/0027" (portal quirk — do not trust that date field).
- Cash ledger: total ₹44,201 (CGST 43,022 = pen 21,791 + fee 600 + intr 3; SGST same; IGST intr 1).
- GSTR-1 and GSTR-3B: Filed for Mar-26 … Jul-26 (GSTR-1 filed on the 11th each month, 3B on 20th/30th).

## Discovery items still open (Phase 2)
D1 login POST body · D2 logout endpoint · D3 Referer/WAF rules for a plain HTTP client · D4 filed-returns search API · D5 ledger date-range statement APIs (cash/credit/liability) · D6 profile API · D7 comparison API · D8 GSTR-1/3B/2A/2B view + download (generate-then-download is async on this portal) · D9 session lifetime / idle timeout · D10 whether the portal ever demands OTP (none seen on 2 logins).
