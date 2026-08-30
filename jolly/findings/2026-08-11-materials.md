# Finding 08 — the full chain, order to purchase order

**Date:** 2026-08-11 · Jivo Oil · read-only
**Engine:** `jolly/engine/materials.py` · **Output:** `jolly/out/materials-2026-08-11.csv`

```
open orders + 35% buffer − finished stock − work already released
   → BOM explosion (271 components)
   → minus material stock
   → minus what is already on order
   → against real per-vendor lead times
   = what has to be bought, and how long it takes
```

**271 components. 11 must buy. 9 are covered only by goods in transit.**

---

## The shortage, in one line

| | |
|---|---|
| Mustard loose oil needed | **342,616 L** |
| In the tank now | 163,117 L |
| Already on order | **458,619 L** |
| Lead time | **13 days from one vendor, 50 from another** |

There is more mustard oil on order than the requirement calls for. **The oil is
bought. Whether the line starves is a question of which supplier it was bought from
and when it lands** — not whether anyone remembered to buy it.

That reframes the whole problem. This is not primarily a purchasing-volume failure.
It is a timing and vendor-selection failure, and it is the single most fixable thing
in the chain: same money, same suppliers, different sequencing.

## Must buy — stock and open POs together do not cover it

| Code | Material | Need | Stock | On order | **Short** | Fastest vendor |
|---|---|---:|---:|---:|---:|---|
| RM0000011 | GROUNDNUT LOOSE OIL | 78,126 | 32,770 | 28,000 | **17,356** | 8d · Vinod Agro Industries |
| RM0000021 | **LOOSE OIL GOLD** | 9,732 | 1,179 | 0 | **8,553** | ⚠️ **no purchase history at all** |
| PM0000885 | LABEL 869 GM CP MUSTARD — FRONT | 59,396 | 55,760 | 0 | **3,636** | 5d · Royal Prime Labels |
| PM0000886 | LABEL 869 GM CP MUSTARD — BACK | 59,396 | 55,760 | 0 | **3,636** | 5d · Royal Prime Labels |
| PM0000890 | LABEL 12 KG REFINED SOYABEAN | 3,324 | 370 | 0 | **2,954** | 4d · Packgen International |
| RM0000030 | REFINED COTTON OIL | 2,864 | 22 | 0 | **2,842** | 4d · National Agro Foods |
| SF0000001 | SOYABEAN OIL 13 KGS TIN IMP | 2,266 | 201 | 0 | **2,065** | 3d · Maa Jawala Overseas |
| PM0000836 | TIN 3 LTR EXTRA VIRGIN CANOLA | 403 | 5 | 0 | **398** | **17d** · National Tin Industries |
| PM0000260 | TIN 5 LTR SO OLIVE PRINTED | 352 | 337 | 0 | **15** | **22d** · National Tin Industries |

### Three of these need acting on today, for different reasons

**1. The two tins are the most urgent things on the page, and the smallest.**
PM0000836 is 398 units short with a **17-day** lead; PM0000260 is **15 units** short
with a **22-day** lead. Ranked by quantity they are last. Ranked by *when you have to
act*, they are first. This is exactly the case for lead-time-aware alarms rather than
a shortage list sorted by size — and it is the kind of thing a human scanning a
spreadsheet reliably misses.

**2. `RM0000021 LOOSE OIL GOLD` — 8,553 L short and no purchase history.**
The engine cannot derive a lead time or a vendor because this material has never
been received against a purchase order in the last year. Either it is made in-house,
or it is bought some way that does not go through SAP purchasing. Until that is
answered it is a blind spot: real demand, no known way to supply it.
*(`FG0000389 JIVO GOLD 1 LTR ROUND BOTTLE` needs 7,456 bottles and has no line in
the August plan either — same product, invisible twice.)*

**3. The 869 GMS mustard labels.** `FG0000422 JIVO MUSTARD KACCHI GHANI 869 GMS` needs
**59,396 bottles** with **zero finished stock** — it is the 4th largest requirement in
the company. Both its labels are 3,636 short with a 5-day lead. Small shortfall,
short lead, but nothing else about that SKU has any cover at all.

## Covered only by goods in transit — the starvation list

Stock alone does not cover these. The open POs do, **if they arrive in time**.

| Code | Material | Need | Stock | On order | Short vs stock | Lead range |
|---|---|---:|---:|---:|---:|---|
| RM0000003 | MUSTARD LOOSE OIL | 342,616 | 163,117 | 458,619 | **179,499** | **13–50d** |
| PM0000851 | PET BOTTLE 1 LTR 26 GM | 217,035 | 68,068 | 1,642,232 | **148,967** | 10–19d |
| RM0000002 | CANOLA COLD PRESS LOOSE OIL | 99,002 | 19,888 | 115,458 | **79,115** | 14–28d |
| RM0000009 | REFINED SUNFLOWER OIL | 66,317 | 48,483 | 26,000 | **17,833** | 7–12d |
| PM0000121 | PET BOTTLE 1 LTR 52 GMS POMACE | 79,687 | 65,925 | 457,109 | 13,762 | **2–57d** |
| PM0000835 | TIN 5 LTR FP YELLOW MUSTARD | 1,415 | 28 | 10,010 | 1,387 | 21–21d |
| PM0000892/3 | LABEL 1 LTR PRESSED SUNFLOWER | 1,820 | 299 | 5,504 | 1,521 | 4–4d |

**This list is the daily job.** Every row is a line that keeps running only if a
delivery lands before the tank empties. It is where "availability 97%, performance
30%" comes from, and it is exactly what nothing currently watches.

`PM0000121` deserves a note: a **2 to 57 day** spread on the same material. An
average lead time for that item would be meaningless. Only the per-vendor number
means anything.

## What this proves

The premise holds. Every number above came out of SAP with no new data entry, no
template circulated to any department, and nobody asked to fill in a spreadsheet.
Lead times, vendor choice, material-to-machine mapping and the requirement itself
are all derivable from what JIVO already records.

## Still open

- **BH-OT "Param" holds 411,168 L of raw material** — second only to BH-LO's 849,832 L.
  Not yet told whether that stock counts as available. If it does, several of the
  shortfalls above shrink.
- Net-of-returns vs gross for MSL — 70,635 L (~₹1.1 Cr) rides on it.
- Is the 4,241 MT August plan a target or a forecast (Finding 07).
- Contribution per litre — the allocation ranking, once the above is settled.
