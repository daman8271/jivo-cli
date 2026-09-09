# Mark 4 acceptance checklist

Prepared 2026-09-06 from `meeting-transcript.md` and `clarifications.md` in this folder. This is the independent Codex build's requirements record, not Claude's implementation. Confidence is high (at least 95%) for explicit instructions below; unresolved mechanics are labelled separately.

## Authority and scope

The meeting supplies operating knowledge. Daman's subsequent messages override it: the final user message is `[13]` in `clarifications.md`; `[8]` and `[9]` contain earlier user clarifications, substantially duplicated. Statements by the other assistant are research leads, not verified business facts. The recording ends at 17:04 and Daman confirms there is no second part.

- [x] Build an independent Mark 4 that changes the planner's machine behavior and produces more relevant schedules. A frontend restyle alone does not satisfy the request (`clarifications.md` user `[3]`/`[4]`).
- [x] Use a multi-phase plan and multi-agent orchestration (final user `[13]` and current build request).
- [x] Finish V1, inspect and improve it twice, then verify the final result (current build request).
- [x] Publish a distinct public Vercel project and verify logged-out access. This latest explicit request supersedes the earlier localhost-only experiment; preserve Claude's checkout and deployments.
- [x] Keep factory facts sourced from ji.jivo.in, oil/monthly plan from EXIM, GT/MT orders from OMS, and ecom orders from ecom. Never use SAP as a fallback for factory facts.

## Engine requirements: eligibility and preferences

Eligibility is a hard constraint. Preferences decide between eligible machines; a preferred machine does not imply exclusive eligibility unless explicitly ruled below.

| ID | Acceptance criterion | Evidence and latest override |
|---|---|---|
| M1 | No 3 L or 15 L run on Clear Pack. | Meeting 03:03–03:29 and 05:38; user `[8]`/`[9]` reaffirms. |
| M2 | No 15 L run on 10 Head or 6 Head. Route 15 L tins to Tin Head only. | 05:48 and 08:05–08:20. The contradictory wording at 08:21 does not override the repeated exclusive rule; subsequent discussion distinguishes 5 L printed tins. |
| M3 | Allow supported 3 L packs on 10 Head and 6 Head. Do not retain the old blanket “no machine” error. | 03:03–03:29. Exact 3 L tin routing remains an open question; do not treat all 3 L containers identically. |
| M4 | Prefer JP for 1 L mustard. Groundnut is allowed; JP is not restricted to Kachi Ghani alone. | 06:22–06:33 and 12:13–12:20 are superseded by user `[8]`/`[9]`: JP is mainly mustard and also groundnut. |
| M5 | Do not force yellow mustard onto JP. Choose a supported machine from evidence and disclose the choice. | Final user `[13]` says they checked it never ran on JP and authorizes judgement. Previous “all mustard on JP” was explicitly an opinion. |
| M6 | Prefer Clear Pack's current 1 L 40 g bottle family. Treat 52 g as potentially allowed, not Clear-Pack-only. | 06:43–07:07; user `[8]`/`[9]` says 52 g can run there, asks current material check and says use 40 g if current. Detailed specifications deferred to Mark 5/6. |
| M7 | Never schedule sesame 1 L 20 pcs on Clear Pack. Remaining supported 1/2 L bottle families can use 10 Head/6 Head. | 11:42–11:50. Do not generalize bottle weight from SKU name without BOM evidence. |
| M8 | Prefer 1 L/2 L on 10 Head; prefer 5 L on 6 Head because all 10 heads cannot fit large cans. Keep “less suitable” distinct from “impossible.” | 07:07–08:05. |
| M9 | Prefer printed 5 L tins on 6 Head because its labeller is broken and those tins need no label. Do not route every tin to Tin Head simply because it is metal. | 05:57, 08:21–08:44. Exact restriction/workaround for other labelled packs remains uncertain. |
| M10 | Pouches only run on Pouch Machine. Forecast pouch demand can still be planned, considering available labour and cost, even without a current PO. | 09:20, 12:23–13:03. |
| M11 | Drums are excluded from Mark 4 scheduling. Identify excluded demand if needed to reconcile totals; never describe it as physically impossible or add a manual drum capacity. | 02:45–04:07 is superseded repeatedly by user `[8]`, `[9]`, final `[13]`: add drums later. |
| M12 | Read physical container type from BOM/recipe rather than the erroneous plan-sheet pack column; show this decision on the rule/assumption page. | 05:38–05:48 and 08:05; user `[13]` answers Q9 yes and confirms item 2. Claimed specific affected codes from assistant `[7]`/`[12]` require independent BOM verification. |

## Engine requirements: time, efficiency and scheduling

- [x] **10 effective machine hours per session**, not 12. A selected day-plus-night machine may have 20, not 22/24 (14:21–14:38).
- [x] **At most one machine gets the night session**, chosen by the planner/operator. The meeting's mustard-on-JP example is a date-specific example, not a permanent night assignment (11:11–11:30).
- [x] **80% of the capacity basis** is used for planning. Publish the exact rate and its unit, where it came from, the 80% calculation and effective output. Never silently apply 80% to an already derated value and describe it as 80% of rated (09:04; final user `[13]`). Missing pack-specific rates must be disclosed as derived or unavailable, not measured.
- [x] Prefer one product for a whole day/session and minimize repeated changes. If a change is needed, account for setup/clearance and explain why; do not invent a hard all-day single-SKU ban (09:28–09:59).
- [x] **No Sunday production**, including a night session attributed to Sunday. Physical dispatch can still relieve warehouse pressure (13:14–13:24). Do not close dispatch just because production is closed.
- [x] Respect shared material availability across all machine allocations. A bottle/carton/oil unit used on one line cannot also enable another line. Check line hours and stock conservation against the actual schedule.
- [x] Use factory-sourced labour cost per session where available, with basis and coverage. Missing cost must read “not available,” not zero. “JA” means ji.jivo.in, confirmed user `[9]` answer 15 (12:43–13:03).

## Demand, cartons and production value

- [x] Keep the monthly production projection. Do not replace it with current POs plus a flat buffer (10:27–11:02; detailed explanation in final user `[13]`).
- [x] Explain that GT/MT orders tend to arrive heavily near month-end; the plan prepares goods before those orders land. Confirmed POs receive focus when present, while projected requirements remain visible.
- [x] Where history is used, distinguish GT/MT from ecom. OMS is the preferred GT/MT history source. The exact averaging window (3/6 months) was never selected; do not claim a calibrated historical average if none was computed. Continuing the monthly projection is explicitly supported by final `[13]`.
- [ ] Respect trailing demand evidence when ranking low-demand, non-PO products, such as the canola 5 L example (10:19–10:37). Do not implement arbitrary SKU suppression based on that example alone.
- [x] Model the **1 L 16-piece to 20-piece carton transition** in the BOM and product identity. Bottle/piece demand remains a different unit from carton count; 20 bottles per carton requires different carton consumption from 16. Expose substituted product codes/components and unresolved mappings (04:26–04:43, 15:51–16:02; final user `[13]` confirms wherever 16-piece carton is used, use 20-piece instead).
- [x] Do not claim replacement packaging is available or compatible without stock and BOM evidence. Unsupported replacements must remain visible with their reason; do not quietly produce old 16-piece packaging because its legacy BOM exists.
- [x] Treat **₹2.5 crore/day as desired production value**, with ₹2 crore discussed as the minimum. It is not a current billing figure, an achieved result, or permission to force infeasible output (13:41–14:11 superseded by user `[8]`/`[9]` and final `[13]`).
- [x] Show feasible planned production value and the gap to the target, with valuation source/date. Do not promise target attainment merely because it is requested. Resolve daily denominator/closed Sunday presentation explicitly; a Sunday shutdown must not be presented as a surprise production failure.

## UI and operational explanation

- [x] Overview is **line by line**, showing what each machine should do and relevant actual running behavior. Keep aggregate numbers secondary to actionable machine choices (05:05–05:23).
- [x] Show why a SKU belongs on a machine, why a preferred alternative was not used, what material blocks it, and the relevant speed/session assumptions. A plan that still feels like “alien language” misses the user's stated purpose.
- [x] Preserve the warehouse split: unbilled FG plus billed-but-not-physically-dispatched stock. Billing does not release space. BH-BT and BH-PF remain the FG rooms; storage limit remains the previously declared fact (00:37, 14:47–15:04; user `[9]` answer 16).
- [x] Emphasize the **open dispatch book and days of pendency**, rather than “trucks left today.” Show the usual and long-tail wait as measurements/assumptions with their dates, not guaranteed truck appointments (00:43–01:08). If current oldest/detailed pendency is unavailable, say so and show what source does support.
- [x] Preserve upstream stock and missing-material explanations (15:08–15:42).
- [x] Add a dedicated final **“what this plan knows and assumes” page** listing every adopted machine rule, exact speed/rate basis, inferred choices, BOM/container correction, carton substitution, source freshness, exclusions and unresolved questions. This includes things taken as facts, not merely things labelled uncertain (final user `[13]`, repeated several times).
- [x] Keep actual completed days separate from planned future days. Unknown/partial source reads must not appear as zero. Never add MES and booked production because they overlap.
- [x] Use generated/computed business figures, appropriate unit conversions, and no raw phone numbers. Do not carry the old August 0.16% claim over as validation of the changed Mark 4 planner.

## Explicit deferrals and non-requirements

- **August backtest: deferred.** Final `[13]`: build Mark 4 first; skip now. Required tests should verify rules/conservation, not tune Mark 4 to August.
- **Drum scheduling: deferred**, even though the meeting provides a manual rate.
- **Actual WhatsApp sending/employee feedback/autonomous rule updates: deferred** by the final `[13]`. Earlier discussion at 15:21–16:57 describes the future feedback loop. No live messaging is required or authorized by the final Mark 4 scope.
- **Detailed machine engineering/specification matrix: Mark 5/6**, per `[8]`/`[9]`. Mark 4 still needs transparent defensible rates and current known constraints.
- No requested ability to write factory-system records, change production infrastructure, or automatically enact a schedule.
- MTD netting is **not explicitly settled in this transcript**. It is a planning correctness decision, not permission to silently subtract overlapping current stock and historical production.

## Questions to carry visibly, in simple language

These do not block building the agreed parts. Present conservative behavior and the exact assumption until answered.

1. Which 3 L tins should run on Tin Head, and at what pieces/hour? Plastic 3 L is allowed on 10 Head/6 Head; no verified 3 L tin rate/routing appears in the recording (03:03–03:29; user `[9]` answer 11).
2. While the 6 Head labeller is broken, can labelled bottles use a separate labelling process? What labour/time does that add? (08:21–08:44.)
3. For yellow mustard, which bottle and line should be the normal choice? Daman authorizes an evidence-based interim choice and says it never ran on JP (06:43 and final `[13]`).
4. Which 20-piece replacement SKU/carton goes with each old 16-piece SKU, and what should happen to remaining old stock? The transition is agreed; a complete mapping is not supplied (04:26, 15:51–16:02).
5. Is the monthly sheet a target for goods **made** this month, or goods available for sales including opening stock? This determines how to subtract already-made goods without counting the same stock twice. No explicit meeting answer.
6. Should ₹2.5 crore be shown against every calendar day or each production day? Sunday is closed; exact denominator was not resolved (13:24, 14:09, final `[13]`).
7. For any pack without a measured capacity, which rate should Gurvinder confirm? Disclose temporary derived rates; do not turn them into observed facts (03:47–03:56, 09:04).
8. Is Tin Head staffed whenever the plan needs it? Prior assistant claimed sparse run history, but availability is not settled by that claim (user `[9]` answer 10).
9. If GT/MT demand is derived afresh from historical sales, how many months should the average cover? Continue the authorized production projection meanwhile (10:37–11:02, final `[13]`).

## Current source feasibility evidence

Read-only inspection of `../.mark4-local/study/state.json`, collected `2026-09-06T05:12:01+05:30`:

- Factory history reports complete through 2026-09-05 and contains per-day `booked_by_item`. This is a source snapshot, not a claim that every business booking is final.
- Current `factory_production` hourly masters and stocks (`lines`, `line_configs`, `fg_stock`, `pm_stock`, corresponding details) are null in this non-hourly cycle. The public current-state body alone cannot support a stock-constrained planner. Retrieve the correct last-good hourly snapshot privately with its timestamp, or make a scoped current read.
- EXIM `plan` contains aggregates and a private state-file locator, not per-SKU rows. Detailed plan/cache or a privately generated freeze is needed.
- Existing `sim/live-inputs.json` is a useful private integration contract for plan/BOM/items/stock/orders. It should not be published raw: publish only the intentionally selected UI/model fields and source stamps. New replacement SKU BOMs may require additional private reads.
- Existing Mark3 simulator uses global hours, prior efficiency, repeated same-day runs and combined forecast/PO ranking. It cannot implement the above solely through new page copy.

## Evidence needed to close acceptance

For each requirement, retain source/rule reference and the generated output or runtime behavior proving it. Minimum meaningful checks: forbidden line/pack cases, preference fallback, 80% unit math, one-night-line bound, Sunday production-off/dispatch-on, setup hours, shared stock conservation, 16/20 carton math and SKU identity, projection/PO separation, missing-source handling, no unsupported target claim, persistence of user-selected scenarios if offered, responsive rendered pages, full assumptions coverage, and two documented review/fix passes. Verify the final public URL serves the independent build without login.

## Final acceptance status — 6 September 2026

Implemented acceptance criteria above are checked against the current source, 35 passing final model tests, 15 passing feed tests, successful production build, public API checks and all eight rendered views in `BROWSER-FINAL.log`. The independent app serves logged-out HTTP 200 at https://jivo-mark4-astha.vercel.app; persisted scenario reload, refresh failure/recovery, responsive views and current dispatch-age labels are verified. `COMPLETENESS.md` records the detailed evidence audit.

The remaining unchecked trailing-demand item is **evidence-limited, not an unimplemented required V1 feature** under final clarification [13]: the monthly projection is explicitly retained, no historical window was selected, and incomplete OMS history cannot support a trustworthy GT/MT rank. The planner supports an evidence-supplied rank, keeps the forecast and reports the unresolved history basis; it does not arbitrarily suppress the canola example. A computed complete historical rank is not claimed. This is an allowed visible question/data limitation, not permission to call missing historical records zero. All explicitly deferred drums/WhatsApp/backtest work remains deferred.
