# Astha material supply rollout — verified live, 6 September 2026

Scope: the independent `jivo-mark4-astha` application and `/root/mark4-astha` runtime only. Mark 3 and Claude's Mark 4 remain untouched. Source systems receive GET reads only.

## Runtime layout

- `mark4-astha-material-orders.service`: fresh full supplier catalog and PO scan, four workers, target interval 180 seconds, private per-supplier history retained.
- `mark4-astha-materials.service`: independent stock, gate/QC, EXIM and reconciliation loop, target interval 180 seconds.
- `mark4-astha-material-history.service`: hourly check for missing history back to current material PO creation dates; old monthly reads cached for 24 hours. This keeps historical warming separate from the fast loops.
- Shared private cache: `/root/mark4-astha/private/material-supply` (directory mode 700, service umask 0077).
- Published ledger input: `/root/mark4-astha/state/material-supply.json`; only scalar-allowlisted fields reach HTTPS.
- Existing `mark4-astha-inputs.service` merges the ledger into `/inputs.json`.
- Existing factory and demand collectors continue serving their other responsibilities.

These settings are installed. Two complete supplier and material cycles were observed after installation; see the evidence below.

## Release order

1. Preserve existing app and service backups (already captured at `/root/mark4-live-phase3/baseline-app.tgz`, `baseline-factory.service`, `baseline-inputs.service`).
2. Stage integrated source separately on VPS; use existing node dependencies to avoid redundant disk use.
3. Pass Python and TypeScript tests, typecheck, build, independent review and source-to-model replay.
4. Collect a private live candidate and compare PO lines, receipt stages, stock units and dataset clocks with direct source evidence.
5. Install only owned app scripts and feed modules; create the private directory, install the two new units, reload systemd, start orders first and material reconciliation after an initial order scan.
6. Verify candidate feed and observed cycles before deploying the Astha frontend. Do not substitute service `active` for successful full collection.
7. Deploy the linked Astha Vercel project, make public, verify logged-out HTTP 200, expected/recorded views, action list, source ages and dark mode.
8. Capture two independent cycles with `ops/mark4/verify_material_http.py`; investigate mismatched revisions rather than counting an old cached response as new.

## Rollback

Stop and disable only `mark4-astha-material-orders.service`, `mark4-astha-materials.service` and `mark4-astha-material-history.service`. Keep their private evidence. Restore Astha scripts/feed from the dated baseline archive; remove the new material-supply file from the published state directory by moving it into the private evidence directory, then restart only `mark4-astha-inputs.service`. Redeploy the prior Astha frontend if necessary. Existing factory/demand services and all Mark 3 cron jobs stay in place. Never restore the whole repository over concurrent work.

## Verified release evidence

- Vercel deployment `dpl_FoLgAE5ypb1SGVrDS3pbdaqCr9Rp` reached READY and was aliased to `https://jivo-mark4-astha.vercel.app` on 6 September 2026. Public-setting check reported already public, no failures; logged-out HEAD returned HTTP 200.
- Final integrated TypeScript suite: 76/76 passed. Typecheck passed. VPS production build passed using webpack (staging shares an external node_modules symlink, unsupported by Turbopack). Vercel's normal Turbopack production build also passed.
- Python source suite: 50/50 passed. Independent QA: 11 raw source, 11 source-to-model and 4 bookkeeping checks passed, plus nine real HTTP update variants and retained-last-good failure handling.
- Fresh reviewed candidate at 2026-09-06 16:16:32 UTC: 216 material PO lines, 1,206 physical/commitment lots, 110 expected receipt batches including 8 oil batches. 173 PO lines reconciled; 43 remain explicitly unresolved. Physical QC stages are preserved.
- Historical backfill covered 20 additional months, November 2024–June 2026: 422 entries, 86 linked to 33 current material POs. Older API-empty months do not prove all corresponding book receipts never existed.
- Owned collector units installed/enabled at 21:51 IST. Full supplier scans succeeded in 116.65 and 116.97 seconds. Material cycles succeeded in 137.61 and 139.37 seconds. History worker succeeded; all four owned input/material services remained active after verification.
- Auth-cache access: materials service permits the existing EXIM client to refresh `/root/jivo-courier/exim/.secrets`; no business-system write route was added. Other source paths remain protected.
- Additional exact feed backup: `/root/mark4-live-phase3/baseline-feed.tgz`.

## Cutover and automatic refresh

The backwards-compatible frontend was deployed first. After the first production material file completed, the owned inputs service was restarted to enable the ledger. `production-cycle-1.json` and `production-cycle-2.json` both passed the HTTP acceptance script against the public feed and Vercel API.

- First source material observation: 21:54:17 IST, public revision `66c163cc4a07741b6282cdf0`.
- Second source material observation: 21:57:19 IST, public revision `67ba34bcae0f3fb863b93b00`.
- Both public model revisions matched the corresponding source feed. All material dataset reads were complete. Default expected and explicit recorded-only API scenarios both passed.
- Supplier/material workers target 180-second start intervals; full scans take roughly two minutes. The feed caches for 15 seconds, server input caches for 15 seconds, and the open browser polls periodically. These stages mean automatic updates are not an instantaneous guarantee. The controlled source-change HTTP replay observed approximately 16 seconds from fixture change to changed API model without deployment.
- The input response bound is now 10 MB, retaining header and streaming checks; the reviewed source payload was 4.45 MB. API scenario request bounds remain unchanged.

## Visible checks

The public site returned HTTP 200 without login. Browser evidence under `browser/` shows the material comparison in light and dark mode, plus a 390×844 mobile viewport. Mobile scroll width equalled viewport width (390px). Recorded-only selection and dark mode survived reload; recorded-only showed zero estimated-supply litres. Browser console reported no errors. All task-owned browser and candidate-feed processes were stopped and verified gone; production services remain running.

## Limits retained honestly

173 of 216 current material order lines reconcile; 43 have source/history/identity uncertainties and stay actionable. Supplier promised dates remain absent on many POs. Estimates are based on qualifying historical samples and carry explicit arrival/QC assumptions. Accepted-unposted loads with unresolved stock inclusion are not credited again. NM room availability remains an unresolved business rule.

The page's wider partial-source banner also remains valid: five active trade orders lack readable details, and the legacy machine-capacity provenance timestamp is missing. The new material datasets themselves completed successfully. This release does not claim to resolve unrelated demand/recipe/capacity evidence gaps or guarantee future production.

A private follow-up CSV, including real PO references, was saved at `/Users/damanpreetsingh/Documents/Mark4-live-materials-2026-09-06/material-order-followup.csv`. Raw source snapshots remain private on the VPS.
