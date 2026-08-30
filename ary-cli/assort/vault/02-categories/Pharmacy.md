---
type: finding
source: FR8HODBNEW (live)
mined: 2026-08-30
confidence: high
system: ARY / FusionERP8
---

# Pharmacy — the gap is real; the standalone case cannot be sized from this database

Across all 21,479 SKUs ARY lists **not one chronic-disease molecule**, and has never bought
one in the 3.4 years its purchase ledger covers (`PurchaseHeader` starts **2023-04-01** — the
shop is older than its ledger). Total oral/systemic allopathic sales are **Rs 22,324 in 12
months**, Rs 56,520 on the widest reading. That gap is REAL_GAP and it survives
[[Verify-Pass-2026-08-30]]. What this pass **deletes** is the business case: the Rs 2.66 L
gross-margin figure it used to carry has no derivation anywhere in the vault. And the ERP
blocker is real — see [[Data-Quality-Traps]] for why two purpose-built date columns hold
nothing.

**Window for every 12-month figure below: `VoucherDate >= '2025-08-31' AND < '2026-08-31'`.**
The vault's canonical window is 2025-09-01 → 2026-08-31 and differs by ~Rs 1.7 L on the
`Medicare` group; where it matters both are given.

## 1. The absence, proved three independent ways

The strongest proof is the purchase ledger, because a shop cannot sell what it never bought —
but read it knowing it only reaches back to 2023-04-01.

| Test | Result | Status |
|---|---|---|
| Chronic-molecule stem sweep over all 21,479 product names — the 45 stems named below | **0 SKUs on every one of the 45** | **VERIFIED** |
| Chronic molecules ever bought, across all 9,284 purchase bills (ledger spans 2023-04-01 → 2026-08-30) | **0** | **VERIFIED** |
| Drugs ARY *has* ever bought | **14 SKUs · 54 purchase lines · 2,777 units** — all OTC-shaped analgesic, antipyretic, cough or antiemetic | **VERIFIED** |
| Whole `Medicare` group (`ProductGroupID=138`) — balms, churan, chyawanprash, Hajmola, Safi, glucose, mosquito killer | **272 SKUs listed, 100 sold, Rs 3,22,194.46 in 12m** (Rs 3,20,534.46 on the canonical window) = **0.42%** of turnover | **VERIFIED** |
| Pharmacy counters among ARY's 12 warehouses | **0** | **VERIFIED** |

Turnover base, for the ratio above: **Rs 7,68,89,330** on this note's window;
**Rs 7,66,19,249** on the vault's canonical window — the latter is the figure
[[Verify-Pass-2026-08-30]] reconciles the payment modes against. Query:
`SELECT SUM(BillAmount), COUNT(*) FROM SaleHeader WHERE VoucherDate >= … AND < …`.

**The 45 stems, all of them, so the test is auditable:** metfor, glimep, telmi, amlod, atorv,
thyrox, montel, salbu, panto, omepr, azithro, amoxi, cefix, ciprof, oflox, doxycy, metronid,
cetiri, levocet, ondanse, domperi, ranitid, ibupro, diclof, aceclof, nimesu, tramad, predniso,
losart, ramipr, atenol, metopr, insulin, sitaglip, oximet, glucomet, nebulis, sphygmo, gauze,
syringe, stethoscop, teststrip, rehydrat, electral, prolyte. Each run as
`SELECT COUNT(*) FROM ProductMaster WHERE LOWER(REPLACE(REPLACE(REPLACE(REPLACE(ProductName,' ',''),'-',''),'.',''),'_','')) LIKE '%<stem>%'`;
all 45 returned 0, re-run 2026-08-30.

The earlier "63 stems" claim printed only 45; the 18 unnamed were unauditable and the number
is deleted. Not a safe rounding — `thermomet`, a plausible member, returns **3 live SKUs**
(`02BA` Hicks, `01J4`/`01J5` Cipla).

The `Medicare` shelf, read SKU by SKU, is Ayurvedic and Unani: Dabur Honitus, Hamdard Joshina
and Safi, Pudin Hara, Zandu Pancharishta, Boroline, Hajmola, Sugar Free Gold. It is a wellness
aisle wearing a medical name — exactly the class of mislabel [[Catalogue-Shape]] documents.

## 2. What ARY actually sells that is a drug — state the definition with the number

**No pharmacist has drawn either line below.** Both cuts are this author's own
pharmacological judgement, and the choice moves the exposure 2.5×. Whoever acts on this must
have a registered pharmacist re-draw the boundary before quoting either figure.

| Definition | SKUs listed | Sold in 12m | Units | 12m sales | Distinct bills | Status |
|---|---|---|---|---|---|---|
| **Strict** — oral/systemic allopathic only (Crocin ×3, Paracitamol, Stopache, Disprin ×2, Avomine, Wincold, D Cold ×3, Cofsils, Strepsils ×2, Benadryl ×5, Diclowin Plus) | **21** (all active) | **8** | **567** | **Rs 22,324.06** | **498** | **VERIFIED** |
| **Broad** — adds topical NSAIDs (Volini ×9, Moov ×12, Omnigel ×3, Iodex ×7, Diclowin gel ×1), Ortivin nasal spray ×3 and the 5 Cipla/generic ORS SKUs | **61** (all active) | **25** | **1,018** | **Rs 56,519.90** | **859** | **VERIFIED** |

Both rows were reproduced by enumerating the explicit ProductID lists and summing
`Quantity * SaleRate` over `SaleDetail` joined to `SaleHeader` on the window above. The broad
row previously read "42 SKUs"; the stated definition enumerates to **61**, and it is the
61-SKU set that reproduces the sold/units/sales/bills figures exactly.

The verify pass's **"45 active SKUs, Rs 39,672 / 613 bills"** could not be reproduced from
either side and its boundary was never stated. It is recorded in [[Corrections-Log]], not
quoted here.

Share of bills carrying any strict-cut drug: **498 of 373,461 = 0.13%** (VERIFIED, note's
window; 498 of 372,378 = 0.13% canonical).

**No per-resident figure is given.** The old "Rs 4.46 per resident per year" divided by a
5,000 headcount that [[Verify-Pass-2026-08-30]] correction 4 refuted and that [[Population]]
itself puts at ~4,550-4,800. FR8HODBNEW does not measure headcount; the rupee totals above do
not need one.

Two details that change how the exposure reads:

- **Schedule H status is a legal classification this database cannot settle, and this note no
  longer asserts one.** What it can show: Avomine (promethazine) sold **Rs 0 in 12m** — 8
  units all time, Rs 440, 0 on hand. But **GSK Ortivin nasal spray sold Rs 352 in 12m**
  (`0BL8` Rs 246 / 6 bills, `0BL9` Rs 106 / 1 bill; Rs 4,852 all time across all three), and
  Diclowin Plus and Diclowin gel are listed though they have never sold. Oral and topical
  diclofenac and xylometazoline are prescription molecules in India. **Prescription-only trade
  in the last 12 months is therefore not zero.** **NOT-CHECKED** — a pharmacist rules on it.
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
| ...with a real `ExpDate` | **0** — same sentinel | **VERIFIED** |
| ...carrying a **full** batch/mfg/exp triple in the free-text `Field1/2/3` | **24 rows**; **27 rows (0.024%)** carry any one of the three | **VERIFIED** |
| Date those 27 were written | **2017-04-01 → 2019-09-19.** Nothing since. | **VERIFIED** |
| `MatrixID 3` "Food Products" — the only template that names Batch No / Mfg Date / Exp Date | assigned to **50 SKUs (49 active)** | **VERIFIED** |
| `MatrixID 4` "General Products" — names **no** fields at all | assigned to **21,026 SKUs (19,054 active)** | **VERIFIED** |
| Benadryl 150 ml (`02DZ`) "22 batches" | **22 price revisions over nine years**, 2017-04-01 → 2026-07-06. First row cost 73.05 / MRP 90; latest cost 104.29 / MRP 159 (range: cost 69.17-124.21, MRP 90-170). **Every batch field blank** | **VERIFIED** |

**The correction:** the verify pass wrote *"0 real expiry dates, 0 real mfg dates."* That is
true of the two purpose-built columns and false of the schema as a whole — batch and expiry
live in the free-text `Field1/2/3` of a `MatrixID 3` child row. **FusionERP8 CAN hold batch
and expiry. Nobody has used it since 2019, and it is free text with no validation** — row
`05LA0001002` carries an expiry of 11-May-2017 *before* its mfg date of 12-Aug-2017.

That is worse, not better. A capability nobody exercises is a habit problem on top of a
software problem, and the software half is still half-built: the feature reaches 49 SKUs while
19,054 sit on a template that defines nothing. A pharmacy cannot run without batch and expiry
— it is required for recall, for the Schedule H1 register and for expiry returns to the
supplier. **This must be settled with the FusionERP8 vendor before a licence is worth applying
for**, and the question is now sharper: *not* "can it hold expiry" but "will you extend
`MatrixID 3` to the pharmacy range, enforce entry at goods-receipt, and validate the dates?"

## 4. The economics — cannot be sized from this database

| Line | Figure | Status |
|---|---|---|
| Gross margin a pharmacy would earn | **not sized** — the Rs 2.66 L that stood here had no revenue base, no margin %, no SKU count and no demand proxy, in this note or in [[Verify-Pass-2026-08-30]]. Deleted, not softened. | **DELETED** |
| Registered pharmacist, dedicated FTE | **Rs 2.16-3.00 L/yr** | **ESTIMATED** — outside HP salary range, not measurable in FR8HODBNEW |
| Contribution | **cannot be computed** — it was arithmetic on the deleted row | **DELETED** |
| Before rent | ARY pays none — it occupies Trust premises free ([[Verify-Pass-2026-08-30]]) | **VERIFIED** |
| Before shrink, expiry write-off and working capital | Not costed anywhere | **NOT-CHECKED** |

**What can be said:** the cost side is a hard, recurring Rs 2.16-3.00 L/yr and the revenue
side is unmeasured. The pharmacist is not optional and not shareable at the margin — HP
requires one who swears an affidavit that they are *"not engaged anywhere else in any kind of
service or business."* A build/no-build answer needs a revenue estimate with its assumptions
written down; this vault cannot supply one.

**The one thing that would change the answer is a Trust-shared licence and pharmacist.**
Whether Akal Hospital holds a drug licence or runs a dispensary is **unknown — nothing in
FR8HODBNEW touches it.** That conversation is free and it happens before any money moves —
[[Open-Questions]] #2 and #3.

**What the data does say about that hospital, and it is not what anyone assumed:** Akal
Hospital (`CustomerID 00009` / `AccountID 244` — the ledger name, no "Charitable") is **ARY's
customer, not its supplier or its dispensary partner** — **Rs 2,76,343 net debit** (Dr
2,78,469 − Cr 2,126) over **177 vouchers**, 60 bills and Rs 78,210 in the last 12 months.
Its top spend is **tailoring and fabric, not anything medical**: Stitching Charges Rs 69,035,
Fabric Spun Sky Blue Rs 50,260, Bed Sheet Rs 17,940, Fabric Spun Purple Rs 13,775, Navy
Rs 9,000, Curtain 4X7 Rs 5,985, Havells Room Heater Rs 5,199 — roughly half of its all-time
Rs 2.71 L. Across all five clinical accounts (hospital, nursing college, two doctors, the
de-addiction ward), **all-time `Medicare`-group spend is Rs 13,187.85 over 34 SKUs** (Jivo
Pain Relief Oil Rs 3,080, Pudin Hara Rs 1,319, Sugar Free Gold Rs 1,240, Chyawanprash Rs 790)
and **strict-cut drug purchases are Rs 0, zero rows.** **VERIFIED.**

The old "Rs 5,52,686 over 177 vouchers" was exactly double the ledger — `AccountMaster`
carries the same running totals as the `TransactionChild` sum, and adding both sources doubles
the balance. The old "Rs 1,801 of medical purchases" was an undisclosed subset and is deleted.

## 5. The Schedule K question is unsettled — do not report it closed

India has **no statutory OTC category**: there is no schedule of drugs a shop may sell without
a Form 20/21 licence, so a compliant "OTC-only corner" does not exist in Indian law as
commonly imagined. Against that, **Schedule K to the Drugs and Cosmetics Rules carries
exemptions** from licensing for specified classes and circumstances, including household
remedies in villages. **Whether any of them reaches a general store on this campus is a legal
question this database cannot answer.** A lawyer, or the Sirmaur Drug Inspector, decides it.
Status: **NOT-CHECKED, and it must stay that way in writing until somebody qualified rules.**

**The trap to avoid:** the lane's remedy — "stop selling Crocin, Disprin and Volini" — closes
**Rs 7,303.06 of the Rs 56,519.90 broad exposure, 12.9%** (VERIFIED). It leaves Benadryl
(Rs 12,372), Strepsils, Paracitamol, Cofsils and D Cold on the shelf, and leaves Ortivin —
which actually traded — untouched. **A partial de-list that reports the offence closed is a
false all-clear, and that is worse than the original finding.** Either the shelf is lawful as
it stands or it is not; a 13% trim does not decide it.

Calibration, explicitly: this is **Rs 22,000-57,000 a year of exposure inside a Rs 7.66 Cr
business**, and it is what essentially every kirana in India does. Housekeeping to fold into
the pharmacy decision — not a scandal, and not a reason to stop trading.

## What this does NOT show

- **Demand is not measured and cannot be.** Nothing in FR8HODBNEW sees how much chronic
  medicine the campus consumes or where it buys today. **The gap is certain; its value is
  unknown, and this pass deleted the one number that pretended otherwise.**
- **The purchase-ledger proof covers 2023-04-01 onward only.** `02DZ`'s own price history runs
  from 2017, so the shop predates its ledger by years. "Never bought" means never in 3.4 years
  of 9,284 bills.
- **If Akal Hospital's dispensary already retails to residents, the prize shrinks toward zero**
  and is served off-book. That needs a human to walk in and look — [[Open-Questions]].
- **A probe-zero on one correctly-spelled term is still not proof of absence.** ARY spells it
  **"Paracitamol"**: `probe paracetamol` returns 0 while `probe paracitamol` returns 2 SKUs and
  Rs 590 (VERIFIED today). The 2026-08-30 fix normalised punctuation and spacing; it does
  nothing for the house's own misspellings. **Probe stems, not words**, and read the SKU block
  under the verdict row — punctuation-stripping also makes short terms promiscuous (`pan-d` →
  `pand` → "Meiji Hello Panda Biscuits"). See [[Data-Quality-Traps]].
- **The zsh word-split trap invalidates scripted probes and scripted sweeps.** `t='ors
  electral'; ./ary assort probe $t` returns 0 where `probe ors` alone returns 29 SKUs, and
  `for s in $STEMS` under zsh iterates **once over the whole string** — it fired again while
  re-running the stem sweep for this pass. Use an array and quote `"$@"`.
- **The licensing detail below the pharmacist requirement was not re-verified in this pass**
  (Form 19 → Form 20/21, Rs 3,000 challan, Panchayat-Pradhan-stamped site map for a rural
  site, Schedule H1 register retained 3 years, DPCO 2013's 16% retailer cap on scheduled
  formulations). Carried from the research lane as **NOT-CHECKED**; confirm with DHSR Shimla
  before acting on any of it.

## See also

- [[Verify-Pass-2026-08-30]] — the pass that restored this blocker, and correction 4 that
  refuted the population estimate this note no longer consumes
- [[Corrections-Log]] — the full record of what was deleted from this note, including the
  unreproduced "45 SKUs / Rs 39,672 / 613 bills"
- [[Data-Quality-Traps]] — the sentinel-date pattern, and why probe still produces false zeros
  on the house's own spellings
- [[Availability]] — 6 of 21 drug SKUs are empty today; the same replenishment failure runs
  through every category and outranks any new-category decision
- [[Gap-List]] — where the other REAL_GAP (medical devices) sits, and how few survived
- [[Open-Questions]] — #2 the Trust-shared licence and #3 the hospital dispensary; both are
  free to ask and both move this verdict more than any query can
- [[Population]] — why no per-capita figure appears above
- [[Catalogue-Shape]] — the wellness-aisle-wearing-a-medical-name pattern the `Medicare` group
  is an instance of
