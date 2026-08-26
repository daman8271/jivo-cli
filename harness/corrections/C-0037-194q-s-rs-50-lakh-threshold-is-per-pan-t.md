---
id: C-0037
date: 2026-08-26
author: Daman
area: accounts
severity: high
status: active
supersedes: 
tags: [tds, 194q, vendor-master]
---

# 194Q's Rs 50 lakh threshold is per PAN (the seller), not per SAP CardCode — one vendor can have several cards

## Wrong
Measured each vendor's FY purchases against the Rs 50 lakh 194Q threshold using its SAP CardCode, one card = one vendor. On that basis TPAC showed Rs 37,26,273 FY26-27, called it under the threshold, left four A/P drafts with no TDS, and reported an existing Rs 138 deduction on that vendor as an over-deduction.

## Right
A seller under 194Q is identified by PAN, so every SAP card sharing a PAN must be AGGREGATED before testing the Rs 50 lakh threshold. TPAC has TWO Oil cards on one PAN AAGCT4816J: VENDA000937 'TPAC PACKAGING INDIA PVT LTD' (Uttarakhand) Rs 28,73,033 and VENDA000939 'TPAC PACKAGING INDIA PVT LTD II' (Haridwar) Rs 37,26,273. Each is under Rs 50 lakh; together they are Rs 65,99,306 and crossed the threshold on 2026-07-13. So TPAC IS a 194Q vendor in FY26-27, the Rs 138 deduction was correct, and TDS is under-deducted on that PAN by roughly Rs 1,180 (Rs 1,599 due on the Rs 15,99,306 excess vs Rs 419 taken). Always group by CRD7.TaxId0 (PAN), never by CardCode. Note OCRD.LicTradNum and FederalTaxID are EMPTY for the whole vendor master (cf. C-0014) — CRD7.TaxId0 is the only PAN source.

## Evidence
SELECT DISTINCT t."TaxId0", c."CardCode", c."CardName" FROM JIVO_OIL_HANADB.CRD7 t JOIN JIVO_OIL_HANADB.OCRD c ON c."CardCode"=t."CardCode" WHERE t."TaxId0"='AAGCT4816J' -> two rows, VENDA000937 and VENDA000939. Per-card FY26-27 taxable (SUM(DocTotal-VatSum), OPCH, DocDate>='2026-04-01', CANCELED='N'): VENDA000939 Rs 37,26,273 / VENDA000937 Rs 28,73,033; combined Rs 65,99,306. Running cumulative over both cards ordered by DocDate crosses Rs 50,00,000 at invoice 2605000464 dated 2026-07-13 (cum Rs 50,51,005). TDS due on the excess = Rs 1,599 vs Rs 419 actually taken. Every other vendor in the 2026-08-26 batch had exactly one card per PAN, so only TPAC was affected.

## Rule
<!-- ONE line, imperative. This is the only part injected into every session.
     Keep it under ~200 chars. Write it so it is actionable without context. -->
194Q Rs 50 lakh threshold is per PAN, not per CardCode: aggregate every card sharing CRD7.TaxId0 before deciding TDS. TPAC = VENDA000937 + VENDA000939 (PAN AAGCT4816J), together over the limit since 2026-07-13.
