# MARK V machine study: 10 Head

Reviewed 10 September 2026. Design specification and acceptance cases only;
the scheduler has not been changed. Confidence: high in the extracted approved
rates, route restriction and revised changeover wording. Exact oil-pair mapping,
full-shift good output and recovery losses remain unspecified.

## Authority and evidence

- `../WORKING-RULES.md`, especially M5-R01 and M5-A01, and
  `../PDF-REVIEW-2026-09-10.md` govern this study. Daman adopted the revised PDF
  figures as actual operating inputs; they do not await further numeric approval.
- Authoritative PDF: `/Users/damanpreetsingh/Documents/Codex/2026-09-09/make/outputs/Machine_Changeover_Planning_Red_Notes_Edition.pdf`,
  revised 10 September 2026, SHA-256
  `b3388f02852783347fa04f9d23e1a9260d46477f7132d65464bdbc7238636fe3`.
  Directly extracted bounded page groups 2–3, 12–14, 32–33 and 43–45.
- Primary revised notes: N1 Speeds on p12; N4 10 HEAD on p14. Revised tables
  pp2–3 implement those notes. Retained contradictory historical speech does not
  override them.
- Inspected `site-mark4/lib/rules.ts` (eligibility, speeds, setup constant and
  rate conversion), `types.ts` (Product/PlanningSpeed/Rate), and `model.ts`
  (recipe-derived units and physical-fill route matching).
- Visually inspected the supplied screenshot at
  `/Users/damanpreetsingh/.codex/attachments/048b059c-7ac2-421b-af24-d91080dddf58/image-1.png`.
  It shows the factory start-run form, not an observed completed production run.

## Adopted running rates and routes

| Physical bottle fill | Approved rate | Arithmetic hourly equivalent | Operational route |
|---|---|---|---|
| 1 L | 30–35 bottles/min | 1,800–2,100 bottles/hour | Supported |
| 2 L | 15 bottles/min | 900 bottles/hour | Supported |
| 3 L, 4 L, 5 L | No MARK V operating rate | Unavailable | Excluded: larger labels do not fit the operational route |

The revised N4 says all SKUs, immediately qualified by 1 L/2 L and the sticker
restriction. Treat that as broad oil suitability within supported bottle packs,
subject to recipe, identity and packaging compatibility; it is not a waiver for
unknown containers, drums, pouches, tins or unverified label/tooling families.

The late transcript explicitly removes 3/4/5 L (p44, 30:21–30:37), then confirms
1/2 L only (p45, 30:59–31:02). Earlier physical-filler claims (p32,
14:08–14:20) do not create usable finished-goods routes. Do not allow larger
packs with a low preference, nor borrow the 6 Head manual-label arrangement.

These are running speeds before breaks, stops and rejects. Preserve the 1 L
range; selecting a single planning rate requires an explicit visible scenario
choice. Neither 1,950/hour nor the screenshot's 2,100/hour is automatically the
settled full-shift capacity. Do not add an inherited 80% multiplier, or silently
equate running time with every elapsed shift hour.

## Setup specification

| Match | Adopted duration | Meaning and boundary |
|---|---|---|
| Mechanical parts change only | About 30 minutes | Mechanical component; does not establish oil flushing time |
| Mustard, groundnut or EV change category | 1 hour or more | Parts and flushing **combined**; exact from/to pairs are not specified |
| Cold press → sunflower | About 30 minutes | Specific directional change; revised note overrides historical 45-minute suggestion |

For the mustard/groundnut/EV category, never add the mechanical 30 minutes to the
combined 1-hour-plus entry. Preserve an open upper bound; one hour is a lower
bound, not a guaranteed complete duration. EV means the transcript's extra virgin,
but exact SKU/oil classification still needs explicit mapping.

The cold press → sunflower entry must remain directional. The reverse and every
unlisted oil pair remain unspecified. The source does not settle how a simultaneous
new pack/tooling change modifies this particular entry; do not quietly manufacture
either a 60-minute total or universal inclusion rule. A matched specific rule
must be distinguishable from a generic mechanical component.

For implementation, retain machine, physical old/new pack, old/new oil identity,
rule source, approximate/range/open-ended duration, and `parts-only` versus
`combined` scope. An unmatched transition must surface as unresolved instead of
falling through to the old universal one-hour constant. Carrying the same campaign
across a boundary does not by itself prove a new physical changeover occurred;
startup/overnight clearance is a separate unresolved operating detail.

## Flushing reuse

Daman's M5-A01 assumption applies: flushing oil is reused. Flushing still occupies
the line for the applicable setup time. Do not charge the full flushing quantity
as fresh consumption or waste, and do not count it as saleable output.

No 10 Head flushing volume is supplied by these revised notes. The Clear Pack
1,000/550 L and JP 1,500 L entries must not become 10 Head quantities. Record
10 Head flushing volume, recovery fraction, actual unrecovered loss, replenishment
and return-to-usable timing as unknown. Reuse is not measured 100% recovery and
does not create opening inventory or prove zero loss.

## Screenshot and unit contract

The screenshot shows `Production Line: 10 Head`, `Rated Speed (bottles/hr):
2100.00`, and `Required FG Quantity (cases/boxes)`. The product SKU is still
unselected. This verifies the displayed form labels/value only; it cannot prove
the selected pack, actual speed, case size, backend calculation, or approved
2 L rate. The revised PDF remains the rate authority.

Required conversion for a matched SKU:

```
physical bottles = target cases × verified bottles per case
filling hours = physical bottles / selected bottles per running hour
litres = physical bottles × physical fill litres
elapsed finish = calendar allocation of setup + filling + explicit other delays
```

For existing MARK IV types, `containersPerPiece` means physical containers per
sales unit, `fillLitres` is physical fill and `packLitres` is litres per sales
unit. `cartonPieces` is currently derived as the rounded reciprocal of the carton
BOM coefficient: it is sales units per carton in that recipe basis, not safely
a universal bottles-per-case field. When the BOM basis is verified,
`bottlesPerCase = cartonPieces × containersPerPiece`. Case conversion needs an
exact SKU/case definition; missing, ambiguous or invalid conversion must remain
unavailable rather than defaulting to one or rounding an unexplained coefficient.

`rateFor` already divides physical container speed by `containersPerPiece` to
obtain sales units/hour. Preserve that distinction without dividing twice.
`normalizeProducts` currently passes physical `fillLitres` into eligibility;
retain physical-fill matching so two 1 L bottles sold together do not acquire
the 2 L bottle rate. Combo assembly capacity is separately unestablished by the
PDF; correct arithmetic does not grant a complete combo-production route.

## Required MARK IV changes when the MARK V build is approved

1. Separate 10 Head eligibility from the shared 10/6 Head branch. Permit supported
   1/2 L bottle routes; reject 3/4/5 L with the labelling reason.
2. Replace 1 L scalar 2,100 with the adopted 1,800–2,100 range; replace 2 L 1,260
   with 900. Remove schedulable 3 L 720 and 5 L 900 entries for 10 Head.
3. Extend the rate schema beyond a single scalar so source range, selected
   scenario value and running-rate meaning remain visible.
4. Replace generic setup application with scoped machine/transition rules that
   preserve combined time and unknown matches.
5. Show case, sales-unit, bottle and litre quantities with their actual units and
   conversion evidence. Keep the screenshot's rated field as separate evidence.
6. Update explanatory rules that currently say 3 L supported and 5 L less suitable;
   they conflict with the adopted operational exclusion.

## Acceptance cases for the later implementation

These are specifications, not executed tests. Numeric examples below are synthetic
fixtures, not claims about a real SKU or shift.

| Case | Expected result |
|---|---|
| Supported 1 L bottle | Source rate remains 1,800–2,100/hour; chosen scenario value is labelled |
| Supported 2 L bottle | 900 bottles/hour, equivalent to 1,800 L per running hour; no legacy 1,260 |
| 3/4/5 L physical bottle | Ineligible even when a legacy speed row exists; labelling reason displayed |
| Unknown container or unmatched recipe | Existing identity/recipe guard retained; “all SKUs” does not bypass it |
| Mechanical-only change | About 0.5 hours; no inferred flushing volume |
| Matched mustard/groundnut/EV combined category | One combined 1-hour-plus duration; no extra 0.5 hours and no fabricated upper bound |
| Cold press → sunflower | About 0.5 hours; historical 45 minutes does not replace it |
| Sunflower → cold press or unknown oil pair | No automatic reverse match or generic one-hour completion claim |
| Missing 10 Head flushing volume | Unknown remains unknown; no copied 550/1,000/1,500 L and no stock credit |
| Reuse enabled | Full flushing volume is not recurring waste; setup time remains; unmeasured loss is not verified zero |
| 100 cases × verified 20 one-litre bottles/case | 2,000 bottles and 2,000 L; filling takes 57.142857–66.666667 minutes over the adopted speed range, before setup/delays |
| 100 cases × verified 6 two-litre bottles/case | 600 bottles and 1,200 L; filling takes 40 minutes at 900/hour |
| Synthetic 2 × 1 L sales unit, independently eligible | Physical 1 L rate selected; sales-unit rate is 900–1,050/hour, not the 2 L bottle rate |
| Missing/zero/negative/nonfinite bottles per case | Case-based duration unavailable with a unit-mapping reason; no divide-by-zero or one-bottle default |
| Same case count, two verified case sizes | Bottle demand and filling time scale by their respective case factors |
| Setup extends beyond available shift time | Calendar respects setup before saleable filling; no output produced during setup |

Remaining decisions: single-value/range scheduling policy; oil-pair and tooling
mapping; parts overlap for the specific cold press → sunflower change; normal
stops/rejects and net shift hours; full crew and shared resources; flushing
inventory/recovery details; SKU-specific case conversion and combo work. These
gaps do not revoke adoption of the supplied rates and durations.
