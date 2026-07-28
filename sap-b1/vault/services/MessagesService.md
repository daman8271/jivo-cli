---
entity: MessagesService
domain: administration-setup-2
readable: false
methods: [POST]
rows_oil: null
---
# MessagesService
Reads the internal B1 messaging system (inbox, outbox, sent) used for user-to-user and alert messages inside SAP Business One.

## Operations
- MessagesService_GetInbox
- MessagesService_GetOutbox
- MessagesService_GetSentMessages

Function service — there is no entity set to `./sapb1 query` here. Entity sets are the read path in the CLI; browse this service's catalogued operations with `./sapb1 ops MessagesService`.

## Connections
- Domain: [[administration-setup-2]]
- [[Users]] via UserCode — message senders and recipients are B1 users
- [[Messages]] via message number — the underlying internal-message entity set
