---
entity: BusinessPartnerProperties
domain: business-partners-crm
readable: true
methods: [GET, PATCH]
rows_oil: 64
---
# BusinessPartnerProperties
The 64 named boolean property flags assignable to business partners for classification and filtering. Live rows in JIVO_OIL_HANADB: 64.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query BusinessPartnerProperties --top 5
./sapb1 query BusinessPartnerProperties --count
./sapb1 query BusinessPartnerProperties --select "PropertyCode,PropertyName" --top 10
# Find a named (non-default) property flag:
./sapb1 query BusinessPartnerProperties --filter "not startswith(PropertyName,'BP Property')" --top 20
```

## Key fields
| Field | Meaning |
|---|---|
| PropertyCode | Flag slot number 1–64 (key) |
| PropertyName | Flag display label |

## Connections
- Domain: [[business-partners-crm]]
- [[BusinessPartners]] via Properties1–Properties64 flags on the BP master
