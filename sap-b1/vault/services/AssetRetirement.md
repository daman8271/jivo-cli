---
entity: AssetRetirement
domain: fixed-assets
readable: true
methods: [GET, POST, PATCH]
rows_oil: 0
---
# AssetRetirement
Asset retirement documents recording disposal, sale, or scrapping of fixed assets off the books (0 rows in JIVO_OIL). Live rows in JIVO_OIL_HANADB: 0.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query AssetRetirement --top 5
./sapb1 query AssetRetirement --count
./sapb1 query AssetRetirement --select "DocEntry,DocNum,PostingDate,RetirementType" --top 10
```
Useful filter — open retirements posted this fiscal year:
```bash
./sapb1 query AssetRetirement --filter "Status eq 'adsOpen' and PostingDate ge '2025-04-01'" --top 10
```

## Key fields
| Field | Meaning |
|---|---|
| DocEntry | Internal document key |
| DocNum | Document number shown to users |
| Series | Numbering series |
| PostingDate | G/L posting date |
| DocumentDate | Document (tax) date |
| AssetValueDate | Asset value effective date |
| Status | Open / cancelled status |
| RetirementType | Sale vs scrapping mode |
| DepreciationArea | Target depreciation area code |
| DocumentTotal | Total retirement value |
| Currency | Document currency |
| Remarks | Free-text remarks |
| BPLID | Branch (business place) ID |

## Connections
- Domain: [[fixed-assets]]
- [[Items]] via retired fixed-asset item code
- [[DepreciationAreas]] via DepreciationArea code
- [[BusinessPartners]] via customer CardCode on retirement-by-sale
- [[Currencies]] via Currency code
