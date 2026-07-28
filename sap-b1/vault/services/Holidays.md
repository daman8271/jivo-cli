---
entity: Holidays
domain: system-other-1
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 11
---
# Holidays
Company holiday calendars (holiday dates and weekend definitions) driving due-date and delivery-date calculations. Live rows in JIVO_OIL_HANADB: 11 — yearly calendars named "2004 Holidays" through "2016 Holidays" (nothing newer, so the active calendar is stale).

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query Holidays --top 5
./sapb1 query Holidays --count
./sapb1 query Holidays --select "HolidayCode,WeekendFrom,WeekendTO,ValidForOneYearOnly" --top 10
# Pull the newest defined calendar with its date rows:
./sapb1 query Holidays --filter "HolidayCode eq '2016 Holidays'" --top 1
```

## Key fields
| Field | Meaning |
|---|---|
| HolidayCode | Calendar name/key (e.g. "2016 Holidays") |
| HolidayDates | Collection of holiday date rows |
| WeekendFrom | First weekend day |
| WeekendTO | Last weekend day |
| SetWeekendsAsWorkDays | Treat weekends as working days? |
| ValidForOneYearOnly | Calendar limited to one year? |
| WeekNoRule | Week-numbering rule |

## Connections
- Domain: [[system-other-1]]
- [[CompanyService]] via HolidayCode — company admin settings pick the active holiday calendar
