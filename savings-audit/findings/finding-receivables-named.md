---
title: "Named receivables bundle — ₹3.67 Cr claimed, ₹1.66 Cr bankable (one 'debtor' had already paid)"
created: 2026-07-29
verdict: MIXED
amount_verified_inr: 16552032
kind: finding
tags: [savings-audit, finding]
---

# Named receivables — what the 60+ book actually contains

**Verdict: MIXED — ₹3.67 Cr claimed across four cash components, ₹1.66 Cr bankable.
One component is dead (the customer paid ₹1.11 Cr thirteen days ago and nobody
matched the receipt), one is a clean ₹23.80 lakh of tax money nobody has claimed
for 22 months, and the rest is real but needs to be sized honestly.**

## The CFO summary in plain language

Four named items were put forward as collectible money sitting in the 60+ debtor
book. I re-derived every one of them from the ledger, from a different direction
than the original sweep, and tried to break each.

**The one that breaks: B S A ENGINEERING LLP.** The sweep says JIVO Oil is owed
₹110.80 lakh from this customer — 30 open invoices, no receipt since 13-May-2026.
The ledger says JIVO Oil is owed **₹54.87. Fifty-four rupees.** B S A paid
**₹1,10,79,500 on 16-Jul-2026**. The receipt is sitting in SAP unallocated, so
all 30 invoices still display as "Open" with their full value. Nothing is
outstanding; a clerk simply hasn't matched cash to bills. Group-wide, B S A owes
₹4.72 lakh (Beverages ₹4.26 L + Mart ₹0.45 L), not ₹115.06 lakh. **This is the
single most important line in this note: a "₹1.15 Cr collection target" that
would have sent the team chasing a customer who has already paid.**

**The one that is free money: FUTURE RETAIL.** ₹94.57 lakh of debtor from before
SAP go-live, zero receipts ever, debtor now in liquidation. A provision of
**exactly ₹94,56,961.88 — matching the debtor to the paisa** — sits in GL
`2180008`, posted once on 30-Sep-2024 and never touched since. Because the
provision was booked as a liability and the debtor was never reduced, this is a
*provision*, not a *write-off*, and Indian tax law allows no deduction for a
provision. Completing the write-off is a pure balance-sheet reclass — **zero
impact on reported profit** — and releases roughly **₹23.80 lakh of cash tax**.
Nobody has done it in 22 months. It is the cleanest ₹23.80 lakh in the audit.

**The one that is real but ageing badly: AB ENTERPRISES.** ₹1,28,77,772 owed,
confirmed three independent ways to the rupee. Terms are *ADVANCE/CASH/0 DAYS*,
so every rupee has been overdue since the day it was billed. No credit notes, no
disputes, ₹8.35 lakh of GST already paid to government on the underlying bills.
But: **no payment for 306 days, no order for 212 days**, no GSTIN on file, and
the SAP credit limit was set to ₹1,28,77,775 — the exposure plus three rupees —
so the credit control never raised a flag. I bank half.

**The long tail is honest.** ₹98.87 lakh claimed across 15 accounts; I re-derive
₹98.58 lakh — within 0.3%. But roughly a quarter of it is not collectible cash,
and one line (Blessing B-Sahib ₹7.40 L) is being counted twice across the audit.

---

## Component verdicts

| # | Component | Claimed | Verified bankable | Verdict |
|---|---|---:|---:|---|
| 1 | AB ENTERPRISES (Oil `CUSTA001014`) | ₹128.78 L | **₹64.39 L** | CONFIRMED exposure, REVISED bankable |
| 2 | B S A ENGINEERING LLP (group) | ₹115.06 L | **₹4.72 L** | **REFUTED** |
| 3 | Long tail — 15 external accounts 60+ | ₹98.87 L | **₹72.62 L** | REVISED |
| 4 | Interest on the 60+ book *(overlay)* | ₹61.7 L/yr | **₹53.96 L/yr — NOT additive** | REVISED |
| 5 | FUTURE RETAIL tax deduction | ₹23.80 L | **₹23.80 L** | CONFIRMED |
| | **Bankable total (1+2+3+5)** | **₹366.51 L** | **₹165.52 L** | **MIXED** |

---

### 1. AB ENTERPRISES — ₹128.78 lakh exposure CONFIRMED, ₹64.39 lakh banked

Three independent measures agree **to the rupee**:

| Measure | Value |
|---|---:|
| `OCRD."Balance"` | ₹1,28,77,772 |
| `SUM(JDT1.Debit − JDT1.Credit)` on the control account | ₹1,28,77,772 |
| `SUM(OINV."DocTotal" − "PaidToDate")` on open invoices | ₹1,28,77,772 |

```sql
-- ledger truth, independent of DocStatus
SELECT CAST(SUM("Debit"-"Credit") AS DOUBLE) FROM JIVO_OIL_HANADB.JDT1
WHERE "ShortName" = 'CUSTA001014';                    -- 12,877,772
```

**Traps cleared.** No credit notes at all (`ORIN` returns zero rows for this card)
— so the Oil invoice-recycling pattern is absent here. No unapplied receipts —
the balance and the open residual are identical, so trap #3 does not apply. Not a
30-Sep-2024 migration balance: the three open invoices are dated 14-Oct-2025,
17-Dec-2025 and 29-Dec-2025. Not intercompany.

**What the sweep did not say.** The invoices are not finished goods. All ₹14.04 Cr
of lifetime sales to this account are a single line item — `RM0000002 CANOLA COLD
PRESS LOOSE OIL OLD`, **a raw material**, 11.66 lakh kg, shipped out of warehouse
`BH-GJ`, with **StockPrice of ₹2,872 across all 25 lines** — i.e. effectively zero
recorded COGS, so the 100% "gross profit" SAP reports on this account is
meaningless. (See [[finding-inventory-valuation]].) Payment terms are
*ADVANCE/CASH/0 DAYS*. `LicTradNum` (GSTIN) is **NULL** on a card that has taken
₹14 Cr of bulk oil. `CreditLine` = ₹1,28,77,775 against a balance of ₹1,28,77,772
— the limit was back-fitted to the exposure.

**Why I bank 50%.** The claim is undisputed, documented, and GST-paid — legally
strong. But 306 days of total silence with no security, on an unregistered
counterparty in bulk commodity trade, does not support banking 100%. ₹64.39 lakh
at a 50% workout recovery; the remaining ₹64.39 lakh is a provision candidate at
half-year close if there is no response to a legal notice.

### 2. B S A ENGINEERING LLP — REFUTED

```sql
SELECT CAST("Balance" AS DOUBLE) FROM JIVO_OIL_HANADB.OCRD
WHERE "CardCode" = 'CUSTA000680';                     -- 54.8769

SELECT TO_VARCHAR("DocDate",'YYYY-MM-DD'), CAST("DocTotal" AS DOUBLE)
FROM JIVO_OIL_HANADB.ORCT
WHERE "CardCode"='CUSTA000680' AND "Canceled"='N'
ORDER BY "DocDate" DESC;                              -- 2026-07-16  11,079,500
```

The claimed ₹110.80 lakh **is the receipt**. ₹1,10,79,500 landed on 16-Jul-2026
and was posted on account rather than against invoices, so the 30 invoices still
carry `"DocStatus"='O'` with ₹1,23,86,515 of nominal residual while the control
account nets to ₹54.87. Lifetime: ₹5.60 Cr invoiced, ₹1.91 L credited,
**₹5.56 Cr received**.

This is trap #3 in its purest form. The claim also quoted "last receipt
13-May-2026", which is the last receipt that happens to be *allocated*.

| Book | Real balance |
|---|---:|
| Oil `CUSTA000680` | ₹54.87 |
| Beverages `CUSTA000680` | ₹4,26,205 |
| Mart `CUSTA000680` | ₹45,084 |
| **Group** | **₹4,71,344** |

Claim overstated **24×**. The ₹4.72 lakh residue is genuinely 60+ but sits on a
customer who has just paid ₹1.11 Cr — bank it in full. The real issue is a
**₹1.24 Cr allocation backlog** that is corrupting every aged-debtor report the
company runs.

### 3. Long tail — ₹98.58 lakh gross confirmed, ₹72.62 lakh bankable

I re-derived on a consistent basis the original sweep did not use: for each card,
`min(OCRD."Balance", open residual past due >60 days on "DocDueDate")`. Capping at
the ledger balance is what kills the on-account-receipt inflation; using
`"DocDueDate"` rather than `"DocDate"` is what reproduces the sweep's CSD figure
(₹29.96 L vs their ₹29.84 L — the sweep was on due date, correctly).

```sql
WITH X AS (
  SELECT c."CardCode", c."CardName", CAST(c."Balance" AS DOUBLE) AS BAL,
    CAST((SELECT SUM(CASE WHEN DAYS_BETWEEN(i."DocDueDate",TO_DATE('2026-07-29'))>60
                          THEN i."DocTotal"-i."PaidToDate" ELSE 0 END)
          FROM JIVO_OIL_HANADB.OINV i
          WHERE i."CardCode"=c."CardCode" AND i."CANCELED"='N') AS DOUBLE) AS DUE60
  FROM JIVO_OIL_HANADB.OCRD c WHERE c."CardType"='C' AND c."Balance">0)
SELECT "CardCode","CardName", CASE WHEN BAL<DUE60 THEN BAL ELSE DUE60 END AS CAPPED
FROM X ORDER BY CAPPED DESC;
```

| Account | Co | Gross 60+ | Bank | Bankable | Why |
|---|---|---:|---:|---:|---|
| Canteen Stores Department | Oil | ₹29.96 L | 100% | ₹29.96 L | Government, active — paid ₹57 L in the last 6 weeks |
| Zomato Hyperpure | Mart | ₹13.04 L | 80% | ₹10.43 L | Still invoicing to 04-Jul, but no receipt for 120 days |
| Innovative Retail (BigBasket) | Oil | ₹13.28 L | 70% | ₹9.30 L | Dormant since Feb-26; 13 credit notes — deduction culture |
| Cmunity Innovations | Mart | ₹10.67 L | 60% | ₹6.40 L | Dead since 27-Mar-2026 |
| **Blessing Advertising B-Sahib** | Oil | ₹7.40 L | **0%** | **₹0** | See below — double-counted |
| Life Essentials | Oil | ₹4.70 L | 40% | ₹1.88 L | 365+, dormant 10 months |
| Innovative Retail (BigBasket) | Mart | ₹3.98 L | 70% | ₹2.78 L | as above |
| Wal Mart India | Oil | ₹2.48 L | 100% | ₹2.48 L | Paying ₹2.4 Cr per 6 weeks |
| Avenue Supermarts (DMart) | Oil | ₹2.35 L | 90% | ₹2.12 L | Blue chip, but 1,538 credit notes on the card |
| Gulati Traders | Bev | ₹2.32 L | 40% | ₹0.93 L | Last invoice Mar-2025, last receipt May-2025 |
| Super Marche 37 | Bev | ₹2.28 L | 30% | ₹0.69 L | Last receipt Jan-2025 — 18 months dead |
| **Media Mind** | Bev | ₹2.21 L | 100% | ₹2.21 L | **Set-off** — see below |
| **Idea Publicity** | Bev | ₹1.51 L | 100% | ₹1.51 L | **Set-off** — see below |
| Metro Cash & Carry | Oil | ₹1.23 L | 100% | ₹1.23 L | Active, paid Jun-2026 |
| Guru Arjan Dev Trading | Bev | ₹1.18 L | 60% | ₹0.71 L | Nothing since Jan-2026 |
| **Total** | | **₹98.58 L** | | **₹72.62 L** | |

**The two set-offs are legally clean, and better than claimed.** Beverages is not
a separate company — `OADM."CompnyName"` reads *"(BEVERAGE UNIT) JIVO WELLNESS
PVT LTD"*, the same legal entity and PAN as the Oil book. So a Beverages
receivable and an Oil payable to the same counterparty are mutual debts of one
company and set-off is available without consent:

- **Media Mind** — Bev customer `CUSTA001040` owes ₹2.21 L (60+); Oil vendor
  `VENDA000706` is owed ₹18,86,129 (single unpaid A-P invoice, 27-Jun-2026).
  Cover is 8.5×.
- **Idea Publicity** — Bev customer `CUSTA000900` owes ₹1.51 L; Oil customer
  `CUSTA000896` carries a **₹47,02,143 credit** because JIVO has collected
  ₹3.23 Cr against ₹2.72 Cr of invoices. Cover is 31×.

**Blessing B-Sahib must be zeroed here.** Oil `CUSTA000041` shows ₹7.40 L. Every
underlying document is dated **30-Sep-2024 — the migration date** (trap #4), and
there has been no invoice and no receipt in 22 months. The obvious fix is to net
it against the Oil A-P to Blessing (`VENDA001047`, −₹29,65,533) — but
[[finding-blessing-advertising-overdue]] **has already claimed that entire
₹29,65,533 set-off** against the ₹3.11 Cr Beverages balance. The set-off pool is
exhausted. Counting the ₹7.40 L again would be double-counting the same payable.
Treat it as a write-off candidate, not cash.

### 4. Interest overlay — REVISED to ₹53.96 lakh/yr, still not additive

[[finding-cc-interest-conversion-rate]] fixes the conversion rate at **8.25%**
(FY25-26 measured: ₹2,33,56,352 of CC interest on a ₹28.32 Cr day-weighted drawn
balance), not the 8.5% the claim used.

I also re-derived the base. Summing `min(Balance, due-60+ residual)` over all
external customer cards in all three books (excluding intercompany and employee
cards, and excluding `R K WORLDINFOCOM` — ₹8.24 Cr, a live Reliance-group account
with ₹63.6 Cr of open residual and receipts on 28-Jul-2026, clearly not overdue)
gives **₹654.02 lakh**, against the sweep's ₹726.25 lakh — 10% lower.

| | Base | Rate | Annual |
|---|---:|---:|---:|
| Claimed | ₹726.25 L | 8.5% | ₹61.73 L |
| **Restated** | **₹654.02 L** | **8.25%** | **₹53.96 L** |
| Attributable to what *this* note banks | ₹165.52 L | 8.25% | ₹13.66 L |

**This is an overlay and must never be added to the audit total.** It is the price
of carrying the debtor book, not a second pot of money; the cash is already
claimed as the collections above. Its only job is to tell the CFO what the delay
costs while the collections programme runs.

### 5. FUTURE RETAIL — ₹23.80 lakh of unclaimed tax, CONFIRMED

```sql
SELECT "AcctCode","AcctName", CAST("CurrTotal" AS DOUBLE)
FROM JIVO_OIL_HANADB.OACT WHERE "AcctCode"='2180008';
-- PROVISION FOR BAD AND DOUBTFUL DEBTS   -9,456,961.88

SELECT CAST("Balance" AS DOUBLE) FROM JIVO_OIL_HANADB.OCRD
WHERE "CardCode"='CUSTA000891';           --  9,456,961.88
```

The provision and the debtor **match to the paisa**, so the provision is specific
to Future Retail and nothing else. The provision has exactly one posting in its
life — `TransId 62523`, 30-Sep-2024, the migration opening-balance journal — and
has not moved in 22 months. The debtor has **zero receipts ever recorded** and
zero credit notes; its last document is also 30-Sep-2024.

**Why the deduction is genuinely unclaimed.** The provision was credited to a
liability account (`2180008`) and the sundry debtor was left at gross. Under
s.36(1)(vii) read with Explanation 1, a mere provision is not deductible; under
*Vijaya Bank v. CIT* (2010) 323 ITR 166 (SC) the write-off is complete only when
the debtor is simultaneously reduced on the asset side. That second limb has never
been performed, so no deduction can have been taken.

**Cross-checks against double counting.** Future Retail is not in the component-3
long tail. This component claims only the tax value, never the ₹94.57 lakh itself
— the debtor is not collectible and is not counted as cash anywhere. And the
benefit is not already sitting on the balance sheet: a recognised DTA on ₹94.57
lakh would be ~₹23.8 lakh, but `2180001 PROVISION FOR DEFERRED TAX` is a net
**liability** of ₹7.26 lakh.

| | |
|---|---:|
| Debtor / provision | ₹94,56,961.88 |
| Effective rate, s.115BAA (22% + 10% surcharge + 4% cess) | 25.168% |
| **Cash tax released** | **₹23,80,128** |

The entry is `Dr Provision for Bad & Doubtful Debts ₹94,56,961.88 / Cr Sundry
Debtors — Future Retail Ltd ₹94,56,961.88`. **No P&L impact at all** — the charge
was taken years ago. Two conditions to confirm before filing: (a) that the
provision was added back in the year it was created (Form 3CD, disallowances) so
this is not a second bite; (b) taxable profits in FY26-27 to absorb it — the
migrated `Provision for Income Tax` of ₹2.03 Cr says yes. If JIVO is on the old
regime at 34.944% rather than 115BAA, the benefit is ₹33.05 lakh, not ₹23.80 lakh.

---

## Action

| Action | Owner | Amount | When |
|---|---|---:|---|
| **Stop chasing B S A.** Allocate the ₹1,10,79,500 receipt of 16-Jul-2026 against the 30 open invoices, then sweep the whole debtor book for the same pattern — unallocated receipts are corrupting every aged report | Accounts Receivable | *removes ₹110.80 L of phantom overdue* | This week |
| **Write off Future Retail** — `Dr 2180008 / Cr CUSTA000891`, ₹94,56,961.88. Zero P&L impact. Confirm the prior-year add-back with the tax auditor, then claim the deduction in the FY26-27 computation | CFO + tax auditor | **₹23.80 L cash tax** | Before advance-tax, 15-Sep-2026 |
| **AB Enterprises — legal notice.** ₹1,28,77,772, undisputed, no credit notes, GST paid. 306 days silent. Demand notice, then s.9 IBC / s.138 as applicable. Provide the balance at half-year if there is no response | Credit Control + Legal | **₹64.39 L** | Notice within 7 days |
| **Execute the two same-entity set-offs** — Media Mind ₹2.21 L against Oil A-P ₹18.86 L; Idea Publicity ₹1.51 L against the Oil credit of ₹47.02 L. Same PAN, mutual debts; issue set-off letters | Accounts | **₹3.72 L** | This week |
| **Run the long-tail collection programme** on CSD, Zomato Hyperpure, BigBasket, Cmunity, Wal Mart, DMart, Metro | Sales + Credit Control | **₹68.90 L** | 90 days |
| **Fix credit control.** `CreditLine` on AB Enterprises was set to exposure + ₹3, so the limit never blocked anything. Ban back-fitting limits to balances; require a GSTIN before any card trades above ₹10 L | CFO | *control, not cash* | This month |
| **Write off / provide** Blessing B-Sahib ₹7.40 L, Super Marche ₹2.28 L, Gulati ₹2.32 L and the other migration-dated residues rather than reporting them as collectible | Accounts | *cleans ₹12 L of dead book* | Half-year close |

**Suggested owner: the Financial Controller**, with the Future Retail write-off
escalated to the CFO because it needs the tax auditor's confirmation, and the AB
Enterprises notice escalated to Legal.

---

Part of [[SAVINGS-MOC]] · Evidence: [[receivables-aging]]

Related: [[finding-blessing-advertising-overdue]] (owns the ₹29.66 L Oil set-off
pool that Blessing B-Sahib cannot also claim) · [[finding-cc-interest-conversion-rate]]
(the 8.25% rate used for the overlay) · [[finding-inventory-valuation]] (the zero
COGS on the AB Enterprises raw-material sales)
