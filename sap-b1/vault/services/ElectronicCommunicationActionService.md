---
entity: ElectronicCommunicationActionService
domain: administration-setup-1
readable: false
methods: [ElectronicCommunicationActionService_GetAction, ElectronicCommunicationActionService_UpdateAction, ElectronicCommunicationActionService_ConfirmSuccessOfCommunication, ElectronicCommunicationActionService_ReportErrorAndContinue, ElectronicCommunicationActionService_ReportErrorAndStop]
rows_oil: null
---
# ElectronicCommunicationActionService
Drives the electronic document communication workflow (e.g. e-invoicing exchanges), fetching actions and reporting their success or failure.

⚠️ Write-only service — out of scope under our standing READ-ONLY rule ([[00-SAP-B1-Atlas]])

## Connections
- Domain: [[administration-setup-1]]
- [[ElectronicCommunicationActionsService]] — plural batch counterpart of this single-action RPC service
- The electronic documents themselves are not exposed as an entity set in this catalog
