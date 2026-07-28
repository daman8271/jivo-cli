---
entity: ElectronicCommunicationActionsService
domain: administration-setup-1
readable: false
methods: [GetEcmAction, AddEcmAction, UpdateEcmAction, DeleteEcmAction, GetEcmActionByDoc, GetEcmActionLogList, GetEcmActionLog, AddEcmActionLog]
rows_oil: null
---
# ElectronicCommunicationActionsService
Manages electronic communication (ECM) actions and their logs for legally-mandated electronic document exchange with authorities or partners.

## Operations
- GetEcmAction
- AddEcmAction
- UpdateEcmAction
- DeleteEcmAction
- GetEcmActionByDoc
- GetEcmActionLogList
- GetEcmActionLog
- AddEcmActionLog

Function-style service — it exposes no entity set, so there is nothing to `./sapb1 query` here. Entity sets are the read path in the CLI; browse this service's operations with `./sapb1 ops ElectronicCommunicationActionsService`.

## Connections
- Domain: [[administration-setup-1]]
- [[ElectronicFileFormats]] via file format ID — ECM actions reference an electronic file format definition for the generated document
