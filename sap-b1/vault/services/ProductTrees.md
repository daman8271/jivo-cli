---
entity: ProductTrees
domain: system-other-2
readable: true
methods: [GET, POST, PATCH, DELETE]
rows_oil: 620
---
# ProductTrees
Bills of Materials (BOMs) defining which component items and stages make up each produced/assembled item — 620 active BOMs for JIVO's oil production. Live rows in JIVO_OIL_HANADB: 620.
## Read it
```bash
cd ~/sap-b1/cli
./sapb1 query ProductTrees --top 5
./sapb1 query ProductTrees --count
./sapb1 query ProductTrees --select "TreeCode,TreeType,Quantity,Warehouse" --top 10
./sapb1 query ProductTrees --filter "TreeType eq 'iProductionTree'" --top 10
```
## Key fields
| Field | Meaning |
|---|---|
| TreeCode | Parent item code (BOM header) |
| TreeType | BOM type (production/sales/assembly/template) |
| Quantity | Parent output quantity per BOM run |
| Warehouse | Default production warehouse |
| PriceList | Price list for component costing |
| Project | Linked project code |
| ProductDescription | Parent item description |
| PlanAvgProdSize | Planned average production size |
| DistributionRule | Cost distribution rule |
| ProductTreeLines | Component item lines (collection) |
| ProductTreeStages | Production stages (collection) |
| U_CrtDt | UDF: BOM creation date |
| U_AppDt | UDF: BOM approval date |
| U_Bomuser | UDF: user who created BOM |
## Connections
- Domain: [[system-other-2]]
- [[Items]] via TreeCode (parent ItemCode) and component ItemCode on ProductTreeLines
- [[Warehouses]] via Warehouse
- [[PriceLists]] via PriceList
- [[Projects]] via Project
- [[DistributionRules]] via DistributionRule
