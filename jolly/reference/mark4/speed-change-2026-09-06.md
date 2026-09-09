# Astha Mark IV selected speeds — 6 September 2026

User instruction: use the supplied Mark IV base-speed screenshot as the final planning speed table, and recalculate connected outputs. Screenshot values apply directly, without another efficiency reduction. This supersedes the earlier 80% default in the original release record.

Public app: https://jivo-mark4-astha.vercel.app/#rules
Deployment: `dpl_VhhzWz7KuaKkyHLG9Ms3jJbh5kV8`, production Ready. Logged-out HTML and GET/POST model requests returned HTTP 200.

## Authoritative policy

`site-mark4/lib/rules.ts` owns the dated policy. Live factory ratings and inherited capacity inputs cannot replace it. These are declared planning speeds, not measured achieved output.

| Machine | Pack | Final containers/hour or status |
|---|---|---:|
| JP Machine | 1L | 5,400 |
| Clear Pack | 1L | 4,800 |
| Clear Pack | 4L | 800 |
| Clear Pack | 5L | 3,000 |
| 10 Head | 1L | 2,100 |
| 10 Head | 2L | 1,260 |
| 10 Head | 3L | 720 |
| 10 Head | 5L | 900 |
| 6 Head | 1L | 1,080 |
| 6 Head | 2L | 720 |
| 6 Head | 3L | 384 |
| 6 Head | 5L | 600 |
| Tin Head | 15L | unavailable |
| Pouch — Hitech | POUCH | 1,800 |
| Pouch — Samarpan | POUCH | not separately scheduled |
| Manual | — | not modelled |

## Connected behavior

- `rateFor()` supplies scheduling, night selection, run hours, material consumption, warehouse movement and planned value. Combo sales units divide by physical containers per sales unit.
- All policy rows display regardless of current products. Tin is held explicitly; no speed is invented.
- The efficiency slider is removed. Valid legacy settings normalize to efficiency 1 while preserving night, supply, recipe and incoming-date choices. The public browser migration was verified from efficiency 0.8, no night shift and enabled provisional recipes to efficiency 1 with both unrelated choices retained.
- Factory source records and historical observations are unchanged.

## Verification

- 53/53 application tests passed on the isolated VPS copy; TypeScript and production build passed. Vercel production build also passed.
- Two independent code-review passes found no material defects in the final patch.
- Independent QA checked all numeric policy rows, poisoned and missing source-rate resistance, bottle/pouch combo conversion, legacy scenario handling and production/value/material/storage/session conservation across five scenarios. Evidence: `speed-change-evidence/qa-report.json`.
- Public GET and legacy POST both returned the complete selected table and efficiency 1. Browser displayed 16 policy rows, no efficiency slider and no console errors.
- Same-input before/after comparison is recorded in QA evidence. Higher selected speeds do not establish proportionally higher monthly output; material, storage and other model constraints remain.

## Scope

Only Astha app code/tests changed, plus this release evidence. No change to Mark 2, Mark 3, the other Mark 4, factory configuration, source collectors or existing production services. No commit or Git push performed. The original release record remains dated historical evidence.
