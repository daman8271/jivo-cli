---
title: "Adversarial verification — Finding #1: A/P sub-ledger not reconciled (₹186.63 Cr claim)"
created: 2026-07-28
lens: verify-ap-subledger-not-reconciled
tags: [savings-audit, verification, adversarial]
---

# Adversarial verification — Finding #1 [[finding-ap-subledger-not-reconciled]]

Part of [[SAVINGS-MOC]]

**Claim under test** (from [[vendor-money-stuck]] H19): SAP Oil shows **₹292.57 Cr** of open A/P
invoices vs **₹105.94 Cr** of actual A/P ledger balance → **₹186.63 Cr** of invoices "flagged
unpaid that are already settled". Recorded as `kind: working-capital-release`,
`amount_inr: 1,866,319,544`.

**Verdict: REFUTED as money — CONFIRMED as arithmetic.**
The control gap is real and I reproduced it two independent ways (₹188.75 Cr, +1.1%).
But **₹0** of it is recoverable, releasable or saveable cash. Its `amount_inr` must be **0**.

Company: **JIVO_OIL_HANADB (Oil)**. All figures re-derived live 2026-07-28.
SAP go-live / opening-balance migration date = **2024-09-30**.

---

## Summary of the 12 re-derivation tests

| # | Test | Result | Effect on the claim |
|---|---|---|---|
| V1 | Reproduce the ₹292.57 Cr open-A/P figure | ✅ exact | claim's numerator holds |
| V2 | Reproduce the ₹105.94 Cr ledger figure | ✅ exact, but it is **credit-side only**; net A/P is ₹85.11 Cr | denominator is one-sided |
| V3 | Cross-check `OCRD."Balance"` against `JDT1` postings | ✅ matches to the rupee | ledger side is trustworthy |
| V4 | Re-derive gap **per vendor** (no cross-vendor netting) | **₹188.75 Cr** (+1.1% vs claim) | magnitude CONFIRMED |
| V5 | FX misread? `DocTotal` vs `DocTotalFC` on the 50 USD invoices | ✅ `DocTotal` is INR; rates 74–87 sane | not a currency error |
| V6 | Cancelled docs wrongly included? | ✅ 113 cancelled docs excluded; open set is `CANCELED='N'` only | not a cancellation error |
| V7 | Does the open set contain negative dues / contra rows? | ✅ zero negative-due rows | no sign error |
| V8 | Independent shape: SAP's own reconciliation columns `JDT1."BalDueCred"/"BalDueDeb"` | ₹292.57 Cr unreconciled invoice credits — **identical to the rupee** | strongest confirmation |
| V9 | Split the gap by era (go-live migration vs post-go-live) | ₹57.03 Cr / ₹235.54 Cr open; ₹1,908 Cr / ₹168.15 Cr offsetting debits | 30% of "phantom" is migration junk |
| V10 | Worked example AL GHURAIR (50% of the claimed gap) | migrated opening credit **₹1,775 Cr** + **$217 M** of same-day migrated "payments" — ~10× the company's whole annual purchase book | non-transactional migration rows |
| V11 | Has cash actually been lost? net vendor position | **−₹85.11 Cr (JIVO owes)** — no net overpayment anywhere | ₹0 to recover |
| V12 | Real cash consequence (double-pay exposure), Oil | **₹3.68 Cr** — already booked as separate finding #3 | would be double-counted |

---

## V1 — the ₹292.57 Cr numerator ✅ CONFIRMED exactly

```sql
SELECT COUNT(*) AS CNT,
       SUM("DocTotal") AS TOT_GROSS,
       SUM("DocTotal"-IFNULL("PaidToDate",0)) AS DUE_ALL,
       SUM(CASE WHEN ("DocTotal"-IFNULL("PaidToDate",0))<0
                THEN "DocTotal"-IFNULL("PaidToDate",0) ELSE 0 END) AS DUE_NEGONLY,
       MIN("DocDate") AS FIRSTD, MAX("DocDate") AS LASTD
FROM JIVO_OIL_HANADB.OPCH
WHERE "CANCELED"='N' AND "DocStatus"='O';
```

| CNT | Gross | Due | Negative-due rows | Range |
|---:|---:|---:|---:|---|
| 4,239 | ₹314.62 Cr | **₹292.57 Cr** | ₹0 | 2024-09-30 → 2026-07-25 |

Full OPCH population, for context:

```sql
SELECT "DocStatus","CANCELED", COUNT(*) AS CNT, SUM("DocTotal") AS TOT,
       SUM(IFNULL("PaidToDate",0)) AS PAID
FROM JIVO_OIL_HANADB.OPCH GROUP BY "DocStatus","CANCELED";
```

| DocStatus | CANCELED | CNT | Gross | Paid |
|---|---|---:|---:|---:|
| C | N | 11,468 | ₹620.31 Cr | ₹620.31 Cr (100%) |
| O | N | 4,239 | ₹314.62 Cr | ₹22.05 Cr (7%) |
| C | Y | 113 | ₹15.96 Cr | — (cancelled, excluded) |

**V6/V7 pass:** cancelled documents are excluded and there are no negative/contra dues
inflating the sum. The ₹292.57 Cr is a clean number.

---

## V5 — currency misread? ❌ not the explanation

```sql
SELECT "DocCur", COUNT(*) AS CNT, SUM("DocTotal") AS TOT_LC,
       SUM(IFNULL("DocTotalFC",0)) AS TOT_FC,
       SUM("DocTotal"-IFNULL("PaidToDate",0)) AS DUE_LC
FROM JIVO_OIL_HANADB.OPCH WHERE "CANCELED"='N' AND "DocStatus"='O'
GROUP BY "DocCur";
```

| Cur | Docs | Due (INR) | Share |
|---|---:|---:|---:|
| INR | 4,182 | ₹157.19 Cr | 54% |
| USD | 50 | **₹130.60 Cr** ($16.32 M) | 45% |
| AUD | 2 | ₹2.51 Cr | 1% |
| EUR | 5 | ₹2.28 Cr | 1% |

`DocTotal` is stored in **INR** and `DocTotalFC` in the foreign currency; implied rates
(74–87 INR/USD depending on invoice vintage) are correct. **No FX inflation.**
But note: **45% of the entire "open A/P" pool is 50 import invoices** — the finding is
overwhelmingly an *import-vendor* phenomenon, which the original lens did not say.

---

## V2 + V3 — the ₹105.94 Cr denominator ✅ correct number, ⚠️ wrong basis

```sql
SELECT "CardType", COUNT(*) AS CNT,
       SUM(CASE WHEN "Balance">0 THEN "Balance" ELSE 0 END) AS DR_TOT,
       SUM(CASE WHEN "Balance"<0 THEN -"Balance" ELSE 0 END) AS CR_TOT,
       SUM("Balance") AS NET_BAL
FROM JIVO_OIL_HANADB.OCRD GROUP BY "CardType";
```

| CardType | Partners | Debit | Credit | **Net** |
|---|---:|---:|---:|---:|
| S (suppliers) | 2,219 | ₹20.83 Cr | **₹105.94 Cr** | **−₹85.11 Cr** |
| C (customers) | 1,170 | ₹109.15 Cr | ₹4.05 Cr | +₹105.10 Cr |

Independent cross-check from a **different table** — rebuild every vendor's balance from raw
journal lines instead of trusting `OCRD."Balance"`:

```sql
SELECT SUM(x.LEDGER_NET) AS NET, SUM(CASE WHEN x.LEDGER_NET<0 THEN -x.LEDGER_NET ELSE 0 END) AS CR,
       SUM(CASE WHEN x.LEDGER_NET>0 THEN x.LEDGER_NET ELSE 0 END) AS DR, COUNT(*) AS NBP
FROM (SELECT j."ShortName" AS BP, SUM(IFNULL(j."Debit",0)-IFNULL(j."Credit",0)) AS LEDGER_NET
      FROM JIVO_OIL_HANADB.JDT1 j
      WHERE j."ShortName" IN (SELECT "CardCode" FROM JIVO_OIL_HANADB.OCRD WHERE "CardType"='S')
      GROUP BY j."ShortName") x;
```

→ NET **−₹85.11 Cr**, CR **₹105.94 Cr**, DR **₹20.83 Cr** across 1,525 posted vendors.
**Rupee-exact match with `OCRD."Balance"`.** The ledger side is sound.

⚠️ **But the claim's denominator is the credit side only.** It silently drops the ₹20.83 Cr of
vendors in debit. Depending on the basis chosen the "gap" is:

| Basis | Gap |
|---|---:|
| Open due − credit-balance total (the claim) | ₹186.63 Cr |
| Open due − **net** A/P position | ₹207.46 Cr |
| **Per-vendor, no cross-vendor netting (V4, most defensible)** | **₹188.75 Cr** |

⚠️ Second basis problem: **₹78.93 Cr of the ₹105.94 Cr "actual A/P" is intercompany** —
JIVO WELLNESS PVT LTD − HR / PB / DL / HARYANA branches plus JIVO MART. Genuine
**third-party** A/P in Oil is only **₹27.01 Cr**.

---

## V4 — per-vendor re-derivation ✅ magnitude CONFIRMED (₹188.75 Cr)

Different query shape: never net one vendor against another; compare each vendor's open
invoices to what its own ledger says is owed.

```sql
WITH op AS (
  SELECT "CardCode", SUM("DocTotal"-IFNULL("PaidToDate",0)) AS DUE
  FROM JIVO_OIL_HANADB.OPCH WHERE "CANCELED"='N' AND "DocStatus"='O' GROUP BY "CardCode"),
v AS (
  SELECT c."CardCode", c."Balance" AS BAL, IFNULL(op.DUE,0) AS DUE,
         CASE WHEN UPPER(c."CardName") LIKE '%JIVO%' THEN 'INTERCO' ELSE 'THIRD' END AS KIND
  FROM JIVO_OIL_HANADB.OCRD c LEFT JOIN op ON op."CardCode"=c."CardCode"
  WHERE c."CardType"='S')
SELECT KIND, COUNT(*) AS NV, SUM(DUE) AS OPEN_DUE,
       SUM(CASE WHEN BAL<0 THEN -BAL ELSE 0 END) AS LEDGER_CREDIT,
       SUM(GREATEST(0, DUE - GREATEST(0,-BAL))) AS GAP_OVERSTATED,
       SUM(GREATEST(0, GREATEST(0,-BAL) - DUE)) AS GAP_UNDERSTATED
FROM v GROUP BY KIND;
```

| Kind | Vendors | Open due | Ledger credit | **Gap (overstated)** | Gap (understated) |
|---|---:|---:|---:|---:|---:|
| THIRD party | 2,211 | ₹206.72 Cr | ₹27.01 Cr | **₹181.83 Cr** | ₹2.12 Cr |
| INTERCO (8 branches) | 8 | ₹85.85 Cr | ₹78.93 Cr | ₹6.92 Cr | ₹0 |
| **Total** | | **₹292.57 Cr** | **₹105.94 Cr** | **₹188.75 Cr** | ₹2.12 Cr |

**₹188.75 Cr vs the claimed ₹186.63 Cr = +1.1%.** (The claim's aggregate arithmetic equals
₹188.75 Cr − ₹2.12 Cr exactly.) **The magnitude of the control gap holds.**

Notable: the intercompany branch accounts are almost perfectly matched
(JIVO WELLNESS − HR: ledger −₹68.96 Cr vs open due ₹68.96 Cr, difference **₹750**), so the
"phantom" is *not* an intercompany artefact — it is concentrated in import vendors.

---

## V8 — independent shape: SAP's own reconciliation state ✅ rupee-exact

`JDT1."BalDueCred"/"BalDueDeb"` are SAP B1's internal-reconciliation residuals — a completely
different mechanism from `OPCH."DocStatus"`/`"PaidToDate"`.

```sql
SELECT j."TransType", COUNT(*) AS LINES_,
       SUM(IFNULL(j."BalDueCred",0)) AS UNREC_CR,
       SUM(IFNULL(j."BalDueDeb",0))  AS UNREC_DR
FROM JIVO_OIL_HANADB.JDT1 j
JOIN JIVO_OIL_HANADB.OCRD c ON c."CardCode"=j."ShortName" AND c."CardType"='S'
GROUP BY j."TransType";
```

| TransType | Lines | Unreconciled CREDIT | Unreconciled DEBIT |
|---|---:|---:|---:|
| 18 A/P invoice | 15,933 | **₹292.57 Cr** | — |
| 19 A/P credit note | 1,530 | — | ₹0.27 Cr |
| 24 incoming payment | 387 | ₹1.99 Cr | — |
| 30 journal entry | 5,794 | ₹1,866.83 Cr | ₹65.84 Cr |
| 46 outgoing payment | 10,244 | — | **₹2,010.18 Cr** |
| 321 internal recon | 42 | ₹0 | ₹0 |
| **Total** | 33,930 | **₹2,161.39 Cr** | **₹2,076.29 Cr** |

Net = **−₹85.11 Cr**, i.e. exactly the vendor ledger. Two things follow:

1. **TransType 18 unreconciled credit = ₹292.57 Cr, identical to the rupee** to the OPCH-derived
   figure. The open-A/P number is beyond dispute.
2. **The true scale of non-reconciliation is ₹2,076 Cr, not ₹186.63 Cr** — the original lens
   *understated* the control problem by 11×, because it measured the gap net of offsets rather
   than measuring unapplied documents.

🔁 **This also overturns the original lens's H9 kill.** H9 found ₹2,010 Cr via
`OVPM."OpenBal"` and retracted it because "`OpenBal` equals `DocTotal` on every row". That is
not a broken field — `OVPM."OpenBal"` = ₹2,010.18 Cr is **identical** to SAP's own
`BalDueDeb` for TransType 46. It equals `DocTotal` on every row because **not one outgoing
payment in the Oil book has ever been reconciled.** H9 was a true positive killed for the
wrong reason.

---

## V9 + V10 — 30% of the "phantom" is go-live migration junk ⚠️ material caveat

```sql
SELECT BUCKET, COUNT(*) AS CNT, SUM(DUE) AS DUE_TOT FROM (
  SELECT CASE WHEN "DocDate"='2024-09-30' THEN 'A_GOLIVE_MIGRATION'
              WHEN "DocDate"<'2025-07-28' THEN 'B_12mo_plus'
              WHEN "DocDate"<'2026-01-28' THEN 'C_6to12mo'
              WHEN "DocDate"<'2026-04-28' THEN 'D_3to6mo'
              ELSE 'E_under3mo' END AS BUCKET,
         "DocTotal"-IFNULL("PaidToDate",0) AS DUE
  FROM JIVO_OIL_HANADB.OPCH WHERE "CANCELED"='N' AND "DocStatus"='O')
GROUP BY BUCKET;
```

| Bucket | Docs | Open due |
|---|---:|---:|
| A — dated 2024-09-30 (migrated opening items) | 268 | **₹57.03 Cr** |
| B — >12 months old | 1,358 | ₹114.84 Cr |
| C — 6–12 months | 978 | ₹48.73 Cr |
| D — 3–6 months | 747 | ₹38.57 Cr |
| E — under 3 months (plausibly genuinely unpaid) | 888 | ₹33.40 Cr |

Splitting the **V4 gap** the same way:

```sql
WITH op AS (SELECT "CardCode", SUM("DocTotal"-IFNULL("PaidToDate",0)) AS DUE,
       SUM(CASE WHEN "DocDate"='2024-09-30' THEN "DocTotal"-IFNULL("PaidToDate",0) ELSE 0 END) AS DUE_MIG
  FROM JIVO_OIL_HANADB.OPCH WHERE "CANCELED"='N' AND "DocStatus"='O' GROUP BY "CardCode"),
v AS (SELECT IFNULL(op.DUE,0) AS DUE, IFNULL(op.DUE_MIG,0) AS DUE_MIG,
        GREATEST(0, IFNULL(op.DUE,0) - GREATEST(0,-c."Balance")) AS GAP
      FROM JIVO_OIL_HANADB.OCRD c LEFT JOIN op ON op."CardCode"=c."CardCode" WHERE c."CardType"='S')
SELECT COUNT(*) AS NV, SUM(GAP) AS GAP_TOT, SUM(LEAST(GAP,DUE_MIG)) AS GAP_MIGRATED,
       SUM(GAP-LEAST(GAP,DUE_MIG)) AS GAP_POSTGOLIVE FROM v WHERE GAP>0;
```

| | ₹ |
|---|---:|
| Gap total (303 vendors) | ₹188.75 Cr |
| …from **migrated** opening invoices | **₹56.76 Cr (30%)** |
| …from post-go-live invoices | ₹131.98 Cr (70%) |

And the offsetting unapplied debits by era:

| Era | Unreconciled invoice credits | Unapplied debits (payments + JE + CN) |
|---|---:|---:|
| Go-live 2024-09-30 | ₹1,907.27 Cr | ₹1,908.14 Cr |
| Post go-live | ₹254.13 Cr | ₹168.15 Cr |

### Worked example — AL GHURAIR RESOURCES (`VENDA000724`), 50% of the whole claimed gap

```sql
SELECT j."TransType", COUNT(*) AS CNT, SUM(IFNULL(j."Debit",0)) AS DR,
       SUM(IFNULL(j."Credit",0)) AS CR, MIN(j."RefDate") AS F, MAX(j."RefDate") AS L
FROM JIVO_OIL_HANADB.JDT1 j WHERE j."ShortName"='VENDA000724' GROUP BY j."TransType";
```

| TransType | N | Debit | Credit |
|---|---:|---:|---:|
| 18 invoices | 29 | — | ₹95.91 Cr |
| 30 journal | 19 | ₹33.69 Cr | **₹1,775.32 Cr** |
| 46 payments | 17 | **₹1,837.83 Cr** | — |

Ledger balance today: **₹2.35 L debit**. Open invoices in SAP: **₹93.70 Cr**.

The 2024-09-30 rows are the migration: one JE credit of **₹1,775.18 Cr** ("Opening Balance as
30/09/2024") plus **seven** same-day outgoing payments totalling **₹1,796.96 Cr / US$217.7 M**.
JIVO's entire annual purchase book is ~₹500 Cr (~$60 M) — **$217 M in a single day is not a
transaction, it is a legacy-ledger dump.** Row-level corruption is visible too: payment
TransId 220625 (2026-07-01) carries Debit **₹443.40** against FCDebit **$4,434,009** — the INR
and USD amounts are transposed by 10,000×; invoice 625113211 has DocTotal ₹21,509 against
DocTotalFC $215,092,950. A "RETIFICATION OF LEDGER" JE sits alongside it.

Post-go-live the vendor is however genuinely unreconciled and the finder's diagnosis is right:
₹41.18 Cr of Nov-2024→Nov-2025 invoices sit "open" against ₹40.87 Cr of on-account payments
made over the same window. **Paid, never matched.**

---

## V11 — is any of it money? ❌ NO

Three independent reasons the ₹186.63 Cr is not recoverable, releasable, or saveable:

1. **No cash has left in excess.** Net vendor position is **−₹85.11 Cr (JIVO owes)**, derived
   twice (V2, V3). There is no ₹186.63 Cr overpayment sitting anywhere to claw back. The only
   debit balances are ₹20.83 Cr of live advances, already covered by other findings.
2. **Internal reconciliation is balance-neutral by construction.** Matching an invoice credit
   to a payment debit changes no account balance, no bank position, no working capital. The
   balance sheet already carries ₹85.11 Cr; the ₹292.57 Cr never appeared on it. The
   ₹186.63 Cr is an *open-item hygiene* metric, not a stock of value.
3. **30% of it (₹56.76 Cr) has no commercial content at all** — it is 2024-09-30 migration
   residue (V9/V10), and its ₹1,908 Cr of offsetting "payments" are demonstrably synthetic.

**Verdict: ₹0.**

---

## V12 — the real cash number, and the double-count risk

The only genuine cash consequence is paying an invoice twice when the vendor already holds an
advance. Re-derived independently:

```sql
WITH op AS (SELECT "CardCode", SUM("DocTotal"-IFNULL("PaidToDate",0)) AS DUE
  FROM JIVO_OIL_HANADB.OPCH WHERE "CANCELED"='N' AND "DocStatus"='O'
    AND ("DocTotal"-IFNULL("PaidToDate",0))>0 GROUP BY "CardCode")
SELECT COUNT(*) AS NV, SUM(LEAST(c."Balance", op.DUE)) AS DOUBLEPAY_EXPOSURE
FROM JIVO_OIL_HANADB.OCRD c JOIN op ON op."CardCode"=c."CardCode"
LEFT JOIN JIVO_OIL_HANADB.OCRG g ON g."GroupCode"=c."GroupCode"
WHERE c."CardType"='S' AND c."Balance">0 AND IFNULL(g."GroupName",'')<>'FIXED ASSETS';
```

→ 81 vendors, **₹3.68 Cr** (Oil). Matches the original lens's H15 Oil figure of ₹3,68,21,596
exactly; with Mart ₹0.33 Cr + Beverages ₹0.04 Cr it is the **₹4.05 Cr already booked as
[[finding-unapplied-advances-vs-open-bills]]**. Assigning any ₹ to finding #1 therefore
**double-counts finding #3**.

---

## Root cause ✅ CONFIRMED, and it is worse than stated

```sql
SELECT SCHEMA_NAME, TABLE_NAME, RECORD_COUNT FROM SYS.M_TABLES
WHERE SCHEMA_NAME IN ('JIVO_OIL_HANADB','JIVO_MART_HANADB','JIVO_BEVERAGES_HANADB')
  AND TABLE_NAME IN ('ODPO','ODPI','OITR','ITR1');
```

| Schema | ODPO | ODPI | OITR | ITR1 |
|---|---:|---:|---:|---:|
| Oil | 0 | 0 | 29,016 | 119,246 |
| Mart | 0 | 0 | 13,064 | 53,516 |
| Beverages | 0 | 0 | 5,924 | 19,971 |

Down-payment documents are unused in all three companies — **the stated root cause holds.**
Reconciliation *is* being run (OITR/ITR1 are populated) but never on outgoing payments
(TransType 46 unapplied = 100% of value).

The same disease in the other two companies (not part of this finding, flagged for the MOC):

| Company | Open A/P per SAP | True A/P (credit balances) |
|---|---:|---:|
| Oil | ₹292.57 Cr | ₹105.94 Cr |
| **Mart** | **₹199.58 Cr** | ₹30.35 Cr |
| Beverages | ₹3.43 Cr | ₹2.48 Cr |

---

## Verdict

| | |
|---|---|
| **Arithmetic** | ✅ CONFIRMED — independently re-derived at **₹188.75 Cr** (+1.1%); ₹292.57 Cr reproduced rupee-exact from `JDT1."BalDueCred"` |
| **Diagnosis** | ✅ CONFIRMED — advances/payments booked on-account and never internally reconciled; ODPO/ODPI empty |
| **Money** | ❌ **REFUTED — ₹0.** Not recoverable, not releasable, not a working-capital release |
| **Recorded `amount_inr`** | must be **0** (currently 1,866,319,544 with `kind: working-capital-release`) |
| **Keep as** | a **non-monetary control observation** — highest-priority A/P hygiene fix |

### Corrections to fold back into [[vendor-money-stuck]]

1. `kind` should be `control-risk`, not `working-capital-release`; `amount_inr` → 0.
   (The finding's own `action` text already says "Do not add to savings totals" — the
   structured record contradicts it.)
2. Comparison base: ₹105.94 Cr is credit-balances-only. State the **net ₹85.11 Cr**, and that
   ₹78.93 Cr of it is intercompany branch — genuine third-party A/P is **₹27.01 Cr**.
3. Disclose that **₹56.76 Cr (30%)** of the gap is 2024-09-30 migration residue, and that
   **45% of the open pool is 50 import invoices**, ₹93.70 Cr of them one vendor.
4. **Un-kill H9.** `OVPM."OpenBal"` ₹2,010 Cr is a genuine unapplied residual, equal to SAP's
   own `BalDueDeb`. The true non-reconciliation surface is **₹2,076 Cr**, 11× the headline.
5. Add the AL GHURAIR row-level corruption (INR/USD transposed 10,000×) as a data-integrity
   item for IT/SAP partner.
