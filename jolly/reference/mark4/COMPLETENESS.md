# Independent Mark 4 completeness audit

6 September 2026. Reviewer: source-contract/requirements agent. Confidence: high (at least 95%) for the current code and generated-model findings below. Read-only audit except this file. No Claude implementation inspected.

## Status

The implementation is an independent rule-aware planner, not a reduced frontend restyle. The major explicit machine, time, carton, projection, transparency and history requirements are implemented. **This audit does not yet prove full release completion:** the final public source feed/app deployment and logged-out rendered result remain the parent's pending work, and the new cross-day setup change must be included in final verification.

One additional material labeling problem was reported immediately to the parent: open-invoice age is displayed as observed truck waiting time. Correct this before release. Visible unresolved business questions are otherwise generally appropriate and do not, by themselves, make the agreed V1 incomplete.

## Evidence inspected

- `REQUIREMENTS.md`, meeting transcript and final clarification overrides established earlier in this same task.
- Current `site-mark4/lib/model.ts`, `rules.ts`, `types.ts`, `load-input.ts`.
- Current `components/Planner.tsx`, including all navigation views, the complete rule/speed/source page, demand row explanations and actual-history labels.
- `data/seed.json`, `scripts/supplements.json`, sanitizer field handling.
- `QA-PASS-2.md`, `REVIEW-PASS-1.md`, `DATA-EVIDENCE.md`, `UI-DESIGN.md`.
- Directly executed the current `buildModel` from the saved seed with 80% efficiency, no night session, strict recipes and no proposed supply. This was a fresh execution, not merely a test-report read. It emitted 15 rules, 10 questions, completed calendar days 1–5 September, separate MES/booked values, the verified groundnut transition, per-machine raw/effective rate evidence and invoice-age data. These are dated-seed scenario results, not refreshed operational facts.

## Requirement-by-requirement findings

| Requirement group | Current implementation evidence | Assessment |
|---|---|---|
| Independent computation | `buildModel` normalizes recipes/orders/history, performs shared material consumption and daily machine/storage allocation. API recalculates supplied scenario. | Implemented; no Mark3 forward schedule reuse found. |
| Machine compatibility | `rules.ts` rejects Clear Pack 3/15 L and sesame, excludes JP yellow mustard, prioritizes JP mustard/allowed groundnut, 10 Head small bottles, 6 Head 5 L, Tin Head 15 L tins. Plastic 3 L derives a disclosed rate; 3 L tins remain held. | Matches accepted facts/preferences with uncertainty visible. |
| Sessions/efficiency | One effective 10-hour day session, at most one 10-hour night extension, Sunday no production, raw capacity × one efficiency factor. UI can choose night line/auto/none. | Implemented. Cross-date setup accounting is changing during audit; final test/runtime needs latest build. |
| Campaign behavior | At most two justified campaigns per machine/day; 1-hour product-change setup, including across dates; same-product continuation no additional setup. First horizon startup provisionally zero. | Both preference and invented setup bound are disclosed; no unsupported measured setup claim. |
| Carton transition | Verified FG0000142→FG0000461 merges demand identity and uses new per-piece recipe. Whole cartons are consumed. Unsupported 16-piece recipes stay blocked; optional narrow physical-fit hypothesis produces clearly conditional output with strict comparison. | Implemented evidence-backed transition. Broad mapping not supplied by user; visibly held families are legitimate unresolved data, not a silent narrowing. Do not market every family's replacement as solved. |
| Projection/PO priority | Monthly target remains, provisionally subtracting booked MTD; required make is max of remaining production target and stock-uncovered PO demand. Confirmed and inferred ecom allocations are distinguished, future reserve can fulfill later orders. | Implemented current interpretation; target meaning remains explicitly provisional. No independently computed historical GT/MT average is claimed. |
| History | Exact elapsed calendar days retained, missing days represented as null/partial, booked and MES never added, settling day visibly marked. | Implemented. `complete` is presented as “Read,” not “all physical production audited.” |
| Production value | Desired ₹2.5 crore/day, minimum ₹2 crore, production-day denominator, known-value subtotal and unknown full gap when some valuation is missing. | Implemented; denominator and old realization source remain disclosed assumptions. No August calibration transfer or guaranteed target claim found. |
| Labour | Session cost unavailable when no verified rate; rule explains recorded run costs are not session rates. | Appropriate unresolved source limitation, not fabricated zero/free labour. |
| Warehouse/dispatch | Physical pile includes FG and estimated billed waiting stock, declared working limit, daily forecast and Sunday departures. Source age/volume limitations shown. | Implemented, but invoice-age headline below needs correction. |
| Full assumptions page | Rules view shows 15 rules, exact raw/effective capacities and dated evidence, questions, source stamps and collected-input notes. Covers rates, machine rules, setup, carton mapping, demand/MTD, storage/drain lag, inbound assumptions, nonmoving rooms, value, labour, deferrals. | Substantially covers user's explicit “all things you are taking” requirement. Eligibility reasons, container correction, outlier valuation and per-product/carton details also appear on Demand/run drawer. |
| Usability | Line-first shift board, daily selection, machine details, material search/gap filter, dispatch, demand, actuals and final rules navigation exist; scenario persistence is implemented. | Code coverage is substantial. Final rendered/mobile/persistence behavior must be proven in parent's browser verification; tests alone do not establish it. |
| Two reviews | Pass1 discovered substantive identity, storage, quantities and allocation defects; pass2 independently exercises corrected behavior with 31 passing tests. | Two meaningful review iterations exist; latest setup edits need rerun. Final public build must include fixes, not an older preview. |
| Release | Separate source-feed URL and Vercel app planned; hardcoded app input feed points at independent host. | Pending main agent. No final public release assertion can be made from this audit. |

## Actionable gap: open invoice age is not completed dispatch wait

Current `Planner.tsx` Dispatch view labels `model.dispatch.medianDays` as **“Typical observed wait”** and **“Middle wait in the recorded sample.”** The seed's `dispatch_aging`/supplement evidence is a **windowed open invoice book**, with median age 8 days and oldest age 34 days at its source timestamp. It is explicitly not reconciled physical storage and does not establish invoice-to-truck elapsed time.

The same page separately states an inherited usual departure lag of 2 days and tail of 14 days. Without a precise label, the page appears to present competing measured truck-lag results. The requested feature is days of pendency, which the invoice-age sample can inform honestly.

Fix: label these values **“Median age of open invoices”** and **“Oldest open invoice in sample.”** Keep the window/company/reconciliation caveat adjacent. Describe the separate 2/14-day figures as prior invoice-to-gate measurement/scenario assumption with its date, not the same sample. Confidence: high; source schema/note and rendered component text directly establish the mismatch.

## Unresolved questions that are correctly visible

These are not deferred implementation work disguised as questions: the recording/clarifications did not supply the missing facts, and the site preserves their impact rather than pretending they are solved.

- Exact 3 L tin route/speed, broken-labeller workaround, yellow-mustard normal pairing.
- Remaining 16→20 SKU/carton identity and whether existing old FG can ship as-is.
- Production target versus availability target; daily-value denominator.
- Provisional pack/setup rates, Tin Head staffing, nonmoving-room material usability.
- Verified session wage cost and chosen GT/MT historical averaging window.

Do not let these become broad completion claims. In particular, the independent build has one live-verified replacement family, not all replacement families, and a transparent monthly projection, not a newly validated sales-prediction model.

## Final completion proof still required

1. Correct the invoice-age labels and verify the final rendered Dispatch page.
2. Rerun relevant acceptance checks after the cross-day setup changes; verify final browser build is the same current code.
3. Verify all eight views, rule/speed/source coverage, responsive layout, scenario application/reload persistence, and current-versus-saved status on the final running app.
4. Verify independent input feed updates successfully or honestly retains dated inputs with failed-refresh status; do not let a successful HTTP fetch make an old snapshot “live.”
5. Deploy the distinct Vercel project publicly, verify logged-out 200 and application/API behavior, and provide its short production URL.

Drums, live WhatsApp/employee rule updates and August backtesting are explicitly deferred and must not be added as completion blockers.

## Final release audit — supersedes the earlier pending implementation states

The independent application is deployed at **https://jivo-mark4-astha.vercel.app**. Re-read final current source and retained artifacts on 6 September 2026:

- `HTTP-PUBLIC.json`: `passed: true`; nonempty deployed model returns 200 and names the independent deterministic engine. Three distinct scenarios return 200; malformed, invalid and oversized requests are rejected. Public response private-field/path/JWT scan passes. This is runtime evidence from the public app, not the earlier localhost preview.
- `BUILD-FINAL.log`: production compilation and TypeScript complete successfully; generated root page and dynamic `/api/model` route exist.
- `TESTS-FINAL.log`: **35 tests passed, zero failed/skipped**, including the last cross-date product-change setup regression. This supersedes the earlier 31-test snapshot.
- `REVIEW-PASS-2.md`: independent verifier rechecked first-pass identity, material demand, FG allocation, source-retention and storage fixes; then reproduced and verified the cross-date setup correction on the synchronized runtime.
- `BROWSER-FINAL.log`: public Plan, Machines, Materials, Dispatch, Demand, Actuals and Rules views render their intended titles, without page overflow or visible alerts. Rules shows all 15 rules; mobile width 375 and tablet width 768 do not overflow. Tablet Plan includes earlier actuals and blocking explanation. Run dialog closes with Escape and restores focus to its originating run. Parent additionally inspected final desktop/mobile/tablet screenshots visually.
- Current Dispatch component now reads **“Oldest open invoice in sample”** and **“Median age of open invoices.”** The additional gap found by this audit is corrected. Source read clocks and adjacent unreconciled-invoice explanation remain present.
- Current loader still distinguishes retained/error headers, old material/source timestamps, last-good data and seed fallback. Public API success does not replace observation timestamps. The source-loader regressions exercise failure/retention paths.

All proven implemented acceptance checkboxes have been updated in `REQUIREMENTS.md`; M1–M12 table requirements remain covered by the explicit matrix above, source rules and final independent tests. The final public reload/network-recovery and root-page evidence is being appended by the parent; that append must be read before treating the remaining release checkbox as fully proven.

### Honest remaining data limitation, not a new implementation claim

The trailing-demand ranking checkbox remains unchecked intentionally. `data/demand-evidence.json` documents that authenticated prior GT/MT evidence is incomplete/account-scoped; the implementation supports `supplements.salesRank`, but this snapshot does not contain a defensible calculated trailing-sales rank. It continues the authorized monthly projection and asks which historical window to use, without inventing ranks or presenting a new historical average. Final user clarification [13] explicitly supports keeping the production projection. Therefore this does not invalidate the delivered agreed V1, but **a complete historical GT/MT ranking must not be claimed as achieved**.

Likewise, visible unresolved carton families, staffing/labour, 3 L tins, labelling workaround, MTD meaning and value denominator remain conditional knowledge, not demonstrated plant facts. No additional current engine or page feature defect was found by this completion pass. Confidence is high for the implementation/release evidence actually inspected; operational outcome/target attainment is not established by these checks.

### Final release closure

Read the appended `BROWSER-FINAL.log` and security/review closure records after the preceding audit. The previously pending evidence is now present:

- Public `#today` renders “A plan for every line.” with no alerts or overflow and visible source status; this completes all eight views.
- Successful application of a no-night scenario is preserved exactly across a full reload; rendered selection remains `none` and no night run appears.
- Injected network failure retains the calendar and shows the failure/retry message; restoring fetch and refreshing removes the alert while preserving the plan.
- Current public Dispatch labels and material-search/proposed-purchase distinctions were directly checked.
- Public root returned **HTTP/2 200 without a login redirect**, observed 6 September 2026 00:26:48 UTC. Input health reports `ok:true` and `retainedLastGood:false`.
- Final feed suite reports **15 tests passed, exit 0**, including retained/error headers and original observation dates. The separate public API security checks and scoped reviewer closure are recorded.

The release acceptance checkbox is now checked. **No required implementation or release gap remains for the agreed independent Mark 4 V1.** The historical-ranking limitation is an allowed visible source question under final clarification [13], which retained the monthly projection and did not resolve the history window; it must remain disclosed and must not be sold as a completed calculated ranking. The unchecked rank item deliberately preserves that distinction. All other unresolved business assumptions remain shown in the delivered Rules & questions page. Confidence: high for the verified V1 behavior and release; this does not establish actual future production or ₹2.5 crore/day attainment.
