# MARK V — Tin Head

Specification only; 10 September 2026. Owner scope: this file. No scheduler or
source-system change is included. Confidence: high in the adopted 15 L rate and
the source reconciliation; unprovided setup, crew and 15 kg evidence stay unknown.

## Approved machine rule

Use the existing canonical line `Tin Head`, with **15 L tins at 10 tins/min =
600 physical tins/hour**. This is the final user-approved rate for MARK V; do not
apply an additional efficiency multiplier or ask for numeric approval again.
Elapsed shift output still depends on separately represented setup, running time,
stoppages and rejects. The rate alone does not establish any full-shift total.

Source order is current user instruction, then
[WORKING-RULES.md](../WORKING-RULES.md#sources-and-status), then revised PDF notes
and reconciliation, then the retained supporting transcript. The revised PDF
controls the old conflicting numbers. There is one scheduled Tin Head capacity;
do not invent a `3 Head` line or multiply 600 by three.

| Pack identity | MARK V treatment |
|---|---|
| Recipe-confirmed tin, explicitly 15 L per physical tin | Approved Tin Head route and 600 tins/hour; production remains subject to demand, materials, readiness and storage. |
| 15 kg tin | Preserve kg identity. Require sourced litres per filled tin and a separately established route/rate basis. Do not borrow the 15 L rate, infer density, or rename 15 kg as 15 L. |
| Other tin sizes | No Tin Head rate supplied here; report the missing route/rate rather than using the nearest size. |
| Bottle, HDPE can, pouch, drum or unknown container | This tin rate supplies no route or capacity. A numeric 15 L alone is insufficient. |

For a verified 15 L tin, one productive running hour corresponds arithmetically
to 600 tins and 9,000 L. This is not an accepted-output guarantee. If a sales unit
contains multiple physical tins, divide tins/hour by the verified container count
once; do not multiply machine capacity. That conversion establishes neither combo
packing capacity nor crew availability.

## Changeover, flushing and resource boundaries

Tin-specific parts changes, oil changes, label/carton changes, cleaning, flushing
volume, startup clearance and last-good-to-first-good duration are **unknown**.
Do not inherit JP's 5–6 hours, the head fillers' allowances, Clear Pack values, or
MARK IV's provisional one-hour setup as a measured Tin Head fact. Unknown is not
zero: any later scheduler fallback must be an explicit conditional assumption
with its source and effect visible.

The user-approved reuse assumption applies if tin flushing is represented:
flushing time occupies the machine and flushing volume is separate from saleable
output. Full flushing volume is not recurring waste. No tin flushing quantity,
recovery percentage, opening flushing stock or replenishment amount is supplied.

No Tin Head full crew, shift end/break pattern, night crew, night eligibility,
minimum batch, active-head count, downstream sealing/packing rate, shared-resource
map or normal-shift good-output record is supplied. The general one-night-line
statement does not prove Tin Head has a staffed night slot. Do not import Clear
Pack's 07:30 start or six-head labelling headcount into this machine. Routine
inline QC reports do not establish tin startup or finished-lot release timing.

## Existing code and required integration boundary

- `site-mark4/lib/rules.ts`: `LINE_IDS` already includes `Tin Head`;
  `PLANNING_SPEEDS` already contains only `15L` at 600 for it. Preserve the numeric
  rate and update the MARK V evidence attribution to the adopted revised source.
- `eligibility()` currently groups `packLitres >= 14 && packLitres < 20` as a
  15 L / 15 kg tin family. `rateFor()` independently matches
  `fillLitres ?? packLitres` to the `15L` speed key. This is not sufficient proof
  of an approved 15 kg rate. MARK V must retain nominal quantity/unit and its
  provenance so a mass pack cannot acquire the 15 L rate through a numeric fallback.
- `site-mark4/lib/types.ts`: `Product` carries `container`, `packLitres`,
  `fillLitres` and `containersPerPiece`, but no explicit nominal pack-unit or
  fill-conversion evidence fields. Preserve or add that evidence in the eventual
  design; do not guess it from the numeric volume. `PlanningSpeed` and `Rate`
  describe a rate, not a complete setup or staffing contract.
- Keep rate lookup, product eligibility and scheduler explanations consistent:
  an unresolved 15 kg pack must not be presented as production-ready simply
  because broad family eligibility is true. An unsupported rate remains absent,
  with a readable reason, not a zero-speed row or silently scheduled fallback.

## Acceptance cases for implementation

These are required future tests, not tests executed by this documentation change.

1. Explicit 15 L tin, one container per sales unit: lookup returns 600 tins/hour;
   a legacy efficiency argument of 0.8 does not turn it into 480. One verified
   running hour converts to 9,000 L, without asserting ten hours are available.
2. The transcript's `3 Head` / three-machine wording creates no extra line,
   parallel reservation or 1,800-tin/hour aggregate.
3. A 15 kg tin with missing fill-litre evidence remains unresolved. A 15 kg tin
   with sourced fill litres still requires its own route/rate basis. Even a
   numeric 15 L fill fallback must not silently select the 15 L-pack rating.
4. A 15 L bottle or unknown container cannot use the tin rate. A different tin
   size cannot select it through the current 14–<20 L family range.
5. Verified two-tin sales unit: conversion yields 300 sales units/hour while
   preserving 600 physical tins/hour; unknown/nonpositive container count cannot
   create valid scheduling capacity. Downstream combo readiness remains separate.
6. A requested Tin Head product change reports unknown setup evidence rather
   than a factory-confirmed zero or one hour. No other machine's flush volume
   or duration is borrowed. Reuse does not mint opening oil or verified zero loss.
7. No normal-shift throughput, night crew or staffed Tin Head night session is
   created solely from this rate record. Unsupported timing/resource assumptions
   remain visible in any conditional scenario.

## Source anchors

- [WORKING-RULES.md](../WORKING-RULES.md): M5-R01 adoption; approved machine-input
  table; M5-A01 reuse; boundaries requiring decisions.
- [PDF-REVIEW-2026-09-10.md](../PDF-REVIEW-2026-09-10.md): “Tin machine” under
  routes/speeds; shift/crew and QC evidence limits.
- Revised `Machine_Changeover_Planning_Red_Notes_Edition.pdf`, SHA-256
  `b3388f02852783347fa04f9d23e1a9260d46477f7132d65464bdbc7238636fe3`:
  p2 speed table; p4 tin reconciliation; p12 N1 **Speeds**, modified
  9 September 2026 at **17:26:33 IST**, “Tin machine - 15 L : 10 / min”.
  p7 Q7 explicitly leaves 15 kg route/speed missing; p8 Q12 leaves tin setup
  missing; p9 Q15–18 leaves timetable, complete crews and shared resources open;
  p10 Q20/Q22 leaves packing and release evidence open.
- Supporting original transcript only: pp49–51, **36:06–38:14** contains the
  superseded three-head/three-machine and 500/8/10 ambiguity. It does not widen
  the revised 15 L specification.
