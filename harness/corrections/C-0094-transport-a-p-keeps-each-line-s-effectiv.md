---
id: C-0094
date: 2026-09-17
author: Daman
area: accounts
severity: high
status: active
supersedes: 
tags: [transport-ap]
---

# Transport A/P keeps each line's effective month from the freight GRPO it copies

## Wrong
C-0035 tells every A/P draft to set CostingCode2 = the A/P DocDate's month on every line, which would overwrite the month a transport A/P line brings over from its freight GRPO.

## Right
On a transport (freight) A/P invoice copied from freight GRPOs, each line's Effective Month is the month already on that GRPO line (= its sale invoice month, C-0093). Do not overwrite it with the bill's or DocDate's month. C-0035's DocDate-month rule is for goods A/P only.

## Evidence
Daman 2026-09-17: 'as it flows the GRPO only in transport ap'. Transport-Bill-Playbook: CLI draft 39829 copied from a service GRPO came back with Dim1, Dim2, Dim3, Dim5, LocCode and SacEntry identical to the source GRPO lines; one July bill carried 05/06/07-2026 lines.

## Rule
<!-- ONE line, imperative. This is the only part injected into every session.
     Keep it under ~200 chars. Write it so it is actionable without context. -->
Transport A/P copied from freight GRPOs: keep each line's Dim2 (Effective Month) exactly as its GRPO line has it - never overwrite with the bill/DocDate month (C-0035 is goods A/P only).
