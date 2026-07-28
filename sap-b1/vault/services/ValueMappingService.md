---
entity: ValueMappingService
domain: administration-setup-2
readable: false
methods: ["ValueMappingService_GetMappedB1Value", "ValueMappingService_GetThirdPartyValuesForB1Value", "ValueMappingService_RemoveMappedValue"]
rows_oil: null
---
# ValueMappingService
Translates codes between SAP B1 values and third-party system values for integration scenarios.

## Operations
- ValueMappingService_GetMappedB1Value
- ValueMappingService_GetThirdPartyValuesForB1Value
- ValueMappingService_RemoveMappedValue

Function service — no queryable entity set behind it, so the CLI's read path (`./sapb1 query ...`) does not apply here. Entity sets are the read path in the CLI; for the stored mapping rows read [[ValueMapping]] instead. RemoveMappedValue is a write and stays out of scope under our standing READ-ONLY rule. Browse this service's operations with:

```bash
cd ~/sap-b1/cli
./sapb1 ops ValueMappingService
```

## Connections
- Domain: [[administration-setup-2]]
- [[ValueMapping]] — the entity set holding the B1-to-third-party value mapping rows this service translates
