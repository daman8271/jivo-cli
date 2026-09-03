---
id: C-0077
date: 2026-09-03
author: Muqeem (asked that this become the standing rule for every A/P upload) - recorded on his box as C-0075 and renumbered on the way to main, where C-0075 is already the EXIM unload date
area: accounts
severity: high
status: active
supersedes: 
tags: [gst]
---

# A/P line with a GST tax code MUST carry SACEntry (service) or HSNEntry (item) — never switch to Exampt to clear the error

## Wrong
A/P invoice payloads were built with AccountCode + TaxCode 'RCGSG@18' and no SAC code. SAP refused the Add with '[SAP -10] 254000295 - A GST tax code is selected; you must select an SAC code in line 1'. The tempting fix is to change the tax code to 'Exampt', which clears the error.

## Right
Any A/P line carrying a GST-bearing tax code needs the GST classification too: SACEntry on a service / G-L-account line, HSNEntry on an item line. 'Exampt' is the ONLY tax code that posts without one. Switching to 'Exampt' to clear 254000295 silently drops the tax - on a reverse-charge line it removes the whole RCM liability (no INPUT/OUTPUT CGST+SGST @9% pair in the JE). Fix the SAC, never the tax code. NOTE the OData property names are SACEntry and HSNEntry with those exact capitals; 'SacEntry' is accepted with HTTP 204 and writes nothing at all, so always read the line back after patching.

## Evidence
Live counts 2026-09-03, PCH1 joined to OPCH, DocDate>=2026-04-01. OIL service lines by TaxCode: every GST code (RIGST@5 693, GST05R 469, IGST@18 410, CG+SG@18 387, IGST@5 48, IGST@0 24, RISGT@18 22, CG+SG@0 14, RCGSG@18 13, RCGSG@5 3, CG+SG@5 2 = 2085 lines) has SAC set on 100% of lines; only Exampt appears without SAC (1191 lines). MART identical: IGST@18 357, RIGST@5 285, RCGSG@5 144, CG+SG@18 122, GST05R 42, RISGT@18 26, IGST@0 4, RCGSG@18 3, CG+SG@0 1 all SAC-set; Exampt 314 without. Item lines: OIL 3309/3309 and MART 1736/1736 carry HsnEntry. Rent SACs: Oil uses AbsEntry -399 (997211 residential), Mart -398 (997212 non-residential). Seen live on Mart drafts 40148-40150 (refused, then patched with SACEntry -398 and added) and on 40130-40132, which were re-keyed as Exampt on 2026-09-02 and are pending approval with no RCM.

## Rule
<!-- ONE line, imperative. This is the only part injected into every session.
     Keep it under ~200 chars. Write it so it is actionable without context. -->
A/P line with any GST tax code MUST also carry SACEntry (service/G-L line) or HSNEntry (item line), else SAP refuses the Add with 254000295. NEVER clear that error by switching the tax code to Exampt - it drops the tax. OData casing is SACEntry/HSNEntry; wrong casing returns 204 and writes nothing.
