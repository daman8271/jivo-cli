---
id: C-0090
date: 2026-09-16
author: Daman
area: accounts
severity: high
status: active
supersedes: 
tags: [attachments]
---

# Every attachment line gets Copy to Target Document = tYES

## Wrong
Uploaded scans via POST /Attachments2 and only stamped U_CHK/U_CHK2 (and in Mart skipped the PATCH entirely), leaving CopyToTargetDoc at the API default tNO

## Right
Daman 2026-09-16: whatever we attach - draft, GRPO, A/P, credit memo, payment, A/R, any book - every Attachments2 line must carry CopyToTargetDoc='tYES' (ATC1.CopyToTrgt='Y') so the file follows the document when it is copied onward (GRPO -> A/P, draft -> posted). Set it in the same PATCH as the Approve stamp: Oil/Bev {LineNum,U_CHK,U_CHK2:'OK',CopyToTargetDoc:'tYES'}; Mart has no U_CHK columns so {LineNum,CopyToTargetDoc:'tYES'} alone. Read back every line = tYES.


2026-09-17 - Daman: "make it pls and deploy into them". The tick is no longer a recipe step: `sapb1 attach` uploads the files as the lines of one row, PATCHes CopyToTargetDoc='tYES' on every line (+ U_CHK/U_CHK2 where the line carries those keys - Oil/Bev), reads the row back, exits 8 unless every line is tYES. `--row N` re-ticks a row. Old rows stay as they are (Daman: leave the ones not fixed).

## Evidence
Row 174394 read via SL: CopyToTargetDoc tNO. ATC1 since 2026-08-20, CopyToProd='Y' (API fingerprint): Oil 1488 N vs 423 Y, Mart 301 N, Bev 500 N. PATCH proven 2026-09-16 HTTP 204 + read-back tYES: Oil 177767 (alone), 177765 (with U_CHK 686/U_CHK2 OK, kept), Mart 59273, Bev 43223 (U_CHK 530 kept). SYS.TABLE_COLUMNS: U_CHK/U_CHK2 on ATC1 in Oil+Bev only.

## Rule
<!-- ONE line, imperative. This is the only part injected into every session.
     Keep it under ~200 chars. Write it so it is actionable without context. -->
Upload every attachment, any book, any document, with `sapb1 attach <file>...` (ticks CopyToTargetDoc tYES + U_CHK2 OK in Oil/Bev, reads back, fails otherwise) - never curl; API uploads land tNO.
