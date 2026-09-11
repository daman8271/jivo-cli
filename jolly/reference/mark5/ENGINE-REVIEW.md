# MARK V independent engine review

10 September 2026. Reviewed all seven machine specifications and implementation acceptance requirements, the scheduler, machine policy, product normalization and timed material ledger. Only this report was edited. Targeted synthetic probes ran on the VPS with Node's TypeScript stripping; no full build or live factory writes. Quantities below are synthetic, not factory observations.

## Retest outcome

All four findings below were fixed by the engine owner and independently reprobed on the updated VPS source. The night now selects 10 Head for the outstanding 3,800 L due today; the mixed-container combo is excluded; the Clear Pack different-SKU change reserves a conditional 60 minutes with unknown source range; and the decimal 15.0 KG Tin route is rejected. All four targeted regressions pass. No open finding remains from these reproductions. Approved-run replay still requires the broader acceptance suite; it was reviewed by inspection here.

## Findings sent immediately to engine owner and root — now fixed

### P1 — Night selection can make a future order while leaving feasible orders due today

`site-mark5/lib/planning-engine.ts`, night candidate comparator (line 219 at review): candidates sort by **all confirmed litres**, then total litres. The condition that opens the night checks due work, but its choice does not rank output addressing that due work.

Reproduction: fresh 10 September, 06:00 IST opening; no previous campaign; abundant oil, packaging and space. A 2 L sunflower order requires 20,000 L on 10 September; a 15 L sunflower tin order requires 150,000 L on 20 September. Monthly forecast is zero. VPS result:

| Run | Litres |
|---|---:|
| 10 Head day, due 2 L | 16,200 |
| Tin Head day, future 15 L | 81,000 |
| Tin Head night, future 15 L | 27,795 |

Validation is true. The explanation says the night addresses “remaining due work”, although 3,800 L due today remains feasible on 10 Head. Rank night candidates by achievable litres due on/before the planning date before future confirmed demand; make the explanation describe the selected work. Confidence: high, reproduced through `runEngine` on the latest VPS engine available at the probe.

### P1 — Mixed-container combo silently becomes a different physical pack

`site-mark5/lib/model.ts:43`, consumed by `machine-policy.ts:11` and the scheduler: `containersPerPiece` takes the **first** matching primary component coefficient. It does not detect multiple distinct primary containers.

Reproduction through `normalizeProducts`: a 2 L sales unit has one 1 L 40 g bottle, one distinct 1 L 52 g bottle, 2 L oil and a carton coefficient. Result: `containersPerPiece=1`, `fillLitres=2`, `exclusionReason=null`; `route(product, '10 Head')` approves 900/hour. The recipe actually contains two distinct 1 L bottles and lacks a verified single homogeneous machine campaign. The inferred 2 L physical pack is false. Detect multiple primary formats and hold the product until its component campaigns/packing interpretation are established. Merely summing the coefficients is insufficient where bottle formats differ. Confidence: high, reproduced on VPS.

### P2 — Different Clear Pack SKU is given an approved zero-minute change

`site-mark5/lib/machine-policy.ts:55`: different SKU codes, same sunflower oil family and identical bottle component IDs return `minutes=0`, `basis='approved'`, `ruleId='CP-parts-1-to-5'`, `requiresConfirmation=false`.

The machine spec's changeover table proves 1 L→5 L mechanical work at 60 minutes and mentions a generic daytime SKU change around an hour with unresolved inclusion. It does not prove a label/carton/SKU change takes zero. Preserve zero for actual same-campaign continuation; represent unmeasured different-SKU handling explicitly. Confidence: high for reproduced output and unsupported source label; the exact required duration remains unknown.

### P2 — Tin mass guard misses decimal spelling

`site-mark5/lib/machine-policy.ts:14`: the guard only recognizes the literal pattern `15` followed by optional whitespace and `kg`/`kilo`. A product named `SUNFLOWER 15.0 KG`, container tin, normalized fill 15 receives an unconditional 600/hour route. The approved source rates 15 L; a 15 kg product needs sourced physical litres **and a separately established rating basis**. Preserve structured mass identity through normalization and reject mass-rated products without that evidence, independent of name formatting. Confidence: high for direct policy probe; no claim that a current live SKU uses this exact spelling.

## Rechecked / not open findings

- An earlier fixed-machine-order suspicion was withdrawn after the current VPS engine scheduled due 5 L demand before a competing 1 L forecast using shared oil. Global day candidate selection already addresses that reproduction.
- The current source exempts due quantities and exact operator requests from the desirable 125,000 L forecast pacing limit. Do not describe the old hard-cap issue as still present.
- The owner added exact approved-run replay, replacing the earlier changes-only behavior. During review, replayed night runs initially allowed another automatic night machine; the latest local source now guards automatic night with `!runs.some(r => r.shift === 'night')`. This specific path is fixed by inspection; a full approved-plan regression remains Proof's scope.
- The material calendar checks timed receipts and preserves existing future reservations in availability. No additional demonstrated premature-use or double-reservation defect was found in this bounded review. This is not a blanket certification of all receipt-source semantics.
- Root's separate null actual, live-FG double deduction, prior-plan ordering, freshness and date-validation findings were not duplicated here.

## Review boundary

Code was being edited concurrently. Findings above were sent to root, engine owner and Proof, then retested after the fixes. Re-run the small regressions against the release revision. No deployment, source collector or full-build verification was performed by this reviewer.
