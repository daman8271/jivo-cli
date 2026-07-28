---
entity: FAAccountDeterminations
domain: financials-accounting-2
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 4
---
# FAAccountDeterminations
Maps fixed-asset events (acquisition, depreciation, retirement, revaluation) to the G/L accounts they post to. Live rows in JIVO_OIL_HANADB: 4.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query FAAccountDeterminations --top 5
./sapb1 query FAAccountDeterminations --count
./sapb1 query FAAccountDeterminations --select "Code,Description,AssetBalanceSheetAccount,OrdinaryDepreciation" --top 10
```
Useful filter — determinations that actually post ordinary depreciation:
```bash
./sapb1 query FAAccountDeterminations --filter "OrdinaryDepreciation ne null" --top 10
```

## Key fields
| Field | Meaning |
|---|---|
| Code | Determination code (key) |
| Description | Determination name |
| AssetBalanceSheetAccount | Asset balance-sheet G/L account |
| ClearingAccountAcquisition | Acquisition clearing account |
| OrdinaryDepreciation | Ordinary depreciation expense account |
| AccumulatedOrdinaryDepr | Accumulated depreciation account |
| SpecialDepreciation | Special depreciation account |
| UnplannedDepreciation | Unplanned depreciation account |
| RevaluationAccount | Asset revaluation account |
| RevenueAccountforRetirement | Retirement revenue account |
| RevenuefromAssetSalesNet | Net asset-sale revenue account |

## Connections
- Domain: [[financials-accounting-2]]
- [[ChartOfAccounts]] via the G/L account fields (AssetBalanceSheetAccount, OrdinaryDepreciation, …)
- [[AssetClasses]] via the account determination code assigned per asset class / depreciation area
