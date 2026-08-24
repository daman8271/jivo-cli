---
id: C-0025
date: 2026-08-24
author: Daman
area: accounts
severity: medium
status: active
supersedes: 
tags: [sap-writes]
---

# Service-type A/P lines need LocationCode, U_Recvd_Qty and the Budget dimension

## Wrong
Built service-type (no-GRPO) fuel invoice lines with only account/amount/2 dims — no location, no quantity anywhere, first send rejected 'Please select Budget'

## Right
JIVO service lines carry LocationCode (OLCT; 2 = Bhakharpur factory = Haryana place-of-supply display), the paper's per-line qty in U_Recvd_Qty (service rows have no Qty column in the client), and CostingCode3 (Budget dim; guard 1120009). Item-type lines instead use the real Quantity column and leave U_Recvd_Qty empty

## Evidence
posted Om Sai 626073153: every line LocationCode 2, U_Recvd_Qty filled (12.384); posted item invoices (Digicod 626074279) leave U_Recvd_Qty null; SBO_SP_TransactionNotification 1120009 rejected the no-CostingCode3 POST; draft 55130 fixed 2026-08-24, corrected by Daman

## Rule
<!-- ONE line, imperative. This is the only part injected into every session.
     Keep it under ~200 chars. Write it so it is actionable without context. -->
Service-type A/P lines (fuel/transport/expenses): set LocationCode (2=factory/Haryana), put the paper's litres/qty in U_Recvd_Qty, and set CostingCode3 (Budget) — clone ALL populated fields from a posted precedent, not just amounts.
