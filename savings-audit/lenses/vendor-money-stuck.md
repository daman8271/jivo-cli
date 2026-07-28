---
title: "Lens — Money Sitting With Suppliers (vendor-money-stuck)"
created: 2026-07-28
lens: vendor-money-stuck
tags: [savings-audit]
---

# Lens — Money Sitting With Suppliers

Part of [[SAVINGS-MOC]]

**Scope:** advances, overpayments, deposits and unadjusted balances sitting on the *supplier* side of the books, across all three companies (`JIVO_OIL_HANADB`, `JIVO_MART_HANADB`, `JIVO_BEVERAGES_HANADB`).
**Data:** direct read-only HANA SQL against the live SAP B1 core tables. **20 hypotheses tested, 8 killed.**
**Sign convention:** `OCRD."Balance"` positive = **DEBIT** = the vendor holds JIVO's money (advance / overpayment). Negative = **CREDIT** = JIVO owes them.

---

## Headline

| # | Finding | ₹ | Class | Conf. |
|---|---|---|---|---|
| 1 | [[finding-alo-logistics-unrecovered-claims]] — transporter debit notes never collected | **23.41 L** | one-time recovery | high |
| 2 | [[finding-dormant-vendor-advances]] — 11 more dead advances | **26.53 L** | one-time recovery | high |
| 3 | [[finding-unapplied-advances-vs-open-bills]] — advances held while the same vendor's bills sit "open" | **4.05 Cr** | working capital | high |
| 4 | [[finding-ap-subledger-not-reconciled]] — SAP shows ₹292.57 Cr payable, the ledger says ₹105.94 Cr | **186.63 Cr phantom** | control risk | high |
| 5 | [[finding-hs-filling-advance]] — ₹2.4 Cr with a co-packer, zero invoices ever | **2.40 Cr** | working capital | high |
| 6 | [[finding-cross-company-vendor-netting]] — same vendor debit in one company, credit in another | **42.58 L** | working capital | medium |
| 7 | [[finding-vendor-customer-netting]] — parties who are both supplier and customer | **33.48 L** | working capital | medium |
| 8 | [[finding-stale-security-deposits]] — deposits untouched since SAP go-live | **32.29 L** | working capital | medium |
| 9 | [[finding-mangla-related-party-advances]] — ₹13.16 Cr with two individuals (capex) | **13.16 Cr** | working capital | low |

---

## H1 — Total DEBIT balances on supplier partners  ✅ CONFIRMED

```sql
SELECT "CardType", COUNT(*) AS N_PARTNERS,
       SUM(CASE WHEN "Balance">0 THEN 1 ELSE 0 END) AS N_DEBIT,
       SUM(CASE WHEN "Balance">0 THEN "Balance" ELSE 0 END) AS DEBIT_TOTAL,
       SUM(CASE WHEN "Balance"<0 THEN "Balance" ELSE 0 END) AS CREDIT_TOTAL
FROM <SCHEMA>.OCRD GROUP BY "CardType";
```

| Company | Vendors in debit | Debit total | True payable (credit) |
|---|---:|---:|---:|
| Oil | 167 | ₹20.83 Cr | ₹105.94 Cr |
| Mart | 35 | ₹72.05 L | ₹30.35 Cr |
| Beverages | 33 | ₹2.71 Cr | ₹2.48 Cr |
| **Total** | **235** | **₹24.26 Cr** | |

**Verdict: ₹24.26 Cr of JIVO's cash is parked on the vendor side.** This is the gross pool; the rest of the lens carves out how much is genuinely recoverable versus live trade advance.

Segmented by vendor group (Oil):

| Group | N | Debit |
|---|---:|---:|
| FIXED ASSETS | 13 | ₹13.44 Cr |
| PURCHASE OIL | 16 | ₹5.17 Cr |
| SERVICE | 70 | ₹1.45 Cr |
| PURCHASE | 21 | ₹35.50 L |
| TRANSPORTER | 8 | ₹18.88 L |
| STAFF VENDOR | 28 | ₹16.90 L |

---

## H2 — Dead advances: debit balance + no purchasing activity  ✅ CONFIRMED

Aged by last non-cancelled purchase invoice (Oil):

```sql
WITH v AS (SELECT c."CardCode", c."Balance",
  (SELECT MAX(p."DocDate") FROM JIVO_OIL_HANADB.OPCH p
    WHERE p."CardCode"=c."CardCode" AND p."CANCELED"='N') AS LAST_PI
  FROM JIVO_OIL_HANADB.OCRD c WHERE c."CardType"='S' AND c."Balance">0)
SELECT CASE WHEN LAST_PI IS NULL THEN 'A_never_purchased'
            WHEN LAST_PI < '2025-07-28' THEN 'C_no_PI_12mo+'
            WHEN LAST_PI < '2026-01-28' THEN 'D_no_PI_6-12mo'
            ELSE 'E_active' END AS BUCKET,
       COUNT(*) AS N, SUM("Balance") AS DEBIT_TOTAL
FROM v GROUP BY 1;
```

| Bucket | N | Debit |
|---|---:|---:|
| never purchased | 44 | ₹2.67 Cr |
| no PI 12–24 mo | 24 | ₹16.89 L |
| no PI 6–12 mo | 21 | ₹18.38 L |
| active last 6 mo | 78 | ₹17.81 Cr |

⚠️ **Caveat that changed the answer:** most "never purchased" vendors have a *very recent payment* (RAHUL MANGLA paid 2026-07-20, WILLUS 2026-07-02, SERVOKON 2026-07-20, AGGARWAL 2026-07-27) — these are **live advances against work in progress, not dead money**. Tightened the test to require dormancy on *both* sides:

```sql
WHERE (LAST_PI IS NULL OR LAST_PI < '2025-07-28')     -- no bill in 12 months
  AND (LAST_PAY IS NULL OR LAST_PAY < '2026-01-28')   -- no payment in 6 months
  AND "Balance" >= 50000
  AND vendor group <> 'FIXED ASSETS'
```

| Company | N | Recoverable |
|---|---:|---:|
| Oil | 7 | ₹22.31 L |
| Mart | 3 | ₹25.96 L |
| Beverages | 2 | ₹1.67 L |
| **Total** | **12** | **₹49.94 L** |

Detail:

| Co | Vendor | Group | Balance | Last bill | Last payment |
|---|---|---|---:|---|---|
| MART | ALO LOGISTICS LLP | SERVICE | ₹23,40,991 | never | never |
| OIL | AGILENT TECHNOLOGIES INDIA | PURCHASE | ₹11,15,100 | never | 2026-01-08 |
| OIL | VIJAY INDUSTRIES | PURCHASE | ₹4,21,402 | never | never |
| MART | GODAMWALE TRADING & LOGISTICS | SERVICE | ₹1,92,543 | 2025-04-30 | 2025-04-09 |
| OIL | RAMA SALES | SERVICE | ₹1,76,960 | never | 2024-09-30 |
| OIL | JIVO WELLNESS (AKAL INFOSYS) | PURCHASE | ₹1,52,855 | never | never |
| OIL | BHARAT ORGANICS & DAIRY | PURCHASE | ₹1,50,574 | 2025-03-31 | 2024-11-08 |
| OIL | KS AFFINITY PVT LTD | SERVICE | ₹1,07,902 | never | 2024-09-30 |
| OIL | JASRA & JASRA LAW OFFICES | SERVICE | ₹1,06,000 | never | 2025-12-09 |
| BEV | GAGANDEEP SINGH | SERVICE | ₹1,00,000 | never | 2025-05-06 |
| BEV | BONUS PAYABLE | SERVICE | ₹66,748 | 2024-10-26 | 2025-07-30 |
| MART | AJANTA SOYA LIMITED | PURCHASE | ₹62,428 | 2025-02-07 | 2025-02-07 |

**Verdict: ₹49.94 lakh one-time recovery.** ₹23.41 L of it is [[finding-alo-logistics-unrecovered-claims]] (below); the remaining **₹26.53 L** is [[finding-dormant-vendor-advances]].

Note "BONUS PAYABLE" is a *payroll liability head mis-created as a vendor master* — a master-data defect worth fixing regardless of the ₹66,748.

---

## H2b — [[finding-alo-logistics-unrecovered-claims]]  ✅ CONFIRMED

ALO LOGISTICS LLP (Mart, `VENDA000972`) carries ₹23,40,991 debit with **no purchase invoice and no payment document, ever**. Traced to source:

```sql
SELECT TO_VARCHAR(j."RefDate",'YYYY-MM-DD') AS D, j."Debit", j."LineMemo"
FROM JIVO_MART_HANADB.JDT1 j
JOIN JIVO_MART_HANADB.OJDT h ON h."TransId"=j."TransId"
WHERE j."ShortName"='VENDA000972' ORDER BY j."RefDate";
```

13 manual journal entries (`TransType` 30), 2025-06-21 → 2025-12-08:

| Date | ₹ | Memo |
|---|---:|---|
| 2025-11-06 | 8,94,955 | Pending RTV Debit to Transporter |
| 2025-10-30 (×10) | 13,09,124 | BB Royal/Innovative invoices debit from Jivo Wellness |
| 2025-06-21 | 1,16,329 | Approval debit to transporter inv DL/SL/2597/24-25, 2698/24-25 |
| 2025-12-08 | 20,542 | DTDC clearance, transportation charges Kundli warehouse |

**Verdict: ₹23,40,991 one-time recovery, high confidence.** These are damage/RTV claims JIVO raised *against* the transporter and never collected. The relationship is dormant (no invoices, no payments) so there is **no future billing to net them against** — this will be written off unless chased now. 8–13 months old; act before it ages past commercial recoverability.

---

## H3 — Open down-payments never adjusted  ❌ KILLED

```sql
SELECT TABLE_NAME, RECORD_COUNT FROM SYS.M_TABLES
WHERE SCHEMA_NAME='<SCHEMA>' AND TABLE_NAME IN ('ODPO','ODPI');
```

`ODPO` = 0 rows and `ODPI` = 0 rows in **all three** companies. SAP's down-payment functionality is not used at all; advances are booked as on-account outgoing payments instead. **No money here — but this is *why* H15/H19 below are so large.**

---

## H4 — Same vendor as 2+ CardCodes with offsetting balances  ❌ KILLED

```sql
WITH n AS (SELECT "CardCode","CardName","Balance",
  UPPER(TRIM(REPLACE(REPLACE("CardName",'.',''),'PRIVATE LIMITED','PVT LTD'))) AS NN
  FROM <SCHEMA>.OCRD WHERE "CardType"='S')
SELECT a."CardCode", a."Balance", b."CardCode", b."Balance"
FROM n a JOIN n b ON b.NN=a.NN AND b."CardCode">a."CardCode"
WHERE (a."Balance">0 AND b."Balance"<0) OR (a."Balance"<0 AND b."Balance">0);
```

**Zero rows in all three companies.** Vendor master is clean on exact-name duplication. (Near-duplicates like `OM LOGISTICS LTD` vs `OM LOGISTICS SUPPLY CHAIN PVT LTD` are genuinely different legal entities.) **₹0.**

---

## H5 — Employee IMPREST accounts with old debit balances  ❌ KILLED (as a savings item)

```sql
SELECT SUM(CASE WHEN "Balance">0 THEN "Balance" ELSE 0 END) AS DR,
       SUM(CASE WHEN "Balance"<0 THEN "Balance" ELSE 0 END) AS CR, SUM("Balance") AS NET
FROM <SCHEMA>.OCRD
WHERE "CardType"='S' AND (UPPER("CardName") LIKE '%IMPREST%' OR "CardCode" LIKE 'ORGV%');
```

| Company | Debit | Credit | Net |
|---|---:|---:|---:|
| Oil | ₹16.90 L | −₹3.67 L | ₹13.23 L |
| Mart | ₹17.98 L | −₹0.15 L | ₹17.83 L |
| Beverages | ₹0.40 L | −₹5.26 L | −₹4.86 L |
| **Total** | **₹35.28 L** | | **₹26.21 L** |

Then aged by last journal movement (`JDT1."ShortName"`):

| Company | Dormant 6 mo+ |
|---|---:|
| Oil | ₹10,056 |
| Mart | ₹47,124 |
| Beverages | ₹15,375 |
| **Total** | **₹72,555** |

**Verdict: ₹0 material.** Imprest float is actively churning — the ₹35.28 L gross is live working float, not stuck money. Only ₹72,555 is dormant. **Imprest is well managed; do not chase it.**

Bonus caveat found here: the *same employee* appears with a debit in one company and a credit in another (BHUPINDER SINGH GINNI +₹2.87 L Oil / −₹2.60 L Bev; ARVINDER SINGH +₹6.22 L Oil / −₹2.04 L Bev). Gross imprest exposure overstates real exposure — see H14.

---

## H6 — [[finding-vendor-customer-netting]]: parties who are both supplier and customer  ✅ CONFIRMED

```sql
WITH n AS (SELECT "CardType","CardName","Balance",
  UPPER(TRIM(REPLACE(REPLACE("CardName",'.',''),'PRIVATE LIMITED','PVT LTD'))) AS NN
  FROM <SCHEMA>.OCRD WHERE "Balance"<>0),
g AS (SELECT NN,
  SUM(CASE WHEN "CardType"='S' AND "Balance"<0 THEN -"Balance" ELSE 0 END) AS WE_OWE,
  SUM(CASE WHEN "CardType"='C' AND "Balance">0 THEN "Balance" ELSE 0 END) AS THEY_OWE
  FROM n WHERE NN NOT LIKE '%JIVO%' GROUP BY NN)
SELECT COUNT(*), SUM(LEAST(WE_OWE,THEY_OWE)) FROM g WHERE WE_OWE>0 AND THEY_OWE>0;
```

| Company | N parties | Nettable |
|---|---:|---:|
| Oil | 4 | ₹25,26,049 |
| Mart | 3 | ₹8,22,188 |
| Beverages | 0 | ₹0 |
| **Total** | **7** | **₹33,48,236** |

Dominant item — SHIVAY EDIBLES PVT LTD (Oil): vendor `VENDA000616` credit ₹25,12,125 (JIVO owes) **and** customer `CUSTA001094` debit ₹49,39,998 (they owe JIVO). Others: METRO CASH & CARRY, PURE AGROCHEM.

**Verdict: ₹33.48 lakh working-capital release.** Sign a mutual set-off letter instead of paying out cash while chasing the same party for receivables.

⚠️ **Excluded deliberately:** the intercompany/inter-branch pairs (`JIVO WELLNESS PVT LTD - HR/PB/DL`, `JIVO MART PVT LTD`) net ₹76.23 Cr vendor-credit against ₹75.60 Cr customer-debit **inside the Oil book alone**. That is branch-transfer accounting for the same legal entity — it inflates both sides of the balance sheet by ~₹76 Cr but releases **no cash**. Flagged for the balance-sheet-presentation lens, not counted as savings.

---

## H7 — [[finding-stale-security-deposits]]  ✅ CONFIRMED

```sql
SELECT a."AcctCode", a."AcctName", a."CurrTotal",
  (SELECT MAX(j."RefDate") FROM JIVO_OIL_HANADB.JDT1 j WHERE j."Account"=a."AcctCode") AS LAST_MOVE
FROM JIVO_OIL_HANADB.OACT a
WHERE a."AcctCode" LIKE '1107%' AND IFNULL(a."CurrTotal",0)<>0
ORDER BY a."CurrTotal" DESC;
```

| Account | ₹ | Last movement |
|---|---:|---|
| GEETA GUPTA — RENT SECURITY | 11,25,000 | 2024-09-30 |
| ARVIND TULI — MAYAPURI RENT SECURITY | 5,62,500 | 2024-09-30 |
| RANJIT SAIN TULI — MAYAPURI RENT SECURITY | 5,62,500 | 2024-09-30 |
| SECURITY OF ELECTRICITY HR | 4,19,065 | 2024-09-30 |
| SECURITY FOR POLLUTION BAKHARPUR LAND | 3,50,000 | 2024-09-30 |
| KENDRIYA BHANDAR-SECURITY | 50,000 | 2024-09-30 |
| DIVINE DROP DRINKS — RENT SECURITY | 45,000 | 2024-09-30 |
| C FORM-SECURITY | 29,326 | 2024-09-30 |
| MVAT VAT SECURITY | 27,056 | 2024-09-30 |
| GEM SECURITY | 25,000 | 2024-09-30 |
| SALE TAX SECURITY | 20,000 | 2024-09-30 |
| GS 1 INDIA-SECURITY / MVAT CST / PAYTM DEVICE | 14,000 | 2024-09-30 |
| **Total static** | **₹32,29,447** | |

2024-09-30 is the SAP go-live migration date — **these balances have not moved once in the 22 months since**. Excluded from the total: `ADVANCE TAX` ₹4.65 Cr (tax lens), `INTERNATIONAL TRADEMARK WIPO` ₹7.09 L (moved 2025-10), `GUJARAT ENVIRO` ₹16,000 (moved 2026-02).

**Verdict: ₹32.29 lakh.** Two clean sub-pools:
- **₹81,382 provably dead** — `C FORM`, `MVAT VAT`, `MVAT CST`, `SALE TAX SECURITY` are **pre-GST tax-regime deposits (regime ended July 2017)**. Nine years old. Claim or write off.
- **₹22,95,000 rent securities** (Geeta Gupta, both Tulis/Mayapuri, Divine Drop) — recoverable **only if those premises have been vacated**. Requires a lease-status check before claiming; hence medium confidence.

---

## H8 — Purchase invoices paid more than their value  ❌ KILLED

```sql
SELECT COUNT(*), SUM(IFNULL("PaidToDate",0)-"DocTotal")
FROM <SCHEMA>.OPCH WHERE "CANCELED"='N' AND IFNULL("PaidToDate",0) > "DocTotal" + 1;
```

**Zero rows in all three companies.** No invoice-level overpayment exists. **₹0.**

---

## H9 — Unapplied outgoing payments via `OVPM."OpenBal"`  ❌ KILLED (false lead)

First pass returned ₹2,010 Cr in Oil — implausible against ₹193.91 Cr turnover, so I sampled the rows:

```sql
SELECT "DocNum","CardCode","DocTotal","OpenBal" FROM JIVO_OIL_HANADB.OVPM
WHERE "Canceled"='N' AND "DocType"='S' AND IFNULL("OpenBal",0)<>0 ORDER BY "DocDate" DESC;
```

`OpenBal` **equals `DocTotal` on every row** — it mirrors the payment amount, it is not an unapplied residual. Hypothesis retracted; the real signal lives in H15/H19. **₹0.**

---

## H10 — Frozen / inactive vendors holding debit balances  ❌ KILLED

```sql
SELECT "frozenFor", COUNT(*), SUM(CASE WHEN "Balance">0 THEN "Balance" ELSE 0 END)
FROM <SCHEMA>.OCRD WHERE "CardType"='S' AND "Balance">0 GROUP BY "frozenFor";
```

All 235 debit-balance vendors are `frozenFor='N'` in all three companies. No frozen vendor is holding money. **₹0.**

---

## H11 — Staff advance GL accounts  ⚠️ PARTIAL

Distinct from the imprest *vendor* accounts of H5 — these are GL accounts named `<NAME> ADVANCE JWPL<empcode>`.

```sql
SELECT COUNT(*), SUM("CurrTotal") FROM <SCHEMA>.OACT
WHERE UPPER("AcctName") LIKE '%ADVANCE JWPL%' AND IFNULL("CurrTotal",0)>0;
```

| Company | N accounts | Debit |
|---|---:|---:|
| Oil | 55 | ₹62,41,363 |
| Mart | 10 | ₹4,40,554 |
| Beverages | 3 | ₹82,600 |
| **Total** | **68** | **₹67,64,517** |

Aged by last GL movement (Oil): **active ₹60.39 L (53 accounts), dormant 6–12 mo ₹2.02 L (2 accounts), dormant 12 mo+ ₹0.**

**Verdict: ₹2.02 lakh only.** Like imprest, staff advances are churning, not stuck. Largest individual balances (GURVINDERJEET SINGH ₹13.07 L, GAGANDEEP SINGH ₹6.49 L, GURPREET SINGH WINKAL ₹5.70 L) are all live. Worth a policy review on advance size, but no recovery finding.

---

## H12 — Unapplied A/P credit notes  ⚠️ MOSTLY INTERCOMPANY

```sql
SELECT "DocStatus", COUNT(*), SUM("DocTotal"-IFNULL("PaidToDate",0))
FROM <SCHEMA>.ORPC WHERE "CANCELED"='N' GROUP BY "DocStatus";
```

| Company | Open CNs | Unapplied |
|---|---:|---:|
| Oil | 321 | ₹27,40,815 |
| Mart | 362 | ₹15,51,32,074 |
| Beverages | 2 | ₹1,67,560 |

Mart's ₹15.51 Cr looked huge — drilled by vendor:

| Vendor | N | CN total | Vendor balance |
|---|---:|---:|---:|
| JIVO WELLNESS PVT LTD | 278 | ₹16,27,21,802 | −₹22,84,98,023 |
| FLIPKART INTERNET PVT LTD | 66 | ₹9,73,113 | −₹44,75,459 |
| AMAZON SELLER SERVICES | 9 | ₹40,145 | +₹18,45,499 |
| others (logistics) | 9 | ₹70,832 | — |

**Verdict: ~₹10.85 lakh third-party residual, the rest is intercompany stock-transfer noise.** Not a standalone finding — but it confirms `DocStatus='O'` in this system means "not internally reconciled", **not** "unpaid". That insight drives H19.

---

## H13 / H16 — Goods received but never invoiced (open GRPO)  ❌ KILLED

```sql
SELECT CASE WHEN "DocDate"<'2025-01-28' THEN 'A_18mo+'
            WHEN "DocDate"<'2025-07-28' THEN 'B_12-18mo'
            WHEN "DocDate"<'2026-01-28' THEN 'C_6-12mo'
            ELSE 'D_under6mo' END AS AGE_, COUNT(*), SUM("DocTotal")
FROM <SCHEMA>.OPDN WHERE "CANCELED"='N' AND "DocStatus"='O' GROUP BY 1;
```

| Company | 18 mo+ | 12–18 mo | 6–12 mo | <6 mo |
|---|---:|---:|---:|---:|
| Oil | ₹8,036 | ₹28,909 | ₹11.29 L | ₹4.43 Cr |
| Mart | — | — | ₹3.53 L | ₹58.91 L |
| Beverages | ₹5,311 | ₹98,368 | ₹29.64 L | ₹72.58 L |

Open receipts are overwhelmingly **under 6 months = normal purchasing pipeline**. Aged (>12 mo) residue is only ₹1.4 L combined. **₹0 material.**

Open POs for context: Oil ₹56.07 Cr / Mart ₹51.34 Cr / Bev ₹10.22 Cr — commitments, handled by the stock lens.

---

## H14 — [[finding-cross-company-vendor-netting]]  ✅ CONFIRMED

```sql
WITH a AS (
  SELECT 'OIL' AS CO, UPPER(TRIM(REPLACE(REPLACE("CardName",'.',''),'PRIVATE LIMITED','PVT LTD'))) AS NN, "Balance"
    FROM JIVO_OIL_HANADB.OCRD WHERE "CardType"='S' AND "Balance"<>0
  UNION ALL SELECT 'MART', ..., "Balance" FROM JIVO_MART_HANADB.OCRD WHERE ...
  UNION ALL SELECT 'BEV',  ..., "Balance" FROM JIVO_BEVERAGES_HANADB.OCRD WHERE ...),
g AS (SELECT NN, SUM(CASE WHEN "Balance">0 THEN "Balance" ELSE 0 END) AS DR,
             SUM(CASE WHEN "Balance"<0 THEN -"Balance" ELSE 0 END) AS CR,
             COUNT(DISTINCT CO) AS N_CO FROM a GROUP BY NN)
SELECT COUNT(*), SUM(LEAST(DR,CR)) FROM g WHERE DR>0 AND CR>0 AND N_CO>1;
```

**35 vendors, ₹42,58,243 nettable.** Top items:

| Vendor | Debit side | Credit side | Nettable |
|---|---|---|---:|
| UTTAR HARYANA BIJLI VITRAN NIGAM | OIL ₹38.58 L | BEV −₹20.87 L | ₹20,86,834 |
| ARNAV TRANSPORT SERVICE | OIL ₹15.12 L | BEV −₹8.91 L | ₹8,91,334 |
| BHUPINDER SINGH GINNI (imprest) | OIL ₹2.87 L | BEV −₹2.60 L | ₹2,60,314 |
| ARVINDER SINGH (imprest) | OIL ₹6.22 L | BEV −₹2.04 L | ₹2,04,321 |
| VIJAY INDUSTRIES | OIL ₹4.21 L | BEV −₹1.47 L | ₹1,47,492 |
| MEDIA MIND | BEV ₹1.27 L | OIL −₹18.86 L | ₹1,26,553 |

**Verdict: ₹42.58 lakh working-capital release, medium confidence.**
⚠️ **Honest caveat:** Oil / Mart / Beverages are **three separate legal entities**. You cannot unilaterally offset entity A's receivable against entity B's payable to the same third party — it needs a tripartite set-off letter from the vendor, or an intercompany transfer. The employee-imprest rows (Bhupinder, Arvinder) are the easy ones: same person, pure internal reclassification. The UHBVN row is likely *two separate electricity connections* for two plants and may not be offsettable at all — verify before claiming.

---

## H15 — [[finding-unapplied-advances-vs-open-bills]]  ✅ CONFIRMED

The double-payment trap: a vendor holds JIVO's advance **and** shows unpaid invoices in SAP at the same time.

```sql
WITH op AS (SELECT "CardCode", SUM("DocTotal"-IFNULL("PaidToDate",0)) AS DUE
  FROM <SCHEMA>.OPCH WHERE "CANCELED"='N' AND "DocStatus"='O'
    AND ("DocTotal"-IFNULL("PaidToDate",0))>0 GROUP BY "CardCode")
SELECT COUNT(*), SUM(LEAST(c."Balance", op.DUE))
FROM <SCHEMA>.OCRD c JOIN op ON op."CardCode"=c."CardCode"
LEFT JOIN <SCHEMA>.OCRG g ON g."GroupCode"=c."GroupCode"
WHERE c."CardType"='S' AND c."Balance">0 AND IFNULL(g."GroupName",'')<>'FIXED ASSETS';
```

| Company | Vendors | Offsettable (excl. fixed assets) |
|---|---:|---:|
| Oil | 81 | ₹3,68,21,596 |
| Mart | 15 | ₹33,13,209 |
| Beverages | 11 | ₹3,83,332 |
| **Total** | **107** | **₹4,05,18,137** |

Top Oil contributors:

| Vendor | Debit balance | Open PI due | Oldest open | Offsettable |
|---|---:|---:|---|---:|
| AWL AGRI BUSINESS | ₹1.79 Cr | ₹1.21 Cr | 2026-07-02 | ₹1,21,26,130 |
| DHANLAXMI EDIBLES | ₹2.13 Cr | ₹68.87 L | 2026-05-19 | ₹68,87,402 |
| ARORA AGRI BUSINESS | ₹60.86 L | ₹62.19 L | 2026-07-23 | ₹60,85,933 |
| VAISHNODEVI AGRO | ₹59.59 L | ₹4.39 Cr | 2026-04-28 | ₹59,58,741 |
| UHBVN ELECTRICITY | ₹38.58 L | ₹17.90 L | 2026-04-16 | ₹17,89,687 |
| ARNAV TRANSPORT | ₹15.12 L | ₹3.90 L | **2025-01-03** | ₹3,89,688 |
| IFFCO TOKIO INSURANCE | ₹17.84 L | ₹3.50 L | **2024-09-30** | ₹3,50,371 |

**Verdict: ₹4.05 Cr working-capital release + double-payment prevention, high confidence.** Every rupee here is an advance already paid that SAP still presents as an unpaid bill. Run internal reconciliation (`Business Partner → Internal Reconciliation`) to knock advances against open invoices; until then any payment run driven off the "open A/P invoices" report can pay the same money twice.

Including the FIXED ASSETS group the figure is ₹13.44 Cr for Oil, but ₹9.76 Cr of that is the single ANJU MANGLA property invoice — see H20, reported separately to avoid overstating.

---

## H17 — Vendors paid in the last 12 months with zero invoices in the same window  ⚠️ SCREENING ONLY

```sql
WITH pay AS (SELECT "CardCode", SUM("DocTotal") AS PAID FROM <SCHEMA>.OVPM
  WHERE "Canceled"='N' AND "DocType"='S' AND "DocDate">='2025-07-28' GROUP BY "CardCode"),
inv AS (SELECT "CardCode", SUM("DocTotal") AS INVD FROM <SCHEMA>.OPCH
  WHERE "CANCELED"='N' AND "DocDate">='2025-07-28' GROUP BY "CardCode")
SELECT COUNT(*), SUM(pay.PAID) FROM pay LEFT JOIN inv ON inv."CardCode"=pay."CardCode"
WHERE IFNULL(inv.INVD,0)=0;
```

| Company | Vendors | Paid without any bill in window |
|---|---:|---:|
| Oil | 190 | ₹7.23 Cr |
| Mart | 11 | ₹4.65 L |
| Beverages | 45 | ₹3.05 Cr |
| **Total** | **246** | **₹10.33 Cr** |

**Verdict: not a standalone finding.** Most of this is legitimate settlement of *prior-year* invoices, which this window cannot see. Useful as a review queue only; the recoverable subset is already isolated in H2 (the ones that left a debit balance behind).

---

## H18 — Trade advance vs purchase run-rate  ✅ CONFIRMED (small)

```sql
SELECT c."CardName", c."Balance" AS ADVANCE,
  (SELECT SUM(p."DocTotal") FROM JIVO_OIL_HANADB.OPCH p
    WHERE p."CardCode"=c."CardCode" AND p."CANCELED"='N' AND p."DocDate">='2025-07-28') AS PURCH_12M,
  c."Balance" / NULLIF((SELECT SUM(p."DocTotal")/12 FROM ...),0) AS MONTHS_OF_PURCH
FROM JIVO_OIL_HANADB.OCRD c JOIN JIVO_OIL_HANADB.OCRG g ON g."GroupCode"=c."GroupCode"
WHERE c."CardType"='S' AND c."Balance">200000 AND g."GroupName" IN ('PURCHASE OIL','PURCHASE');
```

| Vendor | Advance | 12-mo purchases | Months of cover |
|---|---:|---:|---:|
| DHANLAXMI EDIBLES | ₹2.13 Cr | ₹14.78 Cr | 1.73 |
| ARORA AGRI BUSINESS | ₹60.86 L | ₹10.21 Cr | 0.72 |
| AWL AGRI BUSINESS | ₹1.79 Cr | ₹40.05 Cr | 0.54 |
| VAISHNODEVI AGRO | ₹59.59 L | ₹36.67 Cr | 0.19 |
| AL GHURAIR RESOURCES | ₹2.35 L | ₹10.13 Cr | 0.03 |
| **BERICAP INDIA** | **₹4.41 L** | ₹7.50 L | **7.05** |
| **BEE HIVE FARMS** | **₹4.05 L** | ₹24,129 | **201.6** |
| AGILENT / VIJAY IND. / L B ENTERPRISE | ₹19.37 L | **₹0** | ∞ |

**Verdict: commodity oil advances are healthy (0.19–1.73 months of purchases — normal for edible-oil trade).** The outliers are the ones already captured in H2. BERICAP at 7 months and BEE HIVE at 201 months of cover are the only new names; ~₹8.5 L combined, already inside the H1 pool.

---

## H19 — [[finding-ap-subledger-not-reconciled]]  ✅ CONFIRMED (control finding)

```sql
WITH op AS (SELECT "CardCode", SUM("DocTotal"-IFNULL("PaidToDate",0)) AS DUE
  FROM JIVO_OIL_HANADB.OPCH WHERE "CANCELED"='N' AND "DocStatus"='O'
    AND ("DocTotal"-IFNULL("PaidToDate",0))>0 GROUP BY "CardCode")
SELECT CASE WHEN c."Balance">0 THEN 'vendor_in_DEBIT' WHEN c."Balance"=0 THEN 'ZERO'
            ELSE 'vendor_in_CREDIT' END AS BUCKET, COUNT(*), SUM(op.DUE)
FROM JIVO_OIL_HANADB.OCRD c JOIN op ON op."CardCode"=c."CardCode"
WHERE c."CardType"='S' GROUP BY 1;

SELECT SUM(-"Balance") FROM JIVO_OIL_HANADB.OCRD WHERE "CardType"='S' AND "Balance"<0;
```

**Oil company:**

| Bucket | Vendors | "Open" PI due |
|---|---:|---:|
| vendor in DEBIT (we already advanced) | 87 | ₹141.40 Cr |
| vendor in CREDIT (we genuinely owe) | 265 | ₹128.52 Cr |
| vendor at ZERO balance | 125 | ₹22.66 Cr |
| **Total invoices flagged "open"** | | **₹292.57 Cr** |
| **Actual A/P ledger balance** | | **₹105.94 Cr** |
| **Phantom / already-settled** | | **₹186.63 Cr** |

Worked example — AL GHURAIR RESOURCES shows **₹93.70 Cr of "open" invoices** while its ledger balance is a ₹2.35 L *debit*. Those invoices are fully paid; nobody reconciled them.

**Verdict: ₹186.63 Cr of invoices are marked unpaid in SAP but are already settled.** Root cause is H3 — down-payment documents are never used, so every advance is an unreconciled on-account payment. This is **not ₹186 Cr of cash**; it is the *risk surface*. Its quantified cash consequence is H15's ₹4.05 Cr. Highest-priority control fix in this lens: monthly internal reconciliation per vendor, and stop generating payment proposals from the open-invoice report.

---

## H20 — Large single-vendor advances  ✅ CONFIRMED

### [[finding-hs-filling-advance]] — Beverages, ₹2.40 Cr

```sql
SELECT j."TransType", COUNT(*), SUM(IFNULL(j."Debit",0)), SUM(IFNULL(j."Credit",0)),
       MIN(j."RefDate"), MAX(j."RefDate")
FROM JIVO_BEVERAGES_HANADB.JDT1 j WHERE j."ShortName"='VENDA001347' GROUP BY j."TransType";
```

| TransType | N | Debit | Credit | Window |
|---|---:|---:|---:|---|
| 46 (outgoing payment) | 5 | ₹2,90,00,000 | — | 2026-04-07 → 2026-07-20 |
| 30 (journal entry) | 1 | — | ₹50,00,000 | 2026-05-14 |

HS FILLING AND PACKAGING holds **₹2.40 Cr** of Beverages' cash. **Zero purchase invoices, ever.** Money out from 2026-04-07, i.e. up to 3.7 months with nothing billed against it. It is 88% of Beverages' entire ₹2.71 Cr vendor-debit pool.

**Verdict: ₹2.40 Cr working capital.** Plausibly a legitimate co-packing / equipment advance under an active contract (payments continue to 2026-07-20). Action: obtain the contract and the delivery schedule, confirm goods/services are actually flowing, and get invoices raised so the advance amortises.

### [[finding-mangla-related-party-advances]] — Oil, ₹13.16 Cr

```sql
SELECT j."TransType", COUNT(*), SUM(IFNULL(j."Debit",0)), SUM(IFNULL(j."Credit",0)),
       MIN(j."RefDate"), MAX(j."RefDate")
FROM JIVO_OIL_HANADB.JDT1 j WHERE j."ShortName"='VENDA001603' GROUP BY j."TransType";
```

ANJU MANGLA (`VENDA001603`, FIXED ASSETS group): 10 outgoing payments ₹17.86 Cr (2026-01-09 → 2026-07-20) + a ₹3.20 Cr journal-entry debit on 2026-04-09, against ₹9.76 Cr net invoiced → **₹11.31 Cr debit**. RAHUL MANGLA (`VENDA001601`) holds a further **₹1.85 Cr** with **no invoice at all**, last paid 2026-07-20.

**Verdict: ₹13.16 Cr of capital tied up with two individuals — low confidence as a *recovery*, high importance as a *disclosure*.** This is almost certainly a deliberate land/property capex to related parties, not leakage. Three things still need answers: (a) the ₹3.20 Cr manual journal entry of 2026-04-09 needs a supporting document; (b) ₹1.85 Cr has been paid to RAHUL MANGLA with nothing invoiced; (c) the ₹9.76 Cr invoice sits "open" while ₹11.31 Cr of advance sits unapplied on the same vendor — a live double-payment exposure. Not counted in the savings total.

---

## Killed hypotheses — summary

| # | Hypothesis | Why killed |
|---|---|---|
| H3 | Open down-payments never adjusted | `ODPO`/`ODPI` are empty in all 3 companies |
| H4 | Duplicate vendor masters, offsetting balances | zero exact-name pairs |
| H5 | Old employee imprest debits | only ₹72,555 dormant of ₹35.28 L gross |
| H8 | Invoice-level overpayments | zero rows, all companies |
| H9 | Unapplied payments via `OVPM."OpenBal"` | field mirrors `DocTotal`, not a residual |
| H10 | Frozen vendors holding cash | all debit vendors are `frozenFor='N'` |
| H13/H16 | Aged goods-received-not-invoiced | >12 mo residue only ₹1.4 L |
| H17 | Paid-with-no-invoice screen | mostly legitimate prior-year settlement |

---

## Caveats

1. **Advance ≠ leakage.** ₹17.81 Cr of the ₹24.26 Cr vendor-debit pool sits with vendors actively invoicing in the last 6 months — normal commodity trade advances (0.19–1.73 months of purchase cover). Only the dormant tail is recoverable.
2. **`DocStatus='O'` is unreliable here** (H19). Never size an A/P finding from open-invoice status alone; always cross-check `OCRD."Balance"`.
3. **Cross-company netting needs consent** — three separate legal entities (H14).
4. **2024-09-30 is the SAP go-live date.** A "last movement" of 2024-09-30 means "migrated opening balance, never touched", not "transacted that day". Pre-go-live history is not in these tables, so ageing beyond 22 months cannot be measured from SAP alone.
5. **Rent security deposits** are recoverable only if the premises were vacated — needs a lease check, not a SQL query.
6. Findings 1/2 (recoveries) are disjoint. Finding 3 (₹4.05 Cr) excludes the FIXED ASSETS group so it does not overlap finding 9. Finding 4 is a risk surface, not additive cash.

**Total defensible:**

| | ₹ |
|---|---:|
| One-time recovery (findings 1+2) | **₹49,93,503** |
| Working capital — advances offsettable vs open bills (3) | ₹4,05,18,137 |
| Working capital — cross-company netting (6) | ₹42,58,243 |
| Working capital — vendor/customer netting (7) | ₹33,48,236 |
| Working capital — stale deposits (8) | ₹32,29,447 |
| **Working-capital release subtotal** | **₹5,13,54,063** |
| Plus HS Filling advance to chase down (5) | ₹2,40,00,000 |
| **Working capital incl. HS Filling** | **₹7,53,54,063** |

Against a **₹186.63 Cr A/P reconciliation control gap** (risk surface, not cash) and **₹13.16 Cr** of related-party capex advances flagged for disclosure.
