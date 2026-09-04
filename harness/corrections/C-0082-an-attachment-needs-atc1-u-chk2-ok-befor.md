---
id: C-0082
date: 2026-09-04
author: Mahak
area: accounts
severity: medium
status: active
supersedes: 
tags: [attachments]
---

# An attachment needs ATC1 U_CHK2 = OK before AttachmentEntry will patch on

## Wrong
Uploaded a file to Attachments2, got an AbsoluteEntry, then patched AttachmentEntry onto the draft and got [SAP -1116] (1120025) Select OK in Approve Column After Adding Attachment.

## Right
JIVO has a UDF on ATC1 - alias CHK2, description 'Approve', whose only valid value is OK - and SAP refuses to link the attachment to any document until it is set. Order that works: (1) POST /Attachments2 multipart with -H 'Expect:' to get AbsoluteEntry, (2) PATCH Attachments2(<AbsEntry>) with Attachments2_Lines[{LineNum:1, U_CHK2:'OK'}], (3) PATCH the document with AttachmentEntry. Every existing freight GRPO attachment carries U_CHK2 = OK.

## Evidence
SELECT FldValue FROM UFD1 WHERE TableID='ATC1' -> single value 'OK'. Every PICK and SHIP GRPO attachment row in ATC1 has U_CHK2='OK'. Verified live 2026-09-03 on Oil draft 55994 / AbsEntry 174394: the AttachmentEntry patch failed until U_CHK2 was set, then returned 204.

## Rule
<!-- ONE line, imperative. This is the only part injected into every session.
     Keep it under ~200 chars. Write it so it is actionable without context. -->
After uploading to Attachments2, set ATC1 U_CHK2='OK' on the line BEFORE patching AttachmentEntry onto the document - SAP refuses with -1116 (1120025) otherwise.
