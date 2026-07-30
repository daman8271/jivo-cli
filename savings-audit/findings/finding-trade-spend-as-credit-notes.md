---
title: Trade spend booked as service credit notes — quantum right, diagnosis wrong
created: 2026-07-28
verdict: REVISED
amount_verified_inr: 1450000
kind: annual-recurring
tags: [savings-audit, finding, returns, credit-notes, trade-spend, gst, sap-b1]
---

# Trade spend as credit notes — REVISED (₹3.87 Cr claim → ₹0 saving + ₹14.5 lakh real GST recovery)

Part of [[SAVINGS-MOC]] · Evidence: [[returns-leakage]]

## Plain-language summary for the CFO

JIVO gives roughly **₹3.94 Cr a year of promotional money to its customers** — brand-funded
discounts to Zepto and the q-commerce platforms, promotional discounts to Wal Mart, Metro,
Reliance Retail and the big distributors. Because the customer takes this money by deducting it
from what they owe us, it is delivered through a **credit note against their ledger**, which is the
correct SAP document for a customer deduction. The original audit finding said this money was
"booked as credit notes instead of an expense head", that it hides turnover, and that it escapes
budget control. **Two of those three claims do not survive checking.** The money already lands in
two properly named P&L accounts — `5500004 PROMOTIONAL DISCOUNT` and `5640002 BUSINESS PROMOTION`
— both sitting under `SELLING EXPENSE` in the EXPENDITURE drawer of the chart of accounts. Not one
rupee touches a turnover account, so reported sales are unaffected. Mart even runs a disciplined
monthly provision-and-reversal cycle for it, and Oil has a formal SAP budget on BUSINESS PROMOTION.

**So there is no ₹3.87 Cr saving here.** Re-labelling a correctly-classified selling expense moves
a number between two presentations of the same P&L; it does not stop a rupee of spend. What the
original finding *did* miss is the one genuine cash item: **every one of these credit notes is
issued with zero GST.** We have already paid 5.2–5.9% output GST to the government on the full
invoice value, then handed back ₹3.94 Cr of that value as an untaxed commercial credit note and
recovered none of the tax. Fixing the paperwork so eligible post-sale discounts qualify as GST
credit notes is worth about **₹14.5 lakh a year in cash**, and possibly up to ₹47 lakh if the
e-commerce brand-fund portion is restructured as a taxable promotional service.

There is also a **second, larger consequence that is not money but is important**: because these
service credit notes sit inside the `ORIN` table, the audit's own returns headline of ₹56.40 Cr
counts trade spend as "goods coming back". Stripping it out cuts group returns to ₹52.12 Cr and
**rewrites the Zepto story completely** — ₹89.38 lakh of Zepto's ₹122.6 lakh of "returns" is brand
funding, not product coming back off shelves.

---

## Verdict: REVISED

| Claim in the finding | My test | Result |
|---|---|---|
| ₹3.87 Cr/yr of trade spend via credit notes | GL-based re-derivation | **CONFIRMED — I get ₹3.94 Cr (+1.8%)** |
| "instead of an expense head" | `RIN1."AcctCode"` → `OACT` hierarchy | **REFUTED — 97% lands in EXPENDITURE drawer** |
| "understates turnover" | GroupMask of every posting line | **REFUTED — ₹0 to turnover** |
| "escapes promo-budget control" | `OBGT` budget table | **PARTLY REFUTED — Oil budgets it; Mart budgets nothing** |
| "no claim substantiation" | `ORIN."NumAtCard"` + JE memos | **SPLIT — true for Oil (87% blank), false for Mart (95% referenced)** |
| **Bankable saving from reclassification** | — | **₹0** |
| **Bankable saving found instead (GST)** | `VatGroup` / `VatSum` on all lines | **₹14.5 lakh/yr** |

**Verified bankable: ₹14.5 lakh/yr** (conservative GST recovery). Not a working-capital release, so
no interest saving applies.

---

## Re-derivation 1 — the quantum (different shape: by GL, not by line description)

The original finding grouped `RIN1."Dscription"` free text. I grouped by the **posting account**,
which is what actually drives the P&L, and joined it to the chart of accounts.

```sql
SELECT l."AcctCode", MAX(a."AcctName") AS "GL_NAME", COUNT(*) AS "LINES",
       ROUND(CAST(SUM(l."LineTotal") AS DOUBLE)/100000,2) AS "LAKH"
FROM JIVO_MART_HANADB.RIN1 l
JOIN JIVO_MART_HANADB.ORIN h ON h."DocEntry"=l."DocEntry"
LEFT JOIN JIVO_MART_HANADB.OACT a ON a."AcctCode"=l."AcctCode"
WHERE h."CANCELED"='N' AND h."DocType"='S'
  AND h."DocDate">='2025-07-28' AND h."DocDate"<'2026-07-29'
GROUP BY l."AcctCode" ORDER BY 4 DESC
```

Rolling 12 months, all three companies:

| GL account | Oil ₹L | Mart ₹L | Bev ₹L | Total ₹L |
|---|---:|---:|---:|---:|
| 5500004 PROMOTIONAL DISCOUNT | 129.10 | 81.00 | 0.12 | 210.22 |
| 5640002 BUSINESS PROMOTION | 0.33 | 182.47 | 1.05 | 183.85 |
| **= pure trade spend** | **129.43** | **263.47** | **1.17** | **394.07** |
| 5670001 FREIGHT AND CARTAGE | – | 9.31 | – | 9.31 |
| 5680027 FESTIVAL EXPENSE | 8.20 | – | – | 8.20 |
| 4200003 RENT RECEIVED | 7.90 | – | – | 7.90 |
| 5640004 SAMPLING EXPENSES | 1.54 | 2.85 | 3.49 | 7.88 |
| 5680021 LOSS ON EXPIRED/DAMAGED | 0.70 | – | – | 0.70 |
| 11133263 SAMAN ADVANCE (an **asset** a/c) | 0.23 | – | – | 0.23 |
| 4200006 SCRAP SALES / 5630003 STAFF WELFARE | 0.19 | – | – | 0.19 |
| **All service credit notes** | **148.19** | **275.62** | **4.65** | **428.46** |

**₹3.94 Cr of pure trade spend** against the claimed ₹3.87 Cr — within 2%. The ₹4.28 Cr total also
matches the finding's ₹4.29 Cr. **The number is right.** Note the ₹0.23 lakh posted through a credit
note to `11133263 SAMAN ADVANCE JWPL2831`, an employee-advance *asset* account — a single odd entry
worth one document review.

Note also that the original finding's "BRAND FUND DISCOUNT ₹0.06 Cr" is not a separate account; it
is free text posting into `5640002 BUSINESS PROMOTION`. Grouping by description double-splits what
is one head.

## Re-derivation 2 — the killer: where does it actually post?

```sql
SELECT "AcctCode","AcctName","GroupMask","FatherNum","Levels"
FROM JIVO_OIL_HANADB.OACT
WHERE "AcctCode" IN ('5500004','5640002','5640000','5600000')
```

| Account | Name | Drawer | Parent |
|---|---|---|---|
| 5500004 | PROMOTIONAL DISCOUNT | 5 | 5640000 |
| 5640002 | BUSINESS PROMOTION | 5 | 5640000 |
| 5640000 | **SELLING EXPENSE** | 5 | 5600000 |
| 500000000000000 | **EXPENDITURE** | 5 | (level 1) |

`GroupMask = 5` is the **EXPENDITURE** drawer (level-1 accounts confirm: 1 ASSET, 2 LIABILITY,
3 EQUITY, 4 REVENUE, 5 EXPENDITURE). **These *are* expense heads.** The premise of the finding —
"instead of an expense head" — is factually wrong. The credit note is merely the *document* that
delivers the credit to the customer's ledger; the *charge* is already in Selling Expense.

Sample journal (Mart credit memo 606262353, Knowtable, ₹52.89 lakh, `TransId` 78381):

```sql
SELECT j."Line_ID", j."Account", a."AcctName", j."Debit", j."Credit", j."LineMemo"
FROM JIVO_MART_HANADB.JDT1 j
LEFT JOIN JIVO_MART_HANADB.OACT a ON a."AcctCode"=j."Account"
WHERE j."TransId"=78381 ORDER BY j."Line_ID"
```

> Line 0: **Cr** `1101006 SUNDRY DEBTORS ROI` ₹52.89 L · Lines 1–12: **Dr** `5640002 BUSINESS
> PROMOTION` ₹52.89 L

Dr expense / Cr debtor. Textbook. No revenue account in sight.

## Re-derivation 3 — does it understate turnover? No.

```sql
SELECT IFNULL(a."GroupMask",0) AS "DRAWER", COUNT(*) AS "LINES",
       ROUND(CAST(SUM(l."LineTotal") AS DOUBLE)/100000,2) AS "LAKH"
FROM <SCHEMA>.RIN1 l
JOIN <SCHEMA>.ORIN h ON h."DocEntry"=l."DocEntry"
LEFT JOIN <SCHEMA>.OACT a ON a."AcctCode"=l."AcctCode"
WHERE h."CANCELED"='N' AND h."DocType"='S'
  AND h."DocDate">='2025-07-28' AND h."DocDate"<'2026-07-29'
GROUP BY IFNULL(a."GroupMask",0)
```

| Company | Drawer 1 (asset) | Drawer 4 (revenue) | Drawer 5 (expenditure) |
|---|---:|---:|---:|
| Oil | ₹0.23 L | ₹8.06 L | ₹139.91 L |
| Mart | – | **₹0.00** | ₹275.62 L |
| Beverages | – | **₹0.00** | ₹4.65 L |

The only revenue-drawer lines in the whole population are `4200003 RENT RECEIVED` (₹7.90 L) and
`4200006 SCRAP SALES` (₹0.16 L) — both **INDIRECT INCOME**, correctly reduced, and not turnover.
**Statutory turnover is not understated by a single rupee.** The "understatement" exists only in
the audit's own derived metric (`OINV` − `ORIN`), which wrongly subtracts service credit notes.
That is a defect in the measurement, not in the books.

## Re-derivation 4 — is it off-budget? Half true.

```sql
SELECT b."AcctCode", MAX(a."AcctName") AS "GL", b."FinancYear", COUNT(*) AS "PERIODS",
       ROUND(CAST(SUM(b."DebLTotal") AS DOUBLE)/100000,2) AS "BUDGET_L"
FROM JIVO_OIL_HANADB.OBGT b
LEFT JOIN JIVO_OIL_HANADB.OACT a ON a."AcctCode"=b."AcctCode"
GROUP BY b."AcctCode", b."FinancYear"
```

| Account | FY24-25 budget | FY25-26 budget |
|---|---:|---:|
| 5640001 ADVERTISEMENT | ₹0.38 Cr | ₹5.09 Cr |
| **5640002 BUSINESS PROMOTION** | ₹0.74 Cr | **₹13.41 Cr** |
| **5500004 PROMOTIONAL DISCOUNT** | **no row** | **no row** |

- **Oil formally budgets BUSINESS PROMOTION** at ₹13.41 Cr for FY25-26. Claim of "no budget control"
  fails there.
- But **`5500004 PROMOTIONAL DISCOUNT` — which carries ₹2.10 Cr of the ₹3.94 Cr — has no budget row
  in any company.**
- **`JIVO_MART_HANADB.OBGT` has 0 rows.** Mart operates with no SAP budgets at all — a real control
  gap, but a company-wide one, not something specific to credit notes.

## Re-derivation 5 — is it unsubstantiated? Split, and the opposite way round.

```sql
SELECT "REFTYPE", COUNT(*) AS "DOCS", ROUND(SUM("NET")/100000,2) AS "LAKH" FROM (
  SELECT CASE WHEN h."NumAtCard" IS NULL OR TRIM(h."NumAtCard")='' THEN 'c NO_REF'
              WHEN UPPER(h."NumAtCard") LIKE '%CLAIM%' OR UPPER(h."NumAtCard") LIKE '%DEBIT NOTE%'
                OR h."NumAtCard" LIKE '25320%' THEN 'a CLAIM_REF'
              ELSE 'b GENERIC_LABEL' END AS "REFTYPE",
         CAST(h."DocTotal"-IFNULL(h."VatSum",0) AS DOUBLE) AS "NET"
  FROM <SCHEMA>.ORIN h WHERE h."CANCELED"='N' AND h."DocType"='S'
    AND h."DocDate">='2025-07-28' AND h."DocDate"<'2026-07-29')
GROUP BY "REFTYPE"
```

| | Explicit claim ref | Period/label ref | **No reference at all** |
|---|---:|---:|---:|
| Oil | 1 doc / ₹0.10 L | 75 docs / ₹18.86 L | **167 docs / ₹129.23 L (87%)** |
| Mart | 14 docs / ₹100.09 L | 55 docs / ₹170.99 L | 4 docs / ₹4.54 L (1.6%) |
| Beverages | – | – | 47 docs / ₹4.65 L (100%) |

Mart's documents carry real platform references — `253200552`, `899445.00 ZEPTO DEBIT NOTE CLAIM`,
`DISCOUNT CLAIM ( JAN TO JUN-25 )`, `BRAND FUNDED DISCOUNTS ( MAY -26 )`. And Mart runs a genuine
**monthly provision-and-reversal cycle** visible in `JDT1` `TransType`=30 memos: `RK CCOGS MARCH
2026HRDN2026-2820: 22000193008`, `JULY'25 PROVISION REVERSAL`, `SEP'25 CCOGS PROVISION REVERSAL`.
That is accrual discipline, not an unmanaged leak.

**Oil is where the real gap is:** ₹1.29 Cr of PROMOTIONAL DISCOUNT credit notes to Sai Traders
(₹35.87 L), Wal Mart (₹35.73 L), Oneness Traders (₹20.09 L), CSD (₹10.91 L), Metro, Reliance Retail
— 87% of value with no customer reference, no invoice link, and no budget line.

## The money the original finding missed — zero-GST credit notes

```sql
SELECT IFNULL(l."VatGroup",'(null)') AS "VATGRP", COUNT(*) AS "LINES",
       ROUND(CAST(SUM(l."LineTotal") AS DOUBLE)/100000,2) AS "BASE_L",
       ROUND(CAST(SUM(IFNULL(l."LineVat",0)) AS DOUBLE)/100000,2) AS "VAT_L"
FROM <SCHEMA>.RIN1 l JOIN <SCHEMA>.ORIN h ON h."DocEntry"=l."DocEntry"
WHERE h."CANCELED"='N' AND h."DocType"='S'
  AND h."DocDate">='2025-07-28' AND h."DocDate"<'2026-07-29'
GROUP BY l."VatGroup"
```

**`VatGroup` is blank on all 512 service-credit-note lines. Mart's `VatSum` is exactly ₹0 on
₹2.76 Cr.** Meanwhile the underlying goods bore an effective **5.18% GST in Oil and 5.87% in Mart**
(`OINV`, same window). So JIVO paid output GST on the full invoice value, then returned ₹3.94 Cr of
that value as an untaxed *commercial* credit note and recovered nothing.

| Route | Base | Rate | Annual recovery |
|---|---:|---:|---:|
| A. GST credit note under s.15(3)(b) — Oil general/modern trade | ₹1.29 Cr | 5.18% | ₹6.7 L |
| A. GST credit note under s.15(3)(b) — Mart | ₹2.63 Cr | 5.87% | ₹15.5 L |
| **A total (all eligible)** | **₹3.94 Cr** | | **₹22.3 L** |
| **A conservative (Oil full + Mart at 50%)** | | | **₹14.5 L ← banked** |
| B. Platform bills brand-fund as a taxable service, JIVO takes ITC | ₹2.63 Cr | 18% | ~₹47 L (upside) |

**Why it is not being recovered today, and why that is fixable:** s.15(3)(b) requires the discount to
be agreed in a contract at or before the time of supply, **specifically linked to the relevant
invoices**, with the recipient reversing proportionate ITC. Every one of these lines is
`BaseType = -1` — no invoice linkage exists — so the condition currently fails by construction. That
is an administrative fix entirely within JIVO's control. **Time limit: credit notes affecting FY25-26
output tax must be declared by 30 Nov 2026**, so there is a live ~4-month window to catch part of
the current year. Conditional on a GST consultant's sign-off and a contract amendment; banked
conservatively at ₹14.5 lakh/yr.

## Direction of travel

```sql
SELECT CASE WHEN "DocDate"<'2025-04-01' THEN 'FY24-25'
            WHEN "DocDate"<'2026-04-01' THEN 'FY25-26' ELSE 'FY26-27ytd(4m)' END AS "FY",
       COUNT(*) AS "DOCS", ROUND(CAST(SUM("DocTotal"-IFNULL("VatSum",0)) AS DOUBLE)/100000,2) AS "LAKH"
FROM <SCHEMA>.ORIN WHERE "CANCELED"='N' AND "DocType"='S' AND "DocDate">='2024-04-01' GROUP BY 1
```

| Company | FY24-25 | FY25-26 | FY26-27 YTD (4m) | Annualised forward |
|---|---:|---:|---:|---:|
| Oil | ₹145.74 L | ₹137.06 L | ₹22.27 L | ~₹67 L (**falling**) |
| Mart | – | ₹138.13 L | ₹137.49 L | **~₹412 L (3x, rising fast)** |
| Beverages | ₹9.22 L | ₹2.63 L | ₹2.21 L | ~₹7 L |

Mart has burned a full prior year's trade spend in four months. The ₹3.87 Cr headline actually
**understates the forward run-rate (~₹4.86 Cr)**. This is the part of the finding that deserves
management attention — not the classification, the **trajectory**.

---

## Overlaps — read before adding anything up

1. **This is not additive to the returns lens; it must be SUBTRACTED from it.** All ₹4.28 Cr of
   service credit notes sits inside the ₹56.40 Cr returns headline in [[returns-leakage]].
   Corrected: group returns **₹52.12 Cr**, Mart rate **13.4% → 12.1%**, Oil **6.1% → 5.8%**, group
   **8.3% → 7.7%**.
2. **[[finding-unlinked-credit-notes]]** — every service credit note is `BaseType = -1`, so this
   ₹4.28 Cr is **16.6% of that finding's ₹25.83 Cr**. Do not count both.
3. **[[finding-excess-returns-above-benchmark]]** — H17 sized ₹13.47 Cr from total returns per
   customer, which included this trade spend. That finding is overstated by the amounts below.
4. **[[finding-zepto-return-rate]] is materially wrong because of this.** Kiranakart/Zepto:
   **₹89.38 L of its ₹122.6 L of "returns" is trade spend**; actual goods returned is only ₹33.19 L.
   Zepto's real 12M goods-return rate is ~29%, not 107.9%. Still high, but a different problem with
   a different fix.
5. Other customers whose "return rate" is partly trade spend (Mart, 12M): Hands On Trade ₹52.54 L of
   ₹86.0 L · Chirag Enterprises ₹46.66 L of ₹139.8 L · Knowtable ₹54.98 L of ₹395.8 L · **Octavos
   ₹21.88 L of ₹21.88 L — this fully explains the "credit note with no sales" flagged in H15; it is
   a `DISCOUNT CLAIM ( JAN TO JUN-25 )`, not a mystery credit.**

## Actions

| # | Action | Owner | Value |
|---|---|---|---|
| 1 | Get a GST opinion on converting eligible post-sale discounts to s.15(3)(b) GST credit notes; add the discount clause to modern-trade and platform contracts; require invoice linkage on the credit note. Catch FY25-26 before the **30 Nov 2026** cut-off. | **CFO** (with Sales head for contracts) | **₹14.5 L/yr cash** |
| 2 | Assess whether e-com brand funding should instead be billed by the platform as a taxable promotional service with ITC to JIVO. | **CFO** | up to ₹47 L/yr |
| 3 | Open a budget line on `5500004 PROMOTIONAL DISCOUNT` and give it a named owner; it carries ₹2.10 Cr with no budget in any company. | **CFO / Sales head** | control |
| 4 | Populate `OBGT` for Mart — it currently has **zero** budget rows for any account. | **CFO / Accounts** | control |
| 5 | Require a customer claim reference in `NumAtCard` on every service credit note. Oil is 87% blank by value (₹1.29 Cr). | **Accounts** | control |
| 6 | **Exclude `ORIN."DocType"='S'` from every returns/return-rate KPI** and re-issue the returns lens numbers. Fix the reporting definition. | **IT / Accounts** | measurement |
| 7 | Explain Mart's 3x jump in trade spend (₹138 L full-year FY25-26 → ₹137 L in 4 months of FY26-27). This is the real exposure. | **Sales head** | ₹4.86 Cr run-rate |
| 8 | Review the ₹0.23 L credit note posted to asset account `11133263 SAMAN ADVANCE JWPL2831`. | **Accounts** | one document |

**Do not book ₹3.87 Cr as a saving.** It is a genuine, correctly-classified commercial cost of
selling through modern trade and q-commerce. The saving here is ₹14.5 lakh of recoverable GST; the
rest of the value of this finding is that it **corrects four other findings and the returns headline**.

Back-links: [[SAVINGS-MOC]] · [[returns-leakage]] · [[finding-unlinked-credit-notes]] ·
[[finding-excess-returns-above-benchmark]] · [[finding-zepto-return-rate]]
