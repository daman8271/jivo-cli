---
type: finding
source: FR8HODBNEW (live)
mined: 2026-08-29
confidence: medium
system: ARY / FusionERP8
---

# Pharmacy — the largest gap, and the blocker nobody would guess

A township of 5,000, several thousand of them boarding children, bought **26 strips of
paracetamol** in twelve months. There is no pharmacy.

But the gate is not the licence — it is that **FusionERP8 cannot store an expiry date**
(0 of 111,021 rows). That is a software question, and it must be answered before any money
moves. See [[Open-Questions]].

## The compliance exposure and the licensing path

### ARY already sells drugs, without a drug licence

Verified at SKU level (`ary query` on SaleDetail × ProductMaster, 12-month window):

| Product | Bills | Qty | 12m sales |
|---|---|---|---|
| Vicks VapoRub 10 ml | 228 | 232 | ₹10,833 |
| Vicks Inhaler 0.5 ml | 146 | 156 | ₹10,344 |
| **Johnson's Benadryl 150 ml** | 47 | 49 | **₹8,055** |
| Strepsils 8 Tab | 208 | 246 | ₹7,101 |
| **Omnigel (Cipla) 30 g** | 37 | 37 | **₹5,486** |
| Moov Pain Relief 20 g | 44 | 45 | ₹5,445 |
| Moov Pain Relief 50 g | 22 | 22 | ₹5,035 |
| **Johnson's Benadryl 60 ml** | 43 | 47 | **₹3,760** |
| **Volini Gel 30 g** | 20 | 20 | **₹3,270** |
| + Vicks 50/25/5 ml, Moov spray/10 g, Volini spray/20 g, Vicks BabyRub | | | ₹14,400 |
| **Disprin Tablet** | 107 | 122 | ₹925 |
| **Crocin 500 mg** | 26 | 26 | ₹502 |
| **TOTAL (19 SKUs)** | **~1,100** | | **≈₹75,000** |

The research lane put the "unambiguously allopathic" slice at **₹41,023 across 613 bills**
and called ~76% (₹31,200) Schedule H.

**My correction to that lane, and it matters:** the largest lines by value — **Vicks VapoRub,
Inhaler and BabyRub, ₹28,100 combined — are licensed in India as Ayurvedic proprietary
medicines**, not Schedule H allopathic drugs. Moov is largely a counter-irritant. The
genuinely prescription-schedule molecules here are **Benadryl (diphenhydramine, ₹11,815),
Volini and Omnigel (diclofenac, ₹12,908), Crocin (paracetamol) and Disprin (aspirin)** —
roughly **₹25,000-26,000 a year**, not ₹31,200 of a ₹41,023 base.

**But the lane's underlying legal point is correct and important:** **India has no statutory
OTC category.** There is no schedule of drugs a shop may sell without a licence, so the
common idea of a compliant "OTC-only corner" does not exist in Indian law. Selling Crocin
or Benadryl over a general-store counter without a Form 20/21 licence is technically
unlicensed sale of a drug.

**Calibration, explicitly:** this is real but it is **₹25,000 a year of exposure in a
₹9 Cr business**, and it is what essentially every kirana in India does. It is a
housekeeping item to fold into the pharmacy decision — **not a scandal, and not a reason to
stop trading.** The lane's own adversarial verifier was killed by the quota reset, so
**this lane has not been independently challenged.** Treat the legal detail as
well-sourced-but-unverified until a second pass runs.

### The licensing path (HP-specific, from the lane, VERIFIED against HP sources)

| Requirement | Detail |
|---|---|
| Application | **Form 19** under Rule 59(2), for **Form 20 + Form 21** (retail) |
| Government fee | **₹3,000** challan |
| Pharmacist | A registered pharmacist with **HP Pharmacy Council (Shimla)** registration, who must swear an affidavit they are **"not engaged anywhere else in any kind of service or business"** — so a **dedicated FTE**, not a shared name |
| Premises (rural) | Site map **stamped and signed by the Panchayat Pradhan** — 2 original copies. Rural sites do not use municipal approval |
| Company papers | Board resolution authorising the applicant, plus MOA and AOA (Jivo Wellness Pvt Ltd) |
| Standing duties | **3 months' written notice before closing**; fresh licence on any change of premises or constitution |
| Schedule H1 | Separate register at time of supply: prescriber name and address, patient, drug, quantity — retained **3 years** |
| Margin | **DPCO 2013 caps scheduled-formulation retailer margin at 16%** of price-to-retailer, unchanged as at 30-Jun-2026 |
| Authority to ask | Sirmaur Drug Inspector / DHSR Shimla, **0177-2621383** |

### ⛔ The hard blocker nobody would have guessed — the ERP cannot hold an expiry date

`ary query` on `ProductChildMaster`: **111,021 rows. `ExpDate` populated on ZERO.
`MfgDate` populated on ZERO.**

FusionERP8 as configured **cannot track a pharmaceutical batch or expiry date at all.** A
pharmacy legally cannot operate without batch and expiry tracking — it is required for
recall, for Schedule H1 records and for expiry returns to the supplier. **This must be
solved before a licence is worth applying for**, and the answer depends on whether the
FusionERP8 vendor has a pharmacy module. It is a software question, not a retail one.

### The one internal question to ask first

**Akal Charitable Hospital is on the same campus** — 100 beds, 11 doctors, ~120-131 free
OPD patients a day. It almost certainly already holds a drug licence and runs a dispensary.
Two consequences: (a) it may be able to host or sponsor the licence, and (b) whatever it
already dispenses free to residents is demand a retail pharmacy will **not** get. That is
one conversation inside the same Trust, and it should happen before any money is spent.

## See also

- [[Gap-List]] — the probe evidence: 3 paracetamol SKUs, 1 selling, Rs 502
- [[Open-Questions]] — the hospital licence question that comes first
- [[Data-Quality-Traps]] — the expiry-date finding
