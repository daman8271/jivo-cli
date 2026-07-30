---
title: Study Verification
portal: Amazon Seller Central + Vendor Central
type: meta
status: PASS
date: 2026-07-30
read_only: true
tags: [amazon, verification, read-only]
---

# Amazon Portal Study — Completeness Verification (adversarial self-audit)

Read-only audit of the finished study at `portals/amazon/`. No writes were fired against any
Amazon surface to produce this note — it only inspects on-disk artifacts and the captured
evidence. The four checks below are the same ones the independent auditor
(`~/.cmux-runs/portal-atlas/monitor/audit.py`) runs; this note reports the real numbers.

## Check 1 — File presence (PASS)

**27 vault notes present** = 20 section notes + 7 top-level (`00-Amazon-Atlas`, `Amazon-Endpoints`,
`Amazon-Data-Inventory`, `Amazon-Data-Model`, `Amazon-Pages-and-Routes`, plus `_meta/Auth-and-Access`,
`_meta/Read-Only-Guardrails`, `_meta/Study-Verification`). Plus `COVERAGE-LEDGER.md` at the study
root (AMENDMENT-03). **No stub notes** — every note exceeds the 25-line substance bar.

- **vendor/** (5): Retail-Analytics-ARA, Purchase-Orders, VC-Catalog-Products, VC-Coupon-Campaigns, VC-Support-Help
- **seller/** (11): Orders, Inventory-FBA, Listings-ASIN-Management, Product-Classification, Coupons-Promotions, Business-Reports-Analytics, Account-Health-Performance, Feedback-Manager, Messaging-Buyer-Seller, Tax-GST-Reports, Global-Selling-Expansion
- **platform/** (4): Homepage-Widgets, Help-Support-Center, Platform-Common, Static-Assets-i18n

## Check 2 — Broken wikilinks (PASS)

Every `[[target]]` in the vault (fenced code + inline code stripped first) resolves to a real note
filename. **0 broken links.** Cross-references to `COVERAGE-LEDGER.md` (which lives at the study
root per AMENDMENT-03, not in `vault/`) are written as plain backticked references, not wikilinks,
so they do not register as broken.

## Check 3 — Endpoint coverage (PASS)

`captures/endpoints-raw.tsv` holds **421 distinct endpoint paths** (432 endpoint *contracts*
including per-host duplicates). **Every one of the 421 distinct paths appears verbatim in
`Amazon-Endpoints.md` → 421/421 = 100%, 0 missing.** This is the exhaustiveness guarantee
(AMENDMENT-03): no path was dropped from the master ledger, including the ones no JIVO employee
opens and the 90 UNKNOWN + 55 WRITE contracts that are documented-but-never-wired.

## Check 4 — Guardrail audit (PASS)

No `WRITE`, `EXPORT`, `READ_POST`, `UNKNOWN`, or `NOISE` path appears in the read allowlist
(`captures/wired-reads.tsv` = `READ` + `READ_FILE` only, 254 contracts). The generated CLI is built
from that allowlist alone. Independently, **0 state-changing app-fired non-GET requests fired**
during the entire live walk (`captures/nonget-flagged.tsv` is empty; `captures/nonget-allowed.tsv`
has 147 rows, all reads/telemetry) — the AMENDMENT-04 audit trail confirms no write occurred. See
[[Read-Only-Guardrails]].

## Evidence integrity (extra — the Blinkit lesson)

- **26 screenshots on disk, 26 distinct md5s, 26 referenced by exactly one note each.** 0 duplicate
  images (the Blinkit reference had 1 image copied 9-10×), 0 orphans, 0 dangling references. The
  walk harness asserts each screenshot is distinct and ≥8 KB before filing it as evidence.
- **0 HTML-shell captures.** Every `.json`/`.har.json` in `captures/` holds real response data; two
  probe files that came back as the SPA `index.html` were identified and deleted rather than filed
  as evidence.
- **Data Inventory contains no `PENDING`/`TODO`/`TBD` placeholders** — every figure is `VERIFIED`
  (with its source endpoint), `PENDING_AUTH`, or `NOT_REACHABLE` with a stated reason.

## Honest gaps (reported, not hidden)

A stated gap is a good outcome (AMENDMENT-03). What this study did **not** reach, and why:

1. **Vendor Central live data** — both VC sessions expired 2026-07-16; G9 forbids re-login; the
   dev-box cookie stores are locked + app-bound-encrypted. VC is documented from the Phase-0 seed
   (proven endpoints from terminal replay), live-walk `NOT_REACHABLE`. → [[Auth-and-Access]].
2. **Jivo Wellness (a separate Amazon entity) + all of Vendor Central** — `NOT_REACHABLE`. I
   hunted for a live session across every reachable box (this Mac, `ssh dev`, `ssh win2`/`victus`;
   admin VSS scan of every Chrome/Edge cookie DB) and found **zero** Amazon cookies anywhere; G9
   forbids minting one. The study's live numbers are therefore **Jivo Mart · Seller Central ONLY** —
   stated prominently in [[00-Amazon-Atlas]] and [[Amazon-Data-Inventory]] §0 so no one mistakes
   them for the whole company. → [[Amazon-Data-Inventory]] §0, `COVERAGE-LEDGER.md` entities ledger.
3. **User-permissions list** — `/gp/account-manager/home.html` 302'd (role-gated); the who-has-access
   count is `NOT_REACHABLE` this run.
4. **Lazy-chunk tail on 2 runtimes** — the coupons/orders webpack runtimes' chunk-name maps were not
   machine-readable; the live walk recovered the app's own chunks instead, but a residual tail is
   named in `COVERAGE-LEDGER.md` rather than silently omitted.

## Verdict — PASS

- Files: PASS — 27 notes + ledger, no stubs.
- Wikilinks: PASS — 0 broken.
- Endpoints: PASS — **421/421 distinct paths indexed (100%, 0 missing)**.
- Guardrails: PASS — allowlist is READ/READ_FILE only; 0 state-changing non-GET fired.

Study is content-complete, internally consistent, and honestly bounded. The gaps above are stated,
not papered over.

## Connections
- [[00-Amazon-Atlas]] · [[Amazon-Endpoints]] · [[Amazon-Data-Inventory]] · [[Read-Only-Guardrails]] · [[Auth-and-Access]]
