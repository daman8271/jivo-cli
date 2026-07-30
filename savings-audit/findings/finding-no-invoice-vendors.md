---
title: "No-invoice vendors — ₹5.10 Cr of debit balances with zero A/P invoices"
created: 2026-07-28
verdict: REVISED
amount_verified_inr: 655011
amount_claimed_inr: 51041504
kind: working-capital-release
company: ALL
lens: duplicate-payments
rank: 10
tags: [savings-audit, finding]
---

# Finding #10 (REVISED) — no-invoice vendors

**Claimed:** ₹5,10,41,504 "paid out to 36 vendors that have never raised a single invoice."
**Re-derived bankable:** **₹6,55,011** (₹6.55 lakh).
**Interest released @ 7.3% CC rate:** **₹47,816 a year.**

## Plain-language summary for the CFO

The underlying data point is **completely correct and I could reproduce it to the rupee**: across all three companies there are 36 supplier accounts holding a debit balance of ₹5,10,41,504 against which SAP holds **not one A/P invoice** — not in `OPCH`, and not even as a manual journal (I checked: **zero `TransType`-18 lines** for any of the 36). So the control observation is real and the vendor-master hygiene point stands.

What does **not** stand is the characterisation of that ₹5.10 Cr as recoverable working capital. When you resolve what each balance actually is, **98.7% of it is money JIVO deliberately committed and cannot call back**:

| Bucket | ₹ | Parties | Bankable? |
|---|---:|---:|---|
| Advances against **live capital-goods / building POs** | 3,04,33,680 | 8 | ❌ committed capex |
| **Bakharpur LAND** consideration (Rahul Mangla) | 1,85,47,737 | 1 | ❌ fixed asset |
| **Journal-only** balances — no cash ever left the bank | 2,79,780 | 7 | ❌ not a payment |
| Open **A/P credit notes** we raised on vendors | 4,57,143 | 3 | ⚠️ real, but = lens H9 |
| Employee **IMPREST** accounts (not vendors) | 1,50,759 | 2 | ⚠️ payroll recovery |
| Fresh procurement float (<180 days, bill pending) | 5,17,393 | 8 | ❌ normal |
| **Stale advances ≥180 days, cash paid, no invoice, no PO** | **6,55,011** | **7** | ✅ **BANKABLE** |
| **Total** | **5,10,41,504** | **36** | |

Only the last row is money Accounts can actually go and get back.

## Verdict: REVISED — ₹6,55,011 bankable

### Why the big items died

**1. HS Filling & Packaging (Beverages, VENDA001347) — ₹2.40 Cr → NOT recoverable.**
This is the headline of the original finding and it is a **capex advance for bottling plant**, not a leak. The two open POs are for fixed-asset item codes:

```sql
SELECT p."DocNum", l."ItemCode", l."Dscription", l."LineTotal", l."LineStatus"
FROM   JIVO_BEVERAGES_HANADB.POR1 l
JOIN   JIVO_BEVERAGES_HANADB.OPOR p ON p."DocEntry" = l."DocEntry"
WHERE  p."CardCode" = 'VENDA001347';
```

| PO | Item | Description | ₹ (net) | Status |
|---|---|---|---:|---|
| 426228002 | FA0000424 | 240 BPM FULLY AUTOMATIC WATER PLANT | 48,00,000 | Open |
| 426228002 | FA0000425 | FULLY AUTOMATIC CSD PLANT | 52,00,000 | Open |
| 426228003 | FA0000426 | 300 BPM FULLY AUTOMATIC WATER PLANT | 1,85,00,000 | Open |

Gross PO value ₹3,36,30,000; cash paid ₹2,90,00,000; a ₹50,00,000 manual JE on 2026-05-14 (`AMOUNT RECD IN BEV`, contra `1110109 JIVO WELLNESS OIL INTERNAL`) reduced it to the ₹2.40 Cr balance. HS Filling is also a real, pre-existing supplier — it trades in Oil as `VENDA001046` and exists in Beverages as customer `CUSTA001104`, so it is not a shell. **The money bought a payment milestone on a live plant order, not nothing.**

**On the twin same-day payments** (₹70,00,000 × 2 on 2026-04-07; ₹50,00,000 × 2 on 2026-07-16): I could not prove duplication and I could not disprove it. `TrsfrRef` is **NULL on all five payments**, so SAP holds no bank reference to match — this is lens hypothesis H18 ("untestable"). Two facts argue *against* duplication: the pairs were keyed ~50 minutes apart under separate `TransId`s, and **total cash out (₹2.90 Cr) is still below the order value (₹3.36 Cr)** — the vendor has not been overpaid against the contract. Splitting a ₹1.40 Cr RTGS into 2 × ₹70 L is routine. **The bank-statement match is still the right action, but the ₹1.20 Cr is a contingent recovery, not bankable today.**

**2. Rahul Mangla (Oil, VENDA001601) — ₹1,85,47,737 → NOT recoverable. Land.**
This is the Bakharpur land assembly. The GL proves it outright:

```sql
SELECT j."TransId", h."TransType", h."RefDate", j."ShortName",
       j."Account", a."AcctName", j."Debit", j."Credit", j."LineMemo"
FROM   JIVO_OIL_HANADB.JDT1 j
JOIN   JIVO_OIL_HANADB.OJDT h ON h."TransId" = j."TransId"
LEFT   JOIN JIVO_OIL_HANADB.OACT a ON a."AcctCode" = j."Account"
WHERE  j."TransId" IN (SELECT DISTINCT "TransId" FROM JIVO_OIL_HANADB.JDT1
                       WHERE "ShortName" = 'VENDA001601');
```

Journal `204325` (2026-04-09, `TransType` 30) moves **₹3,20,40,000 from VENDA001601 (Rahul Mangla) to VENDA001603 (Anju Mangla)** with the line memo **`TRF LAND`**. Total cash to Rahul Mangla was ₹5,05,97,737; less the ₹3.20 Cr land transfer and a ₹10,000 receipt leaves exactly the ₹1,85,47,737 balance. The consideration is sitting capitalised in `OACT 1203017 — LAND KILA 20//17(8-0) KEVAT 5//4 … = ₹9,77,12,441`. This is a co-seller in a deliberate fixed-asset purchase — **Round-1 trap #1, refuted.**

**3. Willus Infrastructure (Oil, VENDA001443) — ₹40,00,000 → NOT recoverable.** Same land programme: open POs of ₹5,38,64,060 for `CF0000036 — PEB SHED CANOLA NEW LAND 2 ACRE` and `TIN SHED-NEW LAND WIP II`, tying to GL `1212016 PEB SHED NEW LAND 2 ACRE`. A ₹40 L advance on a ₹5.39 Cr construction contract is under-, not over-, funded.

**4. Seven balances never involved a payment at all.** `VENDA001084 JIVO WELLNESS (AKAL INFOSYS)` ₹1,52,855 (53 manual JEs, an internal clearing account), `VENDA000299 TAIMOOR SARPANCH` ₹40,744, `VENDA000729 BUNDL/SWIGGY` ₹25,433, `VENDA001086 ANSH GLOBAL` ₹15,000, Mart `VENDA000960 AYURVA` ₹16,000 and `VENDA000959 STAR HEALTH` ₹14,748, Bev `VENDA001402 FALAK FABRICATION` ₹15,000 — all `TransType` 30 only, `OVPM` count = 0. **Calling these "paid out" is wrong; they are mis-postings to clean up, not cash.**

**5. Three are open A/P credit notes, i.e. money the vendor owes us** — `VENDA000241 VIJAY INDUSTRIES` ₹4,21,402, `VENDA001074 MIRACLE CONTAINER` ₹15,941 (both Oil, both `DocStatus='O'`, `PaidToDate=0`, dated 2024-09-30), and Bev `VENDA000383 COMFONOMICS` ₹19,800. Genuinely collectible — but this is **exactly the population of lens hypothesis H9** (open A/P credit notes never set off, ₹7.04 L net). Excluded here so the audit total does not double count.

**6. Two are employees, not suppliers** — Mart `ORGV000216 PRABHJOT SINGH IMPREST` ₹91,379 and `ORGV000212 JASNEET KAUR IMPREST` ₹59,380. Imprest floats settle through payroll.

### What IS bankable — ₹6,55,011

Cash actually left the bank, no invoice was ever raised, **no purchase order exists to justify it**, and there has been no movement for 180+ days:

```sql
SELECT c."CardCode", c."CardName", c."Balance",
       (SELECT SUM(p."DocTotal") FROM OVPM p
        WHERE p."CardCode"=c."CardCode" AND p."Canceled"='N')                AS CASH_OUT,
       (SELECT MAX(p."DocDate") FROM OVPM p
        WHERE p."CardCode"=c."CardCode" AND p."Canceled"='N')                AS LAST_PAY
FROM   OCRD c
WHERE  c."CardType"='S' AND c."Balance" > 10000
  AND  NOT EXISTS (SELECT 1 FROM OPCH i WHERE i."CardCode"=c."CardCode" AND i."CANCELED"='N')
  AND  EXISTS     (SELECT 1 FROM OVPM p WHERE p."CardCode"=c."CardCode" AND p."Canceled"='N')
  AND  NOT EXISTS (SELECT 1 FROM OPOR o WHERE o."CardCode"=c."CardCode" AND o."CANCELED"='N');
-- run per schema; then keep rows where last payment is 180+ days before 2026-07-28
```

| Co | CardCode | Vendor | ₹ | Last payment | Age |
|---|---|---|---:|---|---:|
| Oil | VENDA000919 | RAMA SALES (BKPPM9554H) | 1,76,960 | 2024-09-30 | 666 d |
| Oil | VENDA000551 | MARSHTECH AND ALLIED SERVICES | 1,22,250 | 2024-09-30 | 666 d |
| Oil | VENDA000759 | KS AFFINITY PVT LTD | 1,07,902 | 2024-09-30 | 666 d |
| Oil | VENDA001560 | JASRA & JASRA LAW OFFICES | 1,06,000 | 2025-12-09 | 231 d |
| Bev | VENDA001090 | GAGANDEEP SINGH | 1,00,000 | 2025-05-06 | 448 d |
| Oil | VENDA001097 | BAKSHI MARK PVT LTD | 25,000 | 2024-09-30 | 666 d |
| Mart | VENDA000978 | INDIAFILINGS PVT LTD | 16,899 | 2025-05-17 | 437 d |
| | | **Total** | **6,55,011** | | |

Four of the seven have sat untouched since SAP go-live (2024-09-30) — they are opening-balance orphans. `VENDA001090 GAGANDEEP SINGH` is a duplicate master of employee `ORGV000003 GAGANDEEP SINGH IMPREST JWPL0018`, so ₹1 L should be recovered or cleared through his imprest account. Loosening the cut-off to 120 days adds only `VENDA001655 GO ANALYTICAL SOLUTIONS` ₹58,000, taking the total to ₹7,13,011.

**Working-capital release ₹6,55,011 → interest saved at the verified 7.3% CC rate = ₹47,816 per year.**

## Action

| # | Action | Owner |
|---|---|---|
| 1 | Issue recovery / invoice-demand letters to the 7 stale parties above (₹6.55 L) — 4 are 666 days old. Recover or write off with approval by 30 Sep 2026. | **Accounts** |
| 2 | Match the HS Filling ₹1.40 Cr (07-Apr) and ₹1.00 Cr (16-Jul) same-day pairs to the Indian Bank 7051847887 statement. Not proven duplicate, but SAP cannot self-check because `TrsfrRef` is NULL. | **Accounts** |
| 3 | Make `TrsfrRef` / bank UTR **mandatory** on outgoing payments in SAP. This single control is what makes duplicate-payment testing possible at all (lens H18 is untestable today). | **IT + CFO** |
| 4 | Get tax invoices for the ₹3.04 Cr of capex advances — an unbilled advance is **blocked input GST credit**. Chase HS Filling (₹2.40 Cr, 71% of a ₹3.36 Cr plant order paid with zero GRPO after 16 weeks) and Willus (₹40 L). Insist on a delivery milestone or bank guarantee before the next tranche. | **Purchase + CFO** |
| 5 | Clean up the 7 journal-only vendor balances (₹2.80 L) and merge duplicate masters (`GAGANDEEP SINGH`, `MAHBOOB KHAN`, `ALO LOGISTICS` ×2). | **Accounts** |
| 6 | Book the Anju Mangla land invoice against the Mangla advances so ₹1.85 Cr stops showing as a vendor debit. | **CFO** |

## Overlaps — do not double count

- **HS Filling ₹2.40 Cr** appears in **both** this finding and rank #19 (twin low-volume-vendor payments, ₹1.20 Cr carve-out). It is the **same money**; both are refuted as bankable here.
- **Rahul Mangla ₹1.85 Cr** is the same Bakharpur transaction as [[finding-anju-mangla-land-invoice-open]] (₹9.76 Cr). Combined Mangla exposure ₹13.16 Cr is one land deal, counted once, and is capex.
- **ALO Logistics ₹23,40,991** was already excluded from the ₹5.10 Cr headline and is reported at [[finding-alo-logistics-debit-notes]].
- **Vendor debit notes ₹4,57,143** belong to lens hypothesis H9 (open A/P credit notes, ₹7.04 L net) — excluded from my ₹6.55 L.

Part of [[SAVINGS-MOC]] · Evidence: [[duplicate-payments]]
