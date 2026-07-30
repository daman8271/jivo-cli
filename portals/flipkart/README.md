# Flipkart portal study → CLI (Portal Atlas, Wave 1, worker B)

⚠️ **READ-ONLY** study of JIVO's Flipkart seller + vendor ecosystem. No data is ever changed —
corpus harvest + endpoint classification + read-only `GET` replay of the live session only. No
create/edit/save/delete/schedule/approve/upload/report-generate/pay, ever. See
[`vault/_meta/Read-Only-Guardrails.md`](vault/_meta/Read-Only-Guardrails.md).

## Flipkart is four surfaces, not one

| # | Surface | Host | JIVO login | Live? |
|---|---|---|---|---|
| 1 | **Seller Hub** (3P marketplace) | `seller.flipkart.com/napi` | `ecom8@jivo.in` (JIVOMART) | current |
| 2 | **Flipkart Ads / FSN** | `seller.flipkart.com/fed-ads` | `ecom8@jivo.in` | current |
| 3 | **Vendor Hub** (1P / Grocery) | `vendorhub.flipkart.com/vendor` | `gurvinder@jivo.in`, `infinite@jivo.in` | current |
| 4 | Marketplace Seller API (public) | `api.flipkart.net/sellers` | — (no creds) | **never used** |

Surfaces 1+2 are the internal SPA XHR API; surface 4 is Flipkart's published partner API — a
**different product, not a newer generation.** Start at [`vault/00-Flipkart-Atlas.md`](vault/00-Flipkart-Atlas.md).

## The deliverable

- **`vault/`** — 37 wikilinked Obsidian notes (Phase-6 deliverable):
  - `vault/seller/` (14), `vault/ads/` (1), `vault/vendorhub/` (9), `vault/platform/` (5) — 29 section notes.
  - `vault/Flipkart-Endpoints.md` — master read-only endpoint inventory (source of truth for the CLI).
  - `vault/Flipkart-Pages-and-Routes.md` — every SPA route (377) incl. ones nobody at JIVO opens.
  - `vault/Flipkart-Data-Model.md` — how the sections join (Mermaid).
  - `vault/Flipkart-Data-Inventory.md` — **live VERIFIED numbers** vs UNVERIFIED/PENDING, per Amendment 03.
  - `vault/_meta/` — Auth-and-Access, Read-Only-Guardrails, Study-Verification (PASS).
- **`COVERAGE-LEDGER.md`** — one row per route (Amendment-03 requirement), honest walk status.
- **`captures/`** — JS corpus (202 files / 70 MB, gitignored), `seed-intel.md`, `HARVEST.md`,
  `endpoints-raw.tsv`, `sections.json`, `probes/` (live GET responses, gitignored),
  `nonget-allowed.tsv` / `nonget-flagged.tsv` (Amendment-04 audit — empty, GET-only run).
- **`cli/flipkart-portal`** — the read-only Cobra CLI (see `cli/README.md`).

## Study status (2026-07-30) — Phase 7 PASS

- **968 distinct endpoints** across 29 sections: **216 read-safe** (137 READ + 79 READ_FILE),
  **330 write/export out of scope**, **422 UNKNOWN** (documented, denied per G1).
- **377 SPA routes** enumerated (281 Seller Hub + 96 Vendor Hub).
- **202 JS files / 70 MB** harvested fully unauthenticated (0 × 401/403/429, 0 bot-check).
- **Live browser WALK of both portals** (read-only, `HO-IT-PC10`): **37 distinct section screenshots**
  (13 vendor + 24 seller), per-page network capture, 122 app-fired non-GET reads / 0 mutations.
  Live numbers: JIVO MART ~750 completed + ~570 cancelled + 1 open PO (₹6.49 L); JIVOMART 152 active /
  26 blocked / 70 inactive / 182 archived listings; payouts BLOCKED on Ads dues; 73 reports requested.
- **Self-verify PASS + lead auditor 18/18:** notes present, 0 broken wikilinks, 968/968 endpoints
  indexed (100%), 0 guardrail violations, 37 distinct screenshots (0 orphans, ratio 1.0). See
  `vault/_meta/Study-Verification.md`.

## Honest gaps (stated, not hidden)

1. Live walk was scoped to the selected vendor (JIVO MART) + JIVOMART seller; **8 of 9 vendor
   entities are PENDING_AUTH** (vendor switch is a `POST /select-vendor`, not authored). All 9 named.
2. Seller **Ads campaign count NOT_REACHABLE** — the Ads page errored on the live walk (historical
   260 kept UNVERIFIED-today).
3. Per-category **report-type** enumeration PENDING (needs the Type/Sub-Type dropdown opened).
4. 422 UNKNOWN endpoints documented but denied (G1); 7 lazy chunks hard-404 (dead on CDN).

## The CLI — `cli/flipkart-portal`

Cobra Go CLI, **216 read commands across 24 groups** + `doctor`/`auth`/`list`, generated from the
READ allowlist, with a 3-layer code-level read-only guardrail (GET-only transport · READ allowlist ·
`go test`). `cd cli && go build -o flipkart-portal . && go test ./... && ./flipkart-portal doctor`.
Method log: `captures/HARVEST.md`, and JIVO's existing narrow automation lives in `~/ecomcliauto`.
