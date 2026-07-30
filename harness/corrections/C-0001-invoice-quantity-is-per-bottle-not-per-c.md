---
id: C-0001
date: 2026-07-30
author: daman
area: all
severity: high
status: active
supersedes: 
tags: [volume, uom]
---

# Invoice quantity is per bottle, not per carton

## Wrong
Multiplied INV1.Quantity by the 'PCS' count in the item name, treating quantity as cartons. Haiku 4.5 did exactly this and reported 6,556 MT of mustard 1 L for May 2026.

## Right
INV1.Quantity is already in PIECES (single bottles). True figure was 296 MT — the error inflated volume ~22x. For 1-litre SKUs bottles = litres exactly; tonnes = litres x 0.91.

## Evidence
OITM.InvntryUom=PCS and NumInSale=1. FG0000030 MUSTARD KACHI GHANI 1 LTR 20 PCS realises ~Rs147/unit against U_MRP Rs255 — a bottle, not a 20-litre carton. Proven live 2026-07-29 cross-checking three models.

## Rule
<!-- ONE line, imperative. This is the only part injected into every session.
     Keep it under ~200 chars. Write it so it is actionable without context. -->
INV1.Quantity is in PIECES (single bottles), not cartons — InvntryUom=PCS, NumInSale=1. The '20 PCS' in item names is carton config only; multiplying by it inflates volume ~20x.
