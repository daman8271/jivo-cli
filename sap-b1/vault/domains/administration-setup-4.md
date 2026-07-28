# Administration & Setup (part 4)

Company-wide configuration, part 4 of 4 (see [[administration-setup-1]], [[administration-setup-2]], [[administration-setup-3]]) — the tail of readable admin entities: [[Users]] (55 SAP user accounts), [[UserTablesMD]] (custom UDT definitions, 121), and the Web Client personalization stores [[WebClientFormSettings]], [[WebClientListviewFilters]] and [[WebClientVariantGroups]].

Part of the [[00-SAP-B1-Atlas]] — 5 services. Data model context: [[01-Data-Model]]; ready-made queries: [[02-Query-Cookbook]]; live row counts: [[03-Live-Data-Census]].

## Readable entities (rows = live count in JIVO_OIL_HANADB)
- [[UserTablesMD]] **(59 rows)** — Metadata registry of custom user-defined tables (UDTs) added to the company database schema.
- [[Users]] **(55 rows)** — Manages SAP B1 login accounts — user codes, credentials, superuser/lock status, department/branch assignment, and discount/cash limits.
- [[WebClientVariantGroups]] **(3 rows)** — Groups saved view variants (per user and object/view) in the SAP B1 Web Client, tracking each user's default variant.
- [[WebClientFormSettings]] — Stores per-user form layout/personalization settings for the SAP B1 Web Client (empty in JIVO_OIL_HANADB).
- [[WebClientListviewFilters]] — Stores saved list-view filter definitions users create in the SAP B1 Web Client (empty in JIVO_OIL_HANADB).
