---
id: C-0047
date: 2026-08-27
author: Daman
area: accounts
severity: high
status: superseded
supersedes: 
tags: [grpo]
---

# Freight GRPO litres are printed on the AR invoice, not computed

## Wrong
Treated U_UNE_LTS on a freight GRPO line as a figure to derive, and spent two sessions fitting a pack-size parser against SAP item names to reproduce it. Accuracy plateaued around 70% and the gap was blamed on parser edge cases (KGS/GMS packs, combos), leaving 'where does the operator read the litres?' recorded as an open question.

## Right
It is not derived at all. JIVO's own AR invoice PDF prints a Product Category block at the foot of the document — Category / Litre / Gross Wt, with a Total line — and that Total IS the U_UNE_LTS the operator keys. Invoice 626080289 prints Total 1620.00 and GRPO 26081 line 3 carries U_UNE_LTS 1620, exactly. The figure can never be queried out of SAP because OITM.U_UNE_TOTL, U_UNE_TOTB and SVolume are NULL on every finished good — it is computed by the invoice print layout. The PDFs arrive in the logistics@jivo.in mailbox from ppc.ho@jivo.in as '<DocNum> <party>.pdf'; find one with jmail search --text <invoice no>. Never use the Gross Wt column (packaging-inclusive: 1,620 L ships as 1,598.93 kg). Getting the number from the paper is also not a C-0038 violation: the bilty hands you the invoice number in writing, so the invoice is looked up, never searched for.

## Evidence
AR invoice PDF 626080289 (logistics@jivo.in, uid 39057) Product Category block: OLIVE 400.0000 / OLIVE 320.0000 / CANOLA 300.0000 / SOYABEAN 600.0000 / Total 1620.00 — vs hana-sql JIVO_OIL_HANADB.PDN1 DocEntry 26081 LineNum 2 U_UNE_LTS = 1620. OITM U_UNE_TOTL/U_UNE_TOTB NULL for FG0000009/28/33/81/150/151/194/21. Parser fallback reproduces the keyed value on only 4,174 of 6,229 Oil freight lines exactly (67.0%), 74.6% within 2%, even with kg converted at 1/0.91. Measured 2026-08-27.

## Rule
<!-- ONE line, imperative. This is the only part injected into every session.
     Keep it under ~200 chars. Write it so it is actionable without context. -->
Freight GRPO U_UNE_LTS is PRINTED on JIVO's AR invoice PDF (Product Category block -> Total Litre), mailed to logistics@jivo.in. Read it; never compute it — OITM volume fields are NULL on every FG.
