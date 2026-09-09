# Warehouse and oil source audit — 9 September 2026

Verified against original user question log, GODOWNS.md, C-0056, current collector code, and private source snapshot at approximately 00:55 IST. No source-system writes.

## Recorded user scope

- Packaging: BH-BS, BH-PM, BH-NM, BH-SDL, GP-NM, GP-PM, GP-FG.
- Superseded by Daman on 9 September: finished goods and storage for Wellness use BH-BT and BH-PF ONLY. Exclude GP-FG/Gupta and GP-FGM. Packaging scope remains separate.
- Excluded: BH-OT (Param), BH-PP (explicit ignore), BH-WST (waste), GP-FGM (Mart, distinct from Oil GP-FG); unapproved locations stay excluded.
- Original user message in harness/questions/log.jsonl:1136, 2026-08-29T12:50:52, explicitly adds BH-LO, BH-NM, BH-SDL, GP-FG, GP-NM. Line 1138 adds GP-PM. The contradictory 'Not available' NM sentence was assistant-written and cannot override this.
- BH-GJ is a receiving/jobwork location per later 29-August ruling. That does not override 30-August C-0056: oil quantity and grades come only from EXIM.
- Factory planning requirement API's scope (BH-PS/BH-PC/BH-PM for packaging; BH-LO/BH-OT for raw) is an app calculation setting, not Daman's MARK IV allow-list.

## Current source proof

EXIM manual-tank source latest dip stamp: 8 September 14:09 IST; source polling is later than the physical readings. Comparing these records proves differing representations, not a physical reason for the difference.

| Item | EXIM observation | Current/previous collector behavior |
|---|---|---|
| MUSTARD PAKKI GHANI 2B, RM0PKG2 | 34,000 L | Exact grade absent from name mapping; dropped. This is a mapping gap, not absent EXIM stock. |
| SOYABEAN | 318,000 L | Factory BH-LO 194,417.0593 L + BH-GJ 44,043.912 L = 238,460.9713 L. No independent physical explanation established. |
| Extra Light | 22,800 L across EXIM grades mapped RM0000012 | Factory code RM0000008 added 1,432 L separately. Distinct physical stock not proved. |
| Pomace | 82,800 L across EXIM grades mapped RM0000013 | Factory BOM code RM0000010 added 730.57 L separately. Distinct physical stock not proved. |

The old fallback added 90,005.0943 L from BH-LO plus 40 L from BH-GJ. A missing mapped tank code was treated as permission to add factory oil, without evidence it was separate drummed stock. This conflicts with EXIM-only C-0056. Do not merge different oil grades merely to fill this gap.

Private evidence stays on VPS: /root/mark4-astha/private/material-supply/material-raw.json and exim-tanks.json. No credentials or supplier identifiers copied here.
