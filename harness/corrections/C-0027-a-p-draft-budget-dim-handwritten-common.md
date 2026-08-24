---
id: C-0027
date: 2026-08-24
author: Daman
area: accounts
severity: medium
status: active
supersedes: 
tags: [ap-draft]
---

# A/P draft Budget dim: handwritten 'Common' on a factory bill = FACT_COM, not the GRPO's Factory

## Wrong
Drew the A/P draft from the GRPO and kept its Budget dimension CostingCode3='Factory' (Ashok Diwan 1256 → draft 55165), dismissing the July precedent's FACT_COM as a one-off.

## Right
The bill's handwritten allocation note decides the Budget dimension. 'Common' / 'For oil plant Common' = CostingCode3 FACT_COM (ProfitCenters dim 3, name FACTORY COMMON). The GRPO's inherited 'Factory' is the store's default, not Accounts' allocation — the invoice overrides it.

## Evidence
sapb1 query ProfitCenters --filter "InWhichDimension eq 3" → FACT_COM = FACTORY COMMON, Factory = Factory (both active). sapb1 query PurchaseInvoices --filter "CardCode eq 'VENDA000653' and NumAtCard eq '1217'" → DocEntry 48185 line CostingCode3 FACT_COM, while its base GRPO 24725 line CostingCode3 = Factory. Draft 55165 corrected 2026-08-24 by Daman (PATCH 204, read back FACT_COM).

## Rule
<!-- ONE line, imperative. This is the only part injected into every session.
     Keep it under ~200 chars. Write it so it is actionable without context. -->
A/P draft line CostingCode3 (Budget): if the bill says 'Common' set FACT_COM (FACTORY COMMON), never inherit the GRPO's 'Factory'. Read the handwritten allocation note on every factory bill.
