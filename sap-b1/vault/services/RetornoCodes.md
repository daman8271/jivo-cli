---
entity: RetornoCodes
domain: administration-setup-3
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 0
---
# RetornoCodes
Brazil-localization bank-return (retorno) file codes for payment processing; unused in this DB. Live rows in JIVO_OIL_HANADB: 0.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query RetornoCodes --top 5
./sapb1 query RetornoCodes --count
./sapb1 query RetornoCodes --select "AbsEntry,Code,Description" --top 10
# Look up one retorno code (if this Brazil-only set ever gets populated):
./sapb1 query RetornoCodes --filter "Code eq '02'" --top 5
```
Set is empty here — field names above are best-effort; confirm with `./sapb1 fields RetornoCodes` if rows ever appear.

## Key fields
| Field | Meaning |
|---|---|
| AbsEntry | Internal numeric key |
| Code | Bank return code |
| Description | Return code meaning |

(No key fields captured in recon — the set is empty; fields above are best-effort from the standard schema.)

## Connections
- Domain: [[administration-setup-3]]
- No related entities in recon — Brazil-only feature, irrelevant to this Indian localization.
