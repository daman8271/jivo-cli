---
id: C-0026
date: 2026-08-24
author: Daman
area: accounts
severity: medium
status: active
supersedes: 
tags: [sap-writes]
---

# API-uploaded attachments need the approve-column stamp, and drafts carry the base doc's file too

## Wrong
Assumed PATCH Drafts AttachmentEntry works right after POST /Attachments2, and that the operator's scan alone is enough

## Right
JIVO's SBO_SP_TransactionNotification (1120025) refuses a draft attachment until the ATC1 line has U_CHK2='OK' (+U_CHK=size KB); and Daman wants the draft to carry the base document's file (GRPO bill) AS WELL as the operator's scan — added as an independent line on the draft's own Attachments2 row, never a shared pointer

## Evidence
PATCH Drafts(55126/55128/55130) AttachmentEntry each failed -1116/1120025 until the stamp; 55126 line-2 copy of GRPO 25844's file verified 2026-08-24; corrected by Daman

## Rule
<!-- ONE line, imperative. This is the only part injected into every session.
     Keep it under ~200 chars. Write it so it is actionable without context. -->
After POST /Attachments2 set each line U_CHK2='OK' and U_CHK=<size KB> before pointing a draft at it; and copy the base doc's attachment file onto the draft as a second independent line (download $value, re-upload).
