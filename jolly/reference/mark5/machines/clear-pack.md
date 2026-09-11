# Clear Pack — MARK V machine specification

Reviewed 10 September 2026. **Design evidence only; engine unchanged.** Confidence:
high for the approved values and source extraction; incomplete for unlisted
transitions, exact bottle tooling and full-shift output because these are absent
from the supplied evidence. No further numeric-approval gate applies.

Authority: [WORKING-RULES.md](../WORKING-RULES.md), especially M5-R01 and M5-A01;
[complete PDF review](../PDF-REVIEW-2026-09-10.md). Independently read the exact
revised PDF pages 2–3, 12–14, 17–18 and 41–42 in bounded text extractions.
PDF: `/Users/damanpreetsingh/Documents/Codex/2026-09-09/make/outputs/Machine_Changeover_Planning_Red_Notes_Edition.pdf`;
recorded SHA-256 `b3388f02852783347fa04f9d23e1a9260d46477f7132d65464bdbc7238636fe3`.
Revised notes outrank contradictory historical transcript wording. Daman adopts
these operating values and separately instructs the plan to assume flushing reuse.

## Running rates and physical routes

| Physical fill | Approved running rate | MARK IV value | MARK V treatment |
|---|---:|---:|---|
| 1 L bottle | 4,800 containers/hour | 4,800/hour | Retain numeric rate; label running output. |
| 4 L plastic bottle/can | 25–30/min = 1,500–1,800/hour | 800/hour | Replace old rate and retain the range. |
| 5 L plastic bottle/can | 25–30/min = 1,500–1,800/hour | 3,000/hour | Replace old rate and retain the range. |

PDF p12 N1 supplies the final rates; p42, 26:37–27:50 establishes the omitted
1 L hourly unit, rejects 2 L and explicitly supports both 4/5 L. Earlier “only
1 and 5 L” does not exclude 4 L. No 3 L/15 L route is established; previous
explicit exclusions remain. Tins, pouches, drums and unknown primary containers
are not Clear Pack routes.

Running rates are not measured accepted output per elapsed shift. Do not apply
an inherited 80% factor, treat running speed as uninterrupted output, or silently
select the range midpoint/minimum. A scheduling choice within the approved range
must be visible. Per-hour litres are derived from physical fill; sales-unit output
also depends on `containersPerPiece` and cannot be confused with bottle output.

## Bottle and BOM boundary

Current code inspection: `site-mark4/lib/rules.ts` allows 1 L 40 g bottles with
preference 95, 52 g with preference 70, and 4/5 L plastic packs; unknown 1 L
families are held. These preferences are MARK IV scheduling policy, not PDF
measurements. Earlier [requirements M6/M7](../../mark4/REQUIREMENTS.md) support
40 g preference, feasible 52 g use without exclusivity, and the specific exclusion
of sesame 1 L 20-piece packs. The revised PDF does not certify every oil/SKU that
happens to use those weights or revoke the sesame restriction.

`model.ts:physicalRecipe` reads the primary container and gram marking from BOM
component names, excluding labels/caps/cartons; `Product` retains `bom`,
`bottleGrams`, `fillLitres`, `containersPerPiece` and `exclusionReason`. Eligibility
is called with physical `fillLitres`. Preserve recipe/identity holds and conditional
carton-transition status before assigning a route. Do not infer bottle weight
from the finished-goods name, substitute bottle/cap item codes by matching size,
or allow a tin because its nominal litres match a supported plastic pack.

Exact neck, design, change-part set and item-code compatibility are not encoded
by bottle grams alone. “52 g feasible” is distinct from a verified route for a
particular new bottle design. Existing confirmed BOM matches can retain their
routes; unverified new families must remain distinguishable. The source's common
1 L cap-size statement excludes mustard and is not substitution approval.

Code scope issue to resolve explicitly in implementation: the present `/sesame/`
guard rejects all pack sizes although its message and M7 name 1 L. Keep the known
sesame 1 L prohibition; neither assert other sesame sizes are proven impossible
nor enable an unverified route merely by narrowing that regex.

## Changeovers: state and direction matter

| Transition/component | Approved duration | Interpretation |
|---|---:|---|
| Parts: 1 L → 5 L | 1 hour | Mechanical work only; reverse and 4 L transitions are not separately timed. |
| Same bottle design, changed oil | No mechanical part change in the described example | Applicable flushing still occupies the line (p17, 00:31–00:43). Same litres/grams alone do not establish identical bottle design. |
| Base flushing | 30 minutes | Revised note does not assign every oil pair. No universal fallback claim. |
| Mustard → cold press or another oil | 1 hour or more | Flushing; directional; upper bound unknown. |
| Rice bran → cold press | 45 minutes | Flushing; do not use historical 45–50 minutes or infer the reverse. |
| Generic daytime SKU change | About 1 hour | Parts/flushing inclusion unresolved; cannot override a specific longer case. |

The combined mustard/pack-change example (p18, 01:53–02:01) describes flushing
in addition to parts work. For that 1 L → 5 L example, sequential accounting
therefore gives **at least two hours**, not one; this is derived arithmetic, not
a new measured fixed duration. Do not assume overlap or generalize that sum to
every transition. Same-oil pack changes do not automatically require an
oil-change flush. Unknown cleaning requirements must stay explicit.

Scheduler design should carry previous oil family and actual bottle/pack state
across dates, identify mechanical and flushing components, record whether a
source duration is combined, and preserve ranges/open bounds. Unknown transition
timing must be surfaced rather than represented as measured zero or the old
blanket one-hour penalty. “Cold press” in a source pair still requires an explicit
SKU/oil-family mapping; name matching alone cannot resolve every target oil.

## Flushing inventory and calendar

- Approved flushing quantities: mustard **1,000 L**, other oils **550 L**
  (PDF p13 N2). These are operating estimates adopted for MARK V.
- M5-A01 assumes reuse: do not deduct the whole quantity as recurring fresh-oil
  consumption or scrap. Keep volume handled, saleable output and actual loss
  separate. Reuse does not prove 100% recovery, zero make-up, immediate recovery
  or available opening flushing stock. Recovery timing/loss remain unspecified.
- Flushing time remains machine occupancy even when its oil is reused.
- Reported start is **07:30 ±30 minutes**; it does not establish a complete shift
  clock, breaks, preparation time or net hours. One night line is an overall
  operating limit, not a guaranteed Clear Pack night allocation.
- Bottle-jam/cleanup incidents are examples, not a measured failure frequency.
  The deleted space-bottleneck sentence creates neither a new fixed penalty nor
  permission to remove the declared warehouse capacity.

## Acceptance cases for the later implementation

1. Supported 1 L gets 4,800/hour; 4/5 L retain 1,500–1,800/hour with explicit
   range policy. Old 800/3,000 values cannot survive as MARK V approved rates.
2. BOM-based 40/52 g 1 L routes remain distinct from unknown/unsupported bottle
   families. Reject 2/3/15 L, sesame 1 L and non-plastic containers; do not let
   a recipe identity hold or conditional carton recipe become unconditional.
3. A sales unit containing multiple bottles uses the bottle's physical fill to
   select the rate, then divides containers/hour by containers per sales unit.
4. Same bottle with rice bran → cold press gets 45-minute flushing without a
   fictitious one-hour parts change. Its reverse stays unspecified.
5. Mustard → another oil keeps the one-hour-plus flushing bound. Adding the
   documented 1→5 L mechanical work cannot collapse to a one-hour total or
   silently overlap. Specific changes outrank the generic entry.
6. Carry line configuration across midnight; changing the calendar date does
   not erase required setup. Same-SKU continuation does not create a new setup.
7. Flushing reuse does not remove elapsed flushing time, charge 1,000/550 L as
   waste, add that quantity to saleable output, or manufacture available stock.
8. No remaining-session calculation promises a completion time using an unknown
   upper-bound setup, unresolved oil pair or unstated range choice as exact fact.

These are proposed acceptance cases, not executed engine tests. Only this
machine document was created; no scheduling, source-system or deployment changes.
