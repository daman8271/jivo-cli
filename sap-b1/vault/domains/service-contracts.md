# Service & Contracts

SAP B1's after-sales service module: [[ServiceCalls]] (support tickets) resolved against [[KnowledgeBaseSolutions]] and covered by [[ServiceContracts]] built from [[ContractTemplates]]. The rest of the domain is call-classification setup — [[ServiceCallTypes]], [[ServiceCallStatus]], [[ServiceCallOrigins]], problem types/subtypes and solution statuses. At JIVO this module is effectively unused (zero live rows across the board), but the endpoints all read fine.

Part of the [[00-SAP-B1-Atlas]] — 16 services. Data model context: [[01-Data-Model]]; ready-made queries: [[02-Query-Cookbook]]; live row counts: [[03-Live-Data-Census]].

## Readable entities (rows = live count in JIVO_OIL_HANADB)
- [[ServiceCallOrigins]] **(3 rows)** — Catalog of how service calls were reported (e.g. phone, email, web) — 3 seed values in JIVO_OIL.
- [[ServiceCallSolutionStatus]] **(3 rows)** — Status codes for knowledge-base solutions (e.g. internal, review, published) — 3 seed values.
- [[ServiceCallStatus]] **(3 rows)** — Lifecycle status codes for service calls (open/pending/closed) — 3 seed values.
- [[ContractTemplates]] — Reusable blueprints defining coverage, duration and SLA terms from which customer service contracts are created — empty in JIVO_OIL_HANADB (fields listed from standard SAP B1 schema; live sample unavailable).
- [[KnowledgeBaseSolutions]] — Repository of documented symptoms/causes/solutions technicians attach to service calls for faster resolution — empty in this database (fields from standard schema).
- [[ServiceCallProblemSubTypes]] — Second-level classification of service-call problems, nested under problem types — empty here.
- [[ServiceCallProblemTypes]] — Top-level classification of what kind of problem a service call reports — empty here.
- [[ServiceCalls]] — Customer support tickets (complaints/repair requests) tracked from creation to closure with SLA, technician and solution links — zero rows, the service module is unused at JIVO.
- [[ServiceCallTypes]] — Catalog of service-call categories (e.g. repair, maintenance, inquiry) — empty here.
- [[ServiceContracts]] — Customer service/warranty agreements defining coverage periods and SLA terms against which service calls are logged — empty, not used in this oil-trading database.

## Not readable here (write/RPC-side — never called, read-only mandate)
- [[ServiceCallOriginsService]] — RPC helper that returns the list of service-call origin codes (how a call was reported).
- [[ServiceCallProblemSubTypesService]] — RPC helper that returns the list of service-call problem sub-type codes.
- [[ServiceCallProblemTypesService]] — RPC helper that returns the list of service-call problem type codes.
- [[ServiceCallSolutionStatusService]] — RPC helper that returns the list of knowledge-base solution status codes.
- [[ServiceCallStatusService]] — RPC helper that returns the list of service-call status codes.
- [[ServiceCallTypesService]] — RPC helper that returns the list of service-call type codes.
