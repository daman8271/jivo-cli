---
entity: ActivitiesService
domain: business-partners-crm
readable: false
methods: [ActivitiesService_GetActivityList, ActivitiesService_GetSingleInstanceFromSeries, ActivitiesService_UpdateSingleInstanceInSeries, ActivitiesService_DeleteSingleInstanceFromSeries, ActivitiesService_GetTopNActivityInstances]
rows_oil: null
---
# ActivitiesService
RPC helper for CRM activities: list activities and manage individual instances of recurring activity series.

⚠️ Write-only service — out of scope under our standing READ-ONLY rule ([[00-SAP-B1-Atlas]]).

## Connections
- Domain: [[business-partners-crm]]
- [[Activities]] — the activity records the RPCs operate on
- [[BusinessPartners]] — BPs the activities are linked to
