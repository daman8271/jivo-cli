# Rebuild plan — after the verify pass

**Started:** 2026-08-30 · **Trigger:** the verify pass refuted 106 of 293 claims, and the
published brief is materially wrong.

The rule for this rebuild: **nothing gets re-published until the tool that produced it has
been fixed and the claim re-tested against live data.** The verify pass exists because
confident output outran its evidence; repeating that at speed would be worse than the
original.

---

## Phase 1 — Fix the instruments ✅ DONE

Nothing downstream is trustworthy until these hold.

| Defect | Status |
|---|---|
| `probe` blind to punctuation — "sugar-free" returned 0 while ARY holds 24 SKUs as "Sugar Free" | ✅ **fixed** — normalised match on both term and column. All four spellings now converge on 24 SKUs / ₹68,825; "mamaearth" and "Mama Earth" both return 16 |
| `probe` "non-deterministic" | ❌ **not reproduced** — three identical runs returned identical output. The verify pass's own claim does not survive. Recorded, not actioned |
| `assort.go:103` stock valued as `SUM(Qty) × MAX(PurchaseCost)` — reads −₹1.82 Cr vs −₹14.13 L row-wise | Phase 1b |
| `ary audit uncounted` — exception list read as a census | Phase 1b |

## Phase 2 — Reconcile the corpus

- `assort/research/verify/` and `priority/` are **empty on disk** though the work exists in
  the vault note. Harvest them so `ary assort priority` / `sweep` can read them.
- **Re-run every "probe returned zero" verdict** through the fixed probe. The two REAL_GAPs
  (pharmacy-Rx, medical devices) were *confirmed* with the broken tool and must be re-tested
  before they survive.
- Fix `Data-Quality-Traps.md` **trap 3** — payment amounts DO reconcile on the right column
  pair (`Amount − ReturnAmount`): ₹7,66,19,575 vs `SUM(BillAmount)` ₹7,66,19,249, **₹326
  apart on ₹7.66 Cr.** The trap as written is false.

## Phase 3 — Rebuild the vault (multi-agent)

Six notes carry refuted claims. Each is rewritten against the live DB, not against the old
note. Cross-links must survive — the vault is 29 notes / 132 wikilinks with zero broken.

| Note | What has to change |
|---|---|
| `Institutional.md` | **The case is dead.** EU's ₹2.51 Cr is cooked-meal transfer charges plus staff boarding offset by staff collections. ARY's EU account is stoles, kurtis and curtains against ₹3,709 of edible oil |
| `Below-Cost-Leak.md` | **Milk is not a subsidy.** All 13,605 litres and all −₹67,094 go to the Delhi NGO. Zero litres to residents |
| `Pharmacy.md` | Blocker **restored** — FusionERP8 cannot hold batch/expiry (0 real expiry dates in 111,253 rows). And the economics are negative: ₹2.66 L GM against a mandatory pharmacist at ₹2.16–3.00 L |
| `Catalogue-Shape.md` | Dead tail is **₹10.43 L over 397 lines**, not ₹1.07 Cr — 96% of the "13,400-line tail" is empty catalogue rows holding nothing |
| `Data-Quality-Traps.md` | Trap 3 is false; add the probe-punctuation trap and the stock-valuation defect |
| `Ten-Moves.md` | Reordered entirely around replenishment |
| **NEW** `Availability.md` | The finding that replaces the brief — 3,049 of 5,953 retail SKUs out of stock, and the natural experiment that proves it |

## Phase 4 — Rebuild the published brief

The live site still serves all five refuted claims. It is rebuilt around the availability
finding, with the institutional section removed rather than softened.

**New headline:** *ARY is not short of things to sell. It is short of the things it already
sells.*

The natural experiment leads, because it is the strongest evidence in the whole exercise:
on the 42 best-stocked days ARY sold **₹12.55 of snacks per bill**; on the 45 worst, **₹9.47**
— on identical footfall, 998 vs 997 bills/day.

## Phase 5 — Verify the rebuild

Adversarial pass over the rebuilt vault and brief. Every figure re-checked against live
data. No claim ships that a second agent could not reproduce.

---

## Standing rules for this rebuild

- **Never sum the lanes.** ₹13.3 Cr grounds to ₹53 L revenue / ₹9.8 L GM — a 96% cut.
- **Do not add any SKU** as a recommendation until replenishment holds a quarter. 51.2% of
  the working range is empty.
- Read-only throughout. Zero `sapb1` calls.
- Every number: VERIFIED (query recorded) / ESTIMATED (assumption stated) / NOT-CHECKED.
- **A refuted claim is deleted, not softened.** The old text stays only in
  `Corrections-Log.md`, where the pattern is the point.
