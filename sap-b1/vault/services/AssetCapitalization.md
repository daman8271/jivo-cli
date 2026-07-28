---
entity: AssetCapitalization
domain: fixed-assets
readable: true
methods: [GET, POST, PATCH]
rows_oil: 0
---
# AssetCapitalization
Asset capitalization documents that record acquisition cost of fixed assets onto the balance sheet (0 rows in JIVO_OIL — fixed-asset module unused). Live rows in JIVO_OIL_HANADB: 0.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query AssetCapitalization --top 5
./sapb1 query AssetCapitalization --count
./sapb1 query AssetCapitalization --select "DocEntry,DocNum,PostingDate,DocumentTotal" --top 10
```
Useful filter — open capitalizations posted this fiscal year:
```bash
./sapb1 query AssetCapitalization --filter "Status eq 'adsOpen' and PostingDate ge '2025-04-01'" --top 10
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
| DepreciationArea | Target depreciation area code |
| DocumentTotal | Total capitalized amount |
| Currency | Document currency |
| Remarks | Free-text remarks |
| BPLID | Branch (business place) ID |
| AssetDocumentLineCollection | Per-asset capitalization lines |

## Connections
- Domain: [[fixed-assets]]
- [[Items]] via AssetDocumentLineCollection.AssetNumber (fixed-asset item code)
- [[DepreciationAreas]] via DepreciationArea code
- [[BusinessPartners]] via vendor CardCode when capitalizing with vendor
- [[Currencies]] via Currency code
- [[Projects]] via line-level ProjectCode
