---
entity: AssetTransfer
domain: fixed-assets
readable: true
methods: [GET, POST, PATCH]
rows_oil: 0
---
# AssetTransfer
Documents transferring fixed assets between asset classes, cost centers, or employees (0 rows in JIVO_OIL). Live rows in JIVO_OIL_HANADB: 0.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query AssetTransfer --top 5
./sapb1 query AssetTransfer --count
./sapb1 query AssetTransfer --select "DocEntry,DocNum,PostingDate,Status" --top 10
```
Useful filter — transfers posted this fiscal year:
```bash
./sapb1 query AssetTransfer --filter "PostingDate ge '2025-04-01'" --top 10
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
| Remarks | Free-text remarks |
| BPLID | Branch (business place) ID |
| AssetDocumentLineCollection | Per-asset transfer lines |

## Connections
- Domain: [[fixed-assets]]
- [[Items]] via AssetDocumentLineCollection.AssetNumber (fixed-asset item code)
- [[AssetClasses]] via source/target asset class on transfer lines
- [[DistributionRules]] via cost-center distribution rule on transfer lines
