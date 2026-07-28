---
entity: AssetManualDepreciation
domain: fixed-assets
readable: true
methods: [GET, POST, PATCH]
rows_oil: 0
---
# AssetManualDepreciation
Documents posting manual (unplanned/extraordinary) depreciation on fixed assets (0 rows in JIVO_OIL). Live rows in JIVO_OIL_HANADB: 0.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query AssetManualDepreciation --top 5
./sapb1 query AssetManualDepreciation --count
./sapb1 query AssetManualDepreciation --select "DocEntry,DocNum,PostingDate,DocumentTotal" --top 10
```
Useful filter — open manual-depreciation postings this fiscal year:
```bash
./sapb1 query AssetManualDepreciation --filter "Status eq 'adsOpen' and PostingDate ge '2025-04-01'" --top 10
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
| DepreciationType | Depreciation type applied |
| DocumentTotal | Total depreciation amount |
| Currency | Document currency |
| Remarks | Free-text remarks |
| AssetDocumentLineCollection | Per-asset depreciation lines |

## Connections
- Domain: [[fixed-assets]]
- [[Items]] via AssetDocumentLineCollection.AssetNumber (fixed-asset item code)
- [[DepreciationAreas]] via DepreciationArea code
- [[DepreciationTypePools]] via pooled DepreciationType code
