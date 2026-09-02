# Rosetta (lines) — `PurchaseInvoices`.DocumentLines ↔ `PCH1` · OIL

Derived from **29 real line pairs** across DocEntry 49169, 48751, 48147, 47218, 46464, 45433, matched on `LineNum`. A pair had to agree on every line sampled.

- **15** properties mapped to exactly one column
- **9** renamed ← the ones that bite

## Line properties whose name differs

| API property (what you send on a line) | HANA column |
|---|---|
| `AccountCode` | **`AcctCode`** |
| `CostingCode` | **`OcrCode`** |
| `CostingCode2` | **`OcrCode2`** |
| `CostingCode3` | **`OcrCode3`** |
| `CostingCode4` | **`OcrCode4`** |
| `CostingCode5` | **`OcrCode5`** |
| `LocationCode` | **`LocCode`** |
| `SalesPersonCode` | **`SlpCode`** |
| `VisualOrder` | **`VisOrder`** |

## Same name on both sides (6)

`Currency`, `DocEntry`, `LineNum`, `TaxCode`, `U_Recvd_Qty`, `U_Remarks`

## Ambiguous — narrow with a --where that separates the candidates

| API property | Candidates |
|---|---|
| `ActualDeliveryDate` | `ActDelDate`, `DocDate` |
| `BaseType` | `BaseType`, `CiOppLineN`, `NCMCode`, `PcDocType`, `ReturnAct`, `ReturnRsn`, `TargetType`, `TrnsCode` |
| `GrossPrice` | `GPBefDisc`, `GTotal`, `GTotalSC`, `LineTotal`, `OpenSum`, `OpenSumSys`, `Price`, `PriceAfVAT`, `PriceBefDi`, `TotalSumSy` |
| `GrossTotal` | `GPBefDisc`, `GTotal`, `GTotalSC`, `LineTotal`, `OpenSum`, `OpenSumSys`, `Price`, `PriceAfVAT`, `PriceBefDi`, `TotalSumSy` |
| `GrossTotalSC` | `GPBefDisc`, `GTotal`, `GTotalSC`, `LineTotal`, `OpenSum`, `OpenSumSys`, `Price`, `PriceAfVAT`, `PriceBefDi`, `TotalSumSy` |
| `LineTotal` | `GPBefDisc`, `GTotal`, `GTotalSC`, `LineTotal`, `OpenSum`, `OpenSumSys`, `Price`, `PriceAfVAT`, `PriceBefDi`, `TotalSumSy` |
| `NCMCode` | `BaseType`, `CiOppLineN`, `NCMCode`, `PcDocType`, `ReturnAct`, `ReturnRsn`, `TargetType`, `TrnsCode` |
| `OpenAmount` | `GPBefDisc`, `GTotal`, `GTotalSC`, `LineTotal`, `OpenSum`, `OpenSumSys`, `Price`, `PriceAfVAT`, `PriceBefDi`, `TotalSumSy` |
| `OpenAmountSC` | `GPBefDisc`, `GTotal`, `GTotalSC`, `LineTotal`, `OpenSum`, `OpenSumSys`, `Price`, `PriceAfVAT`, `PriceBefDi`, `TotalSumSy` |
| `Price` | `GPBefDisc`, `GTotal`, `GTotalSC`, `LineTotal`, `OpenSum`, `OpenSumSys`, `Price`, `PriceAfVAT`, `PriceBefDi`, `TotalSumSy` |
| `PriceAfterVAT` | `GPBefDisc`, `GTotal`, `GTotalSC`, `LineTotal`, `OpenSum`, `OpenSumSys`, `Price`, `PriceAfVAT`, `PriceBefDi`, `TotalSumSy` |
| `RowTotalSC` | `GPBefDisc`, `GTotal`, `GTotalSC`, `LineTotal`, `OpenSum`, `OpenSumSys`, `Price`, `PriceAfVAT`, `PriceBefDi`, `TotalSumSy` |
| `ShippingMethod` | `BaseType`, `CiOppLineN`, `NCMCode`, `PcDocType`, `ReturnAct`, `ReturnRsn`, `TargetType`, `TrnsCode` |
| `U_UNE_CALI` | `DistribExp`, `PostTax`, `TaxRelev`, `TaxStatus`, `TaxType`, `U_UNE_CALI`, `U_UNE_CUNT`, `UpdInvntry` |
| `U_UNE_CUNT` | `DistribExp`, `PostTax`, `TaxRelev`, `TaxStatus`, `TaxType`, `U_UNE_CALI`, `U_UNE_CUNT`, `UpdInvntry` |
| `U_UNE_SCHI` | `CUSplit`, `DeferrTax`, `DescOW`, `DetailsOW`, `DistribIS`, `DropShip`, `EnSetCost`, `FreeChrgBP`, `IndEscala`, `InvQtyOnly`, `IsAqcuistn`, `IsByPrdct`, `IsCstmAct`, `IsPrscGood`, `LinManClsd`, `LinePoPrss`, `NeedQty`, `NoInvtryMv`, `PartRetire`, `PickStatus`, `PriceEdit`, `RevCharge`, `SpecPrice`, `TaxOnly`, `ThirdParty`, `TreeType`, `U_UNE_SCHI`, `UseBaseUn`, `WtCalced`, `WtLiable`, `isSrvCall` |
| `UnitPrice` | `GPBefDisc`, `GTotal`, `GTotalSC`, `LineTotal`, `OpenSum`, `OpenSumSys`, `Price`, `PriceAfVAT`, `PriceBefDi`, `TotalSumSy` |
