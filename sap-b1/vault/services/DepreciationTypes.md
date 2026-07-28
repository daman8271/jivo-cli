---
entity: DepreciationTypes
domain: fixed-assets
readable: true
methods: ["GET DepreciationTypes", "GET DepreciationTypes(id)", "POST DepreciationTypes", "PATCH DepreciationTypes(id)", "DELETE DepreciationTypes(id)"]
rows_oil: 4
---
# DepreciationTypes
Defines fixed-asset depreciation calculation rules (method, rates, period controls, salvage/limits) that asset classes apply to compute periodic depreciation. Live rows in JIVO_OIL_HANADB: 4.
## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query DepreciationTypes --top 5
./sapb1 query DepreciationTypes --count
./sapb1 query DepreciationTypes --select "Code,Description,DepreciationMethod,StraightLinePercentage" --top 10
# Only the straight-line depreciation rules:
./sapb1 query DepreciationTypes --filter "DepreciationMethod eq 'dmStraightLine'" --select "Code,Description,StraightLinePercentage"
```
## Key fields
| Field | Meaning |
|---|---|
| Code | Depreciation type key |
| Description | Human-readable rule name |
| DepreciationMethod | Calculation method (straight-line, declining, etc.) |
| CalculationBase | Base value for calculation |
| ValidFrom | Rule validity start date |
| ValidTo | Rule validity end date |
| StraightLinePercentage | Annual straight-line rate |
| DecliningPercentage | Declining-balance annual rate |
| DecliningFactor | Declining-balance multiplier factor |
| SalvagePercentage | Salvage value percentage |
| MaximumDepreciableValue | Cap on depreciable amount |
| MinimumDepreciatedValue | Floor for net book value |
| DepreciationTypePool | Pooled-depreciation grouping |
| AcquisitionPeriodControl | Period control at acquisition |
## Connections
- Domain: [[fixed-assets]]
- [[AssetClasses]] via DepreciationType in each class's depreciation-area lines — classes pick which rule computes their periodic depreciation
- [[AssetDepreciationGroups]] via depreciation type assignment — groups bundle assets under shared depreciation rules
- [[DepreciationAreas]] via DepreciationArea — a depreciation type is applied per area (book, tax, etc.)
