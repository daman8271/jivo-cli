---
title: "Dormant vendor advances + ALO Logistics transporter claims — ₹49.9 L claimed, ₹4.06 L bankable"
created: 2026-07-29
verdict: MIXED
amount_verified_inr: 405545
amount_claimed_inr: 4993503
kind: one-time-recovery
company: ALL
lens: vendor-money-stuck
ranks: [49, 52]
tags: [savings-audit, finding]
---

# Dormant vendor advances (rank 49) + ALO Logistics claims (rank 52) — MIXED

**Claimed:** ₹26,52,512 (11 dormant vendors, all companies) + ₹23,40,991 (ALO Logistics, Mart) = **₹49,93,503**.
**Re-derived bankable:** **₹4,05,545** (₹4.06 lakh) — 8.1% of the claim.
**Interest released at the measured 8.25% CC rate:** ₹33,457 a year *(overlay on the ₹4.06 L, not extra money)*.

Part of [[SAVINGS-MOC]] · Evidence: [[vendor-money-stuck]]

---

## Plain-language summary for the CFO

Two findings were bundled here, both saying "a supplier is sitting on our money and nobody is chasing it."

**The population is real and I reproduced it to the rupee.** My own query — different shape from the
original sweep's — returns exactly the same 12 accounts and exactly ₹26,52,512 + ₹23,40,991. So this is
not an arithmetic problem. The problem is **what those balances actually are** once you open each one.

When you resolve every entry back to the general ledger, **90% of the ₹49.9 L is not money anybody can
go and collect**:

| Bucket | ₹ | Why it isn't collectible |
|---|---:|---|
| Capex advance on a live fixed-asset PO (Agilent lab instrument) | 11,15,100 | Deliberate equipment purchase, 70% paid on a ₹15.93 L order |
| Migration opening balances dressed as documents | 5,98,362 | No underlying transaction exists in SAP at all |
| Internal clearing / payroll suspense accounts (not suppliers) | 2,19,603 | Zero cash ever moved; a bookkeeping account, not a party |
| Already claimed by [[finding-no-invoice-vendors]] | 4,90,862 | Same rupees — counting them twice inflates the programme |
| ALO Logistics "transporter claims" | 23,40,991 | Suspense account for e-commerce customer deductions (below) |
| **Genuinely collectible, dormant, undisputed** | **4,05,545** | ✅ **BANKABLE** |
| **Total** | **49,93,503** | |

**Only ₹4.06 lakh is real.** Three names: GODAMWALE ₹1,92,543, BHARAT ORGANICS ₹1,50,574,
AJANTA SOYA ₹62,428. All three are ordinary trading counterparties JIVO actually bought from and
actually paid, whose accounts ended in a small debit and then went quiet 15–18 months ago. A balance-
confirmation letter to each should get the money or a credit note. That is a genuine, if modest, win.

**The ALO Logistics ₹23.4 L is the important story, and it is not a recovery — it is a control failure.**
JIVO has **never received a single freight bill from ALO Logistics LLP and has never paid them a rupee**,
in any of the three companies (there are four ALO master records; three have literally zero ledger lines).
Yet ₹23.4 L of debits sit on one of them. Every one of those debits was created by taking a deduction that
an **e-commerce customer** made against JIVO — Zepto ₹8.95 L, Swiggy ₹1.16 L, BigBasket ₹13.09 L — and
parking it on the transporter's ledger instead of expensing it. The contra side of every entry is a customer
receivable or an intercompany account; **not once is it a freight expense or a claims-recoverable account**.
One line even books a **DTDC** freight charge to ALO. This account is functioning as a suspense bin for
e-com losses. The ₹23.4 L of loss is real and has already been suffered; the idea that ALO owes it is
unsupported by anything in SAP.

---

## Verdict: MIXED — ₹4,05,545 bankable

| Component | Claimed ₹ | Verified ₹ | Verdict |
|---|---:|---:|---|
| Rank 49 — dormant vendor advances (11 vendors) | 26,52,512 | 4,05,545 | **REVISED** |
| Rank 52 — ALO Logistics transporter claims | 23,40,991 | 0 | **REFUTED** |
| **Bundle** | **49,93,503** | **4,05,545** | **MIXED** |

---

## 0. The population replicates exactly — this is not an arithmetic error

```sql
-- run as one UNION ALL across the three schemas; abridged to the Oil arm
WITH v AS (
SELECT 'OIL' AS CO, c."CardCode", c."CardName",
       CAST(c."Balance" AS DECIMAL(18,2)) AS BAL, IFNULL(g."GroupName",'?') AS GRP,
 (SELECT MAX(i."DocDate") FROM JIVO_OIL_HANADB.OPCH i
   WHERE i."CardCode"=c."CardCode" AND i."CANCELED"='N')            AS LASTINV,
 (SELECT MAX(p."DocDate") FROM JIVO_OIL_HANADB.OVPM p
   WHERE p."CardCode"=c."CardCode" AND p."Canceled"='N')            AS LASTPAY,
 (SELECT COUNT(*) FROM JIVO_OIL_HANADB.OPOR o
   WHERE o."CardCode"=c."CardCode" AND o."CANCELED"='N' AND o."DocStatus"='O') AS OPENPO
FROM JIVO_OIL_HANADB.OCRD c
LEFT JOIN JIVO_OIL_HANADB.OCRG g ON g."GroupCode"=c."GroupCode" AND g."GroupType"='S'
WHERE c."CardType"='S' AND CAST(c."Balance" AS DECIMAL(18,2)) >= 50000
/* + MART + BEV arms */ )
SELECT * FROM v
WHERE GRP <> 'FIXED ASSETS'
  AND (LASTINV IS NULL OR LASTINV < TO_DATE('2025-07-29'))
  AND (LASTPAY IS NULL OR LASTPAY < TO_DATE('2026-01-29'))
ORDER BY BAL DESC;
```

Returns **12 rows**: ALO Logistics ₹23,40,991 plus the 11 rank-49 names summing to **₹26,52,512.20**.
Both headline numbers verified. Note the `OPENPO` column, which the original sweep did not carry — it is
what kills the largest single item.

---

## 1. Rank 49, item by item

| # | Co | CardCode | Vendor | ₹ | Verdict |
|---|---|---|---|---:|---|
| 1 | Oil | VENDA001482 | AGILENT TECHNOLOGIES | 11,15,100 | ❌ capex advance |
| 2 | Oil | VENDA000241 | VIJAY INDUSTRIES | 4,21,402 | ❌ migration artefact |
| 3 | Mart | VENDA000936 | GODAMWALE TRADING & LOGISTICS | 1,92,543 | ✅ **bankable** |
| 4 | Oil | VENDA000919 | RAMA SALES | 1,76,960 | ⚠️ already claimed |
| 5 | Oil | VENDA001084 | JIVO WELLNESS (AKAL INFOSYS) | 1,52,855 | ❌ internal clearing |
| 6 | Oil | VENDA000039 | BHARAT ORGANICS & DAIRY | 1,50,574 | ✅ **bankable** |
| 7 | Oil | VENDA000759 | KS AFFINITY | 1,07,902 | ⚠️ already claimed |
| 8 | Oil | VENDA001560 | JASRA & JASRA LAW OFFICES | 1,06,000 | ⚠️ already claimed |
| 9 | Bev | VENDA001090 | GAGANDEEP SINGH | 1,00,000 | ⚠️ already claimed |
| 10 | Bev | VENDA000945 | BONUS PAYABLE | 66,748 | ❌ payroll clearing |
| 11 | Mart | VENDA000938 | AJANTA SOYA LIMITED | 62,428 | ✅ **bankable** |
| | | | **Total** | **26,52,512** | **₹4,05,545 bankable** |

### ❌ AGILENT ₹11,15,100 — the single biggest item, and it is capex (Trap 1)

The sweep says "never invoiced, last paid 2026-01-08." True, and irrelevant: there is a **live open
purchase order for a fixed-asset item**.

```sql
SELECT p."DocNum", p."DocDate", p."DocStatus",
       CAST(p."DocTotal" AS DECIMAL(18,2)) AS GROSS, CAST(p."VatSum" AS DECIMAL(18,2)) AS GST,
       l."ItemCode", l."Dscription", l."LineStatus", CAST(l."OpenQty" AS DECIMAL(18,3)) AS OPENQ
FROM   JIVO_OIL_HANADB.OPOR p JOIN JIVO_OIL_HANADB.POR1 l ON l."DocEntry"=p."DocEntry"
WHERE  p."CardCode"='VENDA001482';
```

| PO | Date | Item | Description | Gross ₹ | GST ₹ | Status |
|---|---|---|---|---:|---:|---|
| 825226582 | 2025-08-20 | **FA0000290** | AGILENT 8860 GC SYSTEM | 15,93,000 | 2,43,000 | Open, OpenQty 1 |

`FA0000290` sits in item group **112 = FIXED ASSETS** (all 397 `FA*` item codes do). Cash out is
₹2,70,000 (28-Aug-2025) + ₹8,45,100 (08-Jan-2026) = **₹11,15,100 = 70% of the order**. The vendor group
is `PURCHASE`, not `FIXED ASSETS`, which is precisely why the sweep's group filter failed to catch it —
**the item is the asset, not the vendor master**.

This is not recoverable money. It **is** a red flag, in the same family as [[finding-hs-filling-advance]]:

- PO due date **2025-08-30**; today 2026-07-29 → **333 days overdue**, `OPDN` (goods receipt) count = **0**.
- ₹2,43,000 of **GST input credit is blocked** until a tax invoice exists.
- The 02-Jan-2026 payment was keyed, reversed the same day (`Reverse Entry for Payment No. 126466512`),
  and re-paid on 08-Jan-2026 from a **different bank** (`2201207 LOAN TERM INDIAN BANK`). Correctly
  reversed — **not** a duplicate payment.

**Verdict: REFUTED as bankable (₹0). Escalate as a delivery/ITC red flag.**

### ❌ VIJAY INDUSTRIES ₹4,21,402 — a migration opening balance wearing a credit note's clothes (Trap 6)

The sweep calls it "never invoiced, never paid — likely posting error." The GL is more specific than that.

```sql
SELECT h."TransId", h."TransType", h."RefDate", j."Account", a."AcctName",
       CAST(j."Debit" AS DECIMAL(18,2)) AS DR, CAST(j."Credit" AS DECIMAL(18,2)) AS CR, j."LineMemo"
FROM   JIVO_OIL_HANADB.JDT1 j
JOIN   JIVO_OIL_HANADB.OJDT h ON h."TransId"=j."TransId"
LEFT   JOIN JIVO_OIL_HANADB.OACT a ON a."AcctCode"=j."Account"
WHERE  j."TransId" IN (SELECT DISTINCT "TransId" FROM JIVO_OIL_HANADB.JDT1
                       WHERE "ShortName"='VENDA000241');
```

One journal, `TransId` 58662, `TransType` **19** (A/P credit memo), dated **2024-09-30** — SAP go-live day:
DR `VENDA000241` ₹4,21,402 / CR **`3200003 OPENING BALANCE ACCOUNT`** ₹4,21,402.

Three tests, all negative:
- `ORPD` (goods returns) for VENDA000241 → **zero rows**. The comment "Based On Goods Return 240710002"
  is legacy narrative carried in from Busy; the document does not exist in SAP.
- The credit memo's only line (`RPC1`) has `ItemCode` **NULL**, `Quantity` **0**, description literally
  **"OPENING BALANCE ACCOUNT"**. There is no goods return — it is a balance-loading document.
- The cited underlying invoice is **no. 364 dated 04-09-2023**, i.e. ~3 years old, and the relationship
  is completely dead (zero `OPCH`, zero `OVPM` in SAP).

SAP holds **no evidence of what this is**. Chasing it needs the legacy Busy ledger and the original debit
note, and it is at or near the 3-year limitation window. **Verdict: REFUTED as bankable (₹0)** —
contingent at best; realistically confirm-then-write-off.

### ❌ AKAL INFOSYS ₹1,52,855 and BONUS PAYABLE ₹66,748 — accounts, not suppliers

- `VENDA001084 JIVO WELLNESS (AKAL INFOSYS)` (Oil): **53 journals, `TransType` 30 only, zero `OVPM`,
  zero `OPCH`.** Contras are `3200003 OPENING BALANCE`, the eight `SUNDRY DEBTORS *` accounts and
  `1110109 JIVO WELLNESS BEVERAGES INTERNAL`. It is an internal clearing account. **No cash ever moved** —
  "recovering" it is meaningless.
- `VENDA000945 BONUS PAYABLE` (Beverages): every line hits **`2110008 SUNDRY CREDITORS PAYABLE CLEARING
  ACCOUNTS`**, against `5630014 BONUS EXPENSES`, `5630001 SALARY EXPENSE`, `2161001 SALARY PAYABLE JAN`,
  `2163015 EPF PAYABLE`, `2163016 ESIC PAYABLE`. It is the **factory payroll clearing route** — bonus and
  wages paid to workers through a vendor-shaped master. The ₹66,748 is an unreconciled payroll clearing
  residual, not a third-party debt. The sweep is right that the master is wrong; it is wrong that it is money.

**Verdict on both: REFUTED as bankable (₹0). Master-data clean-up.**

### ⚠️ ₹4,90,862 is already claimed — do not add it (Trap 8)

`RAMA SALES 1,76,960` + `KS AFFINITY 1,07,902` + `JASRA & JASRA 1,06,000` + `GAGANDEEP SINGH 1,00,000`
are four of the seven names inside the **₹6,55,011 already verified and banked** by
[[finding-no-invoice-vendors]]. Excluded here in full.

Two corrections to that finding while I am in the ledger — they do not change its total, but they change
the collection story:

- **RAMA SALES and KS AFFINITY were never paid in cash.** Their `OVPM` documents dated 2024-09-30 have
  contra **`3200003 OPENING BALANCE ACCOUNT`**, not a bank. They are migration opening balances keyed as
  payment documents. The recovery argument "cash left our bank" does not hold for these two (₹2,84,862);
  they are legacy balances needing confirmation, like Vijay Industries.
- **JASRA & JASRA ₹1,06,000 is the cleanest item in that set** — three genuine ICICI payments
  (₹30,000 on 26-Nov-2025, ₹51,000 on 28-Nov-2025, ₹25,000 on 09-Dec-2025) to a law firm with no bill
  raised. Chase this one first; it is a live relationship and an unbilled retainer.
- **GAGANDEEP SINGH ₹1,00,000 is half intercompany** — ₹50,000 cash (06-May-2025, ICICI) plus ₹50,000
  moved in on 01-Sep-2025 from `1110109 JIVO WELLNESS OIL INTERNAL` ("Gagandeep Singh Balance Transfer").
  A second ₹50,000 payment on 24-May-2025 was keyed and reversed the same day.

### ✅ What IS bankable — ₹4,05,545

```sql
-- Mart: GODAMWALE ledger, every line
SELECT h."TransId", h."TransType", h."RefDate",
       CAST(j."Debit" AS DECIMAL(18,2)) AS DR, CAST(j."Credit" AS DECIMAL(18,2)) AS CR, j."LineMemo"
FROM   JIVO_MART_HANADB.JDT1 j JOIN JIVO_MART_HANADB.OJDT h ON h."TransId"=j."TransId"
WHERE  j."ShortName"='VENDA000936' ORDER BY h."RefDate";
```

| Co | CardCode | Party | ₹ | Dormant | What it actually is |
|---|---|---|---:|---:|---|
| Mart | VENDA000936 | GODAMWALE TRADING & LOGISTICS | 1,92,543 | 455 d | Real 3PL relationship: **19 A/P invoices, ₹13,42,205 paid across 5 payments**. Net debit residual, including two manual debit notes — ₹32,812 *"debit against warehouse shortage"* (31-Mar-2025) and ₹3,00,000 *"amount debited due to stock damage done by transporter"* (30-Apr-2025). Single master, nothing to net against. |
| Oil | VENDA000039 | BHARAT ORGANICS & DAIRY | 1,50,574 | 485 d | Two-way party. Payments ₹42,02,153 − purchase invoices ₹44,29,480 + ₹3,77,901 of **own sales invoices set off** (JEs *"Customer Invoice No. 624101092 / 624101162 / 624101211 / 624111441"*) = ₹1,50,574 net receivable. Its customer master `CUSTA000731` is already down to ₹0.79, so the set-off is finished and this is the residue. |
| Mart | VENDA000938 | AJANTA SOYA LIMITED | 62,428 | 537 d | **Cleanest item in the bundle.** One settlement, one day: paid ₹39,80,955 on 07-Feb-2025 against an invoice of ₹39,22,322, plus a ₹3,795 TDS debit → overpaid by ₹58,633. Listed counterparty, single transaction, undisputed arithmetic. |
| | | **Total** | **4,05,545** | | |

None of the three has an offsetting master in another company (checked all three schemas), so there is
nothing to net — it has to be collected or credit-noted.

**Working-capital release ₹4,05,545 → interest at the measured 8.25% CC rate = ₹33,457 a year.**
Per the audit convention this is an **overlay on the ₹4.06 L, not additional bankable money.**

---

## 2. Rank 52 — ALO Logistics ₹23,40,991: REFUTED

The balance is exactly as described. What it *is* is not.

```sql
SELECT h."TransId", h."TransType", h."RefDate", j."Line_ID", j."ShortName",
       j."Account", a."AcctName",
       CAST(j."Debit" AS DECIMAL(18,2)) AS DR, CAST(j."Credit" AS DECIMAL(18,2)) AS CR, j."LineMemo"
FROM   JIVO_MART_HANADB.JDT1 j
JOIN   JIVO_MART_HANADB.OJDT h ON h."TransId"=j."TransId"
LEFT   JOIN JIVO_MART_HANADB.OACT a ON a."AcctCode"=j."Account"
WHERE  j."TransId" IN (SELECT DISTINCT "TransId" FROM JIVO_MART_HANADB.JDT1
                       WHERE "ShortName"='VENDA000972')
ORDER  BY h."RefDate", j."TransId", j."Line_ID";
```

Four journals, and **the contra side of every single one is a customer or an intercompany account**:

| Journal | Date | ₹ debited to ALO | Contra (credit) side | What it really is |
|---|---|---:|---|---|
| 25605 | 21-Jun-2025 | 1,16,329 | `CUSTA000648` **SCOOTSY LOGISTICS** (= Swiggy Instamart), `1101005 SUNDRY DEBTORS E-COM` | Swiggy deduction absorbed |
| 45713 | 30-Oct-2025 | 13,09,164.53 (10 lines) | `VENDA000001` **JIVO WELLNESS PVT LTD**, `2121002 SUNDRY CREDITORS JIVO WELLNESS` | **Intercompany** |
| 46405 | 06-Nov-2025 | 8,94,955.50 | `CUSTA000722` **KIRANAKART TECHNOLOGIES** (= Zepto), `1101005 SUNDRY DEBTORS E-COM` | Zepto RTV deduction absorbed |
| 53399 | 08-Dec-2025 | 20,542 | `1110107 JIVO WELLNESS PVT. LTD.-SBD` | **Intercompany**, and it is **DTDC** freight |
| | | **23,40,991.03** ✓ | | |

### Test A — the ₹13.09 L is an intercompany-mirrored BigBasket receivable (Trap 2)

The ten `"WellnessIN 6241211xx"` lines are **Oil-company invoice numbers**. On the *same day*, Oil posts
the mirror:

```sql
SELECT h."TransId", h."RefDate", j."ShortName", a."AcctName",
       CAST(j."Debit" AS DECIMAL(18,2)) AS DR, CAST(j."Credit" AS DECIMAL(18,2)) AS CR, j."LineMemo"
FROM   JIVO_OIL_HANADB.JDT1 j JOIN JIVO_OIL_HANADB.OJDT h ON h."TransId"=j."TransId"
LEFT   JOIN JIVO_OIL_HANADB.OACT a ON a."AcctCode"=j."Account"
WHERE  UPPER(j."LineMemo") LIKE '%ALO %' OR UPPER(j."LineMemo") LIKE '%BB ROYAL%';
```

`TransId` 158137, 30-Oct-2025, memo **"Transfer of entries from BB royal ledger to Alo ledger"**:
DR `CUSTA000606` **JIVO MART PVT LTD** ₹13,09,164.53 / CR `CUSTA000496` **INNOVATIVE RETAIL CONCEPTS
PVT LTD** ₹13,09,164.53.

So the chain is: **BigBasket (Innovative Retail) owed it → moved onto the Mart intercompany ledger →
moved onto ALO's ledger.** Mart's "asset" is matched rupee-for-rupee by a Mart payable to Oil
(`VENDA000001`). At group level it **nets to zero** — it is a relabelled BigBasket receivable, not new
money, and its real recoverability question belongs to the BigBasket ledger, not to a transporter.

### Test B — JIVO has never transacted with ALO Logistics at all

There are **four** ALO Logistics LLP master records. Three are frozen (`validFor` = 'N') and have
**zero** ledger lines:

```sql
SELECT 'OIL-VENDA001273',
  (SELECT COUNT(*) FROM JIVO_OIL_HANADB.OPCH WHERE "CardCode"='VENDA001273'),
  (SELECT COUNT(*) FROM JIVO_OIL_HANADB.OVPM WHERE "CardCode"='VENDA001273'),
  (SELECT COUNT(*) FROM JIVO_OIL_HANADB.JDT1 WHERE "ShortName"='VENDA001273') FROM DUMMY
UNION ALL SELECT 'MART-VENDA000946', ... UNION ALL SELECT 'BEV-VENDA001048', ...;
```

| Master | A/P invoices | Payments | Journal lines |
|---|---:|---:|---:|
| Oil `VENDA001273` | 0 | 0 | 0 |
| Mart `VENDA000946` | 0 | 0 | 0 |
| Bev `VENDA001048` | 0 | 0 | 0 |
| Mart `VENDA000972` | **0** | **0** | 22 (the four journals above) |

**Across three companies and four masters, JIVO has never received a freight bill from ALO Logistics LLP
and has never paid them a rupee.** There is no PO, no GRPO, no contract trail, no GSTIN (`LicTradNum` NULL
on all four). You cannot hold a transporter liable for damage in transit on a consignment you have no
record of engaging them for — and you have no payable to net a debit note against.

### Test C — the accounting shape is a suspense account, not a claim

A genuine recovery entry reads *DR Transporter / CR Freight Expense* or *CR Claims Recoverable*. **Not one
of the 22 lines touches a freight expense or a recoverable account.** Every contra is a customer debtor or
an intercompany account. And journal 53399 debits **DTDC**'s Kundli freight to **ALO** — a different
transporter — which proves the account is being used as a parking bin rather than as a party ledger.

### What this actually means

The ₹23.4 L of economic loss is **real and already suffered**: Zepto, Swiggy and BigBasket deducted it and
JIVO gave the credit. What is not real is the asset. Booking it against a transporter JIVO has no
relationship with keeps ₹23.4 L of e-commerce RTV/damage loss **out of the P&L** and parked on the balance
sheet, ageing quietly since 08-Dec-2025 (233 days).

**Verdict: REFUTED as bankable (₹0).** Reclassify to *control observation*. The most that could ever be
chased from ALO is the ₹10,11,284 of customer-contra lines (Zepto ₹8,94,956 + Swiggy ₹1,16,329), and only
if Purchase/Logistics can produce a signed contract, PODs and short-receipt evidence per consignment —
none of which exists in SAP. The ₹13,29,707 of intercompany lines cannot be chased from ALO under any
evidence.

---

## Action

| # | Action | Owner |
|---|---|---|
| 1 | **Balance-confirmation letters to the three real names (₹4,05,545)** — AJANTA SOYA ₹62,428 first (single-transaction overpayment, listed counterparty, undisputed), then BHARAT ORGANICS ₹1,50,574 and GODAMWALE ₹1,92,543. Demand refund or credit note by **30 Sep 2026**. | **Accounts (A/P)** |
| 2 | **AGILENT — escalate, do not chase as a refund.** PO 825226582 is **333 days past due with zero delivery** and ₹11.15 L (70%) already paid. Demand a delivery date or a refund of the advance; ₹2,43,000 of GST ITC stays blocked until a tax invoice arrives. Same pattern as HS Filling — apply the same rule: no further tranche without a delivery milestone. | **Purchase + CFO** |
| 3 | **ALO Logistics — stop calling it a receivable.** Either (a) produce contract + PODs + short-receipt evidence and issue a formal debit note for the ₹10,11,284 of customer-contra lines, or (b) **write the ₹23.4 L back to e-commerce RTV/damage expense where it belongs.** Reverse the ₹20,542 DTDC line immediately — it names the wrong transporter. Decide by 30 Sep 2026. | **CFO + Logistics** |
| 4 | **Ban customer deductions being parked on vendor ledgers.** Route every e-com RTV/damage deduction to a named `CLAIMS RECOVERABLE — LOGISTICS` GL with a claim reference and an ageing report. A vendor account with zero A/P invoices should not be postable by manual journal. | **CFO + IT** |
| 5 | **Master-data clean-up (no rupee value, prevents the next false positive):** merge the four ALO masters; move `BONUS PAYABLE` out of the vendor master into the payroll clearing GL; retire `JIVO WELLNESS (AKAL INFOSYS)` as a supplier. | **Accounts** |
| 6 | **Clear the 2024-09-30 migration debits** — VIJAY INDUSTRIES ₹4,21,402, RAMA SALES ₹1,76,960, KS AFFINITY ₹1,07,902 (₹7,06,264 total) all trace to `3200003 OPENING BALANCE ACCOUNT` with no supporting document. Retrieve the Busy-era backup or write off with approval; the Vijay item is at/near 3-year limitation. | **Accounts + CFO** |

---

## Overlaps — state these before adding anything to a total

- **[[finding-no-invoice-vendors]]** — **₹4,90,862 of my rank-49 population is already inside its verified
  ₹6,55,011** (RAMA SALES ₹1,76,960 · KS AFFINITY ₹1,07,902 · JASRA & JASRA ₹1,06,000 · GAGANDEEP SINGH
  ₹1,00,000). **Excluded from my ₹4,05,545 in full — do not add the two.** I also correct that finding's
  premise for two of them: RAMA SALES and KS AFFINITY were never paid in cash (contra = opening balance).
- **[[finding-advances-vs-open-bills]]** — that note already defers ₹2,70,253 of its ₹4,45,529 dormant
  residual to this finding (GODAMWALE ₹1,92,543 · AJANTA SOYA ₹62,428 · BONUS PAYABLE ₹15,282). Those
  rupees are **counted here, once**. Its incremental amount remains ₹0, so there is no double count.
- **[[finding-hs-filling-advance]]** — AGILENT ₹11,15,100 is the **same pattern, different vendor** (capex
  advance paid, nothing delivered, GST ITC blocked). Separate money, no rupee overlap; report the two
  together as one control theme.
- **[[finding-cc-interest-conversion-rate]]** — the ₹33,457/yr interest figure is the 8.25% multiplier
  applied to my ₹4,05,545. It is an **overlay, never additive** to the bundle total.
- **[[finding-blessing-advertising-overdue]]**, **[[finding-trade-spend-as-credit-notes]]** — no overlap;
  different counterparties and different mechanisms.
- **Internal to this bundle:** the ALO ₹13,29,707 of intercompany lines mirrors Oil's `CUSTA000606`
  JIVO MART account and Oil's `CUSTA000496` INNOVATIVE RETAIL (BigBasket) ledger. If a separate receivables
  finding ever claims the BigBasket balance, **that is the same money** — it must not be claimed twice
  under two counterparty names.
