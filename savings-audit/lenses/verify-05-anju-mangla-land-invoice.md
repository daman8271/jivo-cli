---
title: "Verification #5 — Anju Mangla ₹9.76 Cr land invoice 'unpaid' while ₹17.86 Cr paid"
created: 2026-07-28
lens: adversarial-verification
tags: [savings-audit, verification, accounts-payable, sap-b1, fixed-assets, related-party]
---

# 🔎 Adversarial verification of finding #5 — ANJU MANGLA

Part of [[SAVINGS-MOC]] · verifies [[finding-anju-mangla-land-invoice-open]] from [[duplicate-payments]]

**Company:** `JIVO_OIL_HANADB` (Oil) · **Claim under test:** ₹9,75,72,441 one-time-recovery
**VERDICT: REFUTED — ₹0 recoverable.** Every *fact* in the finding is accurate to the rupee. The *money* is not: the ₹9.76 Cr invoice capitalises a land parcel and is matched **exactly, to the rupee**, by advances already paid before the invoice date. Reconciling it in SAP releases zero cash.

---

## Result summary

| # | Hypothesis tested | Verdict | ₹ |
|---|---|---|---|
| V1 | The three OPCH bookings / one live @ ₹9,75,72,441, `DocStatus='O'`, `PaidToDate=0` | **CONFIRMED as stated** | 9,75,72,441 |
| V2 | OVPM payments to Anju = ₹17,86,06,104 (10 docs, none cancelled) | **CONFIRMED as stated** | 17,86,06,104 |
| V3 | OCRD Balance = +₹11,30,73,663 DEBIT | **CONFIRMED as stated** | 11,30,73,663 |
| V4 | Rahul Mangla ₹1,85,47,737 debit, zero invoices ever | **CONFIRMED as stated** | 1,85,47,737 |
| V5 | Balance reconciles to invoices+payments alone? | **NO — a hidden ₹3.20 Cr contra JE was missed** | 3,20,40,000 |
| V6 | Is the invoice a *payable* at all? | **NO — it debits fixed asset GL 1203017 (LAND)** | — |
| V7 | Pre-invoice advances + contra JE vs invoice value | **EXACT MATCH TO THE RUPEE** | 9,75,72,441 |
| V8 | Are the twin ₹1 Cr transfers of 2026-01-27 a duplicate payment? | **NO** — both required by V7; distinct ICICI debits | 0 |
| V9 | Any payment ever applied to the live invoice (VPM2 / PaidToDate)? | none — pure on-account artifact | 0 |
| V10 | Is the residual ₹13.16 Cr an overpayment or an in-flight capital advance? | **in-flight** (new land GL opened 2026-07-03) | watch item |
| V11 | Price-per-acre sanity vs the 2025 Bakharpur parcels | +52% YoY — plausible, not provable | caveat |
| V12 | TDS 194-IA deducted on ₹9.76 Cr? | only ₹62,000 in 2133013 — likely agri-land exemption | caveat |
| V13 | Mangla exposure in Mart / Beverages | nil (₹0 and ₹278) | 0 |
| V14 | Impact on parent hypothesis H6 | H6 falls ₹13.43 Cr → ₹3.67 Cr (Oil) | −9,75,72,441 |

---

## V1–V4 — the finding's raw facts all replicate exactly

```sql
SELECT "CardCode","CardName","CardType",TO_DECIMAL("Balance",18,2) AS BAL,"CreateDate"
FROM   JIVO_OIL_HANADB.OCRD WHERE UPPER("CardName") LIKE '%MANGLA%';
```

| CardCode | Name | Type | Balance | Created |
|---|---|---|---|---|
| VENDA001603 | ANJU MANGLA | S | **+11,30,73,663 DR** | 2026-01-22 |
| VENDA001601 | RAHUL MANGLA | S | **+1,85,47,737 DR** | 2026-01-22 |
| CUSTA001136 | MANGLA TRADING CO | C | 0 | 2026-07-25 |
| CUSTA000315 | MANGLA AGENCIES | C | 0 | 2024-09-16 |

```sql
SELECT "DocEntry","DocNum","DocDate","NumAtCard",TO_DECIMAL("DocTotal",18,2) AS TOT,
       TO_DECIMAL(IFNULL("VatSum",0),18,2) AS VAT, TO_DECIMAL(IFNULL("PaidToDate",0),18,2) AS PAID,
       "DocStatus","CANCELED","DocType","Comments"
FROM   JIVO_OIL_HANADB.OPCH WHERE "CardCode" IN ('VENDA001603','VENDA001601') ORDER BY "DocEntry";
```

| DocEntry | DocNum | Date | Ref | ₹ | VAT | Paid | Status | Cancel | Comment |
|---|---|---|---|---|---|---|---|---|---|
| 44227 | 626043125 | 2026-04-09 | TAZ2026C17 | 9,75,72,441 | 0 | 9,75,72,441 | C | **Y** | LAND IN BAKHARPUR |
| 44229 | 626043126 | 2026-04-09 | TAZ2026C17 | 9,75,72,441 | 0 | 9,75,72,441 | C | **C** | *Based On A/P Invoices 626043125* |
| 44231 | 626043127 | 2026-04-09 | TAZ2026C17 | **9,75,72,441** | 0 | **0** | **O** | **N** | BAKAHRPUR LAND |

Rahul Mangla: **zero rows** in `OPCH`, `OPOR`, `ODPO`, `OPDN`, `ORPC`. Confirmed.

```sql
SELECT "CardCode",COUNT(*) AS N_PAY,TO_DECIMAL(SUM("DocTotal"),18,2) AS CASH_OUT
FROM   JIVO_OIL_HANADB.OVPM
WHERE  "CardCode" IN ('VENDA001603','VENDA001601') AND "Canceled"='N' GROUP BY "CardCode";
```

| CardCode | # payments | Cash out |
|---|---|---|
| VENDA001603 ANJU | 10 | **₹17,86,06,104** |
| VENDA001601 RAHUL | 5 | **₹5,05,97,737** |
| **Combined** | **15** | **₹22,92,03,841** |

All 15 are `PayNoDoc='Y'` (on account), `DocType='S'`, `TrsfrSum` = full amount. `CounterRef`/`TrsfrRef` NULL throughout.

---

## V5 — the finding missed a ₹3.20 Cr contra JE; only the full GL reconciles

The finding's own arithmetic does **not** close: ₹17.86 Cr − ₹9.76 Cr = ₹8.10 Cr, but the balance is ₹11.31 Cr. A ₹3.20 Cr gap sat unexplained. The full ledger trace finds it:

```sql
SELECT j."TransId",j."RefDate",j."TransType",j."BaseRef",j."ShortName",
       TO_DECIMAL(j."Debit",18,2) AS DR, TO_DECIMAL(j."Credit",18,2) AS CR, j."LineMemo"
FROM   JIVO_OIL_HANADB.JDT1 j JOIN JIVO_OIL_HANADB.OJDT h ON h."TransId"=j."TransId"
WHERE  j."ShortName" IN ('VENDA001603','VENDA001601') ORDER BY j."RefDate", j."TransId";
```

The decisive row — a **manual contra between the two co-sellers** (`TransType`=30, JE 204325, doc 426900061, 2026-04-09):

| TransId | Account | Party | DR | CR | Memo |
|---|---|---|---|---|---|
| 204325 | 2110005 SUNDRY CREDITOR DOM. PURCHASE | **VENDA001603 ANJU** | **3,20,40,000** | — | **TRF LAND** |
| 204325 | 2110005 SUNDRY CREDITOR DOM. PURCHASE | **VENDA001601 RAHUL** | — | **3,20,40,000** | **TRF LAND** |

Full reconciliation (both accounts now close to the rupee):

| VENDA001603 ANJU | ₹ |
|---|---|
| DR payments (10) | 17,86,06,104 |
| DR cancellation doc 626043126 | 9,75,72,441 |
| DR contra "TRF LAND" | 3,20,40,000 |
| CR invoice 626043125 | (9,75,72,441) |
| CR invoice 626043127 | (9,75,72,441) |
| **= OCRD Balance** | **11,30,73,663 ✓** |

| VENDA001601 RAHUL | ₹ |
|---|---|
| DR payments incl. cancelled ₹10 L | 5,15,97,737 |
| CR reversal of cancelled payment 126466905 | (10,00,000) |
| CR contra "TRF LAND" | (3,20,40,000) |
| CR cash received back (ORCT 526246797, *"BEING CASH RECEIVED FROM ISHWENDRA JI"*) | (10,000) |
| **= OCRD Balance** | **1,85,47,737 ✓** |

---

## V6 — this is not a payable. It is a fixed asset.

```sql
SELECT j."TransId",j."Account",a."AcctName",j."ShortName",
       TO_DECIMAL(j."Debit",18,2) AS DR, TO_DECIMAL(j."Credit",18,2) AS CR
FROM   JIVO_OIL_HANADB.JDT1 j LEFT JOIN JIVO_OIL_HANADB.OACT a ON a."AcctCode"=j."Account"
WHERE  j."TransId"=204324 ORDER BY j."Line_ID";
```

| Account | Name | DR | CR |
|---|---|---|---|
| 2110005 | SUNDRY CREDITOR DOMESTIC PURCHASE (VENDA001603) | — | 9,75,72,441 |
| **1203017** | **LAND KILA 20//17(8-0)KEVAT 5//4, KILA 12//24/2/2(6-15)KEVAT 26//25, KILA NO.20//4(8-0)KEVAT 241//226** | **9,75,72,441** | — |

`VatSum`=0, `DocType`='S'. GL 1203017 now stands at **₹9,77,12,441** (invoice + ₹1,40,000 of registration charges billed by VENDA001693 on 2026-05-08). This is JIVO's standing pattern — Bakharpur agricultural land bought parcel-by-parcel, each kila getting its own asset account:

| GL | Parcel | Booked | Sellers |
|---|---|---|---|
| 1203001 | KILA 20//14 KEVAT 58 | ₹2,17,16,459 | VENDA001260 (Apr-2025) |
| 1203008 | KILA 20//7 KEVAT 57 | ₹2,16,94,159 | VENDA000144 (Apr-2025) |
| 1203010 | KILA 20//8/2 KEVAT 249//231 | ₹1,13,00,202 | **four co-sellers** VENDA001411/1412/1413/1414 (Jul-2025) |
| **1203017** | **3 kilas (22 kanal 15 marla ≈ 2.84 ac)** | **₹9,77,12,441** | **VENDA001603 ANJU (+ VENDA001601 RAHUL, not yet invoiced)** |

> Side note for [[finding-yashpal-baru-land-invoice]]: GL 1203010 shows that one bill ref (`TAZ2025F15`) legitimately serves **four** co-owners of a single kila (₹40 L + ₹40 L + ₹16.5 L + ₹16.5 L = ₹1.13 Cr, all landing on one asset account). The "one invoice number cannot serve two sellers" premise is contradicted by JIVO's own documented convention.

---

## V7 (DECISIVE) — the advance was engineered to equal the invoice exactly

```sql
SELECT 'PRE_INV_PAY_ANJU' AS K, TO_DECIMAL(SUM("DocTotal"),18,2) AS AMT
FROM JIVO_OIL_HANADB.OVPM WHERE "CardCode"='VENDA001603' AND "Canceled"='N' AND "DocDate" <= '2026-04-09'
UNION ALL SELECT 'POST_INV_PAY_ANJU', TO_DECIMAL(SUM("DocTotal"),18,2)
FROM JIVO_OIL_HANADB.OVPM WHERE "CardCode"='VENDA001603' AND "Canceled"='N' AND "DocDate" > '2026-04-09'
UNION ALL SELECT 'TRF_LAND_JE', TO_DECIMAL(SUM("Debit"),18,2)
FROM JIVO_OIL_HANADB.JDT1 WHERE "TransId"=204325 AND "ShortName"='VENDA001603'
UNION ALL SELECT 'INVOICE_LIVE', TO_DECIMAL(SUM("DocTotal"),18,2)
FROM JIVO_OIL_HANADB.OPCH WHERE "DocEntry"=44231;
```

| Key | ₹ |
|---|---|
| PRE_INV_PAY_ANJU (advances up to invoice date) | 6,55,32,441 |
| TRF_LAND_JE (share reallocated from Rahul) | 3,20,40,000 |
| **Sum** | **9,75,72,441** |
| INVOICE_LIVE 626043127 | **9,75,72,441** |
| **Difference** | **₹0** |
| POST_INV_PAY_ANJU | 11,30,73,663 *(= the entire current debit balance)* |

**₹6,55,32,441 + ₹3,20,40,000 = ₹9,75,72,441 — exact to the rupee.** The accounts team deliberately transferred ₹3.20 Cr of Rahul's advance onto Anju so that her advance equalled her deed consideration precisely. The invoice is therefore *fully funded* by money already paid. It shows "open" only because every payment was keyed `PayNoDoc='Y'`. Internal Reconciliation would close it and move **₹0**.

Symmetrically, Rahul's residue after the contra is exactly **₹1,00,00,000** (₹4,20,50,000 − ₹3,20,40,000 − ₹10,000), then topped up by ₹85,47,737 on 2026-07-20. Round, deliberate numbers throughout — not the fingerprint of accidental duplication.

---

## V8 — the twin ₹1 Cr transfers of 2026-01-27 are NOT a duplicate

```sql
SELECT j."TransId",j."Account",a."AcctName",j."ShortName",
       TO_DECIMAL(j."Debit",18,2) AS DR,TO_DECIMAL(j."Credit",18,2) AS CR,j."LineMemo",j."Ref1"
FROM   JIVO_OIL_HANADB.JDT1 j LEFT JOIN JIVO_OIL_HANADB.OACT a ON a."AcctCode"=j."Account"
WHERE  j."TransId" IN (180512,180514,180517) ORDER BY j."TransId",j."Line_ID";
```

| TransId | Bank | Ref1 | Amount | Party |
|---|---|---|---|---|
| 180512 | ICICI 2201102 | 126467110 | 1,00,00,000 | ANJU |
| 180514 | ICICI 2201102 | 126467111 | 1,00,00,000 | ANJU |
| 180517 | ICICI 2201102 | 126467112 | 1,00,00,000 | RAHUL |

Three **separate** ₹1 Cr bank debits on the same day — ₹2 Cr to Anju, ₹1 Cr to Rahul, i.e. a 2:1 split consistent with their shares. Both Anju legs are **required** for the V7 identity to hold; drop either one and the pre-invoice advance no longer equals the deed value. The identical narration is the bank's own `TRFR TO:ANJU MANGLA` string, repeated because the transfer was split (a common corporate net-banking per-transaction cap). **Not a duplicate payment.** (Only oddity: JE 180512's memo literally reads `-10000000` — a keying slip in the memo field, no accounting effect.)

---

## V9 — nothing has ever been applied against the live invoice

```sql
SELECT COUNT(*) AS N, TO_DECIMAL(IFNULL(SUM("SumApplied"),0),18,2) AS APPLIED
FROM   JIVO_OIL_HANADB.VPM2
WHERE  "DocEntry" IN (SELECT "DocEntry" FROM JIVO_OIL_HANADB.OVPM
                      WHERE "CardCode" IN ('VENDA001603','VENDA001601'));
```

3 rows / ₹1,98,260 — none touching DocEntry 44231 (`PaidToDate` is still 0). Confirms a pure on-account artifact, exactly the [[duplicate-payments]] H20 root cause. The ₹9.76 Cr on `PaidToDate` of the **cancelled** 626043125 is the SAP cancellation artifact the finder himself correctly killed in H15 — it must not be double-counted as evidence here.

---

## V10 — the residual ₹13.16 Cr is an in-flight capital advance, not a leak

```sql
SELECT j."Account",a."AcctName",MIN(j."RefDate") AS D1,MAX(j."RefDate") AS D2,COUNT(*) AS N,
       TO_DECIMAL(SUM(j."Debit")-SUM(j."Credit"),18,2) AS NET
FROM   JIVO_OIL_HANADB.JDT1 j JOIN JIVO_OIL_HANADB.OACT a ON a."AcctCode"=j."Account"
WHERE  UPPER(a."AcctName") LIKE '%LAND%' AND j."RefDate">='2026-01-01'
GROUP  BY j."Account",a."AcctName" ORDER BY 6 DESC;
```

| GL | Name | First | Last | Net |
|---|---|---|---|---|
| 1203017 | LAND KILA 20//17 … | 2026-04-09 | 2026-05-08 | 9,77,12,441 |
| **1212016** | **PEB SHED NEW LAND 2 ACRE** | **2026-07-03** | 2026-07-12 | 1,73,816 |

A capex account literally named **"NEW LAND 2 ACRE"** was opened on 2026-07-03, and ₹7,16,21,400 went to the two Manglas seventeen days later (2026-07-20). The acquisition is **live right now**. Combined outstanding advance:

| | ₹ |
|---|---|
| Cash paid to both Manglas | 22,92,03,841 |
| Less cash received back (ORCT) | (10,000) |
| Less land capitalised (invoice) | (9,75,72,441) |
| **= combined debit balance** | **13,16,21,400** |

That ₹13.16 Cr is **money already spent on an asset**, not money JIVO can call back. It is a **documentation/governance watch item** — ₹13.16 Cr of unsecured advance to two related-party individuals with no purchase order, no down-payment invoice, no `NumAtCard`, and no deed reference anywhere in SAP — but it is *not* a saving, *not* a recovery, and *not* the ₹9.76 Cr the finding claimed.

---

## V11–V13 — caveats and cross-checks

**V11 — price sanity (inconclusive, flag only).** Parcel 1203017 = 8-0 + 6-15 + 8-0 kanal-marla = 22 kanal 15 marla ≈ **2.84 acres** → **₹3.43 Cr/acre**. The Apr–Jul 2025 Bakharpur parcels ran **₹2.15–2.26 Cr/acre**. A **+52% escalation in ~12 months** on the Kundli/Sonipat belt is plausible (and frontage/access varies parcel to parcel), but it cannot be validated from SAP. Independent circle-rate/valuation check recommended — this, not the invoice status, is where real money could hide.

**V12 — TDS u/s 194-IA.** `2133013 TDS ON PURCHASE OF PROPERTY @1% 194IA` carries only **₹62,000** — 1% of ₹62 lakh, nowhere near 1% of ₹9.76 Cr (₹9.76 L). Most likely correct: rural **agricultural** land (kila/kevat revenue records) is excluded from the s.194-IA definition of immovable property. Worth a one-line confirmation from the tax advisor; not scored.

**V13 — other companies.** `MANGLA` in Mart = ₹0; in Beverages, `VENDA001291 RAHUL MANGLA` = **₹0** and `CUSTA000315` = ₹278. No cross-company exposure.

---

## V14 — knock-on effect on the parent hypothesis H6

```sql
SELECT COUNT(*) AS N_VENDORS,
       TO_DECIMAL(SUM(LEAST(c."Balance",o.OPENB)),18,2) AS H6_TOTAL,
       TO_DECIMAL(SUM(CASE WHEN c."CardCode"<>'VENDA001603'
                           THEN LEAST(c."Balance",o.OPENB) ELSE 0 END),18,2) AS H6_EX_ANJU
FROM   JIVO_OIL_HANADB.OCRD c
JOIN  (SELECT "CardCode", SUM("DocTotal"-IFNULL("PaidToDate",0)) AS OPENB
       FROM JIVO_OIL_HANADB.OPCH WHERE "CANCELED"='N' AND "DocStatus"='O'
       GROUP BY "CardCode") o ON o."CardCode"=c."CardCode"
WHERE  c."CardType"='S' AND c."Balance">10000 AND o.OPENB>10000;
```

| Metric | ₹ |
|---|---|
| H6 Oil total (replicates finder exactly) | 13,43,21,498 |
| **Anju Mangla's share of it** | **9,75,72,441 (72.6%)** |
| **H6 Oil excluding Anju** | **3,67,49,057** |

The parent H6 figure of **₹13.80 Cr** should be restated to **≈₹4.05 Cr** (Oil ₹3.67 Cr + Mart ₹33.01 L + Bev ₹4.11 L) — and even that remainder is a *risk-of-future-double-payment* metric, not recoverable cash.

---

## Verdict

**REFUTED — ₹0.**

| Test | Outcome |
|---|---|
| Facts as stated | every figure replicates to the rupee |
| Cancelled docs mis-included? | no — finder handled `CANCELED` 'Y'/'C' correctly |
| GST wrongly included? | no — `VatSum`=0, land is not GST-bearing |
| Sign error? | no — full GL trace confirms net DEBIT |
| **Double counting?** | **YES — the ₹9.76 Cr invoice and the advances that fund it are the same money counted twice** |
| **Contra/netting account missed?** | **YES — the ₹3,20,40,000 "TRF LAND" JE between the co-sellers** |
| Duplicate that is legitimate? | **YES — the twin ₹1 Cr transfers are a split RTGS, both needed for the exact match** |
| Is any cash recoverable? | **No.** Internal Reconciliation moves ₹0. |

**What is genuinely true and worth doing (₹0 savings, real control value):**
1. Run SAP Internal Reconciliation on VENDA001603 — cosmetic but it removes a ₹9.76 Cr false entry from the open-payables report and stops this finding being re-raised every quarter.
2. Get the registered sale deeds for **both** Manglas on file and key Rahul's ₹13.16 Cr share as an invoice against GL 1212016 / a new land account. Today ₹13.16 Cr of company cash sits with two related-party individuals on **zero** supporting documents in SAP.
3. Have the **valuation**, not the invoice status, independently checked — ₹3.43 Cr/acre vs ₹2.20 Cr/acre a year earlier is the only place real money could actually be leaking here.
4. Restate [[duplicate-payments]] H6 from ₹13.80 Cr to ≈₹4.05 Cr.

---

Back-links: [[SAVINGS-MOC]] · [[duplicate-payments]] · [[finding-anju-mangla-land-invoice-open]] · [[finding-yashpal-baru-land-invoice]] · [[vendor-money-stuck]]
