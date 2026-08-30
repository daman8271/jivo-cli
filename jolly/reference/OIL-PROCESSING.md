---
title: Oil processing — crude in, cold press out
type: reference
company: JIVO_OIL_HANADB
source: "SAP HANA OWOR/WOR1 (180d) + OPDN/PDN1 (365d) + OITW, pulled live"
told_by: Daman
last_verified: 2026-08-29
tags: [jivo/reference, jivo/oil, jivo/canola]
---

# Oil processing — crude in, cold press out

> **Daman, 2026-08-29:** *"canola comes in crude form, and then we process it for
> cold press oil"*

**Confirmed live, and it is bigger than any finding had recorded.** Crude rapeseed
is the largest single raw-oil input in the business, and it is completely invisible
to every stock view the engine currently uses.

---

## The chain

```
RM0000016  CRUDE DEGUMMED RAPESEED OIL NEW      ← bought, imported
     │      (× 1.028 – 1.031 — ~3% refining loss)
     ├──→  RM0000002  CANOLA COLD PRESS LOOSE OIL      44 orders · 2,015,685 L
     └──→  RM0000015  LOOSE OIL COLD PRESS/REFINED     14 orders ·   577,568 L
                │
                └──→ feeds CANOLA and OLIVE finished goods
```

**The ratio is above 1.0 and that is correct.** 1,000 L of crude yields ~971 L of
cold-press oil. The loss is the refining. Any engine that assumes 1:1 under-buys
crude by 3%.

### What else goes into CANOLA COLD PRESS (180 days)

`RM0000002` is not one recipe — it is blended seven different ways:

| From | Orders | Litres used | Ratio |
|---|---:|---:|---:|
| **CRUDE DEGUMMED RAPESEED** | **44** | **2,015,685** | 1.0281 |
| SOYABEAN REFINED | 35 | 526,730 | 0.6570 |
| COLD PRESS RAPESEED CANOLA (RM0000035) | 9 | 313,395 | 0.8316 |
| LOOSE OIL COLD PRESS/REFINED | 25 | 281,011 | 0.6350 |
| MUSTARD LOOSE OIL | 12 | 185,002 | 0.6921 |
| RICE BRAN REFINED | 1 | 12,500 | 0.5000 |
| PEANUT OIL | 4 | 10,850 | 0.5000 |

Crude rapeseed is the **most-used component by both order count and volume.**
The true cold-press route (crude) and the blended route (soyabean/mustard) run
side by side, batch by batch.

---

## Where it physically happens — `BH-GJ`, not Bhakharpur

Every receipt of crude lands at the **Gujarat Job Worker**:

| Item | GRPOs (365d) | Litres | Warehouse | Last receipt |
|---|---:|---:|---|---|
| **RM0000016** CRUDE DEGUMMED RAPESEED NEW | 18 | **5,690,764** | `BH-GJ` | **2026-06-28** |
| RM0000062 CRUDE DEGUMMED RAPESEED (DOMESTIC) | 14 | 501,989 | `BH-CRUDE` | 2025-10-21 |
| RM0000035 COLD PRESS RAPESEED CANOLA OIL | 8 | 363,395 | `BH-GJ` | 2026-06-16 |
| RM0000002 CANOLA COLD PRESS LOOSE OIL | 1 | 288,033 | `BH-GJ` | 2025-10-29 |

*(Inference, not proven: the warehouse is named "Gujarat Job Worker" and both the
crude going in and the cold-press oil coming back are booked against it — so this
reads as send-crude / receive-processed job work. Worth one question to Shunty
Veerji or Gopi before it is treated as fact.)*

---

## Three traps this creates

**1. `BH-GJ` is OFF the stock allow-list.** Ruled 2026-08-29. That is the right
call for finished goods, but it means **the entire crude→cold-press chain reads as
zero stock** in `blend_mrp.py`. Today that happens to be harmless — crude really is
at zero across every warehouse — but the moment a shipment lands at Gujarat, the
engine will keep saying "short" while the oil sits in the tank.

**2. Every crude item reads 0 on hand AND 0 on order, in every godown.**

| Item | On hand | On order |
|---|---:|---:|
| RM0000016 CRUDE DEGUMMED RAPESEED NEW | 0 | 0 |
| RM0000020 CRUDE SUNFLOWER | 0 | 0 |
| RM0000031 CRUDE DEGUMMED SOYABEAN | 0 | 0 |
| RM0000062 CRUDE DEGUMMED RAPESEED (DOMESTIC) | 0 | 0 |
| RM0000035 COLD PRESS RAPESEED CANOLA | 0 | 0 |

**No crude has been received since 28 June 2026 — two months.** Meanwhile EXIM
shows **750,000 L of CRUDE CANOLA contracted from Ukraine with no SAP purchase
order behind it** (Finding 10). SAP cannot see the pipeline that keeps canola
alive.

**3. `RM0000035` is modelled as a pure BUY.** The engine gives it 0% made and
reports it short. It is really the same crude→cold-press process, and it is
*received* rather than produced. Until that is settled, its shortage figure is
not trustworthy.

---

## What the engine should do about it

- Explode `RM0000002` and `RM0000015` through **crude rapeseed**, at the observed
  1.028–1.031 ratio — not stop at "canola is made".
- Count `BH-GJ` for **crude and cold-press oil specifically**, or the first Ukraine
  landing will be invisible.
- Treat **EXIM as a source for crude**, not an afterthought. It is the only system
  that shows what is coming.

## Links

[[GODOWNS]] · [[../findings/2026-08-27-what-jivo-actually-buys]]

---

# GROUNDNUT **IS** PEANUT — one oil, two item codes

**Daman, 2026-08-29.** `RM0000011 GROUNDNUT LOOSE OIL` and `RM0000066 PEANUT OIL`
are the SAME OIL. Groundnut and peanut are two names for one thing.

**This was the single largest error in the August analysis:**

| | Treated as two oils | **Merged (correct)** |
|---|---|---|
| GROUNDNUT | need 526,221 · have 3,848 → **SHORT 522,373** | |
| PEANUT | need 6,465 · have 364,100 → **STRANDED 357,635** | |
| **Together** | | need 532,686 · have 367,948 → **short 164,738** |

**The 357,635 L "stranded peanut" was never stranded. It IS the groundnut supply.**
And groundnut was never 522,373 L short — it was 164,738 L short, and **69% covered.**

**It also dissolves part of the "substitution" story.** When SAP shows 218,845 L of
peanut consumed making GROUNDNUT LOOSE OIL, that is not substitution and not a book
fiddle — **it is the same oil, correctly consumed, recorded under whichever code the
stock happened to sit in.** Genuine substitution (sunflower made from soyabean, canola
made from soya + rice bran) is a separate and real thing; this one was a duplicate code.

> **RULE: never treat two RM codes as different oils on the strength of their names.**
> Merge synonyms before computing any shortage. A duplicate code manufactures a
> phantom shortage on one side and phantom stranded stock on the other, and both
> numbers look completely credible.

## Candidate pairs still awaiting a ruling

| A | B | Same oil? |
|---|---|---|
| `RM0000002` CANOLA COLD PRESS LOOSE OIL OLD | `RM0000035` COLD PRESS RAPESSED OIL CANOLA OIL | ? |
| `RM0000016` CRUDE DEGUMMED RAPESEED NEW | `RM0000062` CRUDE DEGUMMED RAPESEED (DOMESTIC) | ? |
| `RM0000001` LOOSE REFINED OLIVE OIL | `RM0000052` LOOSE REFINED OLIVE OIL (DARK COLOUR) | ? |
| `RM0000013` POMACE OLIVE IMPORTED | `RM0000012` EXTRA LIGHT OLIVE LOOSE IMPORTED | ? |

Canola and rapeseed are the same plant, so the first two look likely. `RM0000052` is
literally the same name plus "(DARK COLOUR)" and 141,000 L of it fed olive production
in August. Confirm each before the next run.
