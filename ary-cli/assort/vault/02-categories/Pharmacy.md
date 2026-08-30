---
type: finding
source: FR8HODBNEW (live)
mined: 2026-08-30
confidence: high
system: ARY / FusionERP8
---

# Pharmacy — the gap is total and certain; the standalone economics are not

Across all 21,479 SKUs ARY lists **not one chronic-disease molecule**, has never bought one
in the whole life of its purchase ledger, and sells about **Rs 4.46 of allopathic medicine
per resident per year**. That is REAL_GAP and it survives [[Verify-Pass-2026-08-30]] intact.
What does not survive is the business case: **Rs 2.66 L of gross margin against a mandatory
dedicated pharmacist at Rs 2.16-3.00 L/yr.** And the ERP blocker is real — see
[[Data-Quality-Traps]] for why two purpose-built date columns hold nothing.

## 1. The absence, proved three independent ways

The strongest proof is the purchase ledger, because a shop cannot sell what it never bought.

| Test | Result | Status |
|---|---|---|
| Chronic-molecule stem sweep over all 21,479 product names (metfor, glimep, telmi, amlod, atorv, thyrox, montel, salbu, panto, omepr, azithro, amoxi, cefix, ciprof, oflox, doxycy, metronid, cetiri, levocet, ondanse, domperi, ranitid, ibupro, diclof, aceclof, nimesu, tramad, predniso, losart, ramipr, atenol, metopr, insulin, sitaglip, oximet, glucomet, nebulis, sphygmo, gauze, syringe, stethoscop, teststrip, rehydrat, electral, prolyte + 18 more) | **0 SKUs on every one of 63 stems** | **VERIFIED** |
| Chronic molecules ever bought, across all 9,284 purchase bills (ledger spans 2023-04-01 → 2026-08-30) | **0** | **VERIFIED** |
| Drugs ARY *has* ever bought | **14 SKUs · 54 purchase lines (7 of them opening) · 2,777 units** — all OTC-shaped analgesic, antipyretic, cough or antiemetic | **VERIFIED** |
| Whole `Medicare` group — balms, churan, chyawanprash, Hajmola, Safi, glucose, mosquito killer | **272 SKUs listed, 100 sold, Rs 3,23,327 in 12m** = 0.42% of Rs 7.71 Cr turnover | **VERIFIED** |
| Pharmacy counters among ARY's 12 warehouses | **0** | **VERIFIED** |

Query for the stem sweep: a 63-term `UNION ALL` CTE `LEFT JOIN`ed to
`LOWER(REPLACE(REPLACE(REPLACE(REPLACE(ProductName,' ',''),'-',''),'.',''),'_',''))` over
`ProductMaster`, grouped by stem. Every row returned `0`.

The `Medicare` shelf, read SKU by SKU, is Ayurvedic and Unani: Dabur Honitus, Hamdard
Joshina and Safi, Pudin Hara, Zandu Pancharishta, Boroline, Hajmola, Sugar Free Gold. It is
a wellness aisle wearing a medical name — exactly the class of mislabel [[Catalogue-Shape]]
documents.

## 2. What ARY actually sells that is a drug — state the definition with the number

The verify pass quoted **"45 active SKUs, Rs 39,672 / 613 bills"** and never stated how it
drew the boundary. **I could not reproduce it from either side.** Both reconstructions below
are reproducible; quote one of these, with its definition attached.

| Definition | SKUs listed | Sold in 12m | Units | 12m sales | Distinct bills | Status |
|---|---|---|---|---|---|---|
| **Strict** — oral/systemic allopathic only (Crocin ×3, Paracitamol, Stopache, Disprin ×2, Avomine, Wincold, D Cold ×3, Cofsils, Strepsils ×2, Benadryl ×5, Diclowin Plus) | **21** (all active) | **8** | **567** | **Rs 22,324.06** | **498** | **VERIFIED** |
| **Broad** — adds topical NSAIDs (Volini, Moov, Omnigel, Iodex, Diclowin gel), Ortivin nasal spray and the 5 Cipla/generic ORS SKUs | **42** | **25** | **1,018** | **Rs 56,519.90** | **859** | **VERIFIED** |
| Verify pass's stated figure | 45 | — | — | Rs 39,672 | 613 | **NOT REPRODUCED** — sits between the two, definition unstated |

Share of bills carrying any oral/systemic drug: **498 of 374,448 = 0.13%** (VERIFIED).
Per resident per year: **Rs 4.46** (ESTIMATED — Rs 22,324.06 is VERIFIED, the 5,000
headcount is the campus figure from [[Population]] and is not measurable in FR8HODBNEW).

Two details that change how the exposure reads:

- **Avomine (promethazine, Schedule H) is the only prescription-only medicine in the
  catalogue — and it sold Rs 0 in the last 12 months.** 8 units all time, last sale
  2025-03-22, 0 on hand today. Listed, not traded. **VERIFIED.**
- **ORS is stocked but filed under `Soft Drinks`** — Cipla Ors 200 Ml and four siblings,
  **Rs 8,161.20** in 12m. It is the one rehydration item that is not a hard zero, and only
  because it is sold as a beverage. **VERIFIED.**

**And this shelf has the same availability disease as the rest of the shop:** only **6 of the
21** strict-list SKUs have stock today. Crocin 500 mg last sold 2026-02-14 and is empty;
Benadryl 60 ml sold on 2026-08-24 and is empty. **VERIFIED** — see [[Availability]].

## 3. ⛔ The ERP blocker — restored, with the evidence corrected

The blocker is REAL. The sentence the verify pass used to state it was wrong, and the
correction makes the case *stronger*, not weaker.

| Fact | Value | Status |
|---|---|---|
| `ProductChildMaster` rows | **111,253** | **VERIFIED** |
| ...with a real `MfgDate` | **0** — every row is the `1900-01-01` sentinel | **VERIFIED** |
| ...with a real `ExpDate` | **0** — same sentinel, min = max = 1900-01-01 | **VERIFIED** |
| ...carrying a batch/mfg/exp triple in the free-text `Field1/2/3` | **27 rows (0.024%)**, e.g. `Gt-08` / `01-Apr-2017` / `31-Mar-2018` | **VERIFIED** |
| Date those 27 were written | **2017-04-01 → 2019-09-19.** Nothing since. | **VERIFIED** |
| `MatrixID 3` "Food Products" — the only template that names Batch No / Mfg Date / Exp Date | assigned to **50 SKUs (49 active)** | **VERIFIED** |
| `MatrixID 4` "General Products" — names **no** fields at all | assigned to **21,026 SKUs (19,054 active)** | **VERIFIED** |
| Benadryl 150 ml (`02DZ`) "22 batches" | **22 price revisions over nine years**, 2017-04-01 → 2026-07-06, cost 69.17 → 124.21, MRP 90 → 170, **every batch field blank** | **VERIFIED** |

**The correction:** the verify pass wrote *"0 real expiry dates, 0 real mfg dates."* That is
true of the two purpose-built columns and false of the schema as a whole — batch and expiry
live in the free-text `Field1/2/3` of a `MatrixID 3` child row, and 27 of them carry real
values. **FusionERP8 CAN hold batch and expiry. Nobody has used it since 2019.**

That is worse, not better. A capability nobody exercises is a habit problem on top of a
software problem, and the software half is still half-built: the feature reaches 49 SKUs
while 19,054 sit on a template that defines nothing. A pharmacy cannot run without batch and
expiry — it is required for recall, for the Schedule H1 register and for expiry returns to
the supplier. **This must be settled with the FusionERP8 vendor before a licence is worth
applying for**, and the question is now sharper: *not* "can it hold expiry" but "will you
extend `MatrixID 3` to the pharmacy range and enforce entry at goods-receipt?"

## 4. The economics — the gap is real, the standalone case is not

| Line | Figure | Status |
|---|---|---|
| Gross margin a pharmacy would earn | **Rs 2.66 L/yr** | **ESTIMATED** — the sizer's figure, carried forward, **not re-derived here** |
| Registered pharmacist, dedicated FTE | **Rs 2.16-3.00 L/yr** | **ESTIMATED** — outside HP salary range, not measurable in FR8HODBNEW |
| **Contribution** | **-Rs 0.34 L to +Rs 0.50 L** | **ESTIMATED** — arithmetic on the two rows above |
| Before rent | ARY pays none — it occupies Trust premises free ([[Verify-Pass-2026-08-30]]) | **VERIFIED** |
| Before shrink, expiry write-off and working capital | Not costed anywhere | **NOT-CHECKED** |

**A business whose best case is Rs 50,000 a year and whose worst case is a loss, before
shrink and before capital, is not a business.** The pharmacist is not optional and not
shareable at the margin: HP requires a registered pharmacist who swears an affidavit that
they are *"not engaged anywhere else in any kind of service or business."*

**The one thing that changes the answer is a Trust-shared licence and pharmacist.** Akal
Charitable Hospital is on the same campus and almost certainly already holds both. That
conversation is free and it happens before any money moves — [[Open-Questions]] #2 and #3.

**What the data says about that hospital, and it is not what anyone assumed:** Akal Hospital
(`00009`) is **ARY's customer, not its supplier or its dispensary partner** — Rs 5,52,686
debit balance over 177 vouchers, 60 bills and Rs 78,210.40 in the last 12 months to
2026-08-28, and what it buys is **bed sheets (Rs 17,940), more bed sheets, curtains and a
Havells room heater.** Across all five clinical accounts (hospital, nursing college, two
doctors, the de-addiction ward), **all-time** medical purchases from ARY total **Rs 1,801** —
hot water bottles, 50 band-aids, one Dettol antiseptic, two cotton rolls. **VERIFIED.**

## 5. The Schedule K question is unsettled — do not report it closed

India has **no statutory OTC category**: there is no schedule of drugs a shop may sell
without a Form 20/21 licence, so a compliant "OTC-only corner" does not exist in Indian law
as commonly imagined. Against that, **Schedule K to the Drugs and Cosmetics Rules carries
exemptions** from licensing for specified classes and circumstances, including household
remedies in villages. **Whether any of them reaches a general store serving 5,000 people in
Rajgarh is a legal question this database cannot answer.** A lawyer, or the Sirmaur Drug
Inspector, decides it. Status: **NOT-CHECKED, and it must stay that way in writing until
somebody qualified rules.**

**The trap to avoid:** the lane's remedy — "stop selling Crocin, Disprin and Volini" —
closes **Rs 7,303 of the Rs 56,520 broad exposure, 12.9%** (VERIFIED). It leaves Benadryl
(Rs 12,372), Strepsils, Paracitamol, Cofsils and D Cold on the shelf and leaves Avomine, the
one Schedule H item, still listed. **A partial de-list that reports the offence closed is a
false all-clear, and that is worse than the original finding.** Either the shelf is lawful as
it stands or it is not; a 13% trim does not decide it.

Calibration, explicitly: this is **Rs 22,000-57,000 a year of exposure inside a Rs 7.71 Cr
business**, and it is what essentially every kirana in India does. Housekeeping to fold into
the pharmacy decision — not a scandal, and not a reason to stop trading.

## What this does NOT show

- **Demand is not measured and cannot be.** Nothing in FR8HODBNEW sees how much chronic
  medicine 5,000 residents consume or where they buy it today. **The gap is certain; its
  value is unknown.** The Rs 2.66 L is an outside estimate this pass did not re-derive.
- **If Akal Hospital's dispensary already retails to residents, the prize shrinks toward
  zero** and is served off-book. That needs a human to walk in and look — [[Open-Questions]].
- **A probe-zero on one correctly-spelled term is still not proof of absence.** ARY spells it
  **"Paracitamol"**: `probe paracetamol` returns 0 while `probe paracitamol` returns 2 SKUs
  and Rs 590 (VERIFIED today). The 2026-08-30 fix normalised punctuation and spacing; it does
  nothing for the house's own misspellings. **Probe stems, not words**, and read the SKU block
  under the verdict row — punctuation-stripping also makes short terms promiscuous
  (`pan-d` → `pand` → "Meiji Hello Panda Biscuits"). See [[Data-Quality-Traps]].
- **The zsh word-split trap invalidates scripted probes.** `t='ors electral'; ./ary assort
  probe $t` returns 0 where `probe ors` alone returns 29 SKUs. A scripted zero looks exactly
  like a real gap — quote `"$@"`.
- **The licensing detail below the pharmacist requirement was not re-verified in this pass**
  (Form 19 → Form 20/21, Rs 3,000 challan, Panchayat-Pradhan-stamped site map for a rural
  site, Schedule H1 register retained 3 years, DPCO 2013's 16% retailer cap on scheduled
  formulations). Carried from the research lane as **NOT-CHECKED**; confirm with DHSR Shimla
  before acting on any of it.

## See also

- [[Verify-Pass-2026-08-30]] — the pass that restored this blocker, and the reversal that
  killed the institutional case alongside it
- [[Data-Quality-Traps]] — the sentinel-date pattern, and why probe still produces false
  zeros on the house's own spellings
- [[Availability]] — 6 of 21 drug SKUs are empty today; the same replenishment failure runs
  through every category and outranks any new-category decision
- [[Gap-List]] — where the other REAL_GAP (medical devices) sits, and how few survived
- [[Open-Questions]] — #2 the Trust-shared licence and #3 the hospital dispensary; both are
  free to ask and both move this verdict more than any query can
- [[Catalogue-Shape]] — the wellness-aisle-wearing-a-medical-name pattern the `Medicare`
  group is an instance of
- [[Corrections-Log]] — the full record of what was deleted from this note
