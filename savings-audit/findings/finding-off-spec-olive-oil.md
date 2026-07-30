---
title: "Off-spec olive oil RM0000052 — ₹8.21 Cr of inventory that was never bought, never sold, and only ever created by year-end COGS adjustments"
created: 2026-07-28
verdict: REVISED
amount_verified_inr: 0
kind: control-observation
tags: [savings-audit, finding]
---

# RM0000052 ₹8.21 Cr — REVISED: not slow stock, a year-end book entry. ₹0 bankable, ₹3.89 Cr provably over-valued

Part of [[SAVINGS-MOC]] · Evidence: [[dead-slow-stock]]

## What a CFO needs to know

JIVO Oil's balance sheet carries **₹8,21,15,664 of "LOOSE REFINED OLIVE OIL (DARK COLOUR)" (item RM0000052)** —
**13% of the company's entire ₹63.21 Cr inventory** and **31% of the whole RAW MATERIAL OIL general ledger
account**. The original finding flagged it as dead stock to be QC-tested and blended down. The stock numbers are
exactly right, but the diagnosis is wrong, and the truth is more serious.

**This item has never been bought and never been sold.** Not once in its life. There is no purchase order, no
goods receipt from a supplier, no vendor bill, no delivery note, no sales invoice, no credit note, no production
order, no bill of material, and not one inventory transfer. Zero rows in every one of those tables. Its entire
₹8.21 Cr came from **six manually keyed Goods Receipt / Goods Issue documents**, every one of them dated to a
financial-year-end (31 Mar 2025, 1 Apr 2025, 31 Mar 2026), and every one of them posting the same double entry:
**debit inventory, credit cost of goods sold.** In plain English, ₹8.21 Cr of cost was lifted out of the profit
and loss account and parked on the balance sheet as oil — ₹3.60 Cr of it in FY24-25 and ₹4.61 Cr in FY25-26.
For scale, the FY25-26 slice alone is 2.4% of the company's ₹193.91 Cr turnover, and it lands straight in profit.

Three things make this impossible to wave through. First, **the biggest entry — ₹6.99 Cr, 249,949 litres, dated
31 March 2026 — was actually keyed on 12 June 2026, seventy-three days after the year it belongs to had closed**,
and its only explanation is a free-text note reading "AS PER HK VJI". That is an instruction, not a stock count.
Second, **two of the goods issues have quantities that were reverse-engineered from round rupee targets**: 7,375.17
litres × ₹271.1803 comes to exactly ₹20,00,000.00, and 9,956.48 litres × ₹271.1803 comes to ₹27,00,000.01.
Real oil moves in round *litres*; only book entries move in round *rupees*. Third, and most damning, **on that same
31 March 2026, in that same closing exercise, keyed by that same user, JIVO valued its own prime-grade oil at
₹146.57 a litre — while valuing this off-colour reject grade at ₹279.66 a litre, 1.91 times higher.** An off-spec
by-product cannot be worth 91% more than the good product it came out of. Correcting nothing else but that single
inconsistency — using JIVO's own number for its own oil on its own date — writes the stock down from ₹8.21 Cr to
₹4.32 Cr, a **₹3.89 Cr over-valuation**.

**There is no money to bank here.** The original finding books ₹8.21 Cr as working capital to be released at a
7.3% interest saving. That cannot be right: **no cash was ever spent on this item** — no supplier was ever paid,
because no supplier ever supplied it. You cannot release capital that was never invested. The realistic outcomes
run the other way. If the oil physically exists in tank BH-OT, it can be sold, but only at what off-grade dark
olive oil actually fetches — well under the ₹146.57 the company pays for prime grade, so perhaps ₹2.5–4 Cr of
genuine new cash, and only after a buyer is found. If it does not physically exist, the ₹8.21 Cr must be reversed
and **reported profit falls by ₹8.21 Cr**. Either way this is an asset-quality and closing-controls exposure, not
a saving. **Bankable: ₹0. Certain over-valuation: ₹3.89 Cr. Total amount at risk pending a physical dip-test:
₹8.21 Cr.**

## Verdict

| | |
|---|---|
| Claimed | ₹8,21,15,664 working-capital release |
| Re-derived book value | ₹8,21,15,665 — **exact match**, claim arithmetic is sound |
| **Bankable amount** | **₹0** |
| Provable over-valuation | **₹3,88,77,136** (₹3.89 Cr) |
| Amount at risk pending physical verification | ₹8,21,15,664 |
| Annual interest saving @ 7.3% | **₹0** — nothing is released |
| Verdict | **REVISED** — the item, the value, the zero consumption and the missing BOM all confirm exactly; the *kind* of money is wrong and the direction is reversed |

### What confirmed
- StockValue ₹8,21,15,664.49 in warehouse BH-OT, quantity 294,992.52 — matches the claim to the rupee.
- `ITT1` returns 0 rows for `"Code"='RM0000052'` — in no bill of material. Its sibling RM0000001 appears in **57**.
- Consumption is zero — and not merely for 180 days. It is zero **for the item's entire existence**.
- A receipt of 249,949 units was posted 2026-03-31. Confirmed.
- Implied rate ₹278.37/litre. Confirmed.

### What the claim got wrong
- **"in bulk tank BH-OT"** — `OWHS` names BH-OT **"Param"**. It is a live, ordinary warehouse: 116,175 litres of
  soyabean oil were transferred into it on 2026-07-27 by a normal inventory transfer. Nothing marks it as a tank
  holding rejected oil.
- **"last outward movement 2025-04-01 (16 months)"** — 2025-04-01 is not an outward movement. It is a year-end
  Goods Issue posted against COGS OLIVE, keyed on 2025-10-10. The item has had **no real outward movement ever**.
- **"static for 16 months"** — 85% of the stock (249,949 of 294,993 units) arrived on 2026-03-31, four months ago,
  not sixteen.
- **"sibling RM0000001 holds LESS stock (157,523) yet consumed 2,598,041 units"** — unsafe comparison. RM0000001 is
  transacted in both litres and metric tonnes across documents (₹2.05–3.21 lakh **per MT**), so raw quantities are
  not like-for-like. The sound comparison is per-litre carrying value, which is where the real problem shows.
- **"QC test the tank, blend down or sell as industrial grade"** — premature. The prior question is whether the oil
  exists at all, because nothing in SAP evidences its physical arrival.

## Key SQL evidence

**1. The complete movement history — six documents, all year-end, all against COGS.**

```sql
SELECT L."DocType", L."DocEntry", L."DocDate", L."CardName",
       ROUND(TO_DOUBLE(L."StockQty"),2) AS QTY, L."LocCode"
FROM JIVO_OIL_HANADB.OITL L
WHERE L."ItemCode" = 'RM0000052'
ORDER BY L."DocDate", L."LogEntry";
```

| DocType | DocEntry | DocDate | Offset account | Qty | Keyed on |
|---|---|---|---|---|---|
| 59 Goods Receipt | 3506 | 2025-03-31 | 5000002 COGS OLIVE | +55,000.00 | 2025-04-01 |
| 59 Goods Receipt | 6755 | 2025-03-31 | 5000002 COGS OLIVE | +95,237.18 | **2025-10-10** (+193 d) |
| 60 Goods Issue | 6819 | 2025-03-31 | 5000002 COGS OLIVE | −7,375.17 | 2025-10-10 |
| 60 Goods Issue | 7449 | 2025-03-31 | 5100013 COST OF GOODS SOLD | −9,956.48 | 2025-11-25 |
| 60 Goods Issue | 6822 | 2025-04-01 | 5000002 COGS OLIVE | −87,862.01 | 2025-10-10 |
| 59 Goods Receipt | 11017 | **2026-03-31** | 5100013 COST OF GOODS SOLD | **+249,949.00** | **2026-06-12** (+73 d) |
| | | | **Net** | **294,992.52** | = `OITW."OnHand"` exactly |

Document 11017 carries the comment **"AS PER HK VJI"** and a line value of **₹6,99,00,748**.

**2. The double entry is inventory-up / P&L-down.**

```sql
SELECT J."TransId", J."RefDate", D."Account", A."AcctName",
       ROUND(TO_DOUBLE(D."Debit"),2) AS DR, ROUND(TO_DOUBLE(D."Credit"),2) AS CR
FROM JIVO_OIL_HANADB.OJDT J
JOIN JIVO_OIL_HANADB.JDT1 D ON D."TransId" = J."TransId"
LEFT JOIN JIVO_OIL_HANADB.OACT A ON A."AcctCode" = D."Account"
WHERE J."TransId" IN (102689,153639,153653,153657,163781,213667)
ORDER BY J."TransId", D."Line_ID";
```

Every document posts **Dr 1103006 RAW MATERIAL OIL (asset) / Cr 5000002 COGS OLIVE or 5100013 COST OF GOODS SOLD
(expense)**. `OACT."ActType"='E'` confirms both credit accounts are P&L expense accounts. Net by year:
**FY24-25 ₹3,60,41,364 credited to COGS; FY25-26 ₹4,60,74,301 credited to COGS.**

**3. It exists in no operational document, anywhere — and it is the only such item in the company.**

```sql
WITH STK AS (SELECT "ItemCode", SUM("OnHand") AS QTY, SUM("StockValue") AS VAL
             FROM JIVO_OIL_HANADB.OITW GROUP BY "ItemCode")
SELECT S."ItemCode", I."ItemName", ROUND(TO_DOUBLE(S.VAL)/100000,2) AS VAL_LAKH
FROM STK S JOIN JIVO_OIL_HANADB.OITM I ON I."ItemCode" = S."ItemCode"
WHERE S.VAL > 1000000
  AND NOT EXISTS (SELECT 1 FROM JIVO_OIL_HANADB.PCH1 X WHERE X."ItemCode"=S."ItemCode")
  AND NOT EXISTS (SELECT 1 FROM JIVO_OIL_HANADB.PDN1 X WHERE X."ItemCode"=S."ItemCode")
  AND NOT EXISTS (SELECT 1 FROM JIVO_OIL_HANADB.INV1 X WHERE X."ItemCode"=S."ItemCode")
  AND NOT EXISTS (SELECT 1 FROM JIVO_OIL_HANADB.DLN1 X WHERE X."ItemCode"=S."ItemCode")
  AND NOT EXISTS (SELECT 1 FROM JIVO_OIL_HANADB.WOR1 X WHERE X."ItemCode"=S."ItemCode")
  AND NOT EXISTS (SELECT 1 FROM JIVO_OIL_HANADB.WTR1 X WHERE X."ItemCode"=S."ItemCode")
ORDER BY S.VAL DESC;
```

Fourteen rows come back. **Thirteen are fixed assets** — trucks HR69F9627 / HR69F7125 / HR69E4548, a vegetable
processing line, a filler, a chiller, a sewage treatment plant, a Maruti XL6. Assets legitimately never touch a
purchase or sales document. **RM0000052 is the fourteenth, at ₹821.16 lakh, and it is the only stock item on the
list.** (Note: `NOT IN` returns nothing here because of NULL `ItemCode` rows — `NOT EXISTS` is required.)

**4. The valuation is 1.91× the company's own same-day rate for the prime grade.**

The 2026-03-31 closing exercise contained five COGS-credit goods receipts totalling ₹913.17 lakh. Three of them
top up prime-grade RM0000001 with the note *"As per Audit Report received from Ginni Vg"* / *"March Audit Diff"*:

| Item | Qty | Amount | Implied rate |
|---|---|---|---|
| RM0000001 LOOSE REFINED OLIVE OIL | 16,398.19 | ₹24,03,564.70 | **₹146.5748** |
| RM0000001 LOOSE REFINED OLIVE OIL | 7,357.87 | ₹10,78,479.80 | **₹146.5748** |
| RM0000001 LOOSE REFINED OLIVE OIL | 9,352.79 | ₹13,70,885.19 | **₹146.5748** |
| **RM0000052 (DARK COLOUR)** | **249,949.00** | **₹6,99,00,748.00** | **₹279.66** |

```sql
SELECT ROUND(TO_DOUBLE(2403564.70/16398.19),4) AS PRIME_RATE_31MAR2026,
       ROUND(TO_DOUBLE(279.66/(2403564.70/16398.19)),3) AS PREMIUM_X,
       ROUND(TO_DOUBLE(294992.52*(2403564.70/16398.19)),2) AS VALUE_AT_PRIME_RATE,
       ROUND(TO_DOUBLE(82115664.487 - 294992.52*(2403564.70/16398.19)),2) AS OVERSTATEMENT_INR
FROM DUMMY;
```

→ prime rate **₹146.575**, premium **1.908×**, value at prime rate **₹4,32,38,529**, **overstatement ₹3,88,77,136**.

Carrying value per litre across the olive range confirms the same inversion: RM0000001 prime **₹177.97/l**,
RM0000052 off-spec **₹278.37/l**. Under AS 2 / Ind AS 2 (lower of cost and net realisable value) an off-colour
reject grade must sit **below** the prime grade, not 56% above it.

**5. The traps were checked and cleared.**
- *Intercompany (trap 2):* no mirror. Neither Mart nor Beverages holds this item — `JIVO_BEVERAGES_HANADB`'s
  RM0000052 is ASPARTAME POWDER, an unrelated code collision. There is nothing to net off at group level.
- *Third-party stock:* BH-OT is named "Param", but `OCRD` has no Param stockholding partner — only PARAMBA POLYMER
  (a polymer vendor) and employee imprest accounts. The oil is not evidenced as lying with a job worker.
- *Batches:* the item is batch-managed (`ManBtchNum='Y'`) but its three `OBTN` "batches" are just the three receipt
  document numbers, with **no expiry date and no notes** — no evidence of a real physical lot.

## Action

**Owner: CFO**, with Accounts executing and Internal Audit verifying.

1. **Physically dip-test tank/location BH-OT ("Param") this week** and certify whether 294,992 litres of dark
   olive oil exist. This single step decides whether the ₹8.21 Cr is an asset or a hole. Get it in writing, signed,
   with a date — the same way the RM0000001 audit differences were evidenced.
2. **Obtain the working papers behind Goods Receipt 326596842 ("AS PER HK VJI", ₹6.99 Cr, keyed 2026-06-12).**
   Ask specifically: what physical count supports 249,949 litres, and who authorised valuing it at ₹279.66 when
   prime-grade oil was valued at ₹146.57 the same day in the same exercise.
3. **Re-value immediately, regardless of the count outcome.** At JIVO's own prime-grade rate the write-down is
   **₹3.89 Cr**; at a realistic off-spec discount it is larger. This reduces FY25-26 profit and must be discussed
   with the statutory auditors before the accounts are signed.
4. **Close the control gap (owner: Accounts + IT).** Block back-dated inventory documents into a closed period, and
   require every Goods Receipt whose contra is a COGS account to carry a signed stock-count reference — not a
   free-text name. Note that ₹2.14 Cr of *other* year-end COGS-credit adjustments on 2026-03-31 were properly
   evidenced ("As per Audit Report received from Ginni Vg"), so the standard already exists internally; it simply
   was not applied to the largest entry.
5. **If the oil is confirmed to exist**, then and only then run the QC/blend-down/industrial-sale route the original
   finding proposed — and book the proceeds as a fresh recovery, not as a released asset.

## Overlaps — do not double count

- [[finding-dead-slow-stock-1223cr]] — this ₹8.21 Cr is **91% of the ₹9.37 Cr "dead stock"** and **67% of the
  ₹12.23 Cr dead+slow headline**. Since it is **₹0 bankable**, that headline must drop to roughly **₹4.02 Cr** of
  genuinely releasable dead/slow stock.
- [[finding-stock-carrying-cost]] — the ₹1.22 Cr/yr carrying cost is computed on the ₹12.23 Cr pile. Remove this
  item and the recurring carrying-cost claim falls to about **₹0.40 Cr/yr**. Charging interest on stock that was
  never paid for overstates the saving twice over.
- The ₹2.14 Cr of other 2026-03-31 COGS-credit entries (RM0000001 audit differences ₹48.53 L, finished goods
  ₹39.19 L, and a ₹1.26 Cr Beverages→Oil fixed-asset transfer) are **separately justified and are not part of this
  finding** — they must not be merged into the ₹8.21 Cr.
- Same shape as [[finding-hs-filling-advance]]: a large balance that reads as recoverable working capital but is
  nothing of the kind. Both resolve to **₹0 bankable**.
