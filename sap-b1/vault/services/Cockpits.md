---
entity: Cockpits
domain: system-other-1
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 15
---
# Cockpits
Stores B1 cockpit (dashboard/workbench) definitions per user for the client UI — 15 cockpit layouts exist. Live rows in JIVO_OIL_HANADB: 15.
## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query Cockpits --top 5
./sapb1 query Cockpits --count
./sapb1 query Cockpits --select "AbsEntry,Code,Name,UserSignature" --top 10
# cockpits owned by one user signature
./sapb1 query Cockpits --filter "UserSignature eq 1" --top 10
```
## Key fields
| Field | Meaning |
|---|---|
| AbsEntry | Cockpit record key |
| Code | Cockpit code |
| Name | Cockpit name |
| Description | Cockpit description |
| CockpitType | Cockpit layout type |
| UserSignature | Owning user signature |
| Manufacturer | Providing manufacturer |
| Publisher | Publishing vendor |
| Date | Last update date |
| Time | Last update time |
## Connections
- Domain: [[system-other-1]]
- [[Users]] via UserSignature — the user who owns the cockpit layout
