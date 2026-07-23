---
title: "SOURCES.md — the godown inventory (verified 2026-07-19)"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: reference
tags: [jivogpt, jivo-desk-cli, sources]
---

# SOURCES.md — the godown inventory (verified 2026-07-19)

Every path the CLI reads, with observed shape. All access is READ-ONLY.

## 1. Platform sweep results (live, overwritten per sweep)
`/opt/ecom-intel/platforms/<platform>/result.json` — dict with keys
`summary`, `perPin`, `allRows`, `partial`. `allRows` = flat row list
(sku/product fields, price, mrp, availability, pincode, store info — exact
field names vary per platform; discover defensively).
`result.last-good.json` — last complete run (fallback when `partial`).
Platforms (10): `amazon amazon-fresh amazon-now bigbasket blinkit flipkart
flipkart-minutes instamart swiggy-instamart zepto`.
BigBasket extra: `result_pincode.json` (pincode-wise serviceability).

## 2. Daily snapshots — the today/yesterday axis
`/opt/ecom-intel/today/` — per-section snapshot advanced as sources land:
`_manifest.json  daily/ platforms/ pricematch/ skus/ locations/ competitor/
runs/ weekly/ monthly/ index.md`.
`/opt/ecom-intel/today.prev/` — same structure, yesterday's build.
`--date yesterday` ⇒ today.prev; older dates ⇒ dated files below.

## 3. Price-match
`/opt/ecom-intel/data/pricematch/daily.csv` + `history.csv` (dated rows).
`/opt/ecom-intel/tools/pricematch/Jivo-Price-Match-YYYY-MM-DD.xlsx.summary.json`.
Vault views: `/opt/ecom-intel/today/pricematch/pm-<SKU>.md` (per-SKU markdown).

## 4. DRR panel
`/root/jivo-drr-panel/build/panel.json` and `build/bundle.json`.

## 5. QC + health
`/opt/ecom-intel/reviews/<platform>-daily-YYYY-MM-DD.json` (+ timestamped runs).
`/opt/ecom-intel/logs/doctor/daily-YYYY-MM-DD.json`.
Known gotcha: doctor RED can be just swiggy — don't panic-report.

## 6. Deliverables (list only, don't parse)
`/opt/ecom-intel/output/Competitor-Price-Watch-*-YYYY-MM-DD.xlsx` and siblings.

## 7. Baselines
`/opt/ecom-intel/baselines/<platform>.json` — reference rows for drift checks.

## Semantics contract
- Freshness = source file mtime, always surfaced in `meta.freshness`.
- `partial: true` in a result.json ⇒ prefer `result.last-good.json`, flag it.
- Date resolution: `today` → live files; `yesterday` → today.prev/ or dated
  file; explicit `YYYY-MM-DD` → dated reviews/doctor/output files where kept.

Linked: [[docs/DESK_CLI|DESK_CLI]] · [[docs/READ_ONLY_LAW|READ_ONLY_LAW]] · [[/README|JivoGPT]]
