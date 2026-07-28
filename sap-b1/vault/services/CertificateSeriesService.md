---
entity: CertificateSeriesService
domain: administration-setup-1
readable: false
methods: [CertificateSeriesService_GetCertificateSeriesList]
rows_oil: null
---
# CertificateSeriesService
Lists certificate series used for numbering tax/withholding certificates in certain localizations.

⚠️ Write-only service — out of scope under our standing READ-ONLY rule ([[00-SAP-B1-Atlas]])

## Connections
- Domain: [[administration-setup-1]]
- [[CertificateSeries]] — the certificate series records this RPC lists (AbsEntry)
