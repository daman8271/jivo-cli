# Proof — first V1 review and regression pass

Date: 2026-09-06. Scope: deterministic planner, rules, input normalization and sanitized current seed. Independent test ownership: `site-mark4/tests/acceptance.test.ts`. The original meeting and final user clarification [13] were read alongside REQUIREMENTS.md. No Claude Mark4 implementation inspected.

## Current result

The latest observed run passed **17 independent acceptance tests**, zero failed, zero skipped. Confidence: high for the behaviors exercised below; this is not release clearance. Engine work on provisional carton recipes and purchasing scenarios was still in progress at this run. Public deployment, browser behavior, phone masking, authorization, source freshness and visual acceptance are outside this test pass and require their separate evidence.

Command, executed from `jolly/`:

```text
node --experimental-strip-types --test site-mark4/tests/acceptance.test.ts
# tests 17
# pass 17
# fail 0
# cancelled 0
# skipped 0
# todo 0
# duration_ms 3017.96175
```

Full transient TAP output: `/tmp/mark4-proof-pass1.log`. The suite is self-contained and can be rerun without live network calls.

## Defects reproduced, sent to engine owner, then retested

1. **Missing historical calendar slots:** partial history correctly marked MTD unknown, but omitted missing date rows entirely. Fixture explicitly requires 2 September to remain visible as incomplete/null. It failed, then passed after placeholder generation was added.
2. **Fractional physical cartons:** 19 bottles with one carton consumed `0.9500000000000001` carton. Test requires a whole carton or explained deferral; 0.1 carton stock must never enable two deliverable bottles. It failed, then passed after discrete carton handling.
3. **Handled bottles misclassified:** the real seed's `PET BOTTLE 2 LTR 80 GMS YELLOW HANDLE` was excluded as an accessory because it contained the word `handle`. Seven 2 L families became unknown despite primary-bottle evidence. Independent fixture passed after primary-component discrimination was corrected.

The first transition fixture lacked a finished-good item master, so the engine correctly withheld mapping. The fixture was corrected to include the verified master and replacement recipe; this was a fixture defect, not an engine defect.

## Behavioral coverage

- 3 L plastic allowed on 10/6 Head, prohibited on Clear Pack; 3 L tin held; 15 L tin exclusive to Tin Head.
- Mustard preference/groundnut eligibility on JP, yellow mustard exclusion, sesame exclusion from Clear Pack, 52 g alternative eligibility, printed 5 L tin preference and pouch exclusivity.
- 80% applied once to an explicit raw capacity, source/basis retained, derived 3 L calculation, no invented unknown-size rate.
- BOM overrides erroneous plan-sheet PET identity; drums remain deferred without manual runs.
- Selected night machine, at most one night line, 10-hour day/10-hour night bounds and setup included in machine occupancy.
- Sunday production and target off, physical gate movement on.
- Shared oil/packaging ledger, no negative stock, every material opening + arrivals − consumption = closing.
- Ready blend consumed first, then component oils, conserving a known 75/25 mixture.
- Monthly make target nets booked MTD once, not MES, not FG twice; confirmed and reserve demand remain distinct.
- Unknown MTD and missing calendar slots; no silent completed zero.
- Verified 16/20 product identity with bottle demand retained and five replacement cartons per 100 bottles; old-carton production blocked without a verified mapping.
- Blanket arrivals excluded by default; explicit scenario differs; dated transit cannot support premature production.
- Billing moves FG into waiting; only gate departure releases physical space.
- Full current seed must contain substantial products/materials/days and positive runs. Its run totals and every storage/material equation are checked. It cannot pass by returning an empty model.
- Whole-carton edge cases and handled-bottle regression.

## Open findings and next pass

- The seed initially attached OMS BEVERAGES rows of 24,000 and 7,200 pieces to `FG0000328`, a 200 L drum product, generating approximately 7.7 million excluded litres. This is a source-code/unit mapping concern, sent to the data-feed owner and parent. It must be resolved or explicitly quarantined using evidence; passing the solver's arithmetic does not validate source identity.
- Provisional carton-replacement scenario, suggested purchasing, source error handling and final post-fix model require a second independent pass once the implementation is ready.
- No August backtest performed, as explicitly deferred. No claim that Mark4 inherits Mark3's calibration accuracy.

### Later first-pass extension — clearance remains withheld

Cassius supplied two additional concrete findings. Proof added independent regressions and ran them; **17 of 19 passed, two failed** (`/tmp/mark4-proof-current.log`).

- Make 20 bottles of reserve on Monday, a 20-bottle PO opens Tuesday: those existing goods must become billed/waiting Tuesday and leave under the stated two-day assumption Thursday. The model left them in unbilled reserve and never dispatched them.
- The current seed's authoritative `opening.fg_litres + standing_l` must equal model opening physical storage. Canonical replacement FG was counted both inside the inherited “other FG” bucket and as a plan-family stock, overstating storage by 4,240 L.

Both reproducible failures were sent to the engine owner. Earlier 17/17 result proves the earlier tests only; it is not the latest full-suite status.
