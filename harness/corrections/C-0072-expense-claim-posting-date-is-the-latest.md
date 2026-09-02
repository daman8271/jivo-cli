---
id: C-0072
date: 2026-09-02
author: Daman
area: accounts
severity: high
status: active
supersedes: C-0069
tags: [expense-claims]
---

# Expense-claim posting date is the LATEST expense date on the sheet

## Wrong
Recorded in C-0069 that the posting date is always the 1st of the month after the expense month, and moved four August claims to DocDate 01-09-2026 on the September series.

## Right
Posting date (DocDate) = the LATEST expense date printed on the sheet, because that is when the last of the kharcha happened. It only rolls forward to the 1st of the next open month when the expense month is already CLOSED — which is why a July-only sheet (Bullet service 27-07) posts 01-08-2026 while an August sheet whose last row is 23-08 posts 23-08-2026. Vendor ref (NumAtCard = '<EXPENSE MONTH> YY/<total>') and document date (TaxDate = the expense date) are unchanged from C-0069.

## Evidence
Daman, 2026-09-02: 'change the posting date to 23-8 ... becuz the latest expnse is of this date'. Corroborated independently — a human in the SAP client had already re-dated draft 55804 to 23-08-2026, the last row on that sheet. Applied to 55888 (23-08), 55800 (29-08), 55804 (23-08), 55805 (31-08), all back on the August series 3336; 55799 stays 01-08-2026 because its only expense is 27-07 and July is closed.

## Rule
<!-- ONE line, imperative. This is the only part injected into every session.
     Keep it under ~200 chars. Write it so it is actionable without context. -->
Expense claims: DocDate = the LATEST expense date on the sheet; roll to the 1st of the next open month only if that expense month is closed. TaxDate = that same expense date; NumAtCard = '<EXPENSE MONTH> YY/<total>'.
