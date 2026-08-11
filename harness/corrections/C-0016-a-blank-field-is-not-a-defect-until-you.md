---
id: C-0016
date: 2026-08-12
author: Karanpreet Singh (GST manager), via Daman
area: all
severity: high
status: active
supersedes: 
tags: [method]
---

# A blank field is not a defect until you check where the value legitimately lives

## Wrong
Three wrong figures were reported to a senior operator in one week, all from the same habit: form a hypothesis, run the query that confirms it, never run the query that would kill it. (1) 157 lines / Rs 4.94 Cr called 'missing HSN' - the HSN column was checked, the paired SAC column was not; real defect was 3 lines / Rs 1.07 Cr, wrong by 50x. (2) A HoReCa segment total that silently omitted Rs 1.20 Cr because the same customer is tagged differently in the Oil and Mart books. (3) 2,122 'problem invoices' that were raw add-on error rows, not invoices; real figure 32. In every case the arithmetic was re-verified and reported as 'all figures verify' - which was true and irrelevant, because the sum was right and the population was wrong. Checking the maths created false confidence.

## Right
In SAP B1 a blank is usually a value living somewhere else, not a missing value. Before reporting any blank, absence or exception as a defect, run the disconfirming query first: does the value legitimately sit in a paired column (HSN vs SAC), in another company book (Oil vs Mart vs Beverages), or at a different level (invoice vs customer master, as with GSTIN)? And before quoting a count, confirm the unit - add-on and error tables write multiple rows per document, so COUNT(*) is not an invoice count. Verifying that a total adds up says nothing about whether the right rows were included.

## Evidence
C-0013 (HSN/SAC mutually exclusive: 19,735 HSN-only, 154 SAC-only, 0 both, 3 neither), C-0014 (GSTIN is INV12.BpGSTN not the customer master), C-0015 (U_Main_Group differs across books for 129 customers). All three were found by running the disconfirming query that the original analysis skipped; each took under a minute.

## Rule
<!-- ONE line, imperative. This is the only part injected into every session.
     Keep it under ~200 chars. Write it so it is actionable without context. -->
A blank in SAP usually means the value lives elsewhere. Before calling it a defect check the paired column, the other company books, and the document vs master level - and confirm COUNT(*) counts documents, not add-on rows.
