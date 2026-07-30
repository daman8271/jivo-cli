---
title: "GST ITC reversals ₹71.46 L — the number is exact to the rupee, the story isn't: nothing is recoverable, and the real ₹52.10 L is sitting frozen in a different account"
created: 2026-07-29
verdict: REVISED
amount_verified_inr: 0
kind: control-observation
tags: [savings-audit, finding]
---

# GST ITC reversals — REVISED: ₹71,45,769.71 confirmed as a cost, ₹0 bankable. Live exposure found instead: ₹52.10 L dead ITC asset + ₹1.41 Cr of input credit taken from suppliers with no GSTIN in the ERP

Part of [[SAVINGS-MOC]] · Evidence: [[expense-outliers]]

## What a CFO needs to know

JIVO Oil charged **₹71,45,769.71 to "GST EXPENSE/INELIGIBLE CREDIT" (account 5660008) in FY25-26** — input tax
credit the company had booked, then had to give back. The sweep's figure of ₹71,45,770 is right **to the rupee**,
and it ties exactly to the account's ledger balance. Everything after that is wrong.

**It is not ₹71.46 lakh a year of recoverable money.** Three separate things are stacked in that one number, and
none of them can be collected:

1. **₹51,53,547 of GSTR-9 annual-return reversals.** These are credits written off when the annual return was
   filed. The FY24-25 slice (₹43,10,011) was reversed on 30-Jun-2025; the last date to re-claim any FY24-25
   credit was 30-Nov-2025. That door is shut. The credits are legally extinguished.
2. **₹10,55,433 of DRC-03 reversals on goods physically lost** — two consignments lost in transit and one loss
   on Black Olives. Section 17(5)(h) *requires* this reversal when goods are lost or destroyed. It is not a
   process failure and no tax control prevents it. If anyone owes JIVO here it is the **transporter or the
   insurer**, not the tax department.
3. **₹8,84,804 of GST audit demands for FY2020-21 to FY2023-24**, plus **₹51,986 paid in cash on 02-Feb-2026**.
   These are settled historical assessments from years that pre-date the SAP go-live entirely. One-off. Closed.

**The headline claim — "half from suppliers who never filed" — is not supported by a single rupee in the books.**
All sixteen journal lines credit only the aggregate control accounts (IGST / CGST / SGST / CESS CREDIT LEDGER).
There is no vendor, no CardCode, no sub-ledger on any of them. A GSTR-9 reversal equally covers blocked credits
under s.17(5), proportionate reversals under Rules 42/43, the 180-day non-payment rule, and plain book-vs-GSTR-3B
differences. Nothing in SAP tells you which. You cannot send a recovery letter to a control account.

**And there is nothing to stop this year, either.** FY26-27 (01-Apr-2026 to today) has **zero** entries in this
account. The next annual-return true-up will not land until the FY25-26 GSTR-9 is filed around December 2026.

So on the money question the answer is **₹0 bankable**. But the search turned up three things that matter more
than the saving that isn't there:

- **₹52,09,823 is sitting frozen in account 2131019, "GST INPUT UNCLAIMED A/C (2A)".** This is the account that
  actually *is* the non-filing-supplier pot — ITC JIVO paid its suppliers but could never claim because it never
  showed up in GSTR-2A. It was migrated in as a single opening line on 30-Sep-2024 and **has not moved once in
  22 months**. Because it pre-dates October 2024, the statutory re-claim window closed on 30-Nov-2025. This is
  almost certainly a **dead asset that must be written off** — a future ₹52.10 L hit to profit, not a saving.
  It is the same shape as [[finding-off-spec-olive-oil]]: an asset on the balance sheet that isn't there.
- **The CGST and SGST credit ledgers in the books are NEGATIVE by ₹5,14,191 each — ₹10,28,381 combined.** An
  electronic credit ledger physically cannot go below zero on the GST portal. So ₹10.28 L of FY25-26 reversals
  were posted against balances that did not exist. Either the FY25-26 charge is overstated by that much, or the
  books are ₹10.28 L out of step with the portal. Both need fixing before the next return.
- **₹1,40,73,041 of input GST was claimed in FY25-26 from four suppliers who have no GSTIN recorded anywhere in
  the ERP** — 45 of those 54 invoices, and ₹1,40,23,559 of the credit, from **VAISHNODEVI OIL SEEDS PROCESSING
  INDUSTRIES** (Gujarat), against ₹29.45 Cr of purchases. That is the live exposure, and it is exactly the risk
  the original finding *described* but could not locate. 1,683 of 4,650 vendor addresses (36%) have a blank
  GSTIN and an unset GST type, which is precisely why no one can reconcile ITC by vendor.

For scale: FY25-26 gross input tax booked was **₹24.60 Cr**, so the ₹71.46 L reversal is **2.9%** of ITC availed
— high enough to be worth fixing, nowhere near a crisis.

## Verdict

| | |
|---|---|
| Claimed | ₹71,45,770 / year, annual-recurring saving, "half from non-filing suppliers" |
| Re-derived FY25-26 charge | **₹71,45,769.71** — exact match, ties to account balance to the paisa |
| Recoverable from suppliers | **₹0** — no vendor attribution exists on any of the 16 lines |
| Avoidable in FY26-27 | **₹0 booked YTD**; next true-up ~Dec-2026 |
| **Bankable amount** | **₹0** |
| Dead ITC asset found (write-off risk) | **₹52,09,823** (account 2131019, frozen 22 months) |
| Books-vs-portal break found | **₹10,28,381** (CGST + SGST credit ledgers negative) |
| Unvalidatable input credit found | **₹1,40,73,041** (4 vendors, no GSTIN in ERP) |
| Kind | control observation + asset-quality red flag, **not** a recurring saving |

## Component verdicts

### C1 · "GST ITC reversals ₹71.46 L/yr — half from suppliers who never filed" → REVISED, ₹0 bankable

**Arithmetic: CONFIRMED to the rupee.** Sixteen lines, FY25-26, decomposing as:

| Bucket | ₹ | Lines |
|---|---:|---:|
| GSTR-9 annual-return reversals (₹43,10,011.22 on 30-Jun-2025 for FY24-25; ₹7,88,847.81 HR + ₹54,687.68 DL on 01-Mar-2026) | 51,53,546.71 | 5 |
| DRC-03 — goods lost in transit ₹2,13,835 + ₹5,16,262; loss on Black Olive ₹3,25,336 | 10,55,433.00 | 3 |
| GST audit demands FY2020-21→FY2023-24, settled via credit ledger | 8,84,804.00 | 6 |
| Same audit demands paid in cash 02-Feb-2026 (Indian Bank CC) | 51,986.00 | 2 |
| **Total** | **71,45,769.71** | **16** |

This ties **exactly** to `OACT."CurrTotal"` for 5660008 = 7,145,769.71, because the FY24-25 balance was fully
closed out on 31-Mar-2025.

**Money verdict: ₹0.** Killed on four independent grounds:

- *No vendor attribution.* Every one of the five GSTR-9 lines credits only 2139101/2139102/2139103/2139104
  (IGST/CGST/SGST/CESS CREDIT LEDGER). Zero CardCodes. The "non-filing supplier" story has no evidentiary basis
  in SAP.
- *Statutory window closed.* FY24-25 credits reversed 30-Jun-2025 cannot be re-availed after 30-Nov-2025.
- *DRC-03 is mandatory, not preventable.* s.17(5)(h) forces reversal on goods lost/destroyed. Black Olive is a
  genuine traded item (FG0000284 / FG0000190 SLICED OXIDIZED BLACK OLIVES) — a real physical loss, unrelated to
  RM0000052 in [[finding-off-spec-olive-oil]] (that item was never purchased, so no ITC ever existed on it).
- *Audit demands are historic and closed.* FY2020-21 to FY2023-24 pre-dates the 30-Sep-2024 go-live entirely.

**Not annual-recurring.** Prior year comparison: FY24-25 charged ₹48,04,300.60 to the same account, but
₹39,10,178.00 of that was the migration opening balance and the rest was ten DRC entries — a different mix
entirely. FY26-27 YTD: **zero entries**.

**New defect found — apparent double booking of ₹51,986.** TransIds 181706 / 181707 (02-Feb-2026, outgoing
payment) debit 5660008 by ₹42,976 and ₹9,010 out of the Indian Bank CC account. TransIds 200235 / 200236
(01-Mar-2026) debit 5660008 by the *identical* ₹42,976 and ₹9,010 against the CGST/SGST credit ledgers, with the
same "for audit period 2020-21 to 2023-24" memo. The same demand appears to be expensed twice — once paid in
cash, once reversed from credit. This is consistent with the negative credit-ledger balances below.

### Key SQL

Re-derivation of the charge and its counter-accounts:

```sql
SELECT j."RefDate", j."TransId", j."Account", a."AcctName",
       j."Debit", j."Credit", j."LineMemo"
FROM   JIVO_OIL_HANADB.JDT1 j
LEFT JOIN JIVO_OIL_HANADB.OACT a ON a."AcctCode" = j."Account"
WHERE  j."TransId" IN (
         SELECT "TransId" FROM JIVO_OIL_HANADB.JDT1 WHERE "Account" = '5660008')
ORDER BY j."RefDate", j."TransId", j."Line_ID";
-- 16 FY25-26 lines on 5660008 = 7,145,769.71; every credit lands on 2139101/2/3/4, never on a vendor
```

The frozen unclaimed-2A asset:

```sql
SELECT YEAR("RefDate") AS "Y", MONTH("RefDate") AS "M",
       COUNT(*) AS "N", SUM("Debit") AS "DR", SUM("Credit") AS "CR"
FROM   JIVO_OIL_HANADB.JDT1
WHERE  "Account" = '2131019'          -- GST INPUT UNCLAIMED A/C (2A)
GROUP BY YEAR("RefDate"), MONTH("RefDate") ORDER BY 1,2;
-- one debit of 5,209,823.05 on 2024-09-30 (migration line "21230004"); untouched since
```

The negative credit ledgers:

```sql
SELECT j."Account", a."AcctName", YEAR(j."RefDate") AS "Y",
       SUM(j."Debit") AS "DR", SUM(j."Credit") AS "CR"
FROM   JIVO_OIL_HANADB.JDT1 j
LEFT JOIN JIVO_OIL_HANADB.OACT a ON a."AcctCode" = j."Account"
WHERE  j."Account" IN ('2139101','2139102','2139103','2139104')
GROUP BY j."Account", a."AcctName", YEAR(j."RefDate") ORDER BY 1,3;
-- 2139102 CGST: opened 9,058,934.21, exhausted in 2025, 2026 credits 514,190.67 -> balance -514,190.67
-- 2139103 SGST: opened 5,873,941.03, exhausted in 2025, 2026 credits 514,190.67 -> balance -514,190.67
```

Input credit taken from suppliers with no GSTIN anywhere in the ERP:

```sql
SELECT p."CardCode", MAX(p."CardName") AS "NAME", COUNT(*) AS "INVS",
       SUM(p."VatSum") AS "GST", SUM(p."DocTotal") AS "GROSS"
FROM   JIVO_OIL_HANADB.OPCH p
WHERE  p."CANCELED" = 'N'
  AND  p."DocDate" >= '2025-04-01' AND p."DocDate" < '2026-04-01'
  AND  p."VatSum" > 0
  AND  NOT EXISTS (SELECT 1 FROM JIVO_OIL_HANADB.CRD1 a
                   WHERE a."CardCode" = p."CardCode"
                     AND LENGTH(TRIM(COALESCE(a."GSTRegnNo",''))) = 15)
GROUP BY p."CardCode" ORDER BY SUM(p."VatSum") DESC;
-- 4 vendors / 54 invoices / GST 14,073,041.07 on gross 294,525,788
-- VENDA000950 VAISHNODEVI OIL SEEDS PROCESSING INDUSTRIES  45 inv  14,023,559.25
-- VENDA001101 INFO EDGE (INDIA) LTD                         3 inv      34,560.00
-- VENDA000954 ADMEN                                         5 inv       9,521.82
-- VENDA001094 UFLEX LIMITED                                 1 inv       5,400.00
```

Scale check (why 2.9% is the right denominator):

```sql
SELECT SUM("Debit") AS "DR", SUM("Credit") AS "CR"
FROM   JIVO_OIL_HANADB.JDT1
WHERE  "Account" BETWEEN '2131001' AND '2131018'
  AND  "RefDate" >= '2025-04-01' AND "RefDate" < '2026-04-01';
-- gross input tax booked FY25-26 = 245,954,191.12 (₹24.60 Cr); reversal = 2.9% of it
```

## Traps checked

- **Capex (Trap 1).** Two large FY25-26 ITC reversals deliberately bypass 5660008: TransId 168658 (12-Nov-2025)
  capitalised ₹41,04,000 of CGST+SGST into `1208001 ACQUISITION CLEARING ACCOUNT`, and TransId 168756
  (13-Nov-2025) moved ₹2,94,02,249.82 of IGST+CGST+SGST to `1110109 JIVO WELLNESS BEVERAGES INTERNAL`. Neither
  is in my number. The ₹41.04 L is worth one question to the tax advisor — GST on **plant & machinery** is
  eligible; only civil works / immovable property is blocked u/s 17(5)(c)/(d) — but on the evidence available it
  is capex treatment, not leakage.
- **Intercompany (Trap 2).** The ₹2.94 Cr above is a group-internal ITC transfer to the Beverages company; it
  mirrors and nets to zero at group level. Not leakage.
- **Trade-spend credit notes (Trap 4/8).** No overlap — that finding is *output* tax on ORIN `DocType` 'S'
  service credit notes; this is *input* tax on the electronic credit ledger. Different tax, different direction.
- **Go-live migration (Trap 6).** Correctly applied: the ₹39,10,178 opening balance on 5660008 and the
  ₹52,09,823 on 2131019 are both 30-Sep-2024 migration lines, excluded from the FY25-26 charge and flagged as
  legacy, not fresh leakage.
- **Cost of capital (Trap 7).** Deliberately **not** applied. This is a P&L expense, not working capital — there
  is no balance to release, so no 8.25% overlay. (Illustration only, explicitly not banked: if the ₹52.10 L dead
  ITC were somehow recovered, the carry saving would be ₹4.30 L/yr.)

## Overlaps

- [[finding-hs-filling-advance]] — that finding already carries the **₹51.3 L of GST input credit unclaimable
  until HS Filling issues an invoice**. That is a *different* ₹51 L from this note's ₹51.54 L GSTR-9 slice and
  the ₹52.10 L unclaimed-2A balance. Three similar-sized GST numbers, three separate causes — **do not add them
  together.**
- [[finding-off-spec-olive-oil]] — checked and distinct. The ₹3,25,336 DRC-03 "loss on Black Olive" relates to
  real traded stock (FG0000284 / FG0000190); RM0000052 was never purchased so no ITC ever attached to it.
- [[finding-trade-spend-as-credit-notes]] — GST, but output-side. No shared rupees.
- [[finding-cc-interest-conversion-rate]] — the 8.25% multiplier is deliberately not applied here (see Trap 7).

## Action

**₹0 to bank. Four things to do instead, none of which is a savings claim:**

1. **Fill in the vendor-master GSTIN, starting with the four exposed suppliers** — VENDA000950 Vaishnodevi Oil
   Seeds (₹1.40 Cr of input credit, ₹29.45 Cr of purchases, no GSTIN on either address), plus Info Edge, ADMEN,
   UFLEX. Then close the remaining 1,683 blank vendor addresses. Until `CRD1."GSTRegnNo"` is populated, no
   GSTR-2B match by vendor is even possible. *Owner: Accounts Head + SAP master-data owner. Cost: days of data
   entry.*
2. **Get a written position on the ₹52,09,823 in account 2131019** before the FY25-26 audit. If it is
   time-barred, it must be written off now, not carried a third year. *Owner: CFO with the GST consultant.*
3. **Reconcile the books' credit ledgers to the portal's electronic credit ledger.** CGST and SGST are negative
   by ₹5,14,191 each. Confirm whether the ₹42,976 + ₹9,010 audit demands were booked twice (cash on 02-Feb-2026
   and again from credit on 01-Mar-2026). *Owner: Accounts Head, before the next GSTR-3B.*
4. **Make GSTR-2B match a payment gate.** No vendor payment released until that vendor's invoice appears in 2B.
   This is the only forward-looking lever, and its value is real but unquantifiable from SAP — the addressable
   base is the GSTR-9 slice, which ran ₹43.10 L for FY24-25 and ₹8.44 L in-year for FY25-26. **Deliberately not
   banked**, because nothing in the ledger says how much of it was 2B mismatch versus blocked credits or Rule 42
   reversals. Re-measure after the FY25-26 GSTR-9 is filed (~Dec-2026), by which time — if step 1 is done —
   the reversal *will* be attributable by vendor and a real recovery number can be put on it.
