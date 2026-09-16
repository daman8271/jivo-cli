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

## Evidence
Row 174394 read via SL: CopyToTargetDoc tNO. ATC1 since 2026-08-20, CopyToProd='Y' (API fingerprint): Oil 1488 N vs 423 Y, Mart 301 N, Bev 500 N. PATCH proven 2026-09-16 HTTP 204 + read-back tYES: Oil 177767 (alone), 177765 (with U_CHK 686/U_CHK2 OK, kept), Mart 59273, Bev 43223 (U_CHK 530 kept). SYS.TABLE_COLUMNS: U_CHK/U_CHK2 on ATC1 in Oil+Bev only.

## Rule
<!-- ONE line, imperative. This is the only part injected into every session.
     Keep it under ~200 chars. Write it so it is actionable without context. -->
Every Attachments2 line we create, any book, any document: PATCH CopyToTargetDoc='tYES' (with U_CHK2 OK in Oil/Bev; alone in Mart) and read back tYES - API uploads land tNO.
