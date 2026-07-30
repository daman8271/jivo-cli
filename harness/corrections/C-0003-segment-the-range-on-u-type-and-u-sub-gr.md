---
id: C-0003
date: 2026-07-30
author: daman
area: sales
severity: high
status: active
supersedes: 
tags: [segmentation]
---

# Segment the range on U_TYPE and U_Sub_Group, never item names

## Wrong
Classified products into premium/commodity and into varieties by matching words in the item name.

## Right
SAP already classifies the range. Name-matching misses badly — COLD PRESS 1 LTR and COLD PRESS 1 LTR (NIRMAL RISHI) are SAP-tagged CANOLA with no 'canola' in the name, and they are most of canola's volume.

## Evidence
OITM.U_TYPE and OITM.U_Sub_Group. Note YELLOW MUSTARD is tagged PREMIUM/MUSTARD so it straddles a premium-vs-mustard cut — state which side you put it on.

## Rule
<!-- ONE line, imperative. This is the only part injected into every session.
     Keep it under ~200 chars. Write it so it is actionable without context. -->
Segment the range on OITM.U_TYPE (PREMIUM/COMMODITY/OTHERS) and U_Sub_Group (variety), never item-name matching — e.g. COLD PRESS 1 LTR is SAP-tagged CANOLA with no 'canola' in the name.
