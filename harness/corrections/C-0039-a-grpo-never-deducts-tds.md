---
id: C-0039
date: 2026-08-27
author: Daman
area: accounts
severity: high
status: active
supersedes: 
tags: [grpo]
---

# A GRPO never deducts TDS

## Wrong
Treated a service GRPO like an A/P invoice and raised TDS as an open item on it, asking whether the 2% contractor code should be set.

## Right
A GRPO has never deducted TDS at JIVO. WTSum is 0 on all 3,923 Oil service GRPOs. The only TDS-shaped field is the line flag WtLiable (Y on 186 of 205 PICK & SHIP lines), which deducts nothing here — it exists so the A/P invoice that copies the GRPO inherits the liability. The deduction happens on the A/P invoice, and there it must be sent explicitly.

## Evidence
SELECT CASE WHEN "WTSum"=0 OR "WTSum" IS NULL THEN 'WTSum = 0' ELSE 'WTSum > 0' END K, COUNT(*) FROM "JIVO_OIL_HANADB"."OPDN" WHERE "CANCELED"='N' AND "DocType"='S' GROUP BY 1;  -- WTSum = 0 : 3923, no other row

## Rule
<!-- ONE line, imperative. This is the only part injected into every session.
     Keep it under ~200 chars. Write it so it is actionable without context. -->
GRPO never deducts TDS — WTSum=0 on all 3,923 Oil service GRPOs. Set line WtLiable so the A/P invoice inherits the liability; never put a TDS figure on a GRPO.
