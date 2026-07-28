---
entity: PaymentTermsTypesService
domain: banking-payments
readable: false
methods: ["PaymentTermsTypesService_UpdateWithBPs"]
rows_oil: null
---
# PaymentTermsTypesService
RPC service that updates a payment-terms definition and propagates the change to linked business partners.

⚠️ Write-only service — out of scope under our standing READ-ONLY rule ([[00-SAP-B1-Atlas]])
## Connections
- Domain: [[banking-payments]]
- [[PaymentTermsTypes]] — the payment-terms master it mutates (query that entity set for reads)
- [[BusinessPartners]] — partners the terms change propagates to
