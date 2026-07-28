---
entity: Countries
domain: system-other-1
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 243
---
# Countries
Standard country master (243 rows) with ISO codes and bank/tax validation rules, referenced by all addresses and business partners. Live rows in JIVO_OIL_HANADB: 243.
## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query Countries --top 5
./sapb1 query Countries --count
./sapb1 query Countries --select "Code,Name,ISOAlpha2Code,ISOAlpha3Code" --top 10
# find India's country record
./sapb1 query Countries --filter "ISOAlpha2Code eq 'IN'" --top 5
```
## Key fields
| Field | Meaning |
|---|---|
| Code | Country key |
| Name | Country name |
| ISOAlpha2Code | ISO 2-letter code |
| ISOAlpha3Code | ISO 3-letter code |
| ISONumeric | ISO numeric code |
| CodeForReports | Reporting country code |
| AddressFormat | Address layout format |
| EU | EU member flag |
| EAEU | EAEU member flag |
| Blacklisted | Fiscal blacklist flag |
| NumberOfDigitsForTaxID | Tax-ID length check |
| IbanValidation | IBAN validation flag |
| BankCodeDigits | Bank code length |
| UICCountryCode | UIC country code |
## Connections
- Domain: [[system-other-1]]
- [[BusinessPartners]] via address Country — partner addresses reference a country
- [[Currencies]] via country currency conventions — currency used per country
- [[States]] via Country — states defined under a country
