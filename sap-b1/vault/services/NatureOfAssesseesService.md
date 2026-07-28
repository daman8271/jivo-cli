---
entity: NatureOfAssesseesService
domain: administration-setup-2
readable: false
methods: [POST]
rows_oil: null
---
# NatureOfAssesseesService
Lists India-localization 'nature of assessee' classifications used for TDS/withholding-tax treatment of business partners.

## Operations
- NatureOfAssesseesService_GetNatureOfAssesseeList

Function service — there is no entity set to `./sapb1 query` here. Entity sets are the read path in the CLI; browse this service's catalogued operations with `./sapb1 ops NatureOfAssesseesService`.

## Connections
- Domain: [[administration-setup-2]]
- [[BusinessPartners]] via the partner's nature-of-assessee classification — drives TDS/withholding-tax treatment
