# Business Partners & CRM

Master data for everyone JIVO trades with: [[BusinessPartners]] (3,384 customers/vendors/leads keyed by CardCode) with [[Contacts]] persons, groups/properties classification, [[Territories]], [[Industries]] and [[BPPriorities]] (in [[system-other-1]]). The CRM layer tracks touchpoints via [[Activities]] (with locations/statuses/types setup), marketing [[Campaigns]] with [[TargetGroups]] and [[CampaignResponseType]], plus [[CustomerEquipmentCards]] for install-base tracking. CardCode from this domain is the most widely used join key in the entire Service Layer.

Part of the [[00-SAP-B1-Atlas]] — 28 services. Data model context: [[01-Data-Model]]; ready-made queries: [[02-Query-Cookbook]]; live row counts: [[03-Live-Data-Census]].

## Readable entities (rows = live count in JIVO_OIL_HANADB)
- [[BusinessPartners]] **(3,384 rows)** — Master data for all 3,384 customers, vendors and leads — the core CRM/AR-AP entity with addresses, bank accounts, contacts and credit terms.
- [[WebClientRecentActivities]] **(97 rows)** — Per-user usage log of recently opened apps/pages in the SAP B1 Web Client, powering its "recent activities" home-screen tiles.
- [[BusinessPartnerProperties]] **(64 rows)** — The 64 named boolean property flags assignable to business partners for classification and filtering.
- [[BusinessPartnerGroups]] **(47 rows)** — Customer/vendor grouping catalog (47 groups) used to segment business partners for reporting and defaults.
- [[ActivityStatuses]] **(2 rows)** — Lookup of activity status values (e.g. Open/Closed) applied to CRM activities.
- [[CampaignResponseType]] **(2 rows)** — Lookup of possible response outcomes recorded against marketing campaign targets.
- [[ActivityLocations]] **(1 row)** — Lookup of meeting/activity locations selectable on CRM activities.
- [[ActivityTypes]] **(1 row)** — Lookup of user-defined activity type categories (call, meeting, task subtypes).
- [[CommissionGroups]] **(1 row)** — Commission percentage groups assignable to BPs, items or salespeople for commission calculation.
- [[Industries]] **(1 row)** — Master list of industry classifications assignable to business partners for CRM segmentation and reporting.
- [[Territories]] **(1 row)** — Hierarchical sales-territory master (parent/child regions) used to segment business partners and sales activity geographically.
- [[Activities]] — CRM activity log (calls, meetings, tasks, notes) linked to business partners; empty in JIVO_OIL_HANADB (fields from standard schema).
- [[ActivityRecipientLists]] — Named recipient distribution lists used to notify multiple users about a CRM activity; empty here.
- [[ActivityRecipientListsService]] — Function service returning the list of activity recipient distribution lists.
- [[Campaigns]] — Marketing campaign records targeting groups of business partners; unused (0 rows) in this company.
- [[CampaignsService]] — Function service returning the list of marketing campaigns.
- [[Contacts]] — Contact persons attached to business partners; empty as a standalone set here (contacts live inline in BusinessPartners.ContactEmployees).
- [[CustomerEquipmentCards]] — Tracks serialized equipment/service cards per customer (which serial-numbered item a customer owns) for after-sales service management; empty in JIVO_OIL_HANADB so fields are inferred from the SAP B1 schema.
- [[MobileAddOnSetting]] — Configuration settings for the SAP B1 mobile add-on/app (per-user or per-device mobile client preferences); empty in JIVO_OIL_HANADB so no fields are inferable.
- [[PartnersSetups]] — Setup list of sales-opportunity partners (external firms cooperating on deals) referenced from opportunity records; empty in this database.

## Not readable here (write/RPC-side — never called, read-only mandate)
- [[ActivitiesService]] — RPC helper for CRM activities: list activities and manage individual instances of recurring activity series.
- [[AddressService]] — Utility that formats/resolves a full address string from address components.
- [[BusinessPartnerPropertiesService]] — RPC to fetch the list of the 64 BP property flags used to classify business partners.
- [[BusinessPartnersService]] — Write-side helper to create an opening balance journal for a business partner (never used here — read-only mandate).
- [[CampaignResponseTypeService]] — RPC returning the catalog of campaign response types.
- [[MobileAddOnSettingService]] — RPC exposing settings for the SAP B1 mobile add-on client.
- [[PartnersSetupsService]] — RPC returning partner setup/configuration records (BP-related setup definitions).
- [[WebClientRecentActivityService]] — RPC feeding the SAP B1 Web Client's recent-activity widget.
