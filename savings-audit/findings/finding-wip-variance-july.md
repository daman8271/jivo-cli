---
title: "July WIP variance ₹2.04 Cr — not production yield loss: 1.32 lakh litres of recovered oil booked into stock at ZERO value"
created: 2026-07-28
verdict: REVISED
amount_verified_inr: 14307747
kind: one-time-recovery
tags: [savings-audit, finding, inventory, costing, production, returns, sap-b1, oil]
---

# WIP variance ₹2.04 Cr (July 2026) — REVISED: the number is right, the diagnosis is wrong, and the money is oil, not yield

Part of [[SAVINGS-MOC]] · Evidence: [[expense-outliers]]

**Verdict: REVISED. ₹2,04,36,523 P&L charge is real to the rupee → ₹0 of it is a "production recovery". ₹1,43,07,747 is bankable, and it is a physical asset nobody can see.**

---

## What a CFO needs to know

JIVO Oil's profit and loss account took a **₹2,04,36,523 hit in July 2026** in an account called `5100003 WORK IN PROGRESS VARIANCE PRODUCTION`. The original finding read that as a factory problem — components worth ₹2 Cr consumed without producing ₹2 Cr of finished goods, a 3.92% yield loss — and asked Production to reconcile it. **Production has nothing to reconcile.** In July, JIVO ran 296 normal production orders and 23 special orders, and between them they produced a variance of **exactly ₹0.00**. Every rupee of the ₹2.04 Cr came from **114 *disassembly* orders**, and 110 of those were run on a single day, 23 July, in warehouse **BH-GR — "Bhakharpur GR", the goods-return warehouse**.

What actually happened is this. Returned stock had been piling up in the returns warehouse since March. On 23 July the plant de-packed **72,326 units** of it — 22,765 one-litre Kachchi Ghani mustard bottles, 3,102 five-litre mustard jerries, 1,653 five-litre pomace olive tins, desi ghee, sunflower, rice bran, cold press, and more — carried in the books at **₹2,09,12,085**. Out of that came two things: the empty bottles, tins, caps, labels and cartons, which SAP valued correctly at **₹13,01,755**, and **131,788.92 litres and kilos of bulk oil and ghee, which SAP valued at ₹0.00**. Not a low value. Zero. All 114 inventory receipt lines carry `TransValue = 0`, and every batch SAP created for that oil carries `CostTotal = 0` and **no expiry date at all**, under batch numbers that are visibly keyboard mash — `6541261`, `45456456465`, `6546545`, `334`, `1`.

Because the oil came in at nothing, the entire remaining value of the returned goods — ₹2,09,12,085 less ₹13,01,755 = **₹1,96,10,330** — had nowhere to go and fell straight into the variance account and into July's profit. **That is 96% of the charge, and it is a costing defect, not a factory loss.** Price the recovered oil at JIVO's own issue rates for the same items over the preceding three months (mustard ₹136.09, olive ₹150.73, canola ₹133.29, sunflower ₹135.51, desi ghee ₹450.12 …) and it comes to **₹1,90,76,996 — 97.3% of the 23-July charge.** The variance *is* the un-costed oil, to within 2.7%.

So the ₹2.04 Cr is not money that can be collected from anyone, and reversing the entry creates no cash — it only moves cost between periods, because the moment that zero-cost oil is consumed, a future month's cost of goods will be understated by the same amount. **What is real is the oil.** Roughly **1.32 lakh litres of edible oil and ghee are sitting in the goods-return warehouse today with a book value of ₹0**, invisible to planning, invisible to any stock statement, and with no traceability or shelf life recorded. Left alone it will be forgotten and eventually dumped, and JIVO will buy 1.32 lakh litres of fresh oil it already owns. Put back into production it displaces that purchase, rupee for rupee. JIVO has done exactly this before — in April and May 2026 Accounts revalued smaller zero-cost recoveries (SAP inventory-revaluation documents, `TransType 162`) and the plant consumed 13,063 litres of them — so the route is proven and the material is evidently considered fit. Against ex-market returns with no recorded expiry a quality reserve is mandatory, so I bank **₹1,43,07,747 (75% of ₹1.91 Cr)** and treat the rest as conditional on QC.

One more correction worth the CFO's attention: the finding's claim that this account is "₹0 in every other month" is not true, and the reason matters. In March, April and May 2026 the same variance arose — ₹27.33 lakh, ₹71.29 lakh, ₹26.41 lakh — and was cleared by four manual journal entries memo'd **"Variance A/c Reconsiled"**, which moved **₹97,70,628 into `5100013 COST OF GOODS SOLD`**. The variance was never zero; it was being quietly reclassified inside the P&L. July's ₹2.04 Cr has not been reclassified yet only because the month is not closed. **If nothing is done before the July close, ₹2.04 Cr will land in cost of goods sold and ₹1.91 Cr of real oil will stay on the books at nil.**

---

## Verdict and re-derived figures

| Claim in rank #22 | My re-derivation | Status |
|---|---|---|
| July net debit to `5100003` = ₹2,04,36,523 | **₹2,04,36,523.32** | ✅ exact |
| "100% TransType 202 (production orders)" | True, but 202 covers **disassembly**; real production = **₹0.00** | ❌ misleading |
| "₹1.96 Cr on a single day 2026-07-23" | **₹1,96,10,330.34**, 110 orders, warehouse BH-GR | ✅ exact |
| "largest: RM0000001 **45,74,634**" | That journal (TransId 221445) nets to **₹0.00** — a +₹45,74,633.63 debit and an equal credit. The figure is the cost of batch `SI 726596810`, a correctly costed 33,000-unit goods receipt at BH-LO | ❌ **wrong** |
| "RM0000002 26,80,081" | Same — nets to **₹0.00** | ❌ **wrong** |
| "FG0000030 30,41,609" | Gross debit only; **net ₹28,84,342.95** | ⚠️ overstated |
| "₹0 in 12 of prior 16 months" | Mar/Apr/May-26 variances of ₹27.33L / ₹71.29L / ₹26.41L were **moved to COGS `5100013`**, not absent. FY24-25 swung ±₹61 lakh/month | ❌ misleading |
| "3.92% yield/costing loss on ₹52.20 Cr WIP throughput" | Throughput checks out (issues ₹53.91 Cr, receipts ₹51.46 Cr) but the gap is **not yield** | ❌ wrong cause |
| kind: `one-time-recovery`, ₹2.04 Cr | No counterparty, no cash. Recovery exists but it is **inventory, not the P&L entry** | ❌ **REVISED** |

**True top contributors (net, not gross):** FG0000030 Mustard Kachi Ghani 1L ₹28,84,343 · FG0000011 Mustard 5L ₹19,48,351 · FG0000008 Pomace Olive 5L Tin ₹17,74,109 · FG0000243 Sano Mustard 869g ₹9,71,973 · FG0000139 Sano Sunflower 5L ₹7,75,582.

**Split of the July charge by production-order type:**

| Order type | Orders | Warehouse | Net variance |
|---|---:|---|---:|
| **D — Disassembly** | 110 | BH-GR (Goods Return) | **₹2,01,26,703** |
| D — Disassembly | 4 | BH-PF | ₹2,38,841 |
| D — Disassembly | 4 | BH-FG | ₹70,980 |
| **S — Standard production** | **296** | BH-PF / BH-BS / BH-PC / BH-GJ | **₹0.00** |
| **P — Special production** | **23** | BH-LO | **₹0.00** |

---

## Key SQL evidence

**1 — The charge replicates exactly (and the account is a P&L expense: `ActType='E'`, `GroupMask=5` Cost of Sales).**

```sql
SELECT TO_VARCHAR(j."RefDate",'YYYY-MM') AS MON, j."TransType", COUNT(*) AS LINES,
       SUM(IFNULL(j."Debit",0)-IFNULL(j."Credit",0)) AS NET
FROM JIVO_OIL_HANADB.JDT1 j
WHERE j."Account"='5100003' AND j."RefDate">='2024-04-01'
GROUP BY TO_VARCHAR(j."RefDate",'YYYY-MM'), j."TransType"
HAVING ABS(SUM(IFNULL(j."Debit",0)-IFNULL(j."Credit",0)))>1 ORDER BY 1,2;
```
→ `2026-07 | 202 | 858 | 20,436,523.32`. Contra is `1103009 WORK IN PROGRESS PRODUCTION` for the exact opposite amount; `1103001` and `1103006` net to zero.

**2 — The whole charge is disassembly at the goods-return warehouse.** Net variance per journal, joined to `OWOR` by `JDT1."BaseRef" = OWOR."DocNum"`, grouped by `OWOR."Type"` / `"Warehouse"` — table above. `OWHS`: `BH-GR = 'Bhakharpur GR'`; sister codes `DL-GR`, `PB-RG`, `PB-SG` confirm GR = goods return.

**3 — The root cause: recovered oil received at zero value.** This is the decisive query — it reconstructs the variance from the *inventory* ledger, independently of the GL:

```sql
SELECT SUBSTRING(m."ItemCode",1,2) AS CLASS, m."TransType", m."Warehouse", COUNT(*) AS N,
       SUM(m."InQty") AS INQ, SUM(m."OutQty") AS OUTQ, SUM(m."TransValue") AS TRANSVAL
FROM JIVO_OIL_HANADB.OINM m
WHERE m."DocDate"='2026-07-23' AND m."TransType" IN (59,60)
GROUP BY SUBSTRING(m."ItemCode",1,2), m."TransType", m."Warehouse";
```

| Class | Type | Whs | Lines | Qty | Value |
|---|---|---|---:|---:|---:|
| FG | 60 issue | BH-GR | 106 | 72,326 out | **−₹2,09,12,085.17** |
| PM | 59 receipt | BH-GR | 671 | 286,164.76 in | +₹13,01,754.84 |
| **RM** | **59 receipt** | **BH-GR** | **114** | **131,788.92 in** | **₹0.00** |

₹2,09,12,085.17 − ₹13,01,754.84 = **₹1,96,10,330.33** = the 23-July variance, to the paisa.

**4 — The zero-cost batches.** `OBTN` rows created 2026-07-23 for `RM%`: every disassembly-recovered batch has `CostTotal = 0`, `ExpDate = NULL`, and a junk `DistNumber`. On the same day the properly-costed batches from real production carry value — `SI 726596810`, 33,000 units, `CostTotal = 4,574,633.63` (this is the number the finding mistook for the largest variance line).

**5 — The oil is still there, still at nil.** `OITW` for `WhsCode='BH-GR'`: RM0000003 Mustard 66,687.60 · RM0000001 Loose Refined Olive 27,788.61 · RM0000002 Canola 15,698.16 · RM0000009 Sunflower 9,931.22 · RM0000025 Soyabean 6,418.79 · RM0000011 Groundnut 3,846 · RM0000007 Rice Bran 2,549 · RM0000006 Desi Ghee 2,457.83 · + 6 more ≈ **140,068 units, book value ₹0**. All-time book value of the entire BH-GR warehouse is now just ₹25,82,596 against 152,228 physical units.

**6 — Valuation of the recovered oil** at JIVO's own issue rates, 2026-05-01 → 2026-07-22 (`OINM`, `OutQty>0`, value ÷ qty per item):

| Item | Qty | JIVO's own rate | Value |
|---|---:|---:|---:|
| RM0000003 Mustard Loose | 62,524.28 | 136.09 | ₹85,08,929 |
| RM0000001 Loose Refined Olive | 27,595.02 | 150.73 | ₹41,59,397 |
| RM0000002 Canola Cold Press | 15,265.16 | 133.29 | ₹20,34,693 |
| RM0000009 Refined Sunflower | 8,064.91 | 135.51 | ₹10,92,876 |
| RM0000006 Desi Ghee | 2,255.00 | 450.12 | ₹10,15,021 |
| RM0000025 Soyabean Refined | 6,418.55 | 136.49 | ₹8,76,068 |
| RM0000011 Groundnut | 3,741.00 | 147.26 | ₹5,50,900 |
| RM0000007 Rice Bran | 2,549.00 | 132.53 | ₹3,37,819 |
| 7 others | 3,376.00 | — | ₹5,01,293 |
| **Total** | **131,788.92** | | **₹1,90,76,996** |

**= 97.3% of the 23-July variance.** The variance and the un-costed oil are the same thing.

**7 — Accounts already knows the fix.** `OJDT` TransIds 208012, 208441, 211421, 211423, memo **"Variance A/c Reconsiled"** (posted 19-May → 02-Jun-2026), moved ₹97,70,628 from `5100003` to `5100013 COST OF GOODS SOLD`. Separately, `OINM TransType 162` (inventory revaluation) rows at BH-GR in April (₹1,37,171) and May (₹5,29,469) put cost onto earlier zero-cost recoveries — after which 13,063 units were issued out to production. **That is the correct treatment, applied at small scale, not applied in July.**

---

## What is bankable, and what is not

| Component | ₹ | Bankable? |
|---|---:|---|
| July P&L variance charge | 2,04,36,523 | **No** — period misallocation, no counterparty, no cash. Reversing it lowers a later month's cost by the same amount. |
| Recovered oil at JIVO's own cost | 1,90,76,996 | **Yes, conditionally** — real, physical, currently invisible at ₹0 |
| Less 25% quality / re-processing reserve (ex-market returns, `ExpDate` NULL, batch traceability destroyed) | (47,69,249) | |
| **Bankable** | **1,43,07,747** | one-time purchase avoidance |

Consuming the recovered oil displaces an equal value of fresh oil purchases — JIVO buys far more than 1.32 lakh litres a year, so it will be absorbed. If that avoided purchase permanently reduces the cash-credit drawdown, the carry saving is **₹10,44,466/yr at 7.3%**, or **₹11,80,389/yr at the audit's corrected 8.25%** (see [[finding-cc-interest-conversion-rate]]). Upside if QC clears everything: ₹1.91 Cr. Downside if the oil is rancid: ₹0 banked, and the ₹2.04 Cr charge is then correct — but JIVO still needs the QC result to know which world it is in, and it does not have one today.

---

## Action

**Owner: CFO (decision), with Plant/Production Head and Accounts (execution), IT/SAP partner (fix).**

1. **Before the July close — do not let ₹2.04 Cr fall into COGS by default.** QC-test the 14 recovered oil batches at BH-GR, then post an inventory revaluation (`TransType 162` — the same route Accounts already used in April and May) putting JIVO's own current cost on the fit-for-use quantity. This reverses up to ₹1.91 Cr of the charge and restores the same amount to inventory.
2. **Production Head:** publish a de-packing recovery norm — litres of oil expected back per 1,000 packs by SKU — and reconcile the 23-July batch against it. Any genuine shortfall is the real yield loss; on this evidence it is close to nil, since packaging recovery alone was booked at full BOM quantity.
3. **Purchase Head:** net 1.32 lakh litres off the next oil indent. It is already paid for.
4. **IT / SAP partner — three configuration fixes:** (a) disassembly orders must assign a component cost to recovered items instead of receiving them at zero; (b) block batch creation where `ExpDate` is null on an FSSAI-regulated item; (c) enforce a batch-number mask — `45456456465` and `334` are not batch numbers, and after this exercise 1.32 lakh litres of oil have no usable traceability.
5. **Accounts:** recognise production/disassembly variance **monthly**, and stop clearing it with free-text "Variance A/c Reconsiled" journals — the reclassification hides a recurring ₹2.9 Cr-a-year item (FY26-27 to date: Apr ₹57.84 L + May ₹26.41 L + Jun ₹3.31 L + Jul ₹204.37 L = **₹2,91,92,368 in four months**).
6. **CFO:** ask why ₹2.09 Cr of finished goods was sitting in a returns warehouse waiting four months to be de-packed. That is the upstream cost.

---

## Overlaps — read before adding anything up

- **[[finding-oil-returns-escalation]]** — same population of goods (customer returns), but that finding banked **₹0**, so there is **no rupee double count**. It does need one correction: it concluded returned goods "go back into stock and get sold to someone else, so the real cost is margin plus a return truck". For at least ₹2.09 Cr of them that is not what happened — they were de-packed and the oil went to zero value. The returns problem is more expensive than that note allowed, and the extra cost surfaces here.
- **[[finding-off-spec-olive-oil]]** — different item (`RM0000052`, warehouse BH-OT) and banked **₹0**, so **no overlap in rupees**. Same theme in mirror image: that one is phantom oil *over*-valued at ₹279.66/L; this one is real oil *under*-valued at ₹0. Useful cross-check — that note's prime-grade benchmark of ₹146.57/L sits right next to my ₹150.73/L for RM0000001.
- **[[finding-cc-interest-conversion-rate]]** — supplies the multiplier; its ₹2.34 Cr finance cost must not be added to this.
- No overlap with [[finding-no-invoice-vendors]], [[finding-blessing-advertising-overdue]], [[finding-trade-spend-as-credit-notes]], [[finding-advances-vs-open-bills]] or [[finding-hs-filling-advance]].

**Do not add the ₹2.04 Cr P&L figure to the audit total.** The only bankable number in this note is **₹1,43,07,747**.
