---
entity: LocalEra
domain: system-other-1
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 0
---
# LocalEra
Localization calendar-era definitions (e.g. Japanese imperial eras) for date display. Live rows in JIVO_OIL_HANADB: 0 — unused in the India localization.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query LocalEra --top 5
./sapb1 query LocalEra --count
./sapb1 query LocalEra --select "AbsEntry,EraName,StartDate" --top 10
# Eras beginning after a given date (if any get defined):
./sapb1 query LocalEra --filter "StartDate ge '2019-05-01'" --top 10
```

## Key fields
| Field | Meaning |
|---|---|
| AbsEntry | Era record key |
| EraName | Era display name |
| StartDate | Era start date |

## Connections
- Domain: [[system-other-1]]
