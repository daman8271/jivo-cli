---
id: C-0065
date: 2026-08-31
author: Daman
area: accounts
severity: high
status: active
supersedes: 
tags: [grpo]
---

# C-0049 applies in MART too, but against the branch we picked — not a fixed 06

## Wrong
In Mart, clone the tax code from that transporter's last Mart GRPO.

## Right
C-0049 governs Mart as well: the code follows the TRANSPORTER's own GSTIN state, read off the bill (Mart's OCRD.LicTradNum is NULL for every transporter, so SAP cannot tell you), compared against JIVO's state — and in Mart that is the branch C-0064 just selected (Delhi 07 or Haryana 06), NOT the fixed Haryana 06 that C-0049 assumes for Oil. Same state = intra, different = inter. Whether it is forward or reverse charge, and the rate, are read off the paper: a GTA bill saying 'GST payable by consignee'/'RCM' is reverse at 5%; a logistics bill printing its own GST line is forward, usually 18%. Mart codes: inter+forward IGST@18 (or IGST@5); intra+forward CG+SG@18; inter+reverse RIGST@5 (RISGT@18 at 18); intra+reverse GST05R (RCGSG@18 at 18).

## Evidence
Daman 2026-08-31, extending C-0049 to Mart. PICK & SHIP bill NCR-349 GSTIN 09AAQCP4145A1ZF = UP(09) vs branch DELHI(07) = inter-state, and the bill prints IGST @ 18.00% forward -> IGST@18, which draft 40072 carries. All four codes are live in Mart freight GRPOs over 400 days: RIGST@5 103, IGST@18 36, GST05R 33. JIVO_MART_HANADB.OSTC: CG+SG@18 'CGST+SGST@18%', RCGSG@18 'RCM CGST+SGST@18%', RISGT@18 'RCM IGST @18%'. JIVO_MART_HANADB.OCRD.LicTradNum is NULL for every transporter card.

## Rule
<!-- ONE line, imperative. This is the only part injected into every session.
     Keep it under ~200 chars. Write it so it is actionable without context. -->
MART freight GRPO tax code: transporter's GSTIN state (off the paper — LicTradNum is NULL) vs the BRANCH state chosen by C-0064, never the destination and never cloned. inter+fwd IGST@18 · intra+fwd CG+SG@18 · inter+rev RIGST@5 · intra+rev GST05R.
