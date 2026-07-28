---
title: "HS Filling advance — ₹2.40 Cr is a bottling-plant capex advance, not recoverable working capital"
created: 2026-07-28
verdict: REVISED
amount_verified_inr: 0
kind: control-observation
tags: [savings-audit, finding]
---

# HS Filling ₹2.40 Cr — REVISED: real balance, wrong class, ₹0 bankable

Part of [[SAVINGS-MOC]] · Evidence: [[vendor-money-stuck]]

## What a CFO needs to know

JIVO Beverages has ₹2.40 Cr sitting as a debit balance with **HS FILLING AND PACKAGING (Sonipat)**, and the
original finding is right that not one purchase invoice has ever been raised against it. But it is **not a
co-packing advance and it is not money we can get back or release.** The two open purchase orders behind it
are for **capital plant** — a 240 BPM fully-automatic water plant (₹48.00 L), a fully-automatic CSD plant
(₹52.00 L) and a 300 BPM fully-automatic water plant (₹1.85 Cr) — booked as fixed-asset items against GL
**1204003 PLANT & MACHINERY-WATER**. This is the machinery for the Beverages bottling line, one of a dozen
plant POs raised between April and July 2026 (SIDEL moulds, PYRUM conveyors and installation, Clearpack,
Hilden, an OCEMS stack analyser). The ₹2.40 Cr is capex in transit; on delivery it becomes a fixed asset, not
cash. **Bankable saving: ₹0.** This is the same shape as the Bakharpur land advances — a deliberate asset
purchase that reads like stuck money.

What *is* worth the CFO's attention is how it was paid. **₹2.90 Cr went out — 86% of the ₹3.36 Cr order value —
before a single machine arrived**, against POs whose delivery date was **2026-04-30, now 89 days overdue**.
There is no goods receipt, no inventory movement and no invoice anywhere in SAP. ₹1.00 Cr of that money was
paid on 16 and 20 July 2026, roughly two and a half months *after* the supplier had already missed the
delivery date. The vendor master carries **no GSTIN in any of the three companies**, and ₹51.30 L of GST is
built into the POs that cannot be claimed as input credit until a tax invoice exists. For scale: ₹2.90 Cr is
63% of everything JIVO Beverages sold in the same four months (₹4.60 Cr net, Apr–Jul 2026).

## Verdict and re-derived number

| | |
|---|---|
| Claimed | ₹2,40,00,000 — "working-capital release", co-packer advance |
| **Re-derived balance** | **₹2,40,00,000 — exact, confirmed three independent ways** |
| **Bankable / releasable** | **₹0** |
| Reclassified as | committed fixed-asset (capex) advance + control observation |
| Carrying cost while undelivered | ₹17.52 L/yr (₹2.40 Cr × 7.3%) = ₹1.46 L/month; ~₹2.06 L already burned since the missed delivery date |

**Verdict: REVISED.** Every factual clause of the original finding is true — the balance, the zero invoices,
the 88% share of the Beverages vendor-debit pool. What fails is the *class*: it was filed as ₹2.40 Cr of
working capital to be released by "requiring invoices so the advance amortises". Invoices will come when the
plant is delivered and the money will convert into machinery, not into bank balance. Nothing here is
collectable while JIVO still wants the plant, so it must **not** be counted in the savings total.

## Key SQL evidence

Three independent derivations of the same ₹2,40,00,000:

```sql
-- (1) partner master
SELECT "CardCode","CardName","Balance","GroupCode","LicTradNum"
FROM JIVO_BEVERAGES_HANADB.OCRD WHERE "CardCode"='VENDA001347';
--> HS FILLING AND PACKAGING · Balance 24,000,000 · group 105 SERVICE · LicTradNum NULL (no GSTIN)

-- (2) journal movement and (3) open residual, same query
SELECT SUM(IFNULL("Debit",0)) - SUM(IFNULL("Credit",0))       AS NET_MOVEMENT,
       SUM(IFNULL("BalDueDeb",0)) - SUM(IFNULL("BalDueCred",0)) AS OPEN_RESIDUAL,
       COUNT(*) AS N_LINES
FROM JIVO_BEVERAGES_HANADB.JDT1 WHERE "ShortName"='VENDA001347';
--> NET_MOVEMENT 24,000,000 · OPEN_RESIDUAL 24,000,000 · 6 lines
```

The line that kills the "co-packing / working capital" reading — resolve the PO to its items and GL:

```sql
SELECT h."DocNum", h."DocDate", h."DocDueDate", h."DocStatus", h."DocTotal",
       l."ItemCode", l."Dscription", l."LineTotal", l."AcctCode", l."ItemType"
FROM JIVO_BEVERAGES_HANADB.POR1 l
JOIN JIVO_BEVERAGES_HANADB.OPOR h ON h."DocEntry"=l."DocEntry"
WHERE h."CardCode"='VENDA001347';
```

| PO | Date | Due | Status | Item | Description | ₹ net | GL |
|---|---|---|---|---|---|---:|---|
| 426228002 | 2026-04-04 | 2026-04-30 | **O** | FA0000424 | 240 BPM FULLY AUTOMATIC WATER PLANT | 48,00,000 | 1204003 |
| 426228002 | 2026-04-04 | 2026-04-30 | **O** | FA0000425 | FULLY AUTOMATIC CSD PLANT | 52,00,000 | 1204003 |
| 426228003 | 2026-04-07 | 2026-04-30 | **O** | FA0000426 | 300 BPM FULLY AUTOMATIC WATER PLANT | 1,85,00,000 | 1204003 |

`ItemType`=4 (fixed asset), item codes prefixed `FA`, GL `1204003 = PLANT & MACHINERY-WATER` (child of 1204000).
Gross PO ₹3,36,30,000 incl. ₹51,30,000 GST. Both POs still `DocStatus='O'`.

Nothing was ever received or billed:

```sql
SELECT (SELECT COUNT(*) FROM JIVO_BEVERAGES_HANADB.OPCH WHERE "CardCode"='VENDA001347') AS AP_INVOICES,
       (SELECT COUNT(*) FROM JIVO_BEVERAGES_HANADB.ORPC WHERE "CardCode"='VENDA001347') AS AP_CREDITS,
       (SELECT COUNT(*) FROM JIVO_BEVERAGES_HANADB.OPDN WHERE "CardCode"='VENDA001347') AS GOODS_RECEIPTS,
       (SELECT COUNT(*) FROM JIVO_BEVERAGES_HANADB.OINM
          WHERE "ItemCode" IN ('FA0000424','FA0000425','FA0000426'))                    AS STOCK_MOVES
FROM DUMMY;
--> 0 · 0 · 0 · 0
```

The five payments (all bank transfers from INDIAN BANK-7051847887, none cancelled, `DocType='S'` = on account,
**`TrsfrRef` NULL on all five — no UTR stored in SAP**):

| DocNum | Date | ₹ | Entered by | Created at |
|---|---|---:|---|---|
| 426468004 | 2026-04-07 | 70,00,000 | TARAN | 12:23 |
| 426468007 | 2026-04-07 | 70,00,000 | TARAN | 13:20 |
| 726468022 | 2026-07-16 | 50,00,000 | TARAN | 16:14 |
| 726468023 | 2026-07-16 | 50,00,000 | TARAN | 17:06 |
| 726468035 | 2026-07-20 | 50,00,000 | TARAN | 17:25 |
| | **Total out** | **2,90,00,000** | | |

Offset by one journal entry, ₹50,00,000 credit on 2026-05-14, memo "AMOUNT RECD IN BEV", contra
**GL 1110109 JIVO WELLNESS OIL INTERNAL**. The mirror exists in Oil — `JIVO_OIL_HANADB` vendor `VENDA001046`
(same name, same address "20 SPORTS GOODS COMPLEX, SONIPAT") shows incoming payments of ₹50,00,111 on
2026-05-13/14 and now nets to a trivial ₹25,331.87 credit. So that ₹50 L came back into the group and is
correctly out of the ₹2.40 Cr. **Intercompany trap checked and cleared** — no other HS Filling exposure
anywhere: Mart has no such partner, and the Beverages customer card `CUSTA001104 H.S. FILLING & PACKAGING`
carries a nil balance (one ₹1.18 L entry, settled January 2026).

Share of the pool, confirmed:

```sql
SELECT COUNT(*) AS N, SUM("Balance") AS DEBIT_TOTAL
FROM JIVO_BEVERAGES_HANADB.OCRD WHERE "CardType"='S' AND "Balance">0;
--> 33 vendors · ₹2,70,68,961.56 · HS Filling = 88.7%
```

## Action

**Owner: CFO** (with Purchase head executing) — this is a capex-governance item, not an Accounts recovery.

1. **Get delivery enforced or the advance secured.** The POs were due 2026-04-30 and are 89 days late with
   ₹2.90 Cr already paid. Demand a firm despatch date; if the contract has a liquidated-damages clause,
   invoice it (5% of ₹2.85 Cr ≈ ₹14.25 L — indicative only, the contract is not in SAP and must be read).
   Failing that, ask for a bank guarantee covering the advance. Every month of further delay costs
   **₹1.46 L** in interest at the 7.3% CC rate.
2. **Stop paying ahead of delivery on plant POs.** 86% of order value paid before receipt, ₹1.00 Cr of it
   after the delivery date had already been missed, is the actual control failure. Set a standing rule for
   capital equipment — e.g. 30% on order, 60% on despatch against documents, 10% on commissioning — and apply
   it to the rest of the Beverages plant build-out.
3. **Fix the vendor master (Accounts / IT).** No GSTIN on `VENDA001347` in any company, ₹51.30 L of GST riding
   on the POs, and no ITC claimable until a tax invoice arrives. Validate the GSTIN before the next payment
   and confirm the vendor is registered; also capture UTRs on payments — none of the five has a `TrsfrRef`.
4. **Reclassify.** The vendor sits in group 105 SERVICE while buying plant and machinery; move it to a
   FIXED ASSETS / PLANT & MACHINERY group so capex advances stop landing in the trade-vendor ageing.
5. **Bank-statement match the two twin pairs** (₹70 L ×2 on 2026-04-07, ₹50 L ×2 on 2026-07-16, identical
   narration, entered ~1 hour apart by the same user). SAP cannot resolve this — no UTRs are stored. Sequential
   doc numbers and an hour's gap point to deliberate tranches rather than a re-key, but ₹1.20 Cr should not
   rest on inference. This is the live question, and it belongs to [[finding-hs-filling-twin-payments]].

## Overlaps — do not double count

The **same ₹2,40,00,000** is claimed by two findings. Count it **once, at ₹0**:

- [[finding-hs-filling-twin-payments]] (rank 10, [[duplicate-payments]] lens, H7 "debit balance + zero invoices
  ever", ₹5.34 Cr pool) — HS Filling is ₹2.40 Cr of that ₹5.34 Cr, i.e. 45% of it. Identical rupees, different
  lens. That finding's *duplicate-payment* question (the twin pairs) survives this note and is the piece worth
  chasing; its *balance* component is this note and is not additive.
- [[vendor-money-stuck]] totals it as "Working capital incl. HS Filling = ₹7,53,54,063". **Remove ₹2,40,00,000
  from that line — the working-capital total falls to ₹5,13,54,063.**
- Structurally identical to [[finding-mangla-related-party-advances]]: a deliberate asset purchase (there land,
  here plant) showing up as a vendor debit. Both are disclosure and governance items, neither is recoverable cash.
