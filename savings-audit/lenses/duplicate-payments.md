---
title: Duplicate Payments — paying the same money twice
created: 2026-07-28
lens: duplicate-payments
tags: [savings-audit, accounts-payable, sap-b1, internal-control]
---

# 💸 Lens: Paying TWICE

Part of [[SAVINGS-MOC]]

**Scope:** all three SAP companies — `JIVO_OIL_HANADB` (Oil), `JIVO_MART_HANADB` (Mart), `JIVO_BEVERAGES_HANADB` (Beverages). Data window = SAP go-live **2024-09-30 → 2026-07-28**. All figures pulled live from HANA. Read-only, SELECT only.

**22 hypotheses tested. 8 carry money. 9 killed with evidence (documented below — the negatives matter, several looked like ₹15–18 Cr findings until verified).**

> **Headline:** JIVO does *not* have a big pile of confirmed double payments. What it has is a **reconciliation vacuum** — **95.3% of Oil's ₹391.80 Cr of vendor payments (8,149 of 13,369 documents) were posted "on account" and never applied to an invoice.** The consequence is measurable: **₹13.80 Cr of vendor accounts simultaneously show an advance we've paid AND invoices SAP still believes are unpaid.** Anyone paying from an "open A/P" report pays that money a second time.

---

## Result summary

| # | Hypothesis | Verdict | ₹ |
|---|---|---|---|
| H1 | Same vendor + same bill no. booked twice | **HIT** (small, after killing serial-reuse noise) | ₹5.11 L |
| H2 | Twin payments (same vendor, same amount, ≤7 d) | KILLED — commodity tanker noise | — |
| H3 | Invoice `PaidToDate > DocTotal` | KILLED — 0 rows, all 3 cos | — |
| H4 | Payments over-applied to one invoice (VPM2) | KILLED — 0 rows | — |
| H5 | Vendor debit (advance) balances | context: ₹24.26 Cr total | — |
| H6 | Debit balance + **open unpaid bills** = double-pay trap | **HIT — biggest** | **₹13.80 Cr** |
| H7 | Debit balance + **zero invoices ever** | **HIT** | ₹5.34 Cr |
| H8 | Dormant debit balances (no activity 12 m) | **HIT** | ₹39.23 L |
| H9 | Open A/P credit notes never set off | **HIT** | ₹7.04 L net |
| H10 | GRPO open + invoice booked standalone | **HIT** (small) | ₹6.60 L |
| H11 | Same bill no. under **two different vendor codes** | **HIT** (1 case) | ₹40.00 L |
| H12 | Same bill in two companies (cross-co double book) | KILLED — ₹17 k total | — |
| H13 | Dot/space-suffixed bill refs (duplicate-check bypass) | INCONCLUSIVE | ≤ ₹5.46 L |
| H14 | Duplicate manual journal entries | KILLED — reversal pairs | — |
| H15 | Payments sitting on **cancelled** invoices | KILLED — SAP artifact | — |
| H16 | Same vendor, same amount, same month | KILLED — verified split claims | — |
| H17 | Duplicate vendor master records | CONTROL GAP (no GSTIN captured) | — |
| H18 | Same cheque / bank ref on 2 payments | UNTESTABLE — `CounterRef` empty | — |
| H19 | Twin payments at low-volume vendors w/ debit bal. | **HIT** (inside H7) | ₹1.20 Cr* |
| H20 | On-account payments never applied | **ROOT CAUSE** | 95.3% of ₹391.80 Cr |
| H21 | Open A/P down-payment invoices (ODPO) | KILLED — 0 rows | — |
| H22 | "Phantom" open payables vs ledger | exposure metric | ₹359 Cr gross |

\* carve-out of H7, not additive.

---

## H20 (ROOT CAUSE) — 95% of vendor payments are never applied to an invoice

```sql
SELECT TO_DECIMAL(SUM(CASE WHEN "PayNoDoc"='Y' THEN "DocTotal" ELSE 0 END),18,2) AS ONACCT,
       COUNT(CASE WHEN "PayNoDoc"='Y' THEN 1 END) AS N_ONACCT,
       TO_DECIMAL(SUM("DocTotal"),18,2) AS TOTAL_PAID, COUNT(*) AS N_ALL
FROM   JIVO_OIL_HANADB.OVPM WHERE "Canceled"='N';
```

| Company | On-account ₹ | On-account docs | Total paid ₹ | Total docs | % on-account (value) |
|---|---|---|---|---|---|
| Oil | **373.23 Cr** | 8,149 | 391.80 Cr | 13,369 | **95.3%** |
| Mart | 211.12 Cr | 1,129 | 285.30 Cr | 1,945 | 74.0% |
| Beverages | 14.15 Cr | 753 | 26.66 Cr | 1,727 | 53.1% |

Because payments are posted on account, **A/P invoices are never closed**. SAP therefore reports as "open" a huge block of invoices that have in fact been paid:

```sql
SELECT COUNT(*) AS N_VENDORS, TO_DECIMAL(SUM(PHANTOM),18,2) AS PHANTOM_OPEN_PAYABLES
FROM ( SELECT c."CardCode",
              GREATEST(0,
                IFNULL((SELECT SUM(i."DocTotal"-i."PaidToDate") FROM JIVO_OIL_HANADB.OPCH i
                        WHERE i."CardCode"=c."CardCode" AND i."CANCELED"='N' AND i."DocStatus"='O'),0)
                - GREATEST(0,-c."Balance")) AS PHANTOM
       FROM JIVO_OIL_HANADB.OCRD c WHERE c."CardType"='S' ) WHERE PHANTOM>1000;
```

| Company | Open A/P per invoice register | "Phantom" (not actually owed per ledger) |
|---|---|---|
| Oil | ₹207.19 Cr | **₹188.75 Cr** |
| Mart | ₹192.83 Cr | **₹169.25 Cr** |
| Beverages | ₹1.31 Cr | ₹1.03 Cr |

**Caveat (important):** ₹359 Cr is *not* a loss. It is the gross size of the reconciliation gap — the register and the ledger disagree by that much. The realistically-at-risk slice is H6 below.

---

## H6 (BIGGEST) — vendors that hold our advance **and** show unpaid bills → ₹13.80 Cr

```sql
SELECT COUNT(*) AS N_VENDORS, TO_DECIMAL(SUM(AT_RISK),18,2) AS DOUBLE_PAY_RISK
FROM ( SELECT c."CardCode",
              LEAST(c."Balance",
                (SELECT SUM(i."DocTotal"-i."PaidToDate") FROM JIVO_OIL_HANADB.OPCH i
                 WHERE i."CardCode"=c."CardCode" AND i."CANCELED"='N' AND i."DocStatus"='O')) AS AT_RISK
       FROM JIVO_OIL_HANADB.OCRD c
       WHERE c."CardType"='S' AND c."Balance">10000
         AND (SELECT SUM(i."DocTotal"-i."PaidToDate") FROM JIVO_OIL_HANADB.OPCH i
              WHERE i."CardCode"=c."CardCode" AND i."CANCELED"='N' AND i."DocStatus"='O')>10000 );
```

| Company | Vendors | Double-pay exposure |
|---|---|---|
| Oil | 48 | **₹13,43,21,498** |
| Mart | 9 | ₹33,00,500 |
| Beverages | 6 | ₹4,11,486 |
| **Total** | **63** | **₹13,80,33,484** |

Top of the Oil list:

| CardCode | Vendor | Debit balance | Open bills | # open |
|---|---|---|---|---|
| VENDA001603 | **ANJU MANGLA** | ₹11,30,73,663 | **₹9,75,72,441** | 1 |
| VENDA000224 | AWL AGRI BUSINESS LTD (Adani Wilmar) | ₹1,79,32,650 | ₹1,21,26,130 | 3 |
| VENDA000614 | DHANLAXMI EDIBLES P LTD | ₹2,12,69,122 | ₹68,87,402 | 3 |
| VENDA001695 | M/S ARORA AGRI BUSINESS VENTURES | ₹60,85,933 | ₹62,19,395 | 1 |
| VENDA000930 | VAISHNODEVI AGRO RESOURCES P LTD | ₹59,58,741 | ₹4,38,89,401 | 18 |
| VENDA000521 | UTTAR HARYANA BIJLI VITRAN NIGAM | ₹38,57,921 | ₹17,89,687 | 4 |
| VENDA000956 | ARNAV TRANSPORT SERVICE | ₹15,11,889 | ₹3,89,688 | 11 |
| VENDA000356 | IFFCO TOKIO GENERAL INSURANCE | ₹17,83,782 | ₹3,50,371 | 11 |

### [[finding-anju-mangla-land-invoice-open]] — ₹9.76 Cr single largest trap

```sql
SELECT 'PAY',"DocNum","DocDate",TO_DECIMAL("DocTotal",18,2),"Canceled","Comments"
FROM JIVO_OIL_HANADB.OVPM WHERE "CardCode"='VENDA001603'
UNION ALL SELECT 'BILL',"DocNum","DocDate",TO_DECIMAL("DocTotal",18,2),"CANCELED","NumAtCard"
FROM JIVO_OIL_HANADB.OPCH WHERE "CardCode"='VENDA001603' ORDER BY 3;
```

| Kind | DocNum | Date | ₹ | Cancelled | Ref |
|---|---|---|---|---|---|
| PAY | 126466906 | 2026-01-09 | 1,00,00,000 | N | TRFR TO:140501000518 |
| PAY | 126467110 | 2026-01-27 | 1,00,00,000 | N | TRFR TO:ANJU MANGLA |
| PAY | 126467111 | 2026-01-27 | 1,00,00,000 | N | TRFR TO:ANJU MANGLA |
| PAY | 326466909 | 2026-03-25 | 64,40,253 | N | — |
| PAY | 326467085 | 2026-03-31 | 1,42,85,000 | N | 603090076113 |
| PAY | 426466591 | 2026-04-08 | 1,48,07,188 | N | — |
| **BILL** | 626043125 | 2026-04-09 | **9,75,72,441** | **Y** | TAZ2026C17 |
| **BILL** | 626043126 | 2026-04-09 | **9,75,72,441** | **C** | TAZ2026C17 |
| **BILL** | 626043127 | 2026-04-09 | **9,75,72,441** | **N** | TAZ2026C17 |
| PAY | 626466955 | 2026-06-23 | 3,00,00,000 | N | — |
| PAY | 726466658 | 2026-07-15 | 2,00,00,000 | N | — |
| PAY | 726466773 | 2026-07-20 | 86,76,400 | N | — |
| PAY | 726466774 | 2026-07-20 | 5,43,97,263 | N | — |

Payments to Anju Mangla total **₹17.86 Cr**; the single live invoice (land, ref `TAZ2026C17`) is **₹9.75 Cr** and is still `DocStatus='O'` (unpaid) with `PaidToDate = 0`. Balance is **₹11.31 Cr DEBIT**. The same invoice was keyed **three times** (one live, one cancelled, one cancellation doc) — the control caught it that time.

Two ₹1 Cr payments went out on the **same day** (2026-01-27) with the identical narration. Related party (Rahul Mangla, the co-seller, also holds a **₹1.85 Cr debit with zero invoices ever**). Combined Mangla exposure = **₹13.16 Cr**.

**Action:** apply the ₹17.86 Cr of on-account payments to invoice `626043127` in SAP before any further disbursement, and get the registered sale deed to confirm total consideration.

---

## H7 — ₹5.34 Cr paid to 37 vendors that have **never** raised an invoice

```sql
SELECT COUNT(*) AS N, TO_DECIMAL(SUM(c."Balance"),18,2) AS DEBIT_NO_BILLS
FROM   JIVO_OIL_HANADB.OCRD c
WHERE  c."CardType"='S' AND c."Balance">10000
  AND NOT EXISTS (SELECT 1 FROM JIVO_OIL_HANADB.OPCH i
                  WHERE i."CardCode"=c."CardCode" AND i."CANCELED"='N');
```

| Company | Vendors | ₹ |
|---|---|---|
| Oil | 27 | ₹2,67,08,297 |
| Mart | 6 | ₹25,39,397 |
| Beverages | 4 | ₹2,41,34,800 |
| **Total** | **37** | **₹5,33,82,495** |

Named items:

| Company | Vendor | ₹ | Note |
|---|---|---|---|
| BEV | **HS FILLING AND PACKAGING** | **2,40,00,000** | 5 payments, 0 invoices, open POs ₹3.36 Cr |
| OIL | RAHUL MANGLA | 1,85,47,737 | related party, land co-seller |
| MART | ALO LOGISTICS LLP | 23,40,991 | see [[finding-alo-logistics-debit-notes]] |
| OIL | SERVOKON SYSTEMS LTD | 7,67,000 | paid 2026-07-20 |
| OIL | VIJAY INDUSTRIES | 4,21,402 | = an open credit note from 2024-09-30 |
| OIL | L B ENTERPRISE | 4,00,000 | paid 2026-07-17 |
| OIL | ASTHA THUKRAL | 2,00,000 | paid 2026-07-03 |
| OIL | RAMA SALES | 1,76,960 | dormant since go-live |
| OIL | JIVO WELLNESS (AKAL INFOSYS) | 1,52,855 | dormant, no payment either |
| OIL | MARSHTECH AND ALLIED SERVICES | 1,22,250 | dormant since go-live |
| OIL | KS AFFINITY PVT LTD | 1,07,902 | dormant since go-live |
| OIL | JASRA & JASRA LAW OFFICES | 1,06,000 | paid 2025-12-09 |

### [[finding-hs-filling-twin-payments]] — ₹2.40 Cr with zero invoices, incl. two same-day twins

```sql
SELECT 'PAY',"DocNum","DocDate",TO_DECIMAL("DocTotal",18,2),"Comments"
FROM JIVO_BEVERAGES_HANADB.OVPM WHERE "CardCode"='VENDA001347'
UNION ALL SELECT 'BILL',"DocNum","DocDate",TO_DECIMAL("DocTotal",18,2),"NumAtCard"
FROM JIVO_BEVERAGES_HANADB.OPCH WHERE "CardCode"='VENDA001347' ORDER BY 3;
```

| DocNum | Date | ₹ | Narration |
|---|---|---|---|
| 426468004 | 2026-04-07 | 70,00,000 | BEING PAYMENT PAID TO HS FILLING AND PACKAGING |
| 426468007 | **2026-04-07** | **70,00,000** | *(identical narration, same day)* |
| 726468022 | 2026-07-16 | 50,00,000 | BEING PAYMENT PAID TO HS FILLING AND PACKAGING |
| 726468023 | **2026-07-16** | **50,00,000** | *(identical narration, same day)* |
| 726468035 | 2026-07-20 | 50,00,000 | — |

Zero purchase invoices ever. Two open POs: ₹2,18,30,000 (2026-04-07) + ₹1,18,00,000 (2026-04-04) = ₹3.36 Cr. **₹1.20 Cr of the ₹2.40 Cr went out as same-day identical twins** — must be tied to the bank statement before assuming both cleared.

---

## H8 — dormant vendor debit balances: ₹39.23 L

Vendors holding our money with **no invoice and no payment for 12+ months**:

```sql
SELECT COUNT(*) AS N, TO_DECIMAL(SUM(c."Balance"),18,2) AS STALE_DEBIT
FROM   JIVO_OIL_HANADB.OCRD c
WHERE  c."CardType"='S' AND c."Balance">25000
  AND IFNULL((SELECT MAX(i."DocDate") FROM JIVO_OIL_HANADB.OPCH i
              WHERE i."CardCode"=c."CardCode" AND i."CANCELED"='N'),'2000-01-01') < '2025-07-28'
  AND IFNULL((SELECT MAX(p."DocDate") FROM JIVO_OIL_HANADB.OVPM p
              WHERE p."CardCode"=c."CardCode" AND p."Canceled"='N'),'2000-01-01') < '2025-07-28';
```

| Company | Vendors | ₹ |
|---|---|---|
| Oil | 9 | ₹12,27,360 |
| Mart | 3 | ₹25,95,962 |
| Beverages | 1 | ₹1,00,000 |
| **Total** | **13** | **₹39,23,322** |

### [[finding-alo-logistics-debit-notes]] — ₹23.41 L of transporter debit notes never recovered

`JIVO_MART_HANADB` / `VENDA000972 — ALO LOGISTICS LLP`: **₹23,40,991 DEBIT, zero purchase invoices, zero payments** — the whole balance was built by manual journal entries:

```sql
SELECT "TransId","RefDate",TO_DECIMAL("Debit",18,2),TO_DECIMAL("Credit",18,2),"LineMemo"
FROM JIVO_MART_HANADB.JDT1 WHERE "ShortName"='VENDA000972' ORDER BY "RefDate";
```

| TransId | Date | Debit ₹ | Memo |
|---|---|---|---|
| 25605 | 2025-06-21 | 1,16,329 | APPROVAL DEBIT TO TRANSPORTER INVOICE NO. DL/SL/2597/24-25, DL/SL/2698/24-25 |
| 45713 | 2025-10-30 | 11 lines, ₹6,041–₹1,62,085 each | `WellnessIN <invoice>` (damage/shortage claims) |
| 46405 | 2025-11-06 | 8,94,955.50 | **Pending RTV Debit to Transporter** |
| 53399 | 2025-12-08 | 20,542 | DTDC clearance, Kundli warehouse |

This is a genuine recoverable claim against a transporter, raised and then forgotten. Nothing offsets it because there are no bills to net against.

---

## H9 — open A/P credit notes never set off: ₹7.04 L net recoverable

```sql
SELECT r."CardCode", MAX(r."CardName") AS VENDOR, COUNT(*) AS N_CN,
       TO_DECIMAL(SUM(r."DocTotal"-r."PaidToDate"),18,2) AS OPEN_CN,
       TO_DECIMAL(MAX(c."Balance"),18,2) AS VENDOR_BAL, MIN(r."DocDate") AS OLDEST
FROM   JIVO_OIL_HANADB.ORPC r JOIN JIVO_OIL_HANADB.OCRD c ON c."CardCode"=r."CardCode"
WHERE  r."CANCELED"='N' AND r."DocStatus"='O'
GROUP BY r."CardCode" ORDER BY 4 DESC;
```

Totals: Oil **₹27,40,815** (321 notes, oldest 2024-09-30) · Mart ₹15.51 Cr *of which ₹15.41 Cr is intercompany JIVO WELLNESS* → external ₹10.54 L · Beverages ₹1,67,560.

Only the notes sitting on vendors we have **already squared up with** are real cash. Those:

| Company | Vendor | Open CN ₹ | Vendor balance |
|---|---|---|---|
| OIL | BEE HIVE FARMS PVT LTD | 6,37,326 | +4,05,317 DR (cap) |
| OIL | OM LOGISTICS LTD | 3,81,553 | +1,21,321 DR (cap) |
| OIL | S M PLAST & CHEMICALS | 35,025 | 0 |
| OIL | M M OVERSEAS | 23,322 | 0 |
| OIL | MIRACLE CONTAINER PVT LTD | 15,941 | +15,941 DR |
| OIL | ARNAV TRANSPORT SERVICE | 15,000 | +15,11,889 DR |
| OIL | UNMEET SINGH IMPREST | 12,807 | +5,410 DR |
| OIL | INTERNATIONAL CO FOR OILS & AGRI FOOD | 9,086 | +9,086 DR |
| OIL | RELIANCE JIO INFOCOM LTD | 1,047 | +1,047 DR |
| MART | BARAL LOGISTICS PVT LTD | 21,539 | ~0 |
| MART | AMAZON SELLER SERVICES | 23,254 | +18,45,499 DR |
| MART | TRUEX / VISHWAKARMA / COMMERCIAL TRANSPORT | 20,000 | 0 |

Net (excluding VIJAY INDUSTRIES ₹4,21,402, already counted in H7): **₹7,03,989**.
RELIANCE JIOMART's ₹6,55,787 of open notes is **excluded** — that account is ₹8,54,755 in credit, so the notes only reduce what we still owe; no cash at stake.

---

## H1 — same vendor, same bill number, booked twice: ₹5.11 L

```sql
SELECT "CardCode", MAX("CardName") AS VENDOR, "NumAtCard", COUNT(*) AS CNT,
       TO_DECIMAL(SUM("DocTotal"),18,2) AS TOT, TO_DECIMAL(SUM("PaidToDate"),18,2) AS PAID,
       TO_DECIMAL(SUM("DocTotal")-MAX("DocTotal"),18,2) AS DUPVAL,
       MIN("DocDate") AS D1, MAX("DocDate") AS D2, STRING_AGG(TO_VARCHAR("DocNum"),',') AS DOCNUMS
FROM   JIVO_OIL_HANADB.OPCH
WHERE  "CANCELED"='N' AND "NumAtCard" IS NOT NULL AND LENGTH(TRIM("NumAtCard"))>2
GROUP BY "CardCode","NumAtCard" HAVING COUNT(*)>1 ORDER BY 7 DESC;
```

Raw: **39 groups / 78 documents / ₹16,47,560** in Oil; **zero** in Mart and Beverages.

**Most of it is noise** — small vendors (RAM BHAJ SURESH KUMAR, JD TRAVELS, MULTILAYER INDUSTRIES, NATIONAL TIN) restart their bill serials every financial year, so the two documents sit ~365 days apart. Tightening to *same amount within 270 days* leaves exactly one:

| Vendor | Bill no. | Docs | Dates | ₹ each | Status |
|---|---|---|---|---|---|
| **RAJ TECHNOPACK PVT LTD** (VENDA000933) | `SNP-0002/25-26` | 625034446, 625094331 | 2025-03-31 & 2025-09-01 | 1,70,078 | **both fully paid** |

Plus two clusters that are booked twice but **not yet paid** — block them before they are:

| Vendor | Bill no.(s) | Dates | Dup ₹ | PaidToDate |
|---|---|---|---|---|
| OCTAVOS ENTERPRISES SOLUTION P LTD | `DN-00652/2024-25` | 2025-03-19 & 2026-03-31 | 2,59,754 | **0** |
| RELIANCE RETAIL LTD C&C | 7 bills (`A31G1100005605` etc.) | 2025-03-31 & 2026-03-31 | 81,200 | **0** |

**Total actionable: ₹5,11,032** (₹1,70,078 recover · ₹3,40,954 block). Intercompany `JIVO AGRI BUSINESS / JWPL/TN/1` adds ₹1,35,000 (netted internally).

---

## H11 — one bill number, two vendor codes, ₹80 L out the door

```sql
SELECT a."CardCode",a."CardName",b."CardCode",b."CardName",a."NumAtCard",
       a."DocNum",b."DocNum",a."DocDate",b."DocDate",TO_DECIMAL(a."DocTotal",18,2)
FROM   JIVO_OIL_HANADB.OPCH a JOIN JIVO_OIL_HANADB.OPCH b
  ON TRIM(a."NumAtCard")=TRIM(b."NumAtCard") AND ABS(a."DocTotal"-b."DocTotal")<1
 AND a."DocEntry"<b."DocEntry" AND a."CardCode"<>b."CardCode"
WHERE a."CANCELED"='N' AND b."CANCELED"='N' AND LENGTH(TRIM(a."NumAtCard"))>3 AND a."DocTotal">5000
ORDER BY 10 DESC;
```

### [[finding-yashpal-baru-land-invoice]]

| CardCode | Vendor | DocNum | Date | Bill no. | ₹ | Paid |
|---|---|---|---|---|---|---|
| VENDA001412 | YASHPAL | 625073221 | 2025-07-01 | **TAZ2025F15** | 40,00,000 | ✔ 625466957, 2025-06-27 |
| VENDA001413 | BARU | 625073222 | 2025-07-01 | **TAZ2025F15** | 40,00,000 | ✔ 625466956, 2025-06-27 |

Both narrated *"Being expense against new land … invoice number TAZ2025F15"* — and BARU's narration reads **"amounting to INR 40000/-"** while the document is ₹40,00,000. Two ₹40 L RTGS on the same day, one invoice number.

Most likely reading: land bought from two joint owners, each paid their share. But **one invoice number cannot legitimately serve two sellers**, and no sale deed reference exists in SAP. **₹40,00,000 at risk pending the registered deed.** Confidence: low-medium.

The other rows returned (ARVIND TULI / RANJIT SAIN TULI / AMIT SAIN TULI Mayapuri rent, ₹1.19 L + ₹1.04 L monthly) were checked month-by-month and are **legitimate** — three co-owners of one property, each invoicing their share, serials overlapping by coincidence.

---

## H10 — GRPO left open while the invoice was booked standalone: ₹6.60 L

```sql
SELECT g."DocNum",g."CardCode",g."CardName",g."NumAtCard",g."DocDate",
       TO_DECIMAL(g."DocTotal",18,2) AS GRPO_AMT,
       (SELECT STRING_AGG(TO_VARCHAR(i."DocNum"),',') FROM JIVO_OIL_HANADB.OPCH i
        WHERE i."CardCode"=g."CardCode" AND i."CANCELED"='N' AND TRIM(i."NumAtCard")=TRIM(g."NumAtCard")) AS INV_DOCS
FROM   JIVO_OIL_HANADB.OPDN g
WHERE  g."CANCELED"='N' AND g."DocStatus"='O'
  AND EXISTS (SELECT 1 FROM JIVO_OIL_HANADB.OPCH i WHERE i."CardCode"=g."CardCode"
              AND i."CANCELED"='N' AND TRIM(i."NumAtCard")=TRIM(g."NumAtCard") AND LENGTH(TRIM(g."NumAtCard"))>2);
```

| Company | GRPO | Vendor | Bill no. | GRPO ₹ | Invoice ₹ | Double-counted ₹ |
|---|---|---|---|---|---|---|
| OIL | 2025096919 | GOBIND RAM KANSHI RAM SALES CORP | 163 | 9,46,401 | 6,48,857 (625114294) | 6,48,857 |
| OIL | 1224206766 | RAM BHAJ SURESH KUMAR | 447 | 2,516 | 2,516 | 2,516 |
| BEV | 1 doc | — | — | 8,260 | — | 8,260 |

**Total ₹6,59,633.** Wider context (not double-billing, but stale GRNI): open GRPOs = Oil ₹4.44 Cr (337 docs, oldest 2024-10-28) · Bev ₹1.03 Cr (353 docs) · Mart ₹62.44 L (40 docs).

---

## H13 — the "trailing dot" fingerprint (SAP duplicate-ref bypass): inconclusive, ≤ ₹5.46 L

Operators who hit SAP's "vendor reference already exists" warning get past it by appending a dot. Searching for refs identical after stripping `.` and spaces, same amount:

```sql
SELECT "CardCode", MAX("CardName"), UPPER(REPLACE(REPLACE(TRIM("NumAtCard"),'.',''),' ','')) AS NKEY,
       COUNT(*) AS N, TO_DECIMAL(MAX("DocTotal"),18,2) AS AMT,
       TO_DECIMAL(SUM("DocTotal")-MAX("DocTotal"),18,2) AS EXTRA
FROM   JIVO_OIL_HANADB.OPCH WHERE "CANCELED"='N' AND LENGTH(TRIM("NumAtCard"))>2
GROUP BY "CardCode", UPPER(REPLACE(REPLACE(TRIM("NumAtCard"),'.',''),' ',''))
HAVING COUNT(*)>1 AND COUNT(DISTINCT TRIM("NumAtCard"))>1 AND COUNT(DISTINCT "DocTotal")=1
ORDER BY 6 DESC;
```

Oil 53 groups / ₹4,59,417 · Beverages 31 groups / ₹86,136 · Mart 1 group / ₹232.

**The top hit was verified and is CLEAN:** `ORGV000042 KARANPREET SINGH IMPREST` — three invoices of ₹1,13,447 on 2026-03-01 (`FEB 26/113447`, `FEB 26/113447.`, `FEB 26/113447..`). Narration on the second reads *"Invoice No FEB 26/340341"* and **3 × 1,13,447 = 3,40,341**, which is exactly the payment made on 2026-04-20 (DocNum 426466818). One foreign-travel claim split three ways, not a duplicate.

The remainder are imprest claims whose reference convention is `MONTH/EMPCODE/AMOUNT`, so identical small expenses in the same month legitimately collide. **Do not book this as savings** — treat as a voucher-review list.

---

## Killed hypotheses (evidence, so nobody re-runs them)

**H3 — no invoice is over-paid.** `SELECT COUNT(*) FROM …OPCH WHERE "CANCELED"='N' AND "PaidToDate" > "DocTotal"+1` → **0** in all three companies. SAP blocks it.

**H4 — no invoice is over-applied.** Grouping `VPM2` (`InvType`=18) by `InvoiceId` and comparing `SUM("SumApplied")` to `OPCH."DocTotal"` → **0 rows**.

**H15 — ₹15.96 Cr "paid on cancelled invoices" is an artifact, not money.**
```sql
SELECT COUNT(*), TO_DECIMAL(SUM("PaidToDate"),18,2) FROM JIVO_OIL_HANADB.OPCH
WHERE "CANCELED"='Y' AND "PaidToDate">1;   -- 113 docs, ₹15,96,22,184
```
Every one has `PaidToDate = DocTotal` exactly. SAP B1 closes a cancelled document by setting `PaidToDate = DocTotal`; the top row is ANJU MANGLA 626043125, which never received a payment. **Not a finding.** (Mart 41 / ₹2.81 Cr, Bev 8 / ₹20.91 L — same artifact.)

**H14 — ₹18.73 Cr of "duplicate journal entries" are reversal pairs.**
```sql
SELECT "RefDate","Memo","LocTotal",COUNT(*) FROM JIVO_OIL_HANADB.OJDT
WHERE "TransType"=30 AND "LocTotal">10000
GROUP BY "RefDate","Memo","LocTotal" HAVING COUNT(*)>1;   -- 83 groups, ₹18.73 Cr "extra"
```
Top five drilled into `JDT1`:
- *"BEING PAYMENT PROCESS BY ICICI TRAN NO.-208895,208904"* ₹1,24,53,500 × 5 (2026-05-23) → 3 entries DR bank / 2 entries CR bank. **Nets to one.**
- *"Salary Ziaul Nov 2025"* ₹19,33,295 × 2 (TransId 169945, 169999) → genuinely posted twice, **but reversed** by TransId 170003 *"Salary Ziaul Nov 2025(Reversal) - 169945"*. Monthly salary expense (accounts 5630001+5630013) runs ₹1.13–1.17 Cr every month and Nov-25 = ₹1,17,48,959 — no bulge. Account 2161011 "SALARY PAYABLE NOV" nets to **0**.
- *"COGS payable trfr to COGS"* ₹4.14 Cr × 3 — P&L reclass, no cash.
- Freight provision / reversal triples (Apr-25, Mar-25) — self-cancelling.
**Zero confirmed duplicate JEs.**

**H2 — twin payments to commodity vendors are real trucks, not duplicates.** SPEAR AGRO INDUSTRIES showed three ₹10,57,493 payments (2025-06-11, 06-26, 07-18) against one matching bill — but the full ledger shows a pay-on-dispatch pattern with a matching bill for every payment and a **balance of exactly ₹0**. Same for AWL AGRI (₹57,90,480 tanker price repeated), VAISHNODEVI, ILAHI CO, DIL EXIM.

**H12 — cross-company duplicates are trivial.** Joining `OPCH` across Oil↔Mart on `NumAtCard`+`CardName`+amount → **0 rows**. Oil↔Beverages → 4 rows totalling **₹17,307** (BHORIA LABOUR ₹14,107, ARNAV ₹1,500, imprest ₹1,700).

**H21 — no open A/P down-payment invoices** (`ODPO` with `DocStatus='O'`) in any company.

**H18 — untestable.** `OVPM."CounterRef"` (cheque / UTR) is **never populated**, and `TrsfrRef` is NULL on every row inspected. Duplicate-instrument detection is impossible from SAP alone.

---

## Control gaps found along the way

1. **No GSTIN on any vendor master.** `SELECT "LicTradNum" … GROUP BY … HAVING COUNT(*)>1` on `OCRD` where `CardType='S'` returns **zero rows because the field is empty for every vendor**. There is therefore *no* systemic duplicate-vendor control.
2. **Duplicate vendor masters exist.** Exact-name pairs: `MAHBOOB KHAN` (VENDA000988 / VENDA001738), `BIO TECH SALES AND SERVICES` (VENDA000114 / VENDA001612), `SHARMA ENTERPRISES` (VENDA001611 / VENDA000366), `LIFE ESSENTIALS PERSONAL CARE` (VENDA001022 / VENDA001102), `CHADHA SALES` (VENDA001055 / VENDA001038), `VINAY SANITARY EMPORIUM` (VENDA001088 / VENDA001674).
3. **Duplicate imprest cards on the same employee ID** — `AMAN MONGIA IMPREST JWPL0970` ×2 (ORGV000089 / ORGV000125), `GURCHARAN SINGH IMPREST JWPL1106` ×2 (ORGV000135 / ORGV000159). Also 5 `AMIT KUMAR IMPREST`, 4 `NEHA IMPREST`, 3 `VIKAS KUMAR IMPREST`, 3 `NEELAM IMPREST` cards. Oil carries **₹16,89,729** of open imprest debit across 28 accounts.
4. **Payment references are not captured** — see H18.

---

## Recommended sequence

1. **Run SAP Internal Reconciliation (Business Partner) for the top 63 vendors in H6** — this alone converts ₹359 Cr of phantom open payables into a truthful A/P ageing and removes the ₹13.80 Cr trap.
2. **Freeze payment on VENDA001603 (Anju Mangla)** until the ₹17.86 Cr already paid is applied to invoice 626043127.
3. **Bank-statement match** the four HS Filling twin payments (₹1.20 Cr) and the two ₹40 L land payments to Yashpal/Baru.
4. **Recover / offset** ALO Logistics ₹23.41 L, the ₹7.04 L of open credit notes, RAJ TECHNOPACK ₹1.70 L.
5. **Block** the OCTAVOS ₹2.60 L and Reliance Retail ₹0.81 L duplicate bills before they are paid.
6. **Turn on** mandatory vendor reference (`NumAtCard`) uniqueness, capture GSTIN on `OCRD`, and populate `CounterRef` on every outgoing payment.
7. **Stop paying on account.** Make invoice selection mandatory on `OVPM`.

---

Back-links: [[SAVINGS-MOC]] · [[vendor-money-stuck]] · [[expense-outliers]]
