---
id: C-0040
date: 2026-08-27
author: Daman
area: accounts
severity: medium
status: active
supersedes: 
tags: [grpo]
---

# A GRPO's attachment is the bilty, not the vendor's bill

## Wrong
Offered to attach the transporter's tax invoice to a service GRPO, treating the GRPO as if it were the A/P entry for the bill.

## Right
A GRPO is the receipt, not the bill. Every PICK & SHIP service GRPO in Oil carries an attachment (135 of 135) and the filenames are the BILTY numbers — 3864.pdf, 3627.pdf, 3221.pdf, 3159.pdf. On a two-part scan the bilty/LR page goes on the GRPO; the transporter's tax invoice goes on the A/P invoice that copies it.

## Evidence
SELECT H."DocNum",H."NumAtCard",A."FileName" FROM "JIVO_OIL_HANADB"."OPDN" H JOIN "JIVO_OIL_HANADB"."ATC1" A ON A."AbsEntry"=H."AtcEntry" WHERE H."CANCELED"='N' AND H."DocType"='S' AND H."CardCode"='VENDA001661';  -- FileName = the bilty number on every row; 135 of 135 have an attachment

## Rule
<!-- ONE line, imperative. This is the only part injected into every session.
     Keep it under ~200 chars. Write it so it is actionable without context. -->
A GRPO's attachment is the BILTY/LR page, filenamed by bilty number (135/135 in Oil) — never the vendor's tax invoice. That belongs on the A/P invoice that copies the GRPO.
