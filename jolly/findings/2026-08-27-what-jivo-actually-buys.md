# Finding 10 — JIVO does not buy the oils it sells. It blends them.

**Date:** 2026-08-27 · Jivo Oil · read-only
**Sources:** SAP HANA (OWOR/WOR1 production orders, OITW, OPOR/POR1, PDN1) · EXIM
(`director-inventorty`, `stock-status`, `tank`)
**This supersedes the "must buy" list in Findings 08 and its 21/27 Aug reruns.**

---

## The finding

Every buy list I have produced so far told the operator to purchase oils that JIVO
**manufactures in-house by blending**. Derived from 51 production orders since 1 June:

| We "sell" | Actually made from | Times | Litres consumed |
|---|---|---:|---:|
| **REFINED SUNFLOWER OIL** | **SOYABEAN** ×0.956 | 34 | **584,310** |
| | MUSTARD ×1.0 | 9 | 137,750 |
| | RICE BRAN ×0.5 | 3 | 21,370 |
| | *actual sunflower oil* | 1 | **1 litre** |
| **GROUNDNUT LOOSE OIL** | **PEANUT** ×0.496 | 51 | **444,815** |
| | **SOYABEAN** ×0.542 | 41 | **364,175** |
| | MUSTARD ×0.571 | 7 | 68,445 |
| **CANOLA COLD PRESS** | **SOYABEAN** ×0.632 | 34 | **515,530** |
| | LOOSE OIL COLD PRESS/REFINED ×0.698 | 25 | 281,011 |
| | MUSTARD ×0.5 | 8 | 82,300 |
| **LOOSE REFINED OLIVE** | SOYABEAN ×0.890 | 17 | 400,840 |
| | COLD PRESS/REFINED ×0.928 | 11 | 150,200 |
| | DARK OLIVE ×0.90 | 1 | 90,000 |
| **LOOSE OIL GOLD** | SOYABEAN ×0.95 | 6 | 43,495 |
| | PEANUT ×0.575 | 4 | 21,983 |
| **MUSTARD LOOSE OIL** | SOYABEAN ×1.0 | 8 | 130,685 |
| **LOOSE OIL COLD PRESS/REFINED** | **CRUDE DEGUMMED RAPESEED** ×1.0309 | 14 | 577,568 |

**We used one litre of real sunflower oil since June, and 584,310 litres of soyabean
to make "sunflower".**

### Why every previous buy list was wrong

The recipes are **not in the BOM tables** (`OITT`/`ITT1`). Only 4 raw materials have
a BOM there. The real recipes live in the **issued components of actual production
orders** (`OWOR` → `WOR1`), and they are different every batch:

```
GROUNDNUT LOOSE OIL, peanut ratio observed:  0.496 … 0.571
CANOLA, soyabean ratio observed:             0.632 … 0.698
```

That is not a recipe. **It is a blending decision taken per batch** — almost
certainly on price and what is in the tank that day. Which means it is exactly the
thing this system should be optimising, not something to look up.

*(Confidence: the ratios and volumes are pulled live and are certain. That the
choice is driven by price/availability is inference — plausible, not proven.)*

---

## What JIVO actually buys — the real purchase list

| Base oil | On hand | On order | Fastest supplier |
|---|---:|---:|---|
| **SOYABEAN REFINED** — the backbone | 213,589 | **656,164** | Vee Kay 2.3d · DIL Exim 12.7d · AWL 17.4d (9 vendors) |
| LOOSE REFINED OLIVE (DARK) | 204,993 | 0 | — |
| **PEANUT OIL** | 189,358 | 139,330 | Dhanlaxmi 9.1d |
| RICE BRAN REFINED | 67,331 | 29,769 | Modi 3.5d · Arora 11.8d |
| LOOSE OIL COLD PRESS/REFINED | 35,295 | 0 | *(made from crude rapeseed)* |
| POMACE OLIVE IMPORTED | 27,222 | 48,352 | Migasa 48.8d |
| **CRUDE DEGUMMED RAPESEED** | **0** | **0** | GrainCorp 14.8d · Alba 21d |

**Soyabean is the single most important material in the business.** It feeds
sunflower, groundnut, canola, olive, gold, mustard and cotton. Nothing in the
previous analysis showed that, because it was hidden one level below every
finished good.

---

## The one real gap: crude rapeseed

`RM0000016 CRUDE DEGUMMED RAPESEED` — **zero stock, zero on order in SAP.** Its last
purchase order (GrainCorp, 523.89 MT) closed on 1 June. It is the only input to
`LOOSE OIL COLD PRESS/REFINED`, which is down to 35,295 L and feeds canola and olive.

**But EXIM shows 750,000 litres of CRUDE CANOLA contracted from UKRAINE** that has
no SAP purchase order behind it. So the material is bought — SAP just cannot see it.

## EXIM holds a pipeline SAP does not show

| Status | Litres | MT |
|---|---:|---:|
| In tank at factory | 887,600 | 808 |
| Outside factory | 86,538 | 79 |
| **In contract** | **1,745,691** | **1,589** |
| On the way | 263,692 | 240 |
| Under loading | 65,934 | 60 |

By oil, the inbound that matters:

| Oil | In contract | On the way | Under loading | From |
|---|---:|---:|---:|---|
| **CRUDE CANOLA** | **750,000** | 0 | 0 | **UKRAINE** |
| SOYABEAN | 443,420 | 200,360 | 0 | AWL, Arora |
| MUSTARD KACHI GHANI | 374,820 | 0 | 0 | AWL, Arora |
| GROUNDNUT FILTER | 0 | 39,600 | 60,000 | Dhanlaxmi |
| VIRGIN OLIVE | 16,000 | 0 | 0 | Cobram |

**Caution — do not add EXIM to SAP.** Checked: EXIM's mustard contracts (AWL
224,820 + Arora 150,000) line up with SAP's open POs (AWL 250 MT 8 Aug, Arora
150 MT 22 Aug). They are the same orders in two systems with different units.
**The exception is crude canola: 750,000 L in EXIM, nothing in SAP.**

## Tanks — and no sunflower anywhere

887,600 L across 19 tank items. For the four focus varieties:

| | Litres in tank |
|---|---:|
| MUSTARD (KG 2B, KG, DEO, Yellow, Pakki) | 373,500 |
| CANOLA (+2B) | 179,500 |
| GROUNDNUT (2B + refined) | 119,000 |
| **SUNFLOWER** | **none — no sunflower tank exists** |

Which is consistent: there is no sunflower tank because JIVO does not stock
sunflower oil. It blends it from soyabean on demand.

---

## What this changes

1. **The buy list must be rebuilt on production-order recipes, not the BOM table.**
   `materials.py` currently explodes `OITT`/`ITT1` and therefore stops at the blended
   oil and calls it a purchase. It has to go one more level, using the ratios above.
2. **"We are short of sunflower / groundnut" is the wrong statement.** We are short,
   or not, of **soyabean, peanut and crude rapeseed**. Everything else is a blending
   choice.
3. **The allocation algorithm just got a second dimension.** It is not only "which
   SKU gets the oil" — it is "which blend, from which base oils, at what ratio".
   That is where the money is, and it is a decision being taken by hand every day.
4. **EXIM must be a source, not an afterthought.** Crude canola is the proof:
   750,000 litres invisible to every SAP-only view.

## Next

- Rebuild the explosion on `WOR1`-derived recipes (weighted by recent usage)
- Re-run the four focus varieties against **base-oil** availability
- Then allocation, on base oils rather than finished oils

---

# Finding 10b — the corrected answer (engine rebuilt, same day)

`jolly/engine/blend_mrp.py` now explodes through the blends using recipes derived
from 90 days of real production orders, applies the make/buy split, and nets stock
once per item level-by-level.

**Result for the four focus varieties: 14 items short out of 151. Only ONE is an oil.**

## What has to be blended (production runs, not purchase orders)

| Oil | To blend | Made from |
|---|---:|---|
| REFINED SUNFLOWER | 314,778 L | soyabean 0.79 + mustard 0.19 + rice bran 0.03 |
| GROUNDNUT LOOSE | 259,172 L | peanut 0.45 + soyabean 0.37 + mustard 0.07 |
| CANOLA COLD PRESS | 149,326 L | soyabean 0.49 + cold-press 0.27 + mustard 0.18 |
| LOOSE OIL COLD PRESS/REFINED | 5,079 L | crude degummed rapeseed 0.86 |
| PET BOTTLE 1 LTR 40 GMS | 261,545 | blown from preform 40 gms |
| PET BOTTLE 1 LTR 52 GMS | 12,072 | blown from preform 49.5 gms |

## What is actually short

| Material | Need | Stock | On order | **Short** | Lead |
|---|---:|---:|---:|---:|---|
| **MUSTARD LOOSE OIL** | 962,818 | 152,723 | 551,806 | **258,289** | 12.7d Vaishnodevi |
| LABEL 200 ML GROUNDNUT front | 98,162 | 65,443 | 1 | 32,718 | 6d Royal Prime |
| LABEL 200 ML GROUNDNUT back | 98,162 | 65,443 | 1 | 32,718 | 6d Royal Prime |
| LABEL 1 LTR SUNFLOWER front | 264,608 | 215,689 | 20,800 | 28,119 | 9d Royal Prime |
| LABEL 1 LTR SUNFLOWER back | 264,608 | 232,204 | 20,800 | 11,604 | 9d Royal Prime |
| CAPS 1&2 LTR WHITE/RED-ORANGE | 29,051 | 17,361 | 3,000 | 8,690 | **22.4d** Maheshwari |
| COLD PRESS RAPESEED CANOLA | 5,929 | 0 | 0 | 5,929 | 7.4d Vaishnodevi |
| LABEL 869 GM MUSTARD front/back | 38,436 | 34,240 | 0 | 4,196 ea | 4.7d Royal Prime |
| TIKKI BARCODE CSD KGMO 1 LTR | 2,182 | 885 | 0 | 1,297 | 2d Media Graphic |
| LABEL 1 LTR PRESSED SUNFLOWER f/b | 6,890 | 5,299 | 504 | 1,087 ea | 5.5d Royal Prime |
| TIN 3 LTR EV CANOLA | 771 | 5 | 0 | 766 | **17d** National Tin |

## The three things that matter in that table

1. **Mustard is the only oil we are short of — 258,289 L.** And the need is
   962,818 L, far above the mustard SKUs alone, because mustard is *also* an
   ingredient in the sunflower (0.19), canola (0.18) and groundnut (0.07) blends.
   Mustard is not one product line. It is a base oil for a third of the range.
2. **Soyabean and peanut are comfortably covered.** Soyabean: need 417,094,
   stock 213,589, on order 656,164. Peanut: need 118,964, stock 189,358, on order
   139,330. The earlier "we're short of sunflower and groundnut" was an artefact of
   stopping the explosion too early.
3. **The long-lead items are tiny and easy to miss.** Caps at 22 days (8,690 short)
   and a 3 LTR tin at 17 days (766 short) rank near the bottom by quantity and near
   the top by urgency.

## Correction to Finding 10's own summary

Finding 10 said crude rapeseed was a hard gap. With the netting fixed it is not:
only 5,079 L of cold-press/refined is needed for these four varieties, so crude
rapeseed demand is small. The 750,000 L Ukraine contract remains real, remains
invisible to SAP, and matters for olive and canola volume beyond this window — but
it is not today's emergency. **Today's emergency is mustard.**
