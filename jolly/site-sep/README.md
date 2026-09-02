# site-sep — JIVO Mark 1, September 2026 FORWARD PLAN

September has NOT happened. Everything on this site is a plan produced by the
calibrated simulator (August backtest: 0.16% off actual), not a record.
Never touch `../site` (the deployed August replay) — read it, copy its idiom.

## The one rule

**NEVER type a business number in JSX/copy.** Every figure is computed by
`scripts/gen-data.py` from the verified artifacts and imported from `data/*.json`
via `lib/data.ts`. UI constants (widths, paddings, Tailwind tokens) are fine.
Rerun with `npm run gen`; the script fails hard (and writes nothing) if any of
its 55 cross-checks or phone-mask scans fail.

## Data contract (`data/`)

| file | what it holds |
|---|---|
| `overview.json` | totals, plan, demand split, opening, storage flags, scenarios mini, materials mini, unproducible SKUs, Q2/Q4/Q13 |
| `spine.json` | 30 rows — per-day made/shipped/util/storage/runs/blocked/bought, orders split REAL vs FORECAST, PO landings, event counts, `open_real_l_computed` |
| `days/day-NN.json` | full day detail: runs, blocked, unblocked, waiting_on, received, orders_real / orders_forecast, dispatches split, events, honesty block |
| `lines.json` | per-line stats + slot rates (`rate_basis`: rated / observed / derived) + all runs by line |
| `storage.json` | physical / in-godown / invoiced-not-trucked / headroom series; ceiling carries `assumed:true` (Q2) |
| `materials.json` | 209 order-by rows (`late`, `zero_literal`, `zero_august_rule` flags), BOTH zero definitions, opening at-zero, 4 unproducible SKUs |
| `build.json` | per-day per-machine sequences with changeovers; recipient number masked |
| `whatsapp.json` | 5 threads, 55 simulated drafts, `assumed:true` on every message, ZERO replies, numbers masked |
| `scenarios.json` | 12×26 baseline vs 22×30 / 24×30 / 12×30, extra-hours-used %, storage-binder evidence |
| `loops.json` | blocker → order → land → unblock → first-run chains from events |
| `honesty.json` | measured[], assumed[], provenance, the 14 label rules, August calibration |
| `questions.json` | Q2 / Q4 / Q13 one-liners |

## Labeling rules that ship or lie (enforced in the data; render them)

1. `book.po_cumulative_value_rs` = **cumulative value ordered** — never "open PO value".
2. Unshipped litres = `open_real_l_computed`; `po_open_l_raw` overstates.
3. Always split orders REAL vs FORECAST — quiet days are 100% forecast; ~60% of demand by litres is forecast (`demand.forecast_share_litres_pct`).
4. `opening.oil_l` and day `oil_on_hand_l` are DIFFERENT definitions — never one series.
5. FORECAST rows stay visually distinct (`SimBadge kind="forecast"`).
6. Storage ceiling is ASSUMED (Daman's spreadsheet, Q2) — badge it.
7. `standing_l` at open is a declared OPTIMISTIC assumption (C-0054).
8. Ecom plan volume is spread evenly (declared assumption, FCST-W0).
9. The day-1 order pile is MEASURED reality (backlog mostly overdue at freeze).
10. Clear Pack 5L / Tin Head: "observed rate, then 50% efficiency" — never "50% of rated" (strings ship in `lines.json`).
11. 4 plan SKUs are UNPRODUCIBLE (no 3L/DRUM line) — show them, don't hide them.
12. FG0000155 realise is an inherited outlier — never headline unqualified (`honesty.json label_rules`).
13. WhatsApp is simulated drafts — never render as sent/received traffic.
14. **NO real phone numbers** — masked at the data layer; keep it that way.

## Dev

```
npm run gen     # rebuild data/ from ../sim + ../out artifacts
npm run dev     # Next.js 16.3.3 (same major as the August site)
npm run build   # must stay green
```

Routes: `/`, `/days`, `/days/[day]`, `/lines`, `/storage`, `/materials`,
`/order-by`, `/build`, `/whatsapp`, `/floor`. All are stubs with live data
readouts — flesh them out in the August site's component idiom
(`components/Card.tsx`, dark zinc, dense, data-forward; `SimBadge` marks
plan/assumed/forecast/measured/derived everywhere).
