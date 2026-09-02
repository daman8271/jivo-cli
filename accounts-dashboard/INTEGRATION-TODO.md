# v2 integration items — found during the build, to close before cutover

Tracked here so nothing found mid-build is lost when the agents finish.

## 1. Section-local caveat codes have no text  — RESOLVED BY DESIGN 22:5x
Specs use two caveat namespaces: `C-00xx` (global JIVO corrections, resolvable
from `harness/corrections/`) and section-local codes like `P-GROSS-NOT-NET`,
`P-LAKHS`, `P-FIFO`. The section-local ones appear in every KPI's `caveats[]`
but **no spec defines their text** — the prose lives in the spec's `traps[]`
with no link back to the code.

Left alone, `derivation.html` renders a bare code and the caveat section — the
whole point of the drill-down — says nothing.

**Resolved:** `derive.py` resolves every `C-*` from `harness/corrections/` and
attaches its full title, rule, wrong and right text. Section-local codes are
emitted with `scope: "section"` and the section's ENTIRE `traps` list travels
with every derivation record (`section_traps`), so the drill-down shows the real
prose rather than a bare code. No separate glossary needed.

## 2. board.css / core.js / ui.js may have been written light-only
CONTRACT.md §0 rule 7 originally said "light-only" — that was wrong; v1 ships a
full dark theme and **defaults to dark**. The contract was corrected (§6.1) at
19:12, but the four Foundation agents may have read the old version.

**Fix:** after Foundation, check `board.css` for a `:root[data-theme="dark"]`
block, `ui.js` for a `#themeToggle`, every page `<head>` for the no-flash
bootstrap script, and `charts.js` for hex literals baked in instead of reading
CSS variables at render time (charts stay light-themed after a toggle otherwise).

## 3. v1 shows a count where it should show money  — CONFIRMED LIVE BUG
`site/index.html:793`
`mk('Over-reversed (debit bal.)', String(dr.length), ...)` renders the COUNT of
accounts, not the amount, beside tiles that all show money. Accounts sees `8`
where the figure is **₹1.37 Cr** (Oil; 8 accounts, ₹1.10 Cr of it
`2161007 SALARY PAYABLE JUL`). Mart ₹0.17 Cr / 7 accounts, Bev ₹0.05 Cr / 5.

Verified independently from `data.json`, all three books. NOT patched in v1:
another session is concurrently editing that file. v2's provisions page must
show the amount.

## 4. A 12th section is arriving in v1
Another session is adding a **JSAP budget register** to `build_data.py` via a new
`pipeline/builders/` mechanism (non-HANA sections with their own connection,
returning the same payload shape). v1 already renders 13 section cards.

v2 assumes 11 sections in several places. `split_data.py` must iterate whatever
`data.json` contains rather than a hardcoded list, and the budget section will
need its own spec + page before cutover — or be explicitly listed as not yet
carried across.

## 5b. Manifest size
80.9 KB (~13 KB gzipped) — over the 40 KB target in CONTRACT §2 because it
carries a label for each of 387 KPIs. Acceptable over the wire; if it grows,
move labels into the section slices.

## 5. Independent verification still reads the same artefact
`verify.py` re-derives each KPI by a different route, but from the same
`data.json`. That catches query and aggregation errors; it cannot catch a wrong
`.sql`. A genuinely independent check would re-query HANA by a different path.

Not worth doing on the 2-minute loop (37s of queries already, ~31% duty cycle on
one HANA session). **Proposal:** a once-daily `deep-verify.py` that re-derives
the eight headline figures straight from HANA by an independent query and files
a dated report. Not built — needs Daman's go-ahead on the extra production load.


---

## RESOLVED — verification results, 2026-08-22 ~23:00

Built and run: `split_data.py`, `kpis.py`, `derive.py`, `verify.py`, `history.py`,
`build-v2.sh`, `browser-check.sh`, `cutover-v2.sh`.

| Check | Result |
|---|---|
| KPIs derived | **387** (129 x 3 books) from 8 section specs |
| Roll-up vs each facet, 13 sections x 3 books | **0 disagreements** |
| A/R and A/P re-derived by a second query | **agree at +0.0000%** on all 3 books |
| C-0005 intercompany | **PASS** — no intercompany card reaches a TRADE headline |
| Corrections located in code | 7 of 7, **0 UNVERIFIED** |
| KPI independent check | 292 green · 37 red · 58 amber (no independent measurement) |

Traps this build walked into and fixed, each now a comment in the code:
1. Summing all non-total rows in a multi-facet section reads **+300%** — five
   facets stacked in one result set. Each facet must reconcile separately.
2. `open-item-list` publishes a **top-N slice** (669 of 13,030 open A/R
   invoices); its `DT_OPEN_ALL` column is the untruncated total. Summing visible
   rows understated the book 20-35%; the first attempt reported a confident
   640% "disagreement" that was entirely an artefact of the check.
3. Comparing a board figure against a **fresh HANA read 22 minutes later**
   measures the clock, not the query. Both routes must come from one build.
4. A `unit: pct` KPI whose closing term is its own column divides by itself and
   reports a confident **100%**.
5. Term closure asserted on `agg='first'` KPIs produced exact 2x / 3x / negated
   "failures" — an artefact, not a defect. Closure is asserted only where
   summing terms is semantically valid.
