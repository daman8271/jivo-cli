# TankhaPay Business portal → study vault + read-only CLI (goal #87)

⚠️ **READ-ONLY** study of JIVO's TankhaPay Business account (`business.tankhapay.com`, HR/payroll/
workforce SaaS by Akal Information Systems). NO data is ever changed — corpus harvest + endpoint
inventory + gentle authenticated read-probes only. No create/edit/save/delete/approve/pay/upload,
ever. See [[Read-Only-Guardrails]].

## The auth model (cracked & PROVEN live 2026-07-25)
**No cookies.** Bearer-token from `localStorage.activeUser.token`, and **every request body is AES
encrypted.**

| Piece | Value |
|---|---|
| Login | `POST /api/login`, body `{email, password:md5(pw), recaptchaToken:"", localhost:true, action:"check_login_by_emailid1"}` (AES-wrapped). reCAPTCHA bypassed via `localhost:true`. **Headless, no browser.** |
| Token | HS256 JWT, **24h**, one token authorizes all 4 backends. Re-login daily. |
| Body crypto | **AES-128-ECB, PKCS7, key `0123456789abcdef`.** Request `{"encrypted": b64(AES(json))}`; response `{statusCode, commonData: b64(AES(json))}`. |

Full detail: `vault/_meta/` → [[Encryption-Scheme]], [[Auth-and-Access]], [[Proven-Login-Recipe]].
Credentials live only in gitignored `.env` (0600). Verified: read returned `total_employees:593`
matching the live dashboard.

## Backends (4, one JWT)
- `business.tankhapay.com/api/` (643) — main HRMS · `mobapi.tankhapay.com/api/` (62) — employer/onboarding
- `mobapi.tankhapay.com/` (9) — mobile employee · `tnd.tankhapay.com/api/` (12) — Training

## The deliverable
- **`vault/`** — Obsidian study notes, wikilinked. Start at **`vault/00-TankhaPay-Atlas.md`**.
  - `vault/_meta/` — crypto, auth, backends, guardrails, login recipe (**done**).
  - 14 section notes (Dashboard, Employee-Management, Attendance, Leave, Payouts, Approvals,
    Accounts-Taxes, Reports, Recruit-ATS, Masters-Config, Org-User-Management, Broadcast-Visitor-Help,
    Contract-Labour-Inventory, Training-Performance).
  - `vault/TankhaPay-Endpoints.md` — master read-only endpoint inventory (weave of `captures/endpoints-raw.tsv`).
- **`captures/`** — JS corpus (58 chunks ~20 MB, gitignored), `endpoints-raw.tsv` (726 endpoints),
  `sections/*.tsv` (per-section splits), probe transcripts.
- **`cli/tankhapay-portal`** — Go cobra read-only CLI: AES-ECB client, headless daily login, `doctor`,
  read commands per section, 3-layer read-only guardrail + tests. Mirrors the zepto/blinkit portal CLIs.

## Study status (2026-07-25)
Phase 0 recon **done** (corpus, backends, auth, crypto, 726-endpoint inventory). Phase 1 `_meta` vault
**done** and proven live. Phase 2 (section notes) + Phase 3 (CLI) in progress via multi-agent orchestration.

Part of the `~/jivo-cli` portal-CLI family — see [[project_blinkit_portal_clis]], [[project_jivogpt_cli_grid]].
