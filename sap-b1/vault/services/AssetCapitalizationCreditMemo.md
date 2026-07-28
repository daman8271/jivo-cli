---
entity: AssetCapitalizationCreditMemo
domain: fixed-assets
readable: true
methods: [GET, POST, PATCH]
rows_oil: 0
---
# AssetCapitalizationCreditMemo
Credit memo documents that reduce or reverse previously capitalized asset acquisition values (0 rows in JIVO_OIL). Live rows in JIVO_OIL_HANADB: 0.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query AssetCapitalizationCreditMemo --top 5
./sapb1 query AssetCapitalizationCreditMemo --count
./sapb1 query AssetCapitalizationCreditMemo --select "DocEntry,DocNum,PostingDate,DocumentTotal" --top 10
```
Useful filter — credit memos against a specific depreciation area:
```bash
./sapb1 query AssetCapitalizationCreditMemo --filter "DepreciationArea eq 'GAAP'" --top 10
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
| DocumentTotal | Total credited amount |
| Currency | Document currency |
| Remarks | Free-text remarks |
| BPLID | Branch (business place) ID |
| AssetDocumentLineCollection | Per-asset credit lines |

## Connections
- Domain: [[fixed-assets]]
- [[AssetCapitalization]] via the base capitalization document it reverses
- [[Items]] via AssetDocumentLineCollection.AssetNumber (fixed-asset item code)
- [[DepreciationAreas]] via DepreciationArea code
- [[Currencies]] via Currency code
