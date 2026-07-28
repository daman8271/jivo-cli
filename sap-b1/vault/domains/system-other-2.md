# System & Other (part 2)

Catch-all entities, part 2 of 2 (see [[system-other-1]]): the standout is [[ProductTrees]] — 620 bills of material driving [[ProductionOrders]]. Around it: [[Relationships]] and [[Teams]] (org/BP relationship maps), [[PredefinedTexts]], [[States]] (Indian state codes on every address), [[SelfCreditMemos]], [[TransportationDocument]], tracking/route setup ([[TrackingNotes]], [[RouteStages]], [[Sections]]), value-mapping tables for EDI, and the Web Client runtime stores (bookmarks, dashboards, launchpads, notifications, preferences, variants — [[WebClientVariants]] holds 320 saved views).

Part of the [[00-SAP-B1-Atlas]] — 22 services. Data model context: [[01-Data-Model]]; ready-made queries: [[02-Query-Cookbook]]; live row counts: [[03-Live-Data-Census]].

## Readable entities (rows = live count in JIVO_OIL_HANADB)
- [[ProductTrees]] **(620 rows)** — Bills of Materials (BOMs) defining which component items and stages make up each produced/assembled item — 620 active BOMs for JIVO's oil production.
- [[WebClientVariants]] **(320 rows)** — Saved list-view/filter/chart variants for Web Client screens (columns, sorts, filters per user or system) — 320 variants.
- [[States]] **(98 rows)** — Master list of states/provinces per country including Indian GST state codes and union-territory flags, used in BP and document addresses — 98 rows.
- [[Sections]] **(26 rows)** — India-localization TDS/withholding-tax sections (e.g. 194C, 194J) referenced by withholding tax codes — 26 statutory sections defined.
- [[WebClientBookmarkTiles]] **(10 rows)** — User-saved bookmark tiles on the SAP B1 Web Client home screen linking to views/URLs — 10 tiles saved.
- [[WeightMeasures]] **(5 rows)** — Master list of weight units of measure (mg-based conversion factors) used on item master weight fields — 5 units defined.
- [[WebClientLaunchpads]] **(2 rows)** — Per-user Web Client home-screen (launchpad) layout and theme settings — 2 users have customized launchpads.
- [[PredefinedTexts]] — Stores reusable predefined text snippets that users can insert into documents and remarks; empty in JIVO_OIL_HANADB.
- [[Relationships]] — Catalog of relationship types used to map connections between business partners and contacts in the relationship map; unused here.
- [[RouteStages]] — Defines production routing stages (steps a manufacturing order passes through); not configured in this database.
- [[SelfCreditMemos]] — Self-invoicing credit memo documents (reverse-charge/self-billing scenarios) with full document lifecycle actions; none issued in this database.
- [[ShortLinkMappings]] — GUID-keyed short-link mappings used by the Web Client to shorten/share deep links; empty.
- [[Teams]] — HR master of employee teams for grouping employees; not used in this database.
- [[TerminationReason]] — HR lookup of employment termination reasons attached to employee records; empty.
- [[TrackingNotes]] — Intrastat tracking notes for EU cross-border goods movement reporting; not applicable to this Indian company, empty.
- [[TransportationDocument]] — Brazil-localization transportation documents (CT-e freight docs) linking freight to sales/delivery documents; unused here.
- [[TSRExceptionalEvents]] — Technical Security Report exceptional events log (fiscal/audit compliance, e.g. Portugal SAF-T); empty.
- [[ValueMapping]] — EDI/interface value-mapping table translating internal codes to external partner codes for electronic communication; unused.
- [[ValueMappingCommunication]] — Defines the communication channels/partners that value mappings apply to in EDI exchanges; unused.
- [[WebClientDashboards]] — Stores user-created analytical dashboards in the Web Client; none created.
- [[WebClientNotifications]] — In-app notifications shown to users in the Web Client notification center; empty.
- [[WebClientPreferences]] — Per-user Web Client preference settings (formats, defaults); none stored.
