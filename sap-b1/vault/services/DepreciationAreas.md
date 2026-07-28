---
entity: DepreciationAreas
domain: fixed-assets
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 3
---
# DepreciationAreas
Depreciation area definitions (book vs tax valuation views) governing how asset values and depreciation post to the G/L (3 areas defined). Live rows in JIVO_OIL_HANADB: 3.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query DepreciationAreas --top 5
./sapb1 query DepreciationAreas --count
./sapb1 query DepreciationAreas --select "Code,Description,AreaType,MainBookingArea" --top 10
```
Useful filter — find the main booking (G/L-posting) area:
```bash
./sapb1 query DepreciationAreas --filter "MainBookingArea eq 'tYES'" --top 10
```

## Key fields
| Field | Meaning |
|---|---|
| Code | Depreciation area code (key) |
| Description | Area name |
| AreaType | Posting vs statistical type |
| MainBookingArea | Flags the G/L-posting area |
| DerivedArea | Derived-from-area flag |
| PostingOfDepreciation | Direct/indirect depreciation posting |
| DirectRevenuePosting | Gross retirement posting flag |
| RetirementMethod | Net vs gross retirement |
| TaxType | Tax handling for area |
| TaxCreditControl | Tax credit control flag |
| BPForTaxCorrection | BP used for tax correction |
| ItemForTaxCorrection | Item used for tax correction |
| UsageForTaxCorrection | Usage used for tax correction |

## Connections
- Domain: [[fixed-assets]]
- [[BusinessPartners]] via BPForTaxCorrection (CardCode)
- [[Items]] via ItemForTaxCorrection (ItemCode)
- [[ChartOfAccounts]] via depreciation posting accounts determined per area
