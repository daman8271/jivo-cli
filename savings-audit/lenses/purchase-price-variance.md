---
title: Purchase Price Variance — same item, different prices
created: 2026-07-28
lens: purchase-price-variance
tags: [savings-audit, procurement, ppv, sap]
---

# Purchase Price Variance (PPV)

Part of [[SAVINGS-MOC]]

**Question:** where is JIVO buying the *same item code* at *different prices* — and how much of that spread is negotiable rather than market movement?

**Window:** last 12 months, `DocDate >= '2025-07-28'` → 2026-07-25 (last data).
**Source:** live SAP HANA, `OPCH`/`PCH1` (A-P invoices + lines), `PDN1` (GRPO), `POR1` (PO), `OIPF` (landed cost), `OCRD`.
**Companies:** `JIVO_OIL_HANADB` · `JIVO_MART_HANADB` · `JIVO_BEVERAGES_HANADB`.

## Spend base (context)

| Company | A-P invoices | Net purchases (excl GST) |
|---|---:|---:|
| Oil | 7,652 | **₹396.42 Cr** |
| Mart | 3,167 | ₹190.64 Cr |
| Beverages | 1,550 | ₹11.58 Cr |

Oil net *sales* over the same window = ₹460.08 Cr, so purchases are ~86% of revenue. **Every 1% off the buy price = ~₹4 Cr of pure margin.** This is the single highest-leverage lens in the audit.

## Method and its guardrails

Naive "min vs max price per item" is garbage here — this is edible oil, prices move weekly. The metric used throughout is:

> **Gap vs best vendor** = for each `ItemCode` × `unitMsr` × **calendar month** with ≥2 vendors, compute each vendor's volume-weighted average price (VWAP), then sum `Qty × (vendor VWAP − cheapest vendor VWAP that month)`.

Comparing **inside a single month** removes almost all market movement. Exclusions applied (each one killed a false positive):

- `ItemCode LIKE 'CG%'` / `'CF%'` — these are **expense/capex catch-all buckets** ("REFRESHMENT", "REPAIR AND MAINTENANCE", "INSTALLATION PARTS"), where wildly different things are booked as "1 PCS". Observed spreads of **7,635,810%**. Not price variance; heterogeneous descriptions under one code.
- Intercompany vendors (`CardName LIKE 'JIVO%'`) — branch transfers, zero- or transfer-priced.
- Non-INR lines — FX movement is not a negotiation gap.
- Vendor premiums >60% — data errors, handled separately under [[finding-line-total-corruption]].

---

## H1 — Same item, same month, different vendors (the core test)

```sql
WITH V AS (
 SELECT L."ItemCode" IC, L."unitMsr" UOM, TO_VARCHAR(H."DocDate",'YYYY-MM') YM, H."CardCode" CC,
        SUM(L."Quantity") Q, SUM(L."LineTotal") LT, SUM(L."LineTotal")/SUM(L."Quantity") VWAP
 FROM JIVO_OIL_HANADB.PCH1 L JOIN JIVO_OIL_HANADB.OPCH H ON H."DocEntry"=L."DocEntry"
 WHERE H."CANCELED"='N' AND H."DocDate">='2025-07-28' AND L."ItemCode" IS NOT NULL
   AND L."Quantity">0 AND L."LineTotal">0 AND L."Currency"='INR'
   AND L."ItemCode" NOT LIKE 'CG%' AND L."ItemCode" NOT LIKE 'CF%'
   AND H."CardCode" NOT IN (SELECT "CardCode" FROM JIVO_OIL_HANADB.OCRD WHERE "CardName" LIKE 'JIVO%')
 GROUP BY L."ItemCode", L."unitMsr", TO_VARCHAR(H."DocDate",'YYYY-MM'), H."CardCode"
), M AS (SELECT IC,UOM,YM,MIN(VWAP) BEST,COUNT(*) NV FROM V GROUP BY IC,UOM,YM)
SELECT ... SUM(V.Q*(V.VWAP-M.BEST)) GAP_VS_BEST
FROM V JOIN M ON V.IC=M.IC AND V.UOM=M.UOM AND V.YM=M.YM
WHERE M.NV>=2 AND (V.VWAP-M.BEST) < 0.60*M.BEST
GROUP BY category
```

**Group roll-up:**

| Company | Category | Items | Contestable spend | Gap vs best vendor | Gap % |
|---|---|---:|---:|---:|---:|
| Oil | Raw oil (RM) | 7 | ₹156.33 Cr | **₹3.24 Cr** | 2.07% |
| Oil | Packaging (PM) | 45 | ₹11.06 Cr | **₹29.26 L** | 2.65% |
| Oil | Finished/semi | 1 | ₹70.28 L | ₹0.85 L | 1.20% |
| Beverages | Packaging | 6 | ₹1.39 Cr | ₹1.96 L | 1.41% |
| Mart | Packaging | 3 | ₹3.17 L | ₹0.22 L | 7.01% |
| Beverages/Oil | Other | 2 | ₹2.48 L | ₹0.16 L | — |
| **Total** | | | **₹169.1 Cr** | **₹3.56 Cr** | **2.11%** |

**Verdict: CONFIRMED. ₹3.56 Cr of same-month price gap over 12 months.** That is the theoretical maximum (100% of volume to the cheapest vendor every month). See capture discussion below.

Mart's finished-goods purchases correctly drop out — Mart buys almost all FG from group companies at transfer price.

### Top items by gap

| Item | Description | Multi-vendor months | Contestable spend | Gap | Gap % |
|---|---|---:|---:|---:|---:|
| RM0000001 | LOOSE REFINED OLIVE OIL | 6 | ₹39.87 Cr | **₹1.36 Cr** | 3.41% |
| RM0000025 | SOYABEAN REFINED LOOSE OIL | 11 | ₹73.04 Cr | **₹93.81 L** | 1.28% |
| RM0000003 | MUSTARD OIL KACHI GHANI | 6 | ₹34.68 Cr | **₹86.53 L** | 2.49% |
| FG0000030 | MUSTARD KACHI GHANI 1L 20PCS | 6 | ₹2.70 Cr | ₹29.26 L | 10.85% |
| PM0000053 | HDPE BOTTLE 5 LTR | 13 | ₹3.25 Cr | ₹21.87 L | 6.72% |
| FG0000136 | SANO MUSTARD OIL 1L 20PCS | 4 | ₹1.65 Cr | ₹11.90 L | 7.19% |
| PM0000121 | PET BOTTLE 1 LTR 52 GMS POMACE | 10 | ₹1.50 Cr | ₹3.26 L | 2.16% |
| PM0000852 | PREFORM 49.5 GMS 36 MM | 4 | ₹1.05 Cr | ₹2.68 L | 2.55% |

---

## H2 — [[finding-mustard-oil-vendor-gap]] (highest-confidence commodity gap)

`RM0000003` MUSTARD OIL KACHI GHANI, ₹48.23 Cr / 3,221 MT bought last 12m.

| Month | Vendor | Qty MT | ₹/MT | Spend |
|---|---|---:|---:|---:|
| 2026-04 | AWL AGRI BUSINESS | 78.72 | **1,38,105** | ₹1.09 Cr |
| 2026-04 | VAISHNODEVI REFOILS & SOLVEX | 39.45 | 1,41,105 | ₹55.7 L |
| 2026-04 | VAISHNODEVI AGRO RESOURCES | 40.42 | 1,45,911 | ₹59.0 L |
| 2026-05 | AWL AGRI BUSINESS | 194.02 | **1,40,070** | ₹2.72 Cr |
| 2026-05 | VAISHNODEVI AGRO RESOURCES | 368.64 | 1,45,552 | ₹5.37 Cr |
| 2026-05 | M/S ARORA AGRI BUSINESS | 116.49 | 1,47,867 | ₹1.72 Cr |
| **2026-06** | **AWL AGRI BUSINESS** | 230.56 | **1,45,569** | ₹3.36 Cr |
| **2026-06** | **VAISHNODEVI AGRO RESOURCES** | **276.57** | **1,58,466** | **₹4.38 Cr** |
| 2026-07 | AWL AGRI BUSINESS | 311.28 | **1,49,164** | ₹4.64 Cr |
| 2026-07 | VAISHNODEVI AGRO RESOURCES | 80.05 | 1,55,360 | ₹1.24 Cr |

**June 2026 alone:** Vaishnodevi Agro charged **₹12,897/MT (8.9%) more** than AWL in the same month for 276.57 MT →
`276.57 × 12,897 = ` **₹35.67 lakh of excess in one month.**

12-month gap for this item: **₹86.53 lakh**.

**Verdict: CONFIRMED, high confidence.** Both are large established refiners supplying the identical item code. Caveat: Kachi Ghani mustard oil quality (FFA, pungency, AGMARK grade) does vary, and delivery terms (ex-mill vs delivered) may differ — but not by 8.9% consistently across five months.

---

## H3 — [[finding-olive-oil-vendor-gap]] (largest ₹, medium confidence)

`RM0000001` LOOSE REFINED OLIVE OIL, ₹49.90 Cr / 1,868 MT.

| Month | Vendor | Qty MT | ₹/MT |
|---|---|---:|---:|
| 2025-09 | MAHA MAYA FOOD PRODUCTS | 124.77 | **2,37,406** |
| 2025-09 | CONCEPT COLOUR | 42.52 | 2,50,352 |
| 2025-09 | VEE KAY ENTERPRISES | 42.00 | 2,68,765 (+13.2%) |
| 2025-12 | VEE KAY ENTERPRISES | 202.05 | **2,58,417** |
| 2025-12 | NURTURING FOODS LLP | 124.72 | 2,63,120 |
| 2025-12 | INDRANI FOODS | 42.11 | 2,87,222 (+11.1%) |
| 2026-01 | MAHA MAYA FOOD PRODUCTS | 41.43 | **2,50,784** |
| 2026-01 | VEE KAY ENTERPRISES | 83.03 | 2,65,908 |
| 2026-01 | NURTURING FOODS LLP | 208.97 | 2,81,067 (+12.1%) |
| 2026-02 | VEE KAY ENTERPRISES | 84.02 | **2,81,066** |
| 2026-02 | NURTURING FOODS LLP | 41.22 | 3,20,931 (+14.2%) |

12-month gap: **₹1.36 Cr** — the largest single-item gap in the group.

**Verdict: CONFIRMED as a spread, MEDIUM confidence as a saving.** Olive oil grade variation (refined vs pomace vs blend ratios, origin, acidity) is genuinely wide and is *not* distinguished by the item code. Some of this spread is real quality difference. Recommend a spec/COA audit before treating the whole gap as negotiable.

---

## H4 — [[finding-soyabean-oil-vendor-gap]] (most fungible commodity)

`RM0000025` SOYABEAN REFINED LOOSE OIL, ₹81.91 Cr / 6,171 MT, **9 vendors**.

| Month | Cheapest | Dearest | Spread |
|---|---|---|---:|
| 2025-10 | VAISHNODEVI AGRO 1,22,418 | HINDUSTAN AGRO 1,28,805 | 5.2% |
| 2025-11 | DIL EXIM 1,21,925 | BD EDIBLE OILS 1,23,397 | 1.2% |
| 2026-01 | DIL EXIM 1,24,435 | VEE KAY TRADERS 1,34,995 | **8.5%** |
| 2026-03 | DIL EXIM 1,30,316 | AWL AGRI 1,40,366 | **7.7%** |
| 2026-06 | DIL EXIM 1,46,795 | ARORA AGRI 1,52,822 | 4.1% |
| 2026-07 | DIL EXIM 1,42,047 | AWL AGRI 1,47,856 | 4.1% |

12-month gap: **₹93.81 lakh** on ₹73.04 Cr of contestable spend.

**Verdict: CONFIRMED, high confidence.** Refined soyabean oil is the most fungible product JIVO buys, with a published market reference (NCDEX/SEA). DIL EXIM is consistently the cheapest and consistently under-allocated. Nine vendors on one commodity is fragmentation, not competition.

---

## H5 — Vendor attribution: who carries the premium?

Since 2025-09, top six raw-oil + packaging items, per vendor:

| Vendor | Item | Qty | Spend | Avg premium vs cheapest | Gap ₹ |
|---|---|---:|---:|---:|---:|
| NURTURING FOODS LLP | Olive RM0000001 | 457.6 MT | ₹12.86 Cr | **7.06%** | **₹86.05 L** |
| VAISHNODEVI AGRO RESOURCES | Mustard RM0000003 | 848.7 MT | ₹12.71 Cr | 4.51% | **₹63.99 L** |
| AWL AGRI BUSINESS | Soya RM0000025 | 701.7 MT | ₹10.40 Cr | 4.00% | ₹40.33 L |
| VEE KAY ENTERPRISES | Olive RM0000001 | 494.9 MT | ₹13.39 Cr | 4.37% | ₹32.01 L |
| M/S ARORA AGRI BUSINESS | Soya RM0000025 | 393.0 MT | ₹5.92 Cr | 3.66% | ₹21.58 L |
| RAJ TECHNOPACK PVT LTD | HDPE bottle PM0000053 | 520,890 pcs | ₹2.10 Cr | **10.20%** | ₹15.94 L |
| INDRANI FOODS | Olive RM0000001 | 42.1 MT | ₹1.21 Cr | **11.14%** | ₹12.13 L |
| BD EDIBLE OILS | Soya RM0000025 | 870.8 MT | ₹11.20 Cr | 1.16% | ₹10.73 L |
| M/S ARORA AGRI BUSINESS | Mustard RM0000003 | 185.2 MT | ₹2.74 Cr | 3.57% | ₹10.67 L |
| VEE KAY TRADERS | Soya RM0000025 | 64.3 MT | ₹86.8 L | **8.48%** | ₹6.79 L |
| ECHO PLAST INDIA | HDPE bottle PM0000053 | 201,576 pcs | ₹84.7 L | **10.71%** | ₹5.71 L |

**Verdict: CONFIRMED.** This is the negotiation call-list, ranked. Seven vendor-item pairs account for ~₹2.8 Cr of the ₹3.56 Cr gap.

---

## H6 — [[finding-hdpe-bottle-price-spread]] — packaging has no commodity excuse

`PM0000053` HDPE BOTTLE 5 LTR — ₹3.25 Cr/yr, 809,235 bottles, **7 vendors**, 286 invoice lines.

| Month | A A ENTERPRISES | ECHO PLAST | RAJ TECHNOPACK | Spread |
|---|---:|---:|---:|---:|
| 2025-07 | — | 32.60 | 33.68 | 3.3% |
| 2025-09 | — | 32.60 | 32.81 | 0.6% |
| 2026-01 | **32.50** | — | 33.37 | 2.7% |
| 2026-02 | **32.50** | 34.11 | 34.52 | 6.2% |
| **2026-04** | **32.50** | 50.43 | 51.13 | **57.3%** |
| 2026-05 | 48.00 | 48.45 | 48.69 | 1.4% |
| 2026-06 | 48.00 | 47.99 | 49.15 | 2.4% |

Third-party gap: **₹16.89 lakh/yr** (₹21.87 L including intercompany lines).

Full packaging list (Oil, third-party only, gap > ₹20k):

| Item | Description | Spend | Gap | Gap % | Price range |
|---|---|---:|---:|---:|---|
| PM0000053 | HDPE BOTTLE 5 LTR | ₹3.25 Cr | ₹16.89 L | 5.19% | 32.50 – 51.13 |
| PM0000121 | PET BOTTLE 1L 52 GMS POMACE | ₹1.50 Cr | ₹3.26 L | 2.16% | 8.06 – 10.90 |
| PM0000852 | PREFORM 49.5 GMS 36 MM | ₹1.05 Cr | ₹2.68 L | 2.55% | 6.57 – 7.89 |
| PM0000824 | LABEL 1 LTR KACHI GHANI FULL | ₹1.87 L | ₹1.03 L | **54.8%** | 0.34 – 0.85 |
| PM0000194 | PET BOTTLE 1 LTR 40 GMS | ₹87.3 L | ₹0.94 L | 1.07% | 6.51 – 6.85 |
| PM0000079 | CAPS 1 & 2 LTR GREEN W/ LOGO | ₹14.7 L | ₹0.86 L | 5.84% | 1.00 – 1.30 |
| PM0000594 | PREFORM 40 GMS 36 MM | ₹55.2 L | ₹0.84 L | 1.52% | 5.36 – 6.31 |
| PM0000076 | TIN 15 LTR | ₹1.05 Cr | ₹0.78 L | 0.74% | 84.50 – 96.00 |
| PM0000891 | POUCH SOYABEAN MULTI KGS | ₹16.5 L | ₹0.60 L | 3.66% | 290 – 304 |
| PM0000013 | CARTON 5 LTR 4 PCS | ₹45.5 L | ₹0.30 L | 0.65% | 29.50 – 32.10 |

**Verdict: CONFIRMED, highest confidence of any finding.** Packaging is made to JIVO's own drawing/spec — there is no market-grade defence for a 5–10% same-month spread, let alone the 57% April gap or the 2.5× label price. Caveat: bottle grammage and resin type can vary under one item code; confirm spec before pushing the April number.

**Supporting observation:** 286 separate invoice lines for one bottle SKU in 12 months (≈5.5/week), every single line under 5,000 pcs. Order fragmentation of this degree normally costs 2–4% on unit price.

---

## H7 — Same vendor, same item, same month, different price

| Item | Description | Spend | Self-gap | Max intra-month spread |
|---|---|---:|---:|---:|
| RM0000001 | LOOSE REFINED OLIVE OIL | ₹28.21 Cr | ₹1.75 Cr | 19.9% |
| RM0000003 | MUSTARD OIL KACHI GHANI | ₹29.21 Cr | ₹94.42 L | 8.6% |
| RM0000025 | SOYABEAN REFINED LOOSE OIL | ₹28.06 Cr | ₹41.15 L | 7.4% |
| RM0000011 | GROUNDNUT LOOSE OIL | ₹5.65 Cr | ₹18.07 L | 8.7% |
| **PM0000852** | **PREFORM 49.5 GMS 36 MM** | ₹47.3 L | **₹3.07 L** | **20.0%** |
| **PM0000817** | **PREFORM 23.8 GMS 29 MM** | ₹22.8 L | **₹2.60 L** | **25.0%** |
| **PM0000594** | **PREFORM 40 GMS 36 MM** | ₹26.1 L | **₹1.79 L** | **20.0%** |

**Verdict: SPLIT.** For raw oils this is mostly legitimate intra-month market movement (mustard moved ₹1.35–1.58 lakh/MT over the year) — **do not bank it**. For **preforms it is not defensible**: preform prices are contracted per-kg-of-resin and should not swing 20–25% from the same vendor inside one month. `PM0000852` + `PM0000817` + `PM0000594` = **₹7.46 lakh/yr** worth auditing.

Cross-check that preform pricing is otherwise sane: 49.5 g preform ₹6.57–7.89 = ₹0.133–0.159/g; 40 g preform ₹5.36–6.31 = ₹0.134–0.158/g. Consistent → resin-linked pricing is broadly correct, so the 20% swings are individual billing anomalies, not a pricing model.

---

## H8 — [[finding-line-total-corruption]] — purchase lines that don't tie to the invoice

```sql
WITH D AS (
 SELECT H."DocNum" DN, H."CardName" CN, H."DocTotal"-IFNULL(H."VatSum",0) NETHDR,
        (SELECT SUM(L."LineTotal") FROM <SCHEMA>.PCH1 L WHERE L."DocEntry"=H."DocEntry") LSUM
 FROM <SCHEMA>.OPCH H WHERE H."CANCELED"='N' AND H."DocDate">='2025-07-28'
)
SELECT COUNT(*) DOCS, SUM(LSUM-NETHDR) OVERSTATE
FROM D WHERE NETHDR > 1000 AND LSUM > NETHDR*1.10 AND LSUM-NETHDR > 50000
```

| Company | Docs | Line value overstated vs invoice |
|---|---:|---:|
| Mart | 6 | **₹7.76 Cr** |
| Oil | 4 | ₹12.34 L |
| Beverages | 0 | — |

Worst offenders (all `JIVO MART PVT LTD - DL`, Aug 2025):

| DocNum | Date | Header net | Sum of lines | Overstated |
|---|---|---:|---:|---:|
| 608254149 | 2025-08-19 | ₹2.64 L | ₹3.03 Cr | ₹3.00 Cr |
| 608254146 | 2025-08-19 | ₹1.19 L | ₹2.00 Cr | ₹1.99 Cr |
| 608254191 | 2025-08-29 | ₹1.24 L | ₹1.79 Cr | ₹1.77 Cr |
| 608254176 | 2025-08-27 | ₹1.51 L | ₹96.5 L | ₹95.0 L |

Example line (608254149): `FG0000311 POMACE OLIVE OIL 1+1+1 LTR`, **200 LTR @ ₹1,51,428/unit = ₹3.03 Cr** — while the same item is booked at ₹795/unit elsewhere and the document header totals ₹2.77 lakh. A ~190× unit-price error.

**Verdict: CONFIRMED — but NON-CASH.** The invoice headers, vendor balances and GST are correct; only the *line* price/quantity is corrupt. Impact is on **item costing, moving-average cost, inventory valuation and every per-SKU margin report**, not on money paid. It also silently poisons any PPV analysis — this is why the >60% outlier filter exists above.

Note: ~160 further "overstated" docs were **correctly excluded** — they are zero-value branch stock transfers (`JIVO WELLNESS PVT LTD - HR/DL/PB`) where `DocTotal = 0` by design.

---

## H9 — Invoice price vs goods-receipt price (three-way match)

`PCH1."BaseType"` is **20 (GRPO)**, not 22 (PO) — 11,545 lines / ₹354.6 Cr flow through goods receipts, 8,608 lines / ₹45.2 Cr are direct.

| Company | Lines invoiced above GRPO price | Variance |
|---|---:|---:|
| Oil | 1 | ₹61.65 L |
| Mart | 4 | ₹3,476 |
| Beverages | 0 | — |

The single Oil case — DocNum 625083105, 2025-08-08, VAISHNODEVI OIL SEEDS, `RM0000003` 37.94 MT:

| | Price/MT | Line total |
|---|---:|---:|
| GRPO | ₹4,398.91 | ₹1,66,894 |
| Invoice | ₹1,66,894.96 | ₹63,31,995 |

The GRPO **total** was keyed into the invoice's **price** field. The invoice is the correct one (₹1.67 lakh/MT matches the market); the **goods receipt understated inventory by ₹61.65 lakh** for that consignment.

**Verdict: CONFIRMED as a control failure, not an overpayment.** Three-way-match discipline is otherwise excellent — 5 exceptions in 20,153 lines is genuinely good.

---

## H10 — Freight / landed-cost rate consistency

Freight is booked as **description-only lines with no ItemCode** — the rate is embedded in free text ("@4000", "@3500"). 11,504 such lines, ₹39.77 Cr.

| Lane | Trips | Spend | Avg/trip | Min | Max | Stated rate |
|---|---:|---:|---:|---:|---:|---:|
| RADHANPUR → SONIPAT | 208 | **₹2.92 Cr** | ₹1,40,429 | ₹75,000 | ₹1,52,218 | ₹3,500/MT |
| MUNDRA → SONIPAT | 77 | ₹1.24 Cr | ₹1,60,947 | ₹1,03,600 | ₹1,80,000 | ₹4,000/MT |
| KANDLA → SONIPAT | 26 | ₹38.6 L | ₹1,48,470 | ₹1,23,506 | ₹1,71,080 | ₹3,700/MT |
| PALANPUR → SONIPAT | 24 | ₹30.8 L | ₹1,28,430 | ₹1,21,211 | ₹1,32,742 | ₹3,100/MT |
| Other freight | 218 | ₹1.38 Cr | ₹63,461 | ₹1 | ₹1,66,280 | mixed |
| **Total identified** | **553** | **₹6.24 Cr** | | | | |

Radhanpur and Palanpur are both north-Gujarat origins ~1,000–1,100 km from Sonipat, yet Radhanpur is billed at **₹3,500/MT vs Palanpur ₹3,100/MT — a 12.9% gap**. Per-MT-per-km: Radhanpur ₹3.18, Mundra ₹3.33, Kandla ₹3.22, Palanpur ₹3.26 — broadly consistent, so the gap is mostly distance, not overcharging.

**Verdict: WEAK-CONFIRMED, low confidence.** No proven overcharge, but ₹6.24 Cr of freight is being bought on standing per-MT rates embedded in free text, with no item master and therefore no systematic rate control. A formal lane tender at 3% = ~₹18.7 lakh/yr. Also a **data hygiene finding**: freight should be an item/expense code, not a description.

---

## Hypotheses tested and KILLED (recorded so they aren't re-run)

| # | Hypothesis | Result |
|---|---|---|
| K1 | Invoiced above **PO** price | **Killed** — 0 lines. `BaseType` is GRPO(20), not PO(22); test re-run correctly as H9. |
| K2 | **Mart pays more than Oil** for the same item-month (₹94.7 L apparent excess across 13 FG items) | **Killed** — Oil "buys" these as branch transfers at cost; Mart buys from Oil at transfer price with margin. Normal intercompany transfer pricing, not a leak. |
| K3 | **Domestic CDRO 25.8% dearer than imported** — Oct 2025: imported `RM0000016` ₹1,09,618/MT (ALBA, 305 MT) vs domestic `RM0000062` ₹1,37,896/MT (PARAS AGRI, 457 MT) = apparent ₹1.29 Cr excess | **Killed** — import invoices carry `TotalExpns = 0` and `VatSum = 0`; customs duty is booked in **separate landed-cost documents (`OIPF`: 280 docs, ₹218.11 Cr since 2025-07-28)**. At ~20% effective duty the imported landed cost is ~₹1.31 lakh/MT, near-identical to domestic. **Do not report this as a saving.** |
| K4 | Duplicate item codes hiding price arbitrage | **Killed** — only 4 name collisions across all RM/PM codes (`PM0000881/2/3`, `PM0000869/70`, `PM0000871/2`, `RM0000063`+`PM0000833` both "DEMO"). Immaterial. |
| K5 | Purchase **discount capture** inconsistent | **Killed** — `DiscPrcnt > 0` on **2 lines out of 8,236** (₹24.3 L). Discounts are negotiated into the unit price, not shown separately. No visible leak (off-invoice rebates would not appear in SAP). |
| K6 | **Import FX / landed-cost variance** across suppliers | **Killed** — one supplier per month, no same-month spread. CDRO CIF rose smoothly $1,088 → $1,250/MT over 12 months (EDIBLE OIL CO D → AL GHURAIR → ALBA → GRAINCORP). Market, not leakage. |
| K7 | **Packaging price creep** beyond resin cost | **Killed** — preform ₹/gram is consistent across sizes (₹0.133–0.159/g for both 40 g and 49.5 g). Pricing model is sound. |
| K8 | **Small-lot premium** on packaging | **Not provable from data** — all 286 HDPE-bottle lines are <5,000 pcs, so there is no large-lot comparison group. Recorded as a supporting observation under H6. |
| K9 | Capex/expense buckets showing huge PPV (`CG*`, `CF*`: REFRESHMENT, REPAIR & MAINTENANCE, HOUSEKEEPING, INSTALLATION PARTS — spreads to 7,635,810%) | **Killed as PPV** — heterogeneous items booked as "1 PCS" under a shared code. Real finding is **coding discipline**, belongs to [[expense-outliers]]. |

---

## What is actually capturable

The ₹3.56 Cr gap is the theoretical ceiling. Honest haircuts:

- The cheapest vendor in a month often **cannot supply the full volume** (DIL EXIM, A A ENTERPRISES both appear at low volumes).
- **Credit terms differ** — a vendor giving 60-day credit legitimately prices higher; that premium is a financing cost, not waste. (Cross-check against [[vendor-money-stuck]].)
- **Grade/spec variation** is real for olive oil and possible for HDPE grammage.
- Delivery terms (ex-mill vs delivered) are not distinguished in the item code.

| Finding | Gap identified | Capture assumed | Annual saving |
|---|---:|---:|---:|
| Soyabean oil RM0000025 | ₹93.81 L | 30% | **₹28.0 L** |
| Mustard oil RM0000003 | ₹86.53 L | 30% | **₹26.0 L** |
| Olive oil RM0000001 | ₹1.36 Cr | 25% | **₹34.0 L** |
| HDPE bottle PM0000053 | ₹16.89 L | 50% | **₹8.5 L** |
| Other packaging (Oil + Bev) | ₹14.33 L | 35% | **₹5.0 L** |
| **Recurring subtotal** | **₹3.48 Cr** | **~29%** | **₹1.02 Cr/yr** |
| Freight lane re-tender (3% of ₹6.24 Cr) | — | — | ₹18.7 L |
| **Total annual recurring** | | | **~₹1.20 Cr/yr** |

Plus non-cash corrections: **₹7.76 Cr** of Mart line-value corruption and **₹61.65 L** of GRPO mis-costing to be repaired in the books.

## Actions

1. **Call list, in order:** NURTURING FOODS (olive, 7.06% premium, ₹86 L), VAISHNODEVI AGRO (mustard, 4.51%, ₹64 L), AWL AGRI (soya, 4.00%, ₹40 L), RAJ TECHNOPACK (HDPE bottle, 10.20%, ₹16 L), INDRANI FOODS (olive, 11.14%).
2. **Shift allocation, don't just haggle** — DIL EXIM is cheapest on soya in 6 of 11 months but under-allocated; AWL is cheapest on mustard in 5 of 6 months. Move volume before renegotiating.
3. **Monthly PPV report** — publish the H1 query as a standing month-end control: item × month × vendor VWAP vs best. This finds the next ₹3 Cr automatically.
4. **Fix the four Mart Aug-2025 documents** (608254149/146/191/176) and GRPO on DocNum 625083105 — item costing is wrong until they are.
5. **Give freight an item code.** ₹6.24 Cr bought on free-text rates cannot be controlled.
6. **Tighten `CG*`/`CF*` coding** — capex/expense catch-alls make item-level analysis impossible.
7. **Consolidate HDPE bottle ordering** — 286 lines/yr, all <5,000 pcs, is fragmentation.

Back-links: [[SAVINGS-MOC]] · [[vendor-money-stuck]] · [[dead-slow-stock]] · [[expense-outliers]]
