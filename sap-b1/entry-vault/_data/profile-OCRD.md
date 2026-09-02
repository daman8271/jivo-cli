# `OCRD` — field profile

> Mined live from HANA. Recent window = last **3650 days**. *Filled* means non-null **and** non-blank/non-zero — SAP stores `''` and `0` in fields nobody ever types in, so a NULL test alone calls every field 100% used.

| Book | Rows | Rows in window | Date column | Span |
|---|---:|---:|---|---|
| OIL | 3,411 | 3,411 | `CreateDate` | 2024-08-31 → 2026-08-24 |
| MART | 2,191 | 2,191 | `CreateDate` | 2024-08-31 → 2026-08-21 |
| BEV | 2,964 | 2,964 | `CreateDate` | 2024-08-31 → 2026-08-24 |

## Fields

Sorted as SAP stores them. **`—`** means the column exists in that book and is empty in every single row: SAP offers it, JIVO never fills it. **`n/a`** means the column does not exist in that book at all — a different fact entirely, and one that makes a write fail rather than merely do nothing.

| Field | Type | OIL all | MART all | BEV all | OIL 3650d | MART 3650d | BEV 3650d | Distinct | Reads as |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| `CardCode` | NVARCHAR(15) | 100% | 100% | 100% | 100% | 100% | 100% | 3,411 | |
| `CardName` | NVARCHAR(200) | 100% | 100% | 100% | 100% | 100% | 100% | 3,318 | |
| `CardType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `GroupCode` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 46 | |
| `CmpPrivate` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `Address` | NVARCHAR(100) | 54% | 33% | 50% | 54% | 33% | 50% | 1,790 | |
| `ZipCode` | NVARCHAR(20) | 96% | 97% | 97% | 96% | 97% | 97% | 880 | |
| `MailAddres` | NVARCHAR(100) | 54% | 33% | 50% | 54% | 33% | 50% | 1,781 | |
| `MailZipCod` | NVARCHAR(20) | 96% | 97% | 97% | 96% | 97% | 97% | 874 | |
| `Phone1` | NVARCHAR(50) | <1% | — | <1% | <1% | — | <1% | 21 | |
| `Phone2` | NVARCHAR(50) | <1% | — | — | <1% | — | — | 3 | |
| `Fax` | NVARCHAR(50) | <1% | <1% | <1% | <1% | <1% | <1% | 2 | |
| `CntctPrsn` | NVARCHAR(90) | 92% | 91% | 93% | 92% | 91% | 93% | 2,290 | |
| `Notes` | NVARCHAR(100) | <1% | — | <1% | <1% | — | <1% | 1 | |
| `Balance` | DECIMAL | 26% | 6% | 17% | 26% | 6% | 17% | 769 | |
| `DNotesBal` | DECIMAL | 7% | 2% | 4% | 7% | 2% | 4% | 219 | |
| `OrdersBal` | DECIMAL | 15% | 4% | 16% | 15% | 4% | 16% | 499 | |
| `GroupNum` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 20 | |
| `CreditLine` | DECIMAL | 9% | 5% | 14% | 9% | 5% | 14% | 146 | |
| `DebtLine` | DECIMAL | 36% | 44% | 44% | 36% | 44% | 44% | 34 | |
| `VatStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DdctStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ListNum` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 3 | |
| `DNoteBalFC` | DECIMAL | <1% | — | — | <1% | — | — | 2 | |
| `OrderBalFC` | DECIMAL | <1% | — | — | <1% | — | — | 3 | |
| `DNoteBalSy` | DECIMAL | 7% | 2% | 4% | 7% | 2% | 4% | 219 | |
| `OrderBalSy` | DECIMAL | 15% | 4% | 16% | 15% | 4% | 16% | 499 | |
| `Transfered` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `BalTrnsfrd` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Free_Text` | NCLOB | <1% | <1% | — | <1% | <1% | — | 0 | |
| `SlpCode` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 148 | |
| `PrevYearAc` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Currency` | NVARCHAR(3) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `BalanceSys` | DECIMAL | 26% | 6% | 17% | 26% | 6% | 17% | 769 | |
| `BalanceFC` | DECIMAL | <1% | — | — | <1% | — | — | 5 | |
| `Protected` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Cellular` | NVARCHAR(50) | 16% | 3% | 8% | 16% | 3% | 8% | 483 | |
| `City` | NVARCHAR(100) | 98% | 98% | 98% | 98% | 98% | 98% | 412 | |
| `County` | NVARCHAR(100) | <1% | <1% | <1% | <1% | <1% | <1% | 4 | |
| `Country` | NVARCHAR(3) | 100% | 100% | 100% | 100% | 100% | 100% | 15 | |
| `MailCity` | NVARCHAR(100) | 97% | 98% | 98% | 97% | 98% | 98% | 409 | |
| `MailCounty` | NVARCHAR(100) | <1% | <1% | <1% | <1% | <1% | <1% | 4 | |
| `MailCountr` | NVARCHAR(3) | 99% | 100% | 100% | 99% | 100% | 100% | 15 | |
| `E_Mail` | NVARCHAR(100) | <1% | — | <1% | <1% | — | <1% | 26 | |
| `DflAccount` | NVARCHAR(50) | 56% | 40% | 46% | 56% | 40% | 46% | 1,819 | |
| `DflBranch` | NVARCHAR(50) | 1% | <1% | <1% | 1% | <1% | <1% | 16 | |
| `BankCode` | NVARCHAR(30) | 100% | 100% | 100% | 100% | 100% | 100% | 60 | |
| `CardFName` | NVARCHAR(200) | 65% | 91% | 69% | 65% | 91% | 69% | 2,199 | |
| `FatherType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `QryGroup1` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `QryGroup2` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `QryGroup3` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `QryGroup4` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `QryGroup5` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `QryGroup6` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `QryGroup7` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `QryGroup8` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `QryGroup9` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `QryGroup10` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `QryGroup11` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `QryGroup12` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `QryGroup13` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `QryGroup14` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `QryGroup15` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `QryGroup16` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `QryGroup17` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `QryGroup18` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `QryGroup19` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `QryGroup20` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `QryGroup21` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `QryGroup22` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `QryGroup23` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `QryGroup24` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `QryGroup25` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `QryGroup26` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `QryGroup27` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `QryGroup28` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `QryGroup29` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `QryGroup30` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `QryGroup31` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `QryGroup32` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `QryGroup33` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `QryGroup34` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `QryGroup35` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `QryGroup36` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `QryGroup37` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `QryGroup38` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `QryGroup39` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `QryGroup40` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `QryGroup41` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `QryGroup42` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `QryGroup43` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `QryGroup44` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `QryGroup45` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `QryGroup46` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `QryGroup47` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `QryGroup48` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `QryGroup49` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `QryGroup50` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `QryGroup51` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `QryGroup52` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `QryGroup53` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `QryGroup54` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `QryGroup55` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `QryGroup56` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `QryGroup57` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `QryGroup58` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `QryGroup59` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `QryGroup60` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `QryGroup61` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `QryGroup62` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `QryGroup63` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `QryGroup64` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CreateDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 450 | |
| `DscntObjct` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DscntRel` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Priority` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CreditCard` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CrCardNum` | NVARCHAR(254) | 18% | 7% | 20% | 18% | 7% | 20% | 603 | |
| `UserSign` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 5 | |
| `LocMth` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `validFor` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `frozenFor` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `sEmployed` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DdgKey` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DdtKey` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `FrozenComm` | NVARCHAR(30) | <1% | <1% | <1% | <1% | <1% | <1% | 1 | |
| `chainStore` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DiscInRet` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `State1` | NVARCHAR(3) | 99% | 99% | 99% | 99% | 99% | 99% | 39 | |
| `State2` | NVARCHAR(3) | 98% | 99% | 99% | 98% | 99% | 99% | 38 | |
| `ObjType` | NVARCHAR(20) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DebPayAcct` | NVARCHAR(15) | 100% | 100% | 100% | 100% | 100% | 100% | 36 | |
| `ShipToDef` | NVARCHAR(50) | 99% | 100% | 100% | 99% | 100% | 100% | 2,510 | |
| `Block` | NVARCHAR(100) | 47% | 25% | 43% | 47% | 25% | 43% | 1,388 | |
| `MailBlock` | NVARCHAR(100) | 47% | 25% | 43% | 47% | 25% | 43% | 1,391 | |
| `Deleted` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `IBAN` | NVARCHAR(50) | <1% | — | — | <1% | — | — | 1 | |
| `DocEntry` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 3,411 | |
| `BackOrder` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PartDelivr` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `BlockDunn` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `BankCountr` | NVARCHAR(3) | 98% | 100% | 95% | 98% | 100% | 95% | 7 | |
| `CollecAuth` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `SinglePaym` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PaymBlock` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `HouseBank` | NVARCHAR(30) | 90% | 16% | 88% | 90% | 16% | 88% | 1 | |
| `PyBlckDesc` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `HousBnkCry` | NVARCHAR(3) | 9% | 2% | 11% | 9% | 2% | 11% | 1 | |
| `SysMatchNo` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DeferrTax` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `WTLiable` | NVARCHAR(1) | 93% | 98% | 94% | 93% | 98% | 94% | 2 | |
| `AccCritria` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `WTCode` | NVARCHAR(4) | <1% | — | <1% | <1% | — | <1% | 2 | |
| `Equ` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `TypWTReprt` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `IsDomestic` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `IsResident` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `AutoCalBCG` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Building` | NCLOB | <1% | <1% | <1% | <1% | <1% | <1% | 0 | |
| `MailBuildi` | NCLOB | <1% | <1% | <1% | <1% | <1% | <1% | 0 | |
| `BillToDef` | NVARCHAR(50) | 99% | 100% | 100% | 99% | 100% | 100% | 2,518 | |
| `IntrntSite` | NVARCHAR(100) | <1% | — | — | <1% | — | — | 1 | |
| `LangCode` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `DflBankKey` | INTEGER | 56% | 40% | 46% | 56% | 40% | 46% | 60 | |
| `UseShpdGd` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `InsurOp347` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `StreetNo` | NVARCHAR(100) | <1% | <1% | <1% | <1% | <1% | <1% | 9 | |
| `MailStrNo` | NVARCHAR(100) | <1% | <1% | <1% | <1% | <1% | <1% | 9 | |
| `TaxRndRule` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `VendTID` | INTEGER | <1% | <1% | <1% | <1% | <1% | <1% | 1 | |
| `ThreshOver` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `SurOver` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `OpCode347` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `ResidenNum` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Affiliate` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `MivzExpSts` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `HierchDdct` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CertWHT` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `CertBKeep` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `WHShaamGrp` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DatevFirst` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DflSwift` | NVARCHAR(50) | 56% | 40% | 46% | 56% | 40% | 46% | 1,374 | |
| `AutoPost` | NVARCHAR(1) | 26% | 39% | 29% | 26% | 39% | 29% | 1 | |
| `Series` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 6 | |
| `Number` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1,762 | |
| `TaxIdIdent` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Attachment` | NCLOB | 31% | 8% | 22% | 31% | 8% | 22% | 0 | |
| `AtcEntry` | INTEGER | 31% | 8% | 22% | 31% | 8% | 22% | 1,042 | |
| `DiscRel` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `NoDiscount` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `SCAdjust` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `GlblLocNum` | NVARCHAR(50) | <1% | — | <1% | <1% | — | <1% | 1 | |
| `SenderID` | NVARCHAR(50) | <1% | — | — | <1% | — | — | 1 | |
| `RcpntID` | NVARCHAR(50) | <1% | — | — | <1% | — | — | 2 | |
| `SefazCheck` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `TpCusPres` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `BlockComm` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `EdrsFromBP` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `EdrsToBP` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `CreateTS` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1,709 | |
| `UpdateTS` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 3,189 | |
| `EffecPrice` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `TxExMxVdTp` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `MerchantID` | NVARCHAR(15) | <1% | — | — | <1% | — | — | 1 | |
| `UseBilAddr` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 2 | |
| `NaturalPer` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DPPStatus` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `EnERD4In` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `EnERD4Out` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DflCustomr` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `FCERelevnt` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `FCEVldte` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `AggregDoc` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `EffcAllSrc` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DataVers` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 231 | |
| `DefaultCur` | NVARCHAR(3) | <1% | <1% | <1% | <1% | <1% | <1% | 1 | |
| `FCEPmnMean` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `NotRel4MI` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `U_Emp_Code` | NVARCHAR(8) | 15% | 11% | 9% | 15% | 11% | 9% | 480 | |
| `U_Main_Group` | NVARCHAR(50) | 99% | 100% | 100% | 99% | 100% | 100% | 63 | |
| `U_Chain` | NVARCHAR(50) | 44% | 52% | 50% | 44% | 52% | 50% | 48 | |
| `U_AddressIdPrint` | NVARCHAR(10) | <1% | — | — | <1% | — | — | 1 | |
| `U_BranchHomeBpl` | NVARCHAR(11) | <1% | — | — | <1% | — | — | 4 | |
| `U_UNE_BRCH` | NVARCHAR(100) | <1% | — | — | <1% | — | — | 1 | |
| `U_CATGCODE` | NVARCHAR(10) | <1% | — | — | <1% | — | — | 1 | |
| `U_CMDTCODE` | NVARCHAR(20) | — | — | <1% | — | — | <1% | 0 | |
| `U_WG_CardCode` | NVARCHAR(11) | 71% | n/a | n/a | 71% | n/a | n/a | 2,399 | |
| `U_MSME` | NVARCHAR(20) | 9% | 3% | 8% | 9% | 3% | 8% | 299 | |
| `U_MSME_Type` | NVARCHAR(15) | 8% | 3% | 7% | 8% | 3% | 7% | 3 | |
| `U_MSME_BType` | NVARCHAR(25) | 8% | 3% | 7% | 8% | 3% | 7% | 14 | |
| `U_Fssai` | NVARCHAR(20) | 3% | <1% | <1% | 3% | <1% | <1% | 99 | |
| `U_TDS_RECOV` | NVARCHAR(1) | 100% | 100% | n/a | 100% | 100% | n/a | 1 | |
| `U_TDS_RECOV_GL` | NVARCHAR(15) | — | <1% | n/a | — | <1% | n/a | 0 | |

_**Reads as** is deliberately blank: fill it with what the field means in JIVO's terms, not SAP's. That column is the whole point of the note._

## Columns that do not exist in every book (4)

A field present in one book and absent in another. Sending it to the book that lacks it is an error, not a no-op.

| Column | Present in | Missing from |
|---|---|---|
| `U_OIL_CardCode` | BEV | **OIL, MART** |
| `U_TDS_RECOV` | OIL, MART | **BEV** |
| `U_TDS_RECOV_GL` | OIL, MART | **BEV** |
| `U_WG_CardCode` | OIL | **MART, BEV** |

## Value vocabularies (OIL)

Columns holding a small closed set of values. These are the drop-downs and flags an operator picks from, so the list *is* the rule.

- **`CardType`** (2 values) — `S`×2,235, `C`×1,176
- **`CmpPrivate`** (2 values) — `C`×3,402, `I`×9
- **`Phone1`** (22 values) — `NULL`×3,389, `8700926578`×2, `9210547383`×1, `9034161541`×1, `9314089065`×1, `9810223744`×1, `9810886638`×1, `ANIL`×1, `8699506689`×1, `9718924084`×1, `9810996103`×1, `9836510005`×1, `9818567654`×1, `9811288000`×1, `7210212398`×1, `9988479544`×1, `8816054256`×1, `011-23722345-48`×1, `9810107806`×1, `912836619800`×1, `9677731500`×1, `9210525110`×1
- **`Phone2`** (4 values) — `NULL`×3,408, `+91-22-6754 3456`×1, `+91 -2836296805`×1, `002233958000`×1
- **`Fax`** (3 values) — `NULL`×3,409, `8968084724`×1, `Sai-traders@hotmail.com`×1
- **`Notes`** (2 values) — `NULL`×3,408, `OK`×3
- **`GroupNum`** (20 values) — `-1`×2,831, `1`×375, `10`×78, `19`×61, `17`×18, `20`×11, `18`×10, `21`×8, `16`×5, `29`×2, `9`×2, `4`×2, `6`×1, `7`×1, `14`×1, `3`×1, `22`×1, `13`×1, `11`×1, `25`×1
- **`DebtLine`** (30 values) — `0.000000`×2,180, `10.000000`×1,136, `5000.000000`×39, `200000.000000`×8, `300000.000000`×5, `2000000.000000`×5, `1000000.000000`×4, `100000.000000`×3, `50000.000000`×2, `13000000.000000`×2, `4000000.000000`×2, `2500000.000000`×2, `10000000.000000`×2, `5400000.000000`×1, `12500000.000000`×1, `150000.000000`×1, `1548900.000000`×1, `261000000.000000`×1, `30000.000000`×1, `7500000.000000`×1, `9450000.000000`×1, `1500000.000000`×1, `80206.000000`×1, `25000.000000`×1, `9000000.000000`×1, `45846.000000`×1, `30000000.000000`×1, `19839755.000000`×1, `35000.000000`×1, `5000000.000000`×1
- **`VatStatus`** (1 values) — `Y`×3,411
- **`DdctStatus`** (1 values) — `N`×3,411
- **`ListNum`** (3 values) — `1`×3,405, `-1`×4, `4`×2
- **`DNoteBalFC`** (2 values) — `0.000000`×3,410, `-110000.000000`×1
- **`OrderBalFC`** (3 values) — `0.000000`×3,409, `-728.000000`×1, `-274414.560000`×1
- **`Transfered`** (1 values) — `N`×3,411
- **`BalTrnsfrd`** (1 values) — `N`×3,411
- **`PrevYearAc`** (1 values) — `N`×3,411
- **`Currency`** (2 values) — `INR`×3,380, `##`×31
- **`BalanceFC`** (5 values) — `0.000000`×3,407, `60704.000000`×1, `9384385.000000`×1, `211746139.930000`×1, `8006739.825000`×1
- **`Protected`** (1 values) — `N`×3,411
- **`County`** (5 values) — `NULL`×3,391, `INDIA`×15, `India`×3, `110058`×1, `110077`×1
- **`Country`** (15 values) — `IN`×3,368, `US`×17, `AE`×8, `AU`×3, `ES`×2, `QA`×2, `DE`×2, `SG`×2, `DK`×1, `CA`×1, `EG`×1, `FR`×1, `IE`×1, `SW`×1, `GB`×1
- **`MailCounty`** (5 values) — `NULL`×3,391, `INDIA`×15, `India`×3, `110058`×1, `110077`×1
- **`MailCountr`** (16 values) — `IN`×3,336, `NULL`×34, `US`×16, `AE`×8, `SG`×2, `DE`×2, `ES`×2, `AU`×2, `QA`×2, `DK`×1, `CA`×1, `EG`×1, `FR`×1, `IE`×1, `SW`×1, `GB`×1
- **`E_Mail`** (27 values) — `NULL`×3,385, `mailforsolutions@yahoo.com`×1, `starlightgraphics77@gmail.com`×1, `anamikaraj81@gmail.com`×1, `mahalaxmiagrisolution@gmail.com`×1, `SANJIB.CSD@GMAIL.COM`×1, `ajay@pearlind.in`×1, `abhishek@abhimanexpress.com`×1, `khushiramsharma2010@gmail.com`×1, `squibgroup@outlook.com`×1, `vinaymukhi@yahoo.com`×1, `vijay.chandran@apexcoconuts.com`×1, `a.kumar@abctransport.co.in`×1, `AARAVCONCPC@GMAIL.COM`×1, `starlitedel@gmail.com`×1, `vikash@matagroup.in`×1, `CHINTU.ARORA.781@REDIFFMAIL.COM`×1, `sunit62411@gmail.com`×1, `snindustries27@gmail.com`×1, `info@smccert.com`×1, `timingbeltcentre25110@gmail.com`×1, `accounts@dhtcindia.com`×1, `care@Paytm.com`×1, `hariomservice103@gmail.com`×1, `purchase@jivo.in`×1, `pyrumengineers4256@gmail.com`×1, `lalsonsfurnishers@gmail.com`×1
- **`DflBranch`** (17 values) — `NULL`×3,351, `∅`×18, `Rajouri Garden`×18, `RAJOURI GARDEN`×11, `PRASHANT VIHAR`×1, `SREEBHUMI BRANCH`×1, `KAROL BAGH`×1, `Hinjewadi Branch, Pune`×1, `ROHINI`×1, `GANAUR`×1, `GARIS BRANCH`×1, `Senior Mall, Noida`×1, `Ajmeri Gate`×1, `NETAJI SUBHASH PALACE`×1, `Sonipat`×1, `Shradhanand Marg, Ajmeri Gate`×1, `Samalkha`×1
- **`FatherType`** (1 values) — `P`×3,411
- **`QryGroup1`** (1 values) — `N`×3,411
- **`QryGroup2`** (1 values) — `N`×3,411
- **`QryGroup3`** (1 values) — `N`×3,411
- **`QryGroup4`** (1 values) — `N`×3,411
- **`QryGroup5`** (1 values) — `N`×3,411
- **`QryGroup6`** (1 values) — `N`×3,411
- **`QryGroup7`** (1 values) — `N`×3,411
- **`QryGroup8`** (1 values) — `N`×3,411
- **`QryGroup9`** (1 values) — `N`×3,411
- **`QryGroup10`** (1 values) — `N`×3,411
- **`QryGroup11`** (1 values) — `N`×3,411
- **`QryGroup12`** (1 values) — `N`×3,411
- **`QryGroup13`** (1 values) — `N`×3,411
- **`QryGroup14`** (1 values) — `N`×3,411
- **`QryGroup15`** (1 values) — `N`×3,411
- **`QryGroup16`** (1 values) — `N`×3,411
- **`QryGroup17`** (1 values) — `N`×3,411
- **`QryGroup18`** (1 values) — `N`×3,411
- **`QryGroup19`** (1 values) — `N`×3,411
- **`QryGroup20`** (1 values) — `N`×3,411
- **`QryGroup21`** (1 values) — `N`×3,411
- **`QryGroup22`** (1 values) — `N`×3,411
- **`QryGroup23`** (1 values) — `N`×3,411
- **`QryGroup24`** (1 values) — `N`×3,411
- **`QryGroup25`** (1 values) — `N`×3,411
- **`QryGroup26`** (1 values) — `N`×3,411
- **`QryGroup27`** (1 values) — `N`×3,411
- **`QryGroup28`** (1 values) — `N`×3,411
- **`QryGroup29`** (1 values) — `N`×3,411
- **`QryGroup30`** (1 values) — `N`×3,411
- **`QryGroup31`** (1 values) — `N`×3,411
- **`QryGroup32`** (1 values) — `N`×3,411
- **`QryGroup33`** (1 values) — `N`×3,411
- **`QryGroup34`** (1 values) — `N`×3,411
- **`QryGroup35`** (1 values) — `N`×3,411
- **`QryGroup36`** (1 values) — `N`×3,411
- **`QryGroup37`** (1 values) — `N`×3,411
- **`QryGroup38`** (1 values) — `N`×3,411
- **`QryGroup39`** (1 values) — `N`×3,411
- **`QryGroup40`** (1 values) — `N`×3,411
- **`QryGroup41`** (1 values) — `N`×3,411
- **`QryGroup42`** (1 values) — `N`×3,411
- **`QryGroup43`** (1 values) — `N`×3,411
- **`QryGroup44`** (1 values) — `N`×3,411
- **`QryGroup45`** (1 values) — `N`×3,411
- **`QryGroup46`** (1 values) — `N`×3,411
- **`QryGroup47`** (1 values) — `N`×3,411
- **`QryGroup48`** (1 values) — `N`×3,411
- **`QryGroup49`** (1 values) — `N`×3,411
- **`QryGroup50`** (1 values) — `N`×3,411
- **`QryGroup51`** (1 values) — `N`×3,411
- **`QryGroup52`** (1 values) — `N`×3,411
- **`QryGroup53`** (1 values) — `N`×3,411
- **`QryGroup54`** (1 values) — `N`×3,411
- **`QryGroup55`** (1 values) — `N`×3,411
- **`QryGroup56`** (1 values) — `N`×3,411
- **`QryGroup57`** (1 values) — `N`×3,411
- **`QryGroup58`** (1 values) — `N`×3,411
- **`QryGroup59`** (1 values) — `N`×3,411
- **`QryGroup60`** (1 values) — `N`×3,411
- **`QryGroup61`** (1 values) — `N`×3,411
- **`QryGroup62`** (1 values) — `N`×3,411
- **`QryGroup63`** (1 values) — `N`×3,411
- **`QryGroup64`** (1 values) — `N`×3,411
- **`DscntObjct`** (1 values) — `-1`×3,411
- **`DscntRel`** (1 values) — `L`×3,411
- **`Priority`** (1 values) — `-1`×3,411
- **`CreditCard`** (1 values) — `-1`×3,411
- **`UserSign`** (5 values) — `1`×2,072, `38`×794, `40`×275, `39`×136, `47`×134
- **`LocMth`** (1 values) — `Y`×3,411
- **`validFor`** (2 values) — `Y`×3,387, `N`×24
- **`frozenFor`** (2 values) — `N`×3,387, `Y`×24
- **`sEmployed`** (1 values) — `N`×3,411
- **`DdgKey`** (1 values) — `-1`×3,411
- **`DdtKey`** (1 values) — `-1`×3,411
- **`FrozenComm`** (2 values) — `NULL`×3,410, `to be created in mart`×1
- **`chainStore`** (1 values) — `N`×3,411
- **`DiscInRet`** (1 values) — `N`×3,411
- **`State1`** (30 values) — `DL`×1,245, `HR`×704, `PB`×492, `UP`×307, `GJ`×120, `MH`×99, `RJ`×61, `NULL`×51, `KT`×45, `HP`×37, `UK`×34, `WB`×31, `JK`×23, `CH`×18, `TN`×17, `MP`×17, `AP`×16, `BH`×14, `TE`×14, `AS`×11, `GO`×10, `KR`×9, `AN`×5, `OD`×5, `CA`×4, `CT`×4, `AZ`×2, `AD`×2, `JH`×2, `MN`×2
- **`State2`** (30 values) — `DL`×1,239, `HR`×705, `PB`×490, `UP`×304, `GJ`×120, `MH`×99, `NULL`×61, `RJ`×59, `KT`×45, `HP`×37, `UK`×35, `WB`×32, `JK`×24, `CH`×19, `MP`×18, `TN`×17, `AP`×16, `BH`×14, `TE`×14, `AS`×11, `GO`×10, `KR`×9, `OD`×5, `CA`×4, `AN`×4, `CT`×4, `AZ`×2, `AD`×2, `JH`×2, `AUS`×1
- **`ObjType`** (1 values) — `2`×3,411
- **`DebPayAcct`** (30 values) — `2110004`×1,141, `1101001`×715, `2110003`×478, `2110005`×466, `1101008`×132, `2110001`×107, `1101005`×100, `1101006`×45, `1101015`×38, `1101007`×34, `1101012`×29, `1101004`×21, `2110006`×16, `1101009`×15, `2110002`×12, `1101011`×11, `1101010`×10, `1101013`×7, `1101002`×6, `2110008`×5, `1101014`×4, `1102001`×3, `2110007`×2, `2120002`×2, `1102008`×1, `2121002`×1, `2120001`×1, `1102003`×1, `1101003`×1, `2121001`×1
- **`Deleted`** (1 values) — `N`×3,411
- **`IBAN`** (2 values) — `NULL`×3,410, `STADD`×1
- **`BackOrder`** (1 values) — `Y`×3,411
- **`PartDelivr`** (1 values) — `Y`×3,411
- **`BlockDunn`** (1 values) — `N`×3,411
- **`BankCountr`** (8 values) — `IN`×3,341, `NULL`×62, `∅`×2, `AU`×2, `EG`×1, `QA`×1, `AE`×1, `ES`×1
- **`CollecAuth`** (1 values) — `N`×3,411
- **`SinglePaym`** (1 values) — `N`×3,411
- **`PaymBlock`** (1 values) — `N`×3,411
- **`HouseBank`** (2 values) — `-1`×3,084, `NULL`×327
- **`PyBlckDesc`** (1 values) — `-1`×3,411
- **`HousBnkCry`** (2 values) — `NULL`×3,093, `IN`×318
- **`SysMatchNo`** (1 values) — `-1`×3,411
- **`DeferrTax`** (1 values) — `N`×3,411
- **`WTLiable`** (3 values) — `N`×2,632, `Y`×552, `NULL`×227
- **`AccCritria`** (2 values) — `N`×3,408, `Y`×3
- **`WTCode`** (3 values) — `NULL`×3,353, `∅`×49, `TDS`×9
- **`Equ`** (1 values) — `N`×3,411
- **`TypWTReprt`** (1 values) — `C`×3,411
- **`IsDomestic`** (1 values) — `Y`×3,411
- **`IsResident`** (1 values) — `Y`×3,411
- **`AutoCalBCG`** (1 values) — `N`×3,411
- **`IntrntSite`** (2 values) — `NULL`×3,410, `9910112433`×1
- **`LangCode`** (2 values) — `8`×3,410, `33`×1
- **`UseShpdGd`** (1 values) — `N`×3,411
- **`InsurOp347`** (1 values) — `N`×3,411
- **`StreetNo`** (10 values) — `NULL`×3,402, `40 FEET ROAD`×1, `B 408 KHASRA NO 13/23`×1, `B-408 KHASRA NO. 13/23`×1, `54/5A STRAND ROAD`×1, `NEAR HANS CINEMA`×1, `JAI NIWAS TUBEWELL COLONY`×1, `OLD GRAIN MARKET`×1, `PASCHIM VIHAR`×1, `THEING ROAD PHILLAUR`×1
- **`MailStrNo`** (10 values) — `NULL`×3,402, `40 FEET ROAD`×1, `B 408 KHASRA NO 13/23`×1, `54/5A STRAND ROAD`×1, `NEAR HANS CINEMA`×1, `JAI NIWAS TUBEWELL COLONY`×1, `PASCHIM VIHAR`×1, `THEING ROAD PHILLAUR`×1, `B-408 KHASRA NO. 13/23`×1, `S NO 402/2B1`×1
- **`TaxRndRule`** (1 values) — `D`×3,411
- **`VendTID`** (2 values) — `NULL`×3,410, `4`×1
- **`ThreshOver`** (2 values) — `N`×2,875, `Y`×536
- **`SurOver`** (1 values) — `N`×3,411
- **`OpCode347`** (2 values) — `A`×2,235, `B`×1,176
- **`ResidenNum`** (1 values) — `1`×3,411
- **`Affiliate`** (1 values) — `N`×3,411
- **`MivzExpSts`** (1 values) — `B`×3,411
- **`HierchDdct`** (1 values) — `N`×3,411
- **`CertWHT`** (1 values) — `N`×3,411
- **`CertBKeep`** (1 values) — `N`×3,411
- **`WHShaamGrp`** (1 values) — `1`×3,411
- **`DatevFirst`** (1 values) — `Y`×3,411
- **`AutoPost`** (2 values) — `NULL`×2,530, `N`×881
- **`Series`** (6 values) — `87`×1,755, `85`×1,137, `88`×478, `86`×38, `2`×2, `1`×1
- **`TaxIdIdent`** (1 values) — `3`×3,411
- **`DiscRel`** (1 values) — `L`×3,411
- **`NoDiscount`** (2 values) — `N`×3,408, `Y`×3
- **`SCAdjust`** (1 values) — `N`×3,411
- **`GlblLocNum`** (2 values) — `NULL`×3,410, ```×1
- **`SenderID`** (2 values) — `NULL`×3,410, `O`×1
- **`RcpntID`** (3 values) — `NULL`×3,409, `V`×1, `OO`×1
- **`SefazCheck`** (1 values) — `N`×3,411
- **`TpCusPres`** (1 values) — `9`×3,411
- **`BlockComm`** (1 values) — `N`×3,411
- **`EdrsFromBP`** (1 values) — `Y`×3,411
- **`EdrsToBP`** (2 values) — `N`×3,410, `Y`×1
- **`EffecPrice`** (1 values) — `D`×3,411
- **`TxExMxVdTp`** (1 values) — `I`×3,411
- **`MerchantID`** (2 values) — `NULL`×3,409, `Address ID Addr`×2
- **`UseBilAddr`** (2 values) — `N`×2,266, `Y`×1,145
- **`NaturalPer`** (1 values) — `N`×3,411
- **`DPPStatus`** (1 values) — `N`×3,411
- **`EnERD4In`** (1 values) — `Y`×3,411
- **`EnERD4Out`** (1 values) — `Y`×3,411
- **`DflCustomr`** (1 values) — `N`×3,411
- **`FCERelevnt`** (1 values) — `N`×3,411
- **`FCEVldte`** (1 values) — `N`×3,411
- **`AggregDoc`** (1 values) — `N`×3,411
- **`EffcAllSrc`** (1 values) — `N`×3,411
- **`DefaultCur`** (2 values) — `NULL`×3,380, `INR`×31
- **`FCEPmnMean`** (1 values) — `N`×3,411
- **`NotRel4MI`** (1 values) — `N`×3,411
- **`U_AddressIdPrint`** (2 values) — `NULL`×3,410, `Y`×1
- **`U_BranchHomeBpl`** (5 values) — `NULL`×3,401, `1`×4, `2`×2, `3`×2, `4`×2
- **`U_UNE_BRCH`** (2 values) — `NULL`×3,410, `SREEBHUMI BRANCH`×1
- **`U_CATGCODE`** (2 values) — `NULL`×3,399, `103`×12
- **`U_MSME_Type`** (4 values) — `NULL`×3,132, `MICRO`×174, `SMALL`×77, `MEDIUM`×28
- **`U_MSME_BType`** (15 values) — `NULL`×3,130, `MANUFACTURING`×113, `TRADING`×74, `SERVICES`×67, `MANUFACTURER`×6, `SERVICE`×4, `TRADER`×4, `Manufacturing`×3, `SERVICE PROVIDER`×2, `MANUFATURING`×2, `Service`×2, `SERVICES(TRADING)`×1, `FMCG`×1, `SMALL`×1, `MICRO`×1
- **`U_TDS_RECOV`** (1 values) — `N`×3,411
