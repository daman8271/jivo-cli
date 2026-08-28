---
type: finding
source: FR8HODBNEW (live)
mined: 2026-08-29
confidence: high
system: ARY / FusionERP8
---

# Gap list — probe-verified, not diff-derived

Every gap here was checked with `ary assort probe` against all 21,466 SKUs by name,
**not** taken from the automated diff, which produced 81 false positives
([[Data-Quality-Traps]]).

## Category coverage by group tag — with its caveat

`per_resident_yr` = that category's annualised sales ÷ 5,000 residents.

| Category | active SKUs | sold | dead | 12m sales | **₹/resident/YEAR** |
|---|---|---|---|---|---|
| Mobile | 8 | 2 | 6 | ₹2,690 | **₹0.54** |
| Fashion Jewellery | 91 | 2 | 89 | ₹9,890 | ₹1.98 |
| Disposable | 53 | 17 | 36 | ₹30,899 | ₹6.18 |
| **Gurmat** (Sikh religious articles) | 27 | 7 | 20 | ₹34,555 | **₹6.91** |
| Kids Wear | 83 | 13 | 70 | ₹40,121 | **₹8.02** |
| Frozen | 57 | 24 | 33 | ₹49,244 | ₹9.85 |
| Toys | 220 | 18 | 202 | ₹74,369 | ₹14.87 |
| Cookware | 133 | 40 | 93 | ₹1,44,155 | ₹28.83 |
| Electricals | 120 | 31 | 89 | ₹1,50,568 | ₹30.11 |
| Sports | 136 | 41 | 95 | ₹1,71,021 | ₹34.20 |
| Appliances | 184 | 47 | 137 | ₹1,72,256 | ₹34.45 |
| Food Supplement | 205 | 56 | 149 | ₹2,99,990 | ₹60.00 |
| **Medicare** | 272 | 99 | 173 | **₹3,15,279** | **₹63.06** |
| Dairy Products | 41 | 15 | 26 | ₹9,31,461 | ₹186.29 |

Categories with **no group at all**: baby care (3 SKUs sit in an "Accessories →
Baby Accessories" subgroup), pet care, optical/eyewear, hardware/tools/DIY.
"Academy Books" holds 288 SKUs, **all deactivated**. "Raw Material" holds 149 active
SKUs with zero sales.

The thick end, for contrast: Confectionery ₹1,969/resident/yr, Personal Care ₹1,013,
Academy Dress ₹931, Winter Wear ₹865, Fruits ₹717, Vegetable ₹538.

### Medicare is not a pharmacy

Top 12 Medicare sellers, 12 months — every one is a general-store home remedy:

| Product | Sub-group | 12m sales |
|---|---|---|
| Dettol Antiseptic Liquid 210 ml | Antisept Lotion | ₹20,214 |
| **Jivo Pain Relief Oil 250 ml** | Pain Relief | ₹18,040 |
| GSK Eno 5 g Lemon Fresh | Eno | ₹17,931 |
| Dabur Honitus Cough Remedy 100 ml | Cough Syrup | ₹17,202 |
| Dettol Antisept Lotion 60 ml | Antisept Lotion | ₹11,105 |
| Vicks VapoRub 10 ml | Vaporub | ₹10,833 |
| Dabur Chyawanprash 450+50 g | Chyawanprash | ₹10,800 |
| Vicks Inhaler 0.5 ml | Medicare | ₹10,344 |
| Boroline Antiseptic Cream 20 g | Medicare | ₹9,945 |
| Dwarkesh Anar Dana Goli 100 g | Pachak Churan | ₹8,350 |
| Dabur Glucose D 125 g | Glucose | ₹8,089 |
| Johnson's Benadryl 150 ml | Banadryl | ₹8,055 |

No paracetamol. No antibiotic. No antacid tablet. No ORS sachet. No BP, diabetes,
thyroid or asthma medicine. No prescription anything. **A township of 5,000 — including
several thousand boarding children — has ₹63 per head per year of Dettol and churan and
no pharmacy.** JIVO's own Pain Relief Oil is the second-best seller in the category.

## The honest gap table

This is the trustworthy version of §6. It ignores ARY's category tree entirely and searches
product names across the whole catalogue, so a category filed in the wrong group still
counts. 12-month window, 5,000 residents.

| Probe | SKUs in catalogue | active | sold 12m | groups | 12m sales | ₹/resident/YEAR |
|---|---|---|---|---|---|---|
| **paracetamol / crocin / dolo / calpol / combiflam** | **3** | 3 | **1** | 1 | **₹502** | **₹0.10** |
| **antacid** (digene, gelusil, pantop, omez, rantac) | **0** | 0 | 0 | — | **₹0** | **₹0.00** |
| **antibiotic** (azithro, amoxy, cipro, augmentin) | **0** | 0 | 0 | — | **₹0** | **₹0.00** |
| **diabetes / BP / thyroid** (metformin, telma, amlodipine, thyronorm) | **0** | 0 | 0 | — | **₹0** | **₹0.00** |
| **pet food** (pedigree, whiskas, dog/cat food) | **0** | 0 | 0 | — | **₹0** | **₹0.00** |
| **eyewear** (spectacles, reading glasses, goggles) | **0** | 0 | 0 | — | **₹0** | **₹0.00** |
| medical devices (thermometer, oximeter, glucometer, nebuliser) | 3 | 3 | **0** | 1 | ₹0 | ₹0.00 |
| hand tools (screwdriver, plier, hammer, spanner, wrench) | 18 | **8** | **0** | 1 | ₹0 | ₹0.00 |
| ORS / rehydration (ORS, Electral, Enerzal) | 13 | 13 | 7 | 4 | ₹7,453 | ₹1.49 |
| LED bulb / battery / torch | 47 | 47 | **5** | 5 | ₹8,575 | ₹1.72 |
| protein / malted drinks (whey, Horlicks, Bournvita) | 40 | 39 | 15 | 7 | ₹60,443 | ₹12.09 |
| sunscreen / SPF | 48 | 48 | 23 | 1 | ₹88,414 | ₹17.68 |
| mobile charger / cable / earphone / power bank | 14 | 14 | 5 | 3 | ₹99,713 | ₹19.94 |
| sanitary pads / napkins | 81 | 81 | 21 | 3 | ₹4,16,962 | **₹83.39** |

### What this proves

**1. There is no pharmacy, and this is now measured, not inferred.** Across 21,466 SKUs,
ARY holds **three** paracetamol SKUs. **One** sold: Crocin 500 mg, 26 strips, **₹502.06 in
twelve months, last sold 14-Feb-2026.** Antacid, antibiotic, and every chronic-disease
medicine return a **hard zero** — not "filed elsewhere", not "thin": absent from the
catalogue. A township of 5,000 people, several thousand of them boarding children, bought
26 strips of paracetamol in a year. This is the clearest gap in the business.

**2. Three categories are listed but literally never sell.** Medical devices (3 SKUs),
hand tools (18 SKUs, 8 active) and LED/battery (47 SKUs, only 5 moving) are on the
catalogue and produced **₹0 and ₹8,575** respectively. That is not assortment; it is
paperwork.

**3. Two categories do not exist at all** — pet food and eyewear, zero SKUs. Reading
glasses for an ageing staff and teaching population, on a campus 30-50 km from an optician,
is worth a look.

**4. Sanitary pads are the one hygiene category working** — ₹83/resident/year on 81 SKUs
with 21 moving. Given ~2,000+ women and girls on campus that is roughly ₹200 each a year,
which is a plausible real number. It shows the model works when the range exists.

**5. Mobile accessories: 14 SKUs, ₹99,713.** My §6 figure of "8 SKUs, ₹2,690" came from the
"Mobile" **group tag** — the real answer, found by name, is 14 SKUs across 3 groups doing
₹1 lakh. Still tiny for 5,000 phone owners, but the group-tag number was wrong by 37×.
**This is exactly why `probe` exists.**

## Verified true zeros

Every row below was checked with `ary assort probe` against all 21,466 SKUs (not the
category tree, not the diff), so a zero here means the words appear in **no product name in
the catalogue**. 12-month window, ₹/resident/year on 5,000 residents.

### Women's health — a hard zero, on a campus with 2,000+ women and girls

| Probe | SKUs | Sold | 12m sales |
|---|---|---|---|
| **menstrual cup** (incl. Sirona, Pee Safe) | **0** | 0 | **₹0** |
| **intimate wash** (incl. Everteen, VWash) | **0** | 0 | **₹0** |
| **pregnancy test kit** (incl. Prega News) | **0** | 0 | **₹0** |
| **tampons** | **0** | 0 | **₹0** |
| *(for contrast)* sanitary pads | 81 | 21 | ₹4,16,962 |

ARY does pads well — ₹83/resident/year, roughly ₹200 a year per woman on campus, which is a
plausible real figure. But **the entire rest of women's intimate health does not exist in
the catalogue.** The cohort is ~1,102 university students (487 of them AIRWE rural women),
several hundred senior schoolgirls, and resident staff women. This is the clearest
underserved cohort in the business, and pads prove the demand converts when the product is
on the shelf.

Menstrual cups deserve their own note: 2026 adoption in India is rising fast (the
demand-side research flagged it as a live trend), a cup is a **₹300-500 one-off replacing
years of pads**, and a residential campus with limited disposal infrastructure is close to
the ideal use case. Zero SKUs.

### Elderly and chronic care — also a hard zero

| Probe | SKUs | Sold | 12m sales |
|---|---|---|---|
| **walking stick / crutch / walker** | **0** | 0 | **₹0** |
| **adult diaper / pull-ups** | **0** | 0 | **₹0** |
| reading glasses / spectacles | 4 | **0** | **₹0** |

Against a resident population that includes elderly people, ~690 staff, a 100-bed hospital
with ~120 OPD patients a day, and students who break limbs playing sport. Reading glasses
are *listed* (4 SKUs) and have never sold once — the §31 procurement pattern again.

### Skin care — the one category the hill climate already drives

| Probe | SKUs | Sold | 12m sales | ₹/resident/yr |
|---|---|---|---|---|
| moisturiser / cold cream (Nivea, Vaseline) | 200 | 83 | **₹5,48,581** | ₹109.72 |
| petroleum jelly | 86 | 27 | ₹3,30,420 | ₹66.08 |
| sunscreen / SPF | 48 | 23 | ₹88,414 | ₹17.68 |
| **lip balm** | **6** | 6 | ₹9,655 | ₹1.93 |

Cold cream at ₹110/resident/year is one of ARY's better-performing lines — the January
average low is 2.8 °C and it is dry from October to December, so the demand is structural.

Two gaps stand out against that: **sunscreen at ₹17.68** on a campus at 1,551 m where UV is
materially higher than the plains and students are outdoors daily; and **lip balm at 6 SKUs
/ ₹9,655**, where every one of the 6 sold — a fully sold-through range that is simply too
small. Chapped lips at altitude in a Himachal winter are near-universal.

**Ranked by conviction:** lip balm (100% sell-through, trivially cheap, obvious climate
demand) > menstrual cups and intimate wash (large cohort, zero supply, proven category
adjacency in pads) > sunscreen depth > walking sticks and reading glasses (real but small).

## See also

- [[Pharmacy]] — the largest single gap, and its blockers
- [[Institution-Range]] — the categories no retail benchmark contains
- [[Baby-Care]] — a gap that turned out to be a procurement failure
