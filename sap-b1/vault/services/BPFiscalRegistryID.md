---
entity: BPFiscalRegistryID
domain: financials-accounting-1
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 0
---
# BPFiscalRegistryID
Stores localization-specific fiscal registry IDs (tax registration numbers) for business partners (empty in this DB). Live rows in JIVO_OIL_HANADB: 0.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query BPFiscalRegistryID --top 5
./sapb1 query BPFiscalRegistryID --count
./sapb1 fields BPFiscalRegistryID   # discover columns (set is empty, no keyFields sampled)
# Example filter once field names are confirmed via `fields`:
./sapb1 query BPFiscalRegistryID --filter "BPCode eq 'C00001'"
```

## Key fields
| Field | Meaning |
|---|---|
| (none sampled) | Entity set empty — run `./sapb1 fields BPFiscalRegistryID` |

## Connections
- Domain: [[financials-accounting-1]]
- [[BusinessPartners]] via BPCode = CardCode — each fiscal registry ID belongs to one business partner
