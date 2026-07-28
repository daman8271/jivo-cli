---
tags: [tankhapay, meta, backends, source-of-truth]
---
# TankhaPay — Backends & Environment

Extracted from the Angular production env object in `main.7309d5d32824e620.js` (module 45312).

## The SPA
- `business.tankhapay.com` — Angular 17+ SPA (webpack). Shell `index.html` + `runtime` + `main` +
  `polyfills` + `scripts` + **58 lazy chunks** (harvested to `captures/js/`, ~20 MB).
- Single-page HR/payroll/workforce suite by **Akal Information Systems Ltd.**
- ~34 top-level route sections (see [[00-TankhaPay-Atlas]]).

## API backends (four, one JWT authorizes all)

| Env key | Base URL | Prefix in code | Endpoints | Serves |
|---|---|---|---|---|
| `tankhapay_api` | `https://business.tankhapay.com/api/` | `u` | **643** | The main HRMS API — employees, attendance, payouts, approvals, reports, dashboard, masters, everything |
| `tp_employer_api` | `https://mobapi.tankhapay.com/api/` | `w` | 62 | Employer/onboarding, OTP, registration, ESIC/insurance, payments |
| `tpPay_api` | `https://mobapi.tankhapay.com/` | `or` | 9 | Mobile-app employee queries, face check-in, reimbursement claims |
| `tnd_tankhapay_api` | `https://tnd.tankhapay.com/api/` | `I` | 12 | Training & Development (T&D) module |

Total: **726 unique endpoints** (see `captures/endpoints-raw.tsv`; first-pass 322 READ / 333 WRITE / 71 unknown).

## Sibling web apps (SSO targets, not JSON APIs — out of CLI scope for reads)
- `pms.tankhapay.com` — Performance Management (PMS), offer letters
- `tnd.tankhapay.com` — T&D web + `/api/`
- `ats.tankhapay.com` — Applicant Tracking (main ATS account id `10427`)
- `survey.tankhapay.com` — Surveys
- `web.tankhapay.com` / `m.tankhapay.com` — employee self-service / mobile
- `tpayoffice.tankhapay.com` — OnlyOffice document editor
- `hwapi.tankhapay.com` — OnlyOffice callback + some mobile endpoints
- `businessprdapi.azurewebsites.net` — live-tracking API (`TpLiveTrackingApi`)
- `contract-api.azurewebsites.net`, `cj-prod-api-02.azurewebsites.net`, `api.contract-jobs.com` — contract-jobs/CRM

## Non-secret config observed (documented, not credentials)
- Google Maps keys (client-side, referrer-restricted) — noted, not used by the CLI.
- reCAPTCHA v3 site key `6LfBzAgpAAAAAL61hNQkprJ6_015ZG3sTzoYvlUo` — bypassed via `localhost:true` (see [[Auth-and-Access]]).
- `main_ats_account_id: 10427`, `AI_ASSISTANT_API_URL`, `ONLYOFFICE_*` — informational.

## Request shape (all backends)
Every real call is `POST` with `{"encrypted": …}` and (post-login) `Authorization: Bearer <jwt>`;
responses carry `{statusCode, commonData:<enc>, message, code}`. See [[Encryption-Scheme]].

See [[Auth-and-Access]] · [[Encryption-Scheme]] · [[Read-Only-Guardrails]]
