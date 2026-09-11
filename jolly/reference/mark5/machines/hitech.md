# MARK V machine specification: Hitech pouch

Date: 10 September 2026. Status: user-approved operating input; specification
only. Confidence: high in the adopted rate and two-machine distinction; exact
product/configuration mapping remains incomplete.

Authority: [WORKING-RULES.md](../WORKING-RULES.md), M5-R01 and M5-A01, and
[PDF review](../PDF-REVIEW-2026-09-10.md). Revised PDF p2 and N1 on p12 specify
**20 physical pouches/minute = 1,200 pouches/hour while running**. Page 4's
reconciliation provides no alternate Hitech value. Supporting transcript:
p51 38:18–38:31 and p52 38:37–38:44 identify Hitech and confirm 20 per minute.
This replaces the current MARK IV Hitech allowance of 1,800/hour.

## Physical line and routes

Hitech and Samarpan are two separate physical machines. Prefer running together;
either can run singly (revised pp2,12; transcript p52 38:33–39:17). This does not
make their combined rate Hitech's rate, establish identical SKU/film compatibility,
or give either machine an independent night entitlement.

Preserve a separate Hitech identity in scheduling, rate evidence and actuals.
Current code uses `Pouch Machine` with display name `Pouch — Hitech`; source
configuration evidence may instead name `Pouch Machine` plus `POUCH-Hitech`.
Map aliases/configuration IDs explicitly. A source record labelled only
`Pouch Machine` is not enough to attribute actual output to Hitech alone or to
split it between both machines. Retain unresolved aggregate actuals once; do not
duplicate them under each machine or invent a third aggregate capacity line.

The PDF supplies no pouch weight, fill volume, film specification or complete
SKU-to-machine compatibility. Keep the approved machine rate separate from those
missing product fields. Do not assign every pouch to Hitech merely because its
recipe contains film, or assume that every product can move to Samarpan.

## Units and current normalization boundary

- `Product.packLitres` is litres per sales unit; `fillLitres` is litres per physical
  container; `containersPerPiece` is containers per sales unit (`types.ts`).
- `normalizeProducts` takes `packLitres` from plan `litres_per_piece`, identifies
  pouch/film/laminate in the recipe, and computes
  `fillLitres = packLitres / containersPerPiece` (`model.ts`). A film-only recipe
  can fall back to one container per sales unit; that default is not evidence of
  pouch count, weight or film yield.
- `rateFor` uses the generic `POUCH` rate slot and divides physical rate by
  `containersPerPiece`. Preserve correct sales-unit conversion, but add explicit
  supported product/configuration mapping rather than treating that slot as proof
  that all pouch formats have the same demonstrated rate.
- Do not assume a 1 L pouch or treat 700 g as 700 ml. Existing
  `engine/plan_units.py:pack_litres` parses gram-labelled products using the
  separately recorded 910 g/L planning convention. That convention is not supplied
  by this PDF and does not identify which SKU or pouch size the Hitech rate covers.
  Carry the verified item's fill and conversion provenance, including identity
  conflicts, rather than assigning a guessed volume from the machine name.

For a supported configuration with `n` verified pouches per sales unit and `v`
verified litres per pouch: sales units/hour = 1,200/n; running litres/hour =
1,200 × v. Film consumption comes from a verified recipe and its units, not from
pouch count alone. Carton size is a separate conversion. These are arithmetic
running capacities, not guaranteed accepted output over a full elapsed shift.

## Setup, people and material limits

Hitech oil-change, film-roll/format change, cleaning, startup, changeover overlap,
full crew, shared equipment, rejects and minimum batch are not quantified here.
Do not inherit the 10/6 Head timings, the old generic one-hour allowance, or zero
setup as though measured for Hitech. Running together does not quantify the crew
or prove that shared material supply and packing can sustain both rates.

Under M5-A01 assume flushing oil is reused and retain applicable machine time.
Hitech flushing duration, volume, recovery fraction and availability timing remain
unknown. Do not copy other machines' quantities, charge the whole volume as
recurring waste, assume measured 100% recovery, or create flushing stock.

## Required implementation checks

- Hitech rate lookup returns 1,200 physical pouches/hour, never old 1,800 or a
  Hitech-plus-Samarpan aggregate. Samarpan changes cannot alter Hitech's rate.
- Hitech alone is a valid machine choice; joint operation schedules two physical
  machines subject to the common roster/material/resource constraints.
- Aliases resolve to one Hitech machine. An ambiguous aggregate production record
  stays aggregate once and never becomes two attributed actual records.
- One verified pouch per sales unit yields 1,200 sales units/hour; a synthetic
  two-pouch sales unit yields 600. Neither test implies a production pack exists.
- Non-pouch products fail the Hitech route; missing format/film compatibility or
  conflicting item identity stays visible instead of silently enabling every SKU.
- Unknown fill volume cannot become 1 L; gram and litre units are not conflated.
  Correct film and carton units survive normalization and material consumption.
- Missing setup/crew/recovery evidence is not presented as measured zero or a
  borrowed value. Applicable flushing time and reused-oil accounting stay distinct.
- Rate × elapsed shift is not labelled accepted shift output without its stated
  availability/reject basis; no automatic 80% factor is introduced.

Integration warning: `live/freeze_live.py` retains an older summed pouch-line
model, while `site-mark4/scripts/serve_inputs.py` preserves Hitech/Samarpan config
labels as rate evidence. Reconcile those representations when implementing MARK V;
neither the older aggregate nor live config values override the adopted rate.
No engine, collector or executable tests were changed for this specification.
