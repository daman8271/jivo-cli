---
id: C-0043
date: 2026-08-27
author: measured 2026-08-27 (Daman GRPO session)
area: all
severity: high
status: active
supersedes: 
tags: [dimensions]
---

# JIVO Dim5 state codes are not the obvious abbreviations

## Wrong
Was about to write Dim5 'BR' for a Bihar destination, spelling the code from the state name.

## Right
JIVO's Dim5 vocabulary uses its own abbreviations and several are not what you would guess: Bihar is BH (not BR), Odisha is OR, Uttarakhand is UK, Kerala is KE, Karnataka is KN, Telangana is TE, Chandigarh is CD, Chhattisgarh is CH, Goa is GO, Nagaland is NG. A guessed code either fails or silently mis-states destination analysis, so it must be read from OOCR.

## Evidence
SELECT "OcrCode","OcrName" FROM "JIVO_OIL_HANADB"."OOCR" WHERE "DimCode"=5 AND "Active"='Y' ORDER BY "OcrCode";  -- 26 active codes: BH BIHAR, OR ODHISHA, UK UTTRAKHAND, KE KERELA, KN KARNATAKA, TE TELANGANA, CD CHANDIGARH, CH CHHATISGARH, GO GOA, NG NAGALAND ...

## Rule
<!-- ONE line, imperative. This is the only part injected into every session.
     Keep it under ~200 chars. Write it so it is actionable without context. -->
Never spell a Dim5 state code from the state name — Bihar=BH (not BR), Odisha=OR, Uttarakhand=UK, Kerala=KE. Read it: SELECT OcrCode,OcrName FROM OOCR WHERE DimCode=5 AND Active='Y'.
