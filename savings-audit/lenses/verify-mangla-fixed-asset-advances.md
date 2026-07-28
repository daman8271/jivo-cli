---
title: "Verification — Rs 13.16 Cr Mangla FIXED-ASSETS advances (finding #3)"
created: 2026-07-28
lens: verify-mangla-fixed-asset-advances
tags: [savings-audit]
---

# Verification — ₹13.16 Cr advanced to ANJU / RAHUL MANGLA (Oil, FIXED ASSETS)

Part of [[SAVINGS-MOC]]

Adversarial re-derivation of finding #3 from [[vendor-money-stuck]] (H20, `finding-mangla-related-party-advances`).
Claim under test: **₹13,16,21,400 of capital advanced to two individuals under FIXED ASSETS, largely uninvoiced**, classed *working-capital-release*, confidence *low*.

**Verdict: REFUTED as money — ₹0.** The balance is measured *exactly* right (it ties to the rupee), but it is **registered land capex at Bakharpur, mid-programme**, not releasable capital. Two of the three action items rest on a **contra-entry misread** and a **double-count**.

---

## V1 — Does the ₹13.16 Cr balance exist?  ✅ EXACT

```sql
SELECT c."CardCode", c."CardName", c."Balance", g."GroupName", c."frozenFor", c."CreateDate"
FROM JIVO_OIL_HANADB.OCRD c
LEFT JOIN JIVO_OIL_HANADB.OCRG g ON g."GroupCode"=c."GroupCode"
WHERE UPPER(c."CardName") LIKE '%MANGLA%' ORDER BY c."Balance" DESC;
```

| CardCode | Name | Type | Balance | Group | Created |
|---|---|---|---:|---|---|
| VENDA001603 | ANJU MANGLA | S | **₹11,30,73,663** | FIXED ASSETS | 2026-01-22 |
| VENDA001601 | RAHUL MANGLA | S | **₹1,85,47,737** | FIXED ASSETS | 2026-01-22 |
| CUSTA001136 | MANGLA TRADING CO | C | ₹0 | CHANDIGARH | 2026-07-25 |
| CUSTA000315 | MANGLA AGENCIES | C | ₹0 | PUNJAB | 2024-09-16 |

Sum = **₹13,16,21,400**. Identical to the claim. No Mangla debit in Mart (₹0) or Beverages (RAHUL MANGLA `VENDA001291` ₹0, MANGLA AGENCIES ₹278) — no cross-company inflation, no netting account hiding elsewhere.

Group context re-derived independently:

```sql
SELECT g."GroupName", COUNT(*) N,
       SUM(CASE WHEN c."Balance">0 THEN c."Balance" ELSE 0 END) DR
FROM JIVO_OIL_HANADB.OCRD c LEFT JOIN JIVO_OIL_HANADB.OCRG g ON g."GroupCode"=c."GroupCode"
WHERE c."CardType"='S' GROUP BY g."GroupName" ORDER BY DR DESC;
```

FIXED ASSETS debit pool = **₹13,44,24,636**. The two Manglas are **97.9%** of it. Finder's ₹13.44 Cr / ₹20.83 Cr framing is correct.

---

## V2 — Cash-flow re-derivation (different query shape)  ✅ TIES TO THE RUPEE

The finder derived from `JDT1`. I rebuilt it from **`OVPM` + `OPCH` + `ORCT`** instead — payment documents, not journal lines.

```sql
SELECT v."DocNum", v."DocDate", v."CardCode", v."DocTotal", v."TrsfrAcct",
       v."Canceled", v."WtSum", v."Comments"
FROM JIVO_OIL_HANADB.OVPM v
WHERE v."CardCode" IN ('VENDA001603','VENDA001601') ORDER BY v."DocDate";
```

| | ₹ |
|---|---:|
| Outgoing payments to ANJU (10 docs, none cancelled) | 17,86,06,104 |
| Outgoing payments to RAHUL (5 docs, none cancelled) | 5,05,97,737 |
| **Gross cash out (15 docs)** | **22,92,03,841** |
| less land invoice booked (`OPCH` 626043127) | −9,75,72,441 |
| less incoming receipt from RAHUL 2026-05-23 | −10,000 |
| **= residual vendor debit** | **13,16,21,400** ✅ |

Cancelled-doc check: exactly one payment cancelled — `126466905` ₹10,00,000 to RAHUL, 2026-01-09 — and `JDT1` carries its matching *"Reverse Entry for Payment No. 126466905"*. Correctly excluded on both sides. **No cancelled-doc contamination.**
All 15 payments are bank transfers (`TrsfrAcct` 2201102 / 2201209 / 2201101), zero cash. This is real money that left real bank accounts.

Scale check: total non-cancelled outgoing payments in Oil since 2026-01-01 = **₹240.09 Cr** over 2,547 docs. The Manglas are **9.5% of all cash paid out in the last seven months**.

---

## V3 — The ₹3.20 Cr "manual journal entry" is a CONTRA, not an advance  ❌ FINDER ERROR

The finder's action item (a) — *"supporting documentation for the ₹3.20 Cr manual journal entry of 2026-04-09"* — treats a `TransType 30` **debit** as unexplained money out. Pulling **both legs** of that entry:

```sql
SELECT j."ShortName", j."TransType", j."RefDate", j."Debit", j."Credit",
       j."LineMemo", j."TransId"
FROM JIVO_OIL_HANADB.JDT1 j
WHERE j."ShortName" IN ('VENDA001603','VENDA001601') ORDER BY j."RefDate", j."TransId";
```

| TransId | Party | Debit | Credit | Memo |
|---|---|---:|---:|---|
| 204325 | VENDA001603 ANJU | 3,20,40,000 | — | **TRF LAND** |
| 204325 | VENDA001601 RAHUL | — | 3,20,40,000 | **TRF LAND** |

**Same `TransId`. Same date. Nets to zero.** It is an internal reallocation of consideration *between the two co-owners* against the same Bakharpur land — no cash moved, no new exposure. Aggregate proof:

```sql
SELECT j."TransType", COUNT(*) N, SUM(IFNULL(j."Debit",0)) DR, SUM(IFNULL(j."Credit",0)) CR,
       SUM(IFNULL(j."Debit",0)-IFNULL(j."Credit",0)) NET
FROM JIVO_OIL_HANADB.JDT1 j
WHERE j."ShortName" IN ('VENDA001603','VENDA001601') GROUP BY j."TransType";
```

| TransType | N | Debit | Credit | Net |
|---|---:|---:|---:|---:|
| 18 A/P invoice | 3 | 9,75,72,441 | 19,51,44,882 | −9,75,72,441 |
| 24 incoming payment | 1 | — | 10,000 | −10,000 |
| **30 journal entry** | **2** | **3,20,40,000** | **3,20,40,000** | **0** |
| 46 outgoing payment | 17 | 23,02,03,841 | 10,00,000 | 22,92,03,841 |

Action item (a) is **dissolved**. It also halves item (b): RAHUL was paid ₹5.06 Cr, of which ₹3.20 Cr is already applied to the land via this transfer; only ₹1.85 Cr is genuinely un-vouched.

---

## V4 — The ₹9.76 Cr "open invoice" is already inside the ₹11.31 Cr  ❌ DOUBLE-COUNT

Action item (c) — *"apply the ₹11.31 Cr advance against the ₹9.76 Cr open invoice … to close a live double-payment exposure"* — implies ₹11.31 Cr of advance sits **alongside** an unpaid ₹9.76 Cr bill. It does not:

`17,86,06,104 + 3,20,40,000 − 9,75,72,441 = 11,30,73,663` — the invoice credit is **already netted into the balance**.

```sql
SELECT p."DocEntry", p."DocNum", p."DocDate", p."DocTotal", p."VatSum",
       p."PaidToDate", p."DocStatus", p."CANCELED", p."Comments"
FROM JIVO_OIL_HANADB.OPCH p WHERE p."CardCode" IN ('VENDA001603','VENDA001601');
```

| DocEntry | DocNum | Date | ₹ | VAT | Paid | Status | Cancelled | Comment |
|---|---|---|---:|---:|---:|---|---|---|
| 44227 | 626043125 | 2026-04-09 | 9,75,72,441 | 0 | 9,75,72,441 | C | **Y** | LAND IN BAKHARPUR |
| 44229 | 626043126 | 2026-04-09 | 9,75,72,441 | 0 | 9,75,72,441 | C | **C** (cancellation doc) | LAND IN BAKHARPUR |
| 44231 | 626043127 | 2026-04-09 | **9,75,72,441** | 0 | 0 | **O** | N | **BAKAHRPUR LAND** |

Only **one** live invoice (the first was cancelled and re-raised same day — not two purchases). RAHUL: **zero** purchase invoices ever, confirmed.

What survives is only the generic unreconciled-subledger risk already logged as `finding-ap-subledger-not-reconciled`: `DocStatus='O'`/`PaidToDate=0` means a payment run driven off the open-invoice report *could* re-pay ₹9.76 Cr. That is a **control fix, not incremental cash**, and counting it here would double-count H19.

---

## V5 — Is this leakage, or documented land capex?  ✅ DOCUMENTED CAPEX

```sql
SELECT l."DocEntry", l."AcctCode", a."AcctName", l."LineTotal"
FROM JIVO_OIL_HANADB.PCH1 l LEFT JOIN JIVO_OIL_HANADB.OACT a ON a."AcctCode"=l."AcctCode"
WHERE l."DocEntry" IN (44227,44229,44231);
```

The invoice debits GL **1203017 — "LAND KILA 20//17(8-0) KEVAT 5//4, KILA 12//24/2/2(6-15) KEVAT 26//25, KILA NO.20//4(8-0) KEVAT 241//226"**. Named khasra/kila-kevat revenue-record survey numbers = a real, identified, registered parcel.

```sql
SELECT a."AcctCode", a."AcctName", a."CurrTotal" FROM JIVO_OIL_HANADB.OACT a
WHERE UPPER(a."AcctName") LIKE '%LAND%' AND IFNULL(a."CurrTotal",0)<>0;
```

| Account | ₹ |
|---|---:|
| 1203001 LAND (KILA 20//14 KEVAT 58) | 2,17,16,459 |
| 1203008 LAND (KILA 20//7 KEVAT 57) | 2,16,94,159 |
| 1203010 LAND (KILA 20//8/2 KEVAT 249//231) | 1,13,00,202 |
| 1203012 LAND | 3,19,51,221 |
| 1203017 LAND (Bakharpur, this deal) | 9,77,12,441 |
| **Total capitalised land** | **₹18,43,74,482** |
| 1107011 SECURITY FOR POLLUTION BAKHARPUR LAND | 3,50,000 |

JIVO Oil is running a **multi-parcel Bakharpur land assembly** — five parcels already capitalised, plus a pollution-clearance security deposit for the same site (the ₹3.50 L flagged in `finding-stale-security-deposits`, which now reads as *live*, not stale). Payments to the Manglas run **2026-01-09 → 2026-07-20 — eight days ago**. This is an in-flight acquisition, not dormant money.

---

## V6 — Adversarial tests that came back clean

| Test | SQL shape | Result |
|---|---|---|
| Cancelled payments inflating the total | `OVPM."Canceled"='Y'` cross-checked to `JDT1` reversal | 1 doc ₹10 L, correctly reversed both sides |
| Duplicate payment (2× ₹1 Cr to ANJU on 2026-01-27) | `JDT1` on bank GL `2201102`, 26–28 Jan | **three distinct bank credits** posted (2 ANJU, 1 RAHUL) — separate documents, real cash each. Two same-day equal tranches to one payee is worth a bank-statement tick, but nothing in SAP shows duplication |
| Frozen / dormant vendor | `OCRD."frozenFor"` | both `'N'`, last payment 8 days ago |
| GST wrongly included | `OPCH."VatSum"` | **₹0** — land is outside GST, no gross-up error |
| Hidden offsetting credit elsewhere | `OCRD` scan across all 3 schemas | none; Bev RAHUL MANGLA = ₹0 |
| Overlap with `finding-unapplied-advances-vs-open-bills` (₹4.05 Cr) | that query excludes `GroupName='FIXED ASSETS'` | **no double-count** — correctly disjoint |

---

## V7 — [[finding-mangla-tds-194ia-question]] — open question, not a ₹ claim

```sql
SELECT SUM(v."WtSum") WT, SUM(v."DocTotal") PAID, COUNT(*) N FROM JIVO_OIL_HANADB.OVPM v
WHERE v."CardCode" IN ('VENDA001603','VENDA001601') AND v."Canceled"='N';
-- WT = 0, PAID = 22,92,03,841, N = 15

SELECT j."RefDate", j."Debit", j."Credit", j."LineMemo" FROM JIVO_OIL_HANADB.JDT1 j
WHERE j."Account"='2133013';   -- TDS ON PURCHASE OF PROPERTY @1% 194IA
```

`WtSum = 0` on every payment; both partners are `WTLiable='N'`. The **only** 194-IA TDS ever booked in the Oil company is **₹62,000** (2025-07/08, a different vendor, Preet Pratap Singh). So ₹22.92 Cr of land consideration carries no s.194-IA deduction in SAP.

⚠️ **Honest caveat — do not book this as an exposure.** s.194-IA expressly excludes **rural agricultural land**, and kila/kevat revenue-record parcels at Bakharpur are agricultural land. If the parcels are rural agricultural, no TDS is due and the treatment is correct. Also, 194-IA is commonly discharged via Form 26QB **outside** the ERP. Verify with the tax team; ₹0 booked here.

---

## Verdict

| Question | Answer |
|---|---|
| Does ₹13,16,21,400 exist as stated? | **Yes — exact, tied two ways** |
| Is it recoverable cash? | **No** |
| Is it releasable working capital? | **No** |
| Verified savings | **₹0** |

**REFUTED.** The measurement is flawless; the *classification* is not. This is ₹22.92 Cr of bank-transferred consideration in a live, documented, multi-parcel land acquisition, of which ₹9.76 Cr is already capitalised to a named-survey-number land GL and ₹13.16 Cr is consideration paid ahead of registration. Nothing here can be recovered, netted or released without abandoning the land deal. The finder's own action text concedes *"treat as a related-party disclosure item, not savings"* — the honest ₹ is therefore **0**, and carrying ₹13.16 Cr in a savings register would overstate it by the full amount.

What genuinely survives, all **non-monetary**:
1. **Presentation defect (real).** ₹13.16 Cr of capital advance sits as a debit inside GL `2110005 SUNDRY CREDITOR DOMESTIC PURCHASE` — a current-liability head. Under Schedule III it belongs in **Capital Advances / Other Non-Current Assets**. Reclassify before year-end.
2. **Related-party disclosure (real).** Two individuals, 9.5% of seven months' total cash out. Needs AS-18 / s.188 treatment and a board-approved valuation.
3. **₹1.85 Cr to RAHUL MANGLA still un-vouched** (down from the implied figure once the ₹3.20 Cr contra is removed) — get the agreement-to-sell.
4. **Invoice 626043127 shows `DocStatus='O'` with the advance unapplied** — reconcile it so no payment run can re-pay ₹9.76 Cr. Already counted under `finding-ap-subledger-not-reconciled`; **do not add it here**.
5. **Two ₹1 Cr transfers to ANJU on the same day (2026-01-27)** — tick to the bank statement. SAP shows two genuine separate postings, so this is a tick-and-tie item, not a finding.
