---
entity: StatesService
domain: administration-setup-2
readable: false
methods: [POST]
rows_oil: null
---
# StatesService
Lists states/provinces per country used in business partner and document addresses (and GST state codes in India).

## Operations
- StatesService_GetStateList

Function service — there is no entity set to `./sapb1 query` here. Entity sets are the read path in the CLI; browse this service's catalogued operations with `./sapb1 ops StatesService`.

## Connections
- Domain: [[administration-setup-2]]
- [[Countries]] via country code — states are defined per country
- [[BusinessPartners]] via address State field — partner addresses reference these state codes
