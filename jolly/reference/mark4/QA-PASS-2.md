# Proof — second independent review

Date: 2026-09-06. Scope: completed V1 deterministic model, scenario behavior, source-loader failure handling and current sanitized seed. Changes made by Proof are confined to acceptance tests and QA evidence; no production application changes.

## Result and practical boundary

**35 tests passed, zero failed, zero skipped:** 30 independent acceptance tests plus 5 engine-authored edge tests. Confidence is high for the exercised rules, stock accounting and source-status behavior. All previously reproduced first-pass failures are covered by passing regressions.

This clears the deterministic-model test gate. It does not establish that every business assumption is true, the production plan will be achieved, supplier lead times are commitments, or the published UI is ready. Browser interaction, responsive rendering and public Vercel release need the parent's separate runtime evidence.

Initial second-pass TAP output, before the final cross-day setup extension, command run from `jolly/`:

```text
node --experimental-strip-types --test site-mark4/tests/*.test.ts
# tests 31
# pass 31
# fail 0
# cancelled 0
# skipped 0
# todo 0
# duration_ms 5460.804166
```

Full transient log: `/tmp/mark4-proof-pass2.log`.

A second direct verification ran from `site-mark4/`, with no pipeline masking its exit status:

```text
node --experimental-strip-types --test --test-reporter=dot tests/*.test.ts
....................
...........
exit_code: 0
```

## First-pass defects: now reproduced by passing regressions

- Missing completed calendar days remain null/incomplete rather than disappearing.
- Partial cartons consume whole physical units; a fraction of one carton does not enable a deliverable pack.
- A PET bottle with an integral handle remains a bottle even when carton/accessory text contains “bottle.”
- Finished goods made before a future order opens are allocated when that order becomes current, billed into the waiting pile, and dispatched under the stated delay.
- The real source physical FG total plus standing stock reconciles exactly with model opening storage; the 4,240 L canonical replacement double count is removed.
- OMS non-Oil product-code collisions are excluded from Oil demand and described in assumptions. The explicit BEVERAGES collision fixture cannot overwhelm the Oil target.
- Buying proposals consume carton units, not bottle units: 100 bottles require five 20-piece cartons. Shared material requirements aggregate across products and net stock/accepted inbound once.

## Combination-pack assertion was corrected from source evidence

The seed contains four distinct combination SKUs: FG0000033, FG0000091, FG0000429 and FG0000088. Each has a 2 L sales-unit volume and a BOM containing two `PM0000194` bottles named `PET BOTTLE 1 LTR 40 GMS`. Therefore the physical filling size is 1 L, while saleable units/hour are physical containers/hour divided by two.

The full-seed assertion now checks:

```text
raw physical containers/hour × 80%
  = effective sales units/hour × containers per sales unit
```

A new independent fixture pins the arithmetic: a line at 100 one-litre bottles/hour produces 80 bottles/hour at 80%, which is 40 two-bottle sales units/hour. Over ten hours it produces 400 sales units, 800 litres, and consumes 800 bottles. It cannot incorrectly claim 800 combination units or route the pack as a physical 2 L bottle.

## New second-pass behavioral coverage

- Provisional carton mode remains off by default. A narrowly matching bottle and closure fixture produces conditional output, retains its old product identity, consumes the replacement carton and reports a separately recomputed strict baseline.
- Changing the closure prevents that provisional substitution. The matching test is nonvacuous: it requires positive conditional production.
- Procurement aggregates shared packaging, nets opening stock plus accepted dated inbound, and computes whole-carton quantities.
- Hypothetical procurement uses the explicitly provisional 7-day packaging / 14-day oil delays. It cannot produce before both receipts; assumed arrivals remain labelled.
- Missing product valuation leaves total valuation and target gap unknown while preserving the known subtotal and unvalued litres. Missing values never become a claimed complete zero.
- Exact OMS order quantities remain distinct from the inferred per-SKU/day ECOM allocation.
- A publisher-retained response is stale even when HTTP succeeds, old stock stamps cannot create a fresh-green status, and an unavailable first fetch falls back to the dated seed rather than fabricating live observations.

## Scenario executions before the final setup correction

Before the final cross-day setup fix, all four scenarios completed with the engine's checked invariants; the independent full-seed test separately checks run totals, positive scheduling, stock and storage equations, physical-container efficiency and routing.

| Scenario | Runs | Planned litres | Conditional litres | Opening physical storage |
|---|---:|---:|---:|---:|
| Strict stock/recipes | 37 | 567,928.6065 | 0 | 596,589 L |
| Proposed supplies | 82 | 1,605,763.3655 | 0 | 596,589 L |
| Provisional recipes only | 37 | 567,928.6065 | 0 | 596,589 L |
| Both switches | 82 | 1,605,763.3655 | 0 | 596,589 L |

These are **earlier derived QA scenario outputs from the saved seed**, not final release figures, live production facts or commitments. The final cross-day setup correction changes some schedules; use the final served model for current output. Seed dates remain visible in the model. No current legacy family passes the narrow bottle-and-closure provisional recipe gate, so the recipe switch correctly has zero impact on this snapshot. The positive matching fixture proves that the scenario does work when the specified evidence is present; the mismatched fixture proves it stays held otherwise.

The corrected excluded drum demand is 41,000 L in these executions. Removing unrelated company-code collisions is a source-identity correction, not evidence that those unrelated orders do not exist in their own companies.

## Remaining stated limits

The original unresolved questions remain business decisions: target meaning, exact replacement packaging mappings, 3 L tin routing, labelling workaround, session labour cost, line staffing, non-moving stock availability, historical demand window, and target-day denominator. Tests confirm transparent handling, not the answer to those questions. Detailed trailing GT/MT evidence remains incomplete. The new planner has not been backtested against August, as explicitly deferred.


## Final second-pass extension and direct verification

Cassius identified a missed day-boundary setup. Proof independently reproduced it: with JP at 100 bottles/hour, day 1 makes 800 A bottles in ten hours. B's packaging arrives on day 2; switching to B incorrectly charged zero setup and allowed a full ten production hours. The regression failed before the fix with `0 !== 1`.

After the engine began retaining the previous product across dates, the same fixture passed: day 2 charges the provisional one-hour changeover, makes 720 B in nine hours, and day 3 continues B without an invented repeat setup, making 800 in ten hours. Day/night capacity checks remain active.

An additional labour fixture confirms two campaigns sharing one occupied session incur the verified session charge once, while a short following session still costs one session. Unknown session labour remains null.

Final direct command from `site-mark4/`, observed exit code 0:

```text
node --experimental-strip-types --test --test-reporter=spec tests/*.test.ts
✔ cross-day product change charges setup while same-product continuation does not
✔ verified session labour charges an occupied session once, including short campaigns
ℹ tests 35
ℹ suites 0
ℹ pass 35
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 5031.38275
exit_code: 0
```

All 30 independent acceptance cases and all 5 engine edge cases ran in that final command, including full current-seed reconciliation. No findings are being waived by a skip. Deterministic-model clearance applies to this post-fix state; runtime/publication checks remain separate.
