---
tags: [tankhapay, atlas, index]
---
# TankhaPay Business Portal — Study Atlas

Read-only reverse-engineering of **business.tankhapay.com** (JIVO's HR/payroll/workforce SaaS by Akal
Information Systems) → an Obsidian study vault + a read-only Go CLI under `~/jivo-cli/portals/tankhapay`.

> **Status (2026-07-25):** Phase 0–1 done. Auth + AES crypto **cracked and PROVEN live** (headless
> login → JWT → encrypted reads returning real data matching the dashboard). 726 endpoints inventoried.

## Start here (`_meta`)
- [[Encryption-Scheme]] — **the crown jewel.** AES-128-ECB, key `0123456789abcdef`, `{encrypted}` req / `commonData` resp.
- [[Auth-and-Access]] — bearer-token (no cookies), email+md5 login, reCAPTCHA bypass, 24h JWT, all 4 backends.
- [[Backends-and-Environment]] — 4 API backends, 726 endpoints, sibling apps, SPA structure.
- [[Read-Only-Guardrails]] — the never-write discipline (live payroll data, 593 real employees).
- [[Proven-Login-Recipe]] — copy-paste reproducible login + read (verified against live data).
- [[Pages-and-Routes]] — **complete coverage map: all 325 app routes (every page + subpage) → section.**

## Coverage guarantee (verified 2026-07-25)
- **726 API endpoints** — confirmed *complete*: all endpoint constants are centralized in one bundle
  module; the 58 lazy chunks define **zero** additional endpoints and there are **no** hardcoded/inline/
  dynamic endpoint paths. Nothing is constructed outside the captured set.
- **325 routes** — every page and child/subpage route across the whole corpus (see [[Pages-and-Routes]]).
- The CLI wires a read command for **every one of the ~322 READ endpoints** (not a curated subset), so the
  data behind every page is reachable. A final coverage-audit cross-checks `captures/endpoints-raw.tsv`
  against the CLI's registered commands and fails if any READ endpoint is unwired.

## Business sections (Phase 2 — one note each, source of truth for the CLI)
Mapped from the portal sidebar + endpoint path segments (`captures/endpoints-raw.tsv`, `captures/sections/`).

| Section | Note | Endpoints (approx) | Primary paths |
|---|---|---|---|
| Dashboard & Alerts | [[Dashboard]] | 12 | `dashboard/*`, employee dashboard notifications |
| Employee Management | [[Employee-Management]] | 104 | `employee/*`, `exitProcess/*` |
| Attendance & Live-Tracking | [[Attendance]] | 89 | `attendance/*`, `device/*`, `livetrack*` |
| Leave Management | [[Leave-Management]] | 51 | `leave/*`, `leaves/*` |
| Payouts, Salary & Advances | [[Payouts]] | 37 | `payoutApi/*`, `allowanceBonus`, `imprest`, `piece`, `payrolling` |
| Approvals & Travel | [[Approvals]] | 21 | `approval/*`, `travel/*` |
| Accounts, Taxes & Investment Proof | [[Accounts-Taxes]] | 19 | `TpTaxesApi`, `TpInvestmentProofApi`, `account` |
| Reports | [[Reports]] | 58 | `Report/*`, `report/*` |
| Recruit & ATS | [[Recruit-ATS]] | 24 | `recruit`, `TpCandidateAPI`, `Consultant` |
| Masters, Policies & Config | [[Masters-Config]] | 62 | `master`, `MasterApi`, `policy`, `formbuilder`, `emailTemplates`, `minimum-wages` |
| Org & User Management | [[Org-User-Management]] | 40 | `user-mgmt`, `employer`, `Business` |
| Broadcast, Visitor & Help | [[Broadcast-Visitor-Help]] | 24 | `NotificationApi`, `visitor`, `TpHelpAndSupportApi` |
| Contract Labour & Inventory | [[Contract-Labour-Inventory]] | 19 | `contractLabor`, `dinventory` |
| Training & Performance (T&D / PMS) | [[Training-Performance]] | 25 | `tnd.tankhapay.com/api/*`, `pms`, `tndApp` |

## The deliverables
- `vault/` — this study (Phase-1 `_meta` done; Phase-2 section notes pending).
- `vault/TankhaPay-Endpoints.md` — master read-only endpoint inventory (Phase 2 weave of `endpoints-raw.tsv`).
- `captures/` — JS corpus (58 chunks, ~20 MB, gitignored), endpoint TSV, probe transcripts.
- `cli/tankhapay-portal` — Go cobra read-only CLI (Phase 3): AES-ECB client, headless daily login, `doctor`,
  read commands per section, 3-layer read-only guardrail. Mirrors the [[project_blinkit_portal_clis|zepto/blinkit]] portal CLIs.

## Account under study
`shunty@jivo.in` (name "ravinder singh", role 2 "Business", `tp_account_id=2719`, JIVO). OUs: Above 40K,
Confidential, Factory, Head Office, Interns, Sales Office. 593 employees.
