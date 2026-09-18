---
id: C-0087
date: 2026-09-09
author: Daman
area: accounts
severity: high
status: active
supersedes: 
tags: [entry]
---

# An A/P draft must be sent, not offered

## Wrong
Showed the operator the dry-run payload and ended the turn asking them to cross-check / confirm before sending — so nothing ever reached SAP. The operator spent 20 minutes looking for a draft that was never created.

## Right
The dry-run and the --yes go in the SAME turn. The preview exists to catch a wrong branch, series, vendor or posting date BEFORE it reaches the books; it is NOT a gate on the operator (RULE 0). A draft posts nothing — no stock movement, no ledger entry — until a human opens Document Drafts and presses Add, so stopping at the preview protects nobody and silently loses the work. Stop before --yes only on precheck exit 2 (already in SAP), exit 3/4 (bad inputs / SAP unreachable), or a real fault the preview itself reveals: wrong vendor, wrong branch, wrong series, or a total that does not match the paper.

## Evidence
Cause found in the skills themselves: ap-rm-pm/SKILL.md:96 said 'Wait for their go.' between step 4 (dry-run) and step 5 (send); jivo-ap-service-draft:67 and jivo-ap-credit-memo:68 said 'Dry-run -> operator's go -> --yes'. Contradicts CLAUDE.md RULE 0 ('Show the --dry-run first, then send. Not as a gate on the operator... One preview they have seen, then go.') and the house pattern in jivo-consumables-direct-indirect-expense:100 ('Dry-run, show the operator, then send.'). All three fixed 2026-09-09. Reported by Daman: 'it is not directly making the drafts but confirming for their confirmation - should not happen like this.'

## Rule
<!-- ONE line, imperative. This is the only part injected into every session.
     Keep it under ~200 chars. Write it so it is actionable without context. -->
A/P draft: run the dry-run then --yes in the SAME turn. Never end a turn on the preview and never ask 'shall I send it?' — a draft posts nothing until a human presses Add.
