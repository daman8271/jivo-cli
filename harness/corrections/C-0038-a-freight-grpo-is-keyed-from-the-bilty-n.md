---
id: C-0038
date: 2026-08-27
author: Daman
area: accounts
severity: high
status: active
supersedes: 
tags: [grpo]
---

# A freight GRPO is keyed from the bilty, never from the AR invoice

## Wrong
Treated SAP's AR invoice as the source for a freight/transport GRPO — proposing to read OINV.U_BilltyNumber to find which sale invoices rode a given truck, then generate the GRPO's lines (U_ARNO, litres, dimensions) from those invoices.

## Right
The transporter hands over the bilty (LR/GCN); that paper is the input, and one bilty becomes one service GRPO. Every value on the GRPO — the invoice number in U_ARNO, the destination, the litres, the freight — is read off the bilty itself. The AR invoice is a separate, later artefact: a photo of the copy the consignee signed, evidence that the goods were physically received. It is not an input to the GRPO and must not be queried to build one.

## Evidence
Daman, 2026-08-27, on the billing/SAP chain. Corroborated live: joining Oil freight GRPO lines (PDN1.AcctCode='5670001', OPDN.CANCELED='N', 365d) to their AR invoice via PDN1.U_ARNO=OINV.DocNum, OINV.U_BilltyNumber equals OPDN.NumAtCard on only 1,434 of 3,273 lines (43.8%); 43.9% after stripping - / and spaces; 46.4% allowing substring. GRPO 25886 = bilty NCR-3627 while its invoice 626070769 carries bilty '1126'. The AR invoice therefore cannot identify which bilty carried it.

## Rule
<!-- ONE line, imperative. This is the only part injected into every session.
     Keep it under ~200 chars. Write it so it is actionable without context. -->
Freight GRPO is keyed from the transporter's BILTY only, never from the AR invoice: U_ARNO, litres and destination come off the bilty paper. The signed AR-invoice photo is later proof of delivery.
