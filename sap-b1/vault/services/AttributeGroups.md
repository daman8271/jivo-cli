---
entity: AttributeGroups
domain: administration-setup-3
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 1
---
# AttributeGroups
Groups of resource/production attributes used to characterize resources in production planning. Live rows in JIVO_OIL_HANADB: 1.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query AttributeGroups --top 5
./sapb1 query AttributeGroups --count
./sapb1 query AttributeGroups --select "Code,Name,Locked" --top 10
# Groups still open for editing:
./sapb1 query AttributeGroups --filter "Locked eq 'tNO'" --top 5
```

## Key fields
| Field | Meaning |
|---|---|
| Code | Group numeric key |
| Name | Group display name |
| Locked | Locked-against-changes flag |
| AttributeGroupCollection | Member attributes collection |

## Connections
- Domain: [[administration-setup-3]]
- No related entities recorded in recon — resources reference these groups in production planning.
