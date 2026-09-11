# MARK V machine specification: JP

Reviewed 10 September 2026. Status: approved operating inputs for design; no
engine change. Confidence: high in the values and source extraction. Exact SKU
mapping and the choice within the setup range remain implementation decisions.

Authority: [WORKING-RULES.md](../WORKING-RULES.md), M5-R01 and M5-A01. Daman's
adoption makes the revised PDF the operating reference; earlier conflicting
numbers do not survive. The PDF's N1 Speeds note supersedes N3's 80/min.

## Operating specification

| Field | MARK V rule | Exact source anchor |
|---|---|---|
| Machine identity | JP rotary filling line; one capacity pool | PDF p27, 09:48–09:52 |
| Approved 1 L running rate | **75 bottles/min = 4,500 bottles/hour** | PDF p2; p12 N1; pp47–48, 34:03–35:17 |
| Primary route | Mostly mustard 1 L | PDF p13 N3 |
| Additional bottle family | Pomace, extra light and rice bran in the **52 g bottle family**, described as 1 L in the transcript | PDF p13 N3; pp37–38, 21:50–22:26 |
| Occasional route | 200 ml; **no approved speed supplied** | PDF p13 N3; p27, 09:52 |
| SKU change | **About 5–6 hours total**, including cleaning and flushing | PDF p3; p13 N3; pp27–28, 10:04–10:31 |
| Flushing quantity | **1,500 L per applicable changeover** | PDF p3; p13 N3; p28, 10:17–10:26 |
| Flushing disposition | Assume reuse; do not consume or scrap 1,500 L of fresh oil on each change | M5-A01, user instruction 10 September |

The 1 L figure is a running rate. It is not full-shift accepted output, a 200 ml
rate, or automatic proof of the same speed for every newly mapped bottle family.
Do not multiply it by an inherited 80% efficiency factor or reinstate 90/min.

## Routes and packaging

1. Keep mustard first preference and the existing groundnut 1 L permission.
   Groundnut is also supported by PDF p37, 21:50–21:54. Keep the existing yellow
   mustard exclusion: the revised note does not explicitly reverse that specific
   earlier user ruling. Current source: `site-mark4/lib/rules.ts:27–32`.
2. Add the approved pomace/extra-light/rice-bran family to the route specification.
   Bind runnable SKU records to their actual BOM bottle and closure components;
   a product-name substring or a weight alone is not complete tooling identity.
   The transcript reports new change parts for this bottle family arriving that
   month (p38, 22:09); it does not list tooling or item codes.
3. A route record and a rate record are separate. Preserve occasional 200 ml as
   a known operating route without generating a schedule at an invented speed.
   Preserve the source qualification when assigning rates to new 52 g mappings.
4. Use physical fill size and container count from the recipe. MARK IV derives
   `container`, `bottleGrams`, `cartonPieces` and `containersPerPiece` in
   `site-mark4/lib/model.ts:31`; `fillLitres` is sales-unit litres divided by
   containers per sales unit. Eligibility already receives `fillLitres` at
   `model.ts:117`, and `rateFor()` divides containers/hour by container count.
5. Preserve missing-recipe, identity-conflict and retired-carton holds. Neither
   a machine permission nor equal cap size authorizes a BOM substitution. The
   PDF p14 N6 explicitly distinguishes mustard caps; p27, 09:31–09:36 says even
   two 1 L bottles can have different necks. Existing verified groundnut carton
   transitions and conditional recipe scenarios retain their existing scope.

## Changeover and oil accounting

- Replace JP's current generic one-hour SKU-change allowance with the approved
  5–6-hour total. Keep both endpoints until an explicit scheduling policy selects
  a value or presents bounded scenarios; do not silently use 5 or 5.5 hours.
- The approximately 2–2.5 hours of cleaning in the transcript is **inside** that
  total. No second cleaning, flushing or generic setup charge is added to it.
- JP has a generic SKU-change entry, not a measured directional oil-pair table.
  Do not borrow Clear Pack's mustard/other-oil times or volumes. Bottle/neck
  changes can trigger setup despite unchanged nominal litres. The same-SKU
  continuation must remain distinguishable from a new SKU or bottle change.
- Reuse changes the material policy, not the occupied machine time. Record
  flushing volume separately from saleable filling and actual unrecovered loss.
  The source does not supply recovery fraction, opening recovered-oil inventory,
  replenishment or recovery timing: do not invent stock credits or verified zero
  losses. The 1,500 L estimate itself is not available opening inventory.

## Practical scheduling effect

JP should favor longer campaigns because each applicable change occupies 5–6
hours. For illustration only, if a session has ten available hours, one such
change leaves four to five running hours: **18,000–22,500 one-litre bottles** at
the approved running rate before other stops or rejects. This is derived
arithmetic, not measured shift output or an approved ten-hour timetable.

Carry setup progress and the previous product/bottle state across adjacent
sessions; do not reset the line to an unknown state each morning or count a
partly completed change twice. The day/night decision must account for JP's real
setup before comparing additional productive output. Bottle dents and cleanup
examples in PDF p56 are incidents, not a new fixed downtime multiplier.

## Meaningful acceptance tests for implementation

1. A supported single 1 L bottle uses 4,500/hour; 200 ml returns no numeric rate.
   A two-bottle sales unit at the supported physical fill size uses 2,250 sales
   units/hour, with correct litres and BOM consumption.
2. Mustard and the supported groundnut family retain their routes; yellow
   mustard retains its explicit exclusion. New 52 g family mapping does not
   admit unrelated oils or unknown bottle recipes. Tins, pouches and drums do
   not reach JP through oil-name matching.
3. A JP SKU transition occupies the selected documented 5–6-hour value exactly
   once. A same-litre/different-neck change cannot disappear merely because its
   pack size is unchanged; a true continuation is not charged a new SKU change.
4. With a ten-hour test window, a five-hour choice permits at most five running
   hours and a six-hour choice at most four. Cross-session setup is neither
   lost nor repeated, and setup alone does not justify a night roster.
5. Repeated changes expose 1,500 L flushing activity each while reusing oil;
   they do not consume 1,500 L fresh oil, create saleable production, or mint
   stock credits. Unquantified losses remain distinct from measured zero.
6. Newly allowed machine routes still fail scheduling when a recipe, required
   carton/closure, usable material or storage headroom is absent.

Source PDF: `/Users/damanpreetsingh/Documents/Codex/2026-09-09/make/outputs/Machine_Changeover_Planning_Red_Notes_Edition.pdf`.
SHA-256 checked: `b3388f02852783347fa04f9d23e1a9260d46477f7132d65464bdbc7238636fe3`.
Relevant pages were read directly from bounded `pdftotext -layout` extraction;
the full review is [PDF-REVIEW-2026-09-10.md](../PDF-REVIEW-2026-09-10.md).
