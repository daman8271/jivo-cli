# Atlas architecture — 6 September 2026

Decision: separate site-mark4 Next application, deterministic TypeScript monthly solver, independent sanitized VPS input feed. Rejected modifying the monolithic earlier simulator (would blur independent versions), and rejected public state-only planning (cheap cycles lack hourly stocks and detailed monthly targets).

Existing Mark3 integrated INPUT data is read-only: /root/jivo-courier/jolly/sim/live-inputs.json plus source caches. No existing future schedule or Claude Mark4 implementation is copied. New feed: https://mark4-astha.srv1685505.hstgr.cloud/inputs.json. Isolated process and route; existing collector, cron and deployments untouched.

## Ownership
- Engine: lib types/source/normalize/rules/planner, app/api/model, tests.
- Data: scripts sanitizer/server, data seed and verified master supplements.
- Frontend: pages/layout/components/CSS.
- Parent: package/config, infrastructure, integration and Vercel release.
- Independent reviewers: correctness, security, QA and original-requirement completion.

## Solver
GET model returns default; POST accepts nightLine, efficiency, allowProposedSupply. For each date: receive dated material; model gate departure (including Sunday); allocate confirmed/forecast needs; schedule eligible day machines and at most one night machine; consume shared stock and blends; update FG/standing storage; record shortages and conditional purchases.

Rates are source-rated where available, otherwise labelled derived/unavailable, with80% applied once.10 effective hours/day plus10 for selected night line. Sunday no production. SKU continuity preferred; any switch must declare setup basis/time.

Container from primary BOM component, not sheet PET column or carton accessory text. Per-carton new BOM normalized to per-piece. Only exact verified mappings auto-merge16/20 product identities; unresolved mappings visible. Drums excluded.

Monthly target provisional interpretation: goods MADE during month. Remaining monthly objective subtracts booked MTD, never FG again. Open confirmed needs subtract FG. Required production=max(remaining objective, uncovered confirmed demand); projection not added on top of the same orders. Booked MTD is a record-floor, not complete physical truth; missing source coverage remains visible.

## Trust
Preserve original carried master/stock stamps, separate model compute time from source time. Sanitize by allowlist; no customer/person/document/contact/internal path passthrough. Seed fallback explicitly dated. Forecast reserve stays monthly plan: no claim of calculated historical GT/MT average without sufficient source coverage. No new August accuracy claim.

₹2.5Cr desired and₹2Cr discussed minimum refer to production value. Targets must not override capacity/material/storage. Labour records are per-run; session cost remains unknown unless verified.

## Delivery gates
Full source acceptance matrix: REQUIREMENTS.md. Two independent review/fix rounds required after V1. Verify routing, hours/night/Sunday, shared stock/blends, carton units, MTD/PO semantics, storage, target values, freshness/fallback, scenario interactions and responsive rendering. Public Vercel release only after concrete evidence. Deferred: August backtest, drums, WhatsApp.
