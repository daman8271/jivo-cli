---
entity: CertificateSeries
domain: administration-setup-3
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 0
---
# CertificateSeries
Numbering series for withholding-tax certificates (e.g. TDS certificates in India localization); unused here. Live rows in JIVO_OIL_HANADB: 0.

## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query CertificateSeries --top 5
./sapb1 query CertificateSeries --count
# Table is empty here; discover fields once populated:
./sapb1 fields CertificateSeries
```

## Key fields
Table is empty in JIVO_OIL_HANADB, so no field sample was captured. Expect a series key plus certificate-number range fields; confirm with `./sapb1 fields CertificateSeries` once populated.

## Connections
- Domain: [[administration-setup-3]]
- No related entities recorded in recon — withholding-tax certificate numbering, unused here.
