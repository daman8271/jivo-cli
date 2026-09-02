# `BTF1` — field profile

> Mined live from HANA. Recent window = last **120 days**. *Filled* means non-null **and** non-blank/non-zero — SAP stores `''` and `0` in fields nobody ever types in, so a NULL test alone calls every field 100% used.

| Book | Rows | Rows in window | Date column | Span |
|---|---:|---:|---|---|
| OIL | 21,093 | 3,552 | `RefDate` | 2024-08-01 → 2026-08-21 |
| MART | 2,963 | 302 | `RefDate` | 2024-12-31 → 2026-08-20 |
| BEV | 4,217 | 444 | `RefDate` | 2024-10-01 → 2026-08-22 |

## Fields

Sorted as SAP stores them. **`—`** means the column exists in that book and is empty in every single row: SAP offers it, JIVO never fills it. **`n/a`** means the column does not exist in that book at all — a different fact entirely, and one that makes a write fail rather than merely do nothing.

| Field | Type | OIL all | MART all | BEV all | OIL 120d | MART 120d | BEV 120d | Distinct | Reads as |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| `TransId` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 5 | |
| `Line_ID` | INTEGER | 85% | 73% | 79% | 90% | 72% | 78% | 525 | |
| `Account` | NVARCHAR(15) | 100% | 100% | 100% | 100% | 100% | 100% | 626 | |
| `Debit` | DECIMAL | 43% | 50% | 47% | 38% | 39% | 41% | 5,317 | |
| `Credit` | DECIMAL | 44% | 49% | 46% | 40% | 57% | 53% | 5,585 | |
| `SYSCred` | DECIMAL | 44% | 49% | 46% | 40% | 57% | 53% | 5,585 | |
| `SYSDeb` | DECIMAL | 43% | 50% | 47% | 38% | 39% | 41% | 5,317 | |
| `DueDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 534 | |
| `ShortName` | NVARCHAR(15) | 100% | 100% | 100% | 100% | 100% | 100% | 1,844 | |
| `LineMemo` | NVARCHAR(254) | 100% | 99% | 100% | 100% | 99% | 100% | 3,205 | |
| `Ref3Line` | NVARCHAR(200) | <1% | — | — | — | — | — | 2 | |
| `TransType` | NVARCHAR(20) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `RefDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 484 | |
| `Ref2` | NVARCHAR(200) | <1% | — | — | — | — | — | 5 | |
| `ProfitCode` | NVARCHAR(8) | 75% | 56% | 59% | 78% | 65% | 58% | 43 | |
| `TaxDate` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 516 | |
| `UserSign` | SMALLINT | 100% | 100% | 100% | 100% | 100% | 100% | 19 | |
| `BatchNum` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 3,223 | |
| `FinncPriod` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 23 | |
| `RelTransId` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `RelLineID` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `RelType` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `AdjTran` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `RevSource` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ObjType` | NVARCHAR(20) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `VatLine` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Closed` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DebCred` | NVARCHAR(1) | 99% | 100% | 100% | 98% | 99% | 99% | 2 | |
| `IsNet` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `DunWizBlck` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `TaxPostAcc` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ValidFrom` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 7 | |
| `OcrCode2` | NVARCHAR(8) | 76% | 58% | 60% | 81% | 63% | 59% | 30 | |
| `OcrCode3` | NVARCHAR(8) | 69% | 42% | 56% | 71% | 48% | 52% | 16 | |
| `OcrCode4` | NVARCHAR(8) | 50% | 17% | 30% | 55% | 19% | 12% | 24 | |
| `OcrCode5` | NVARCHAR(8) | 60% | 22% | 52% | 61% | 39% | 37% | 20 | |
| `CenVatCom` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `MatType` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ValidFrom2` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ValidFrom3` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ValidFrom4` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `ValidFrom5` | TIMESTAMP | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Location` | INTEGER | 19% | 9% | 24% | 11% | 8% | 19% | 5 | |
| `WTLiable` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `WTLine` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `PayBlock` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `Ordered` | NVARCHAR(1) | 100% | 100% | 100% | 100% | 100% | 100% | 1 | |
| `BPLId` | INTEGER | 100% | 100% | 100% | 100% | 100% | 100% | 7 | |
| `BPLName` | NVARCHAR(200) | 100% | 100% | 100% | 100% | 100% | 100% | 7 | |
| `VatRegNum` | NVARCHAR(32) | 100% | 100% | 100% | 100% | 100% | 100% | 5 | |
| `ExpUUID` | NVARCHAR(50) | — | <1% | — | — | — | — | 1 | |
| `U_OcrCode5` | NVARCHAR(10) | 11% | n/a | 11% | — | n/a | — | 7 | |

_**Reads as** is deliberately blank: fill it with what the field means in JIVO's terms, not SAP's. That column is the whole point of the note._

## Columns that do not exist in every book (1)

A field present in one book and absent in another. Sending it to the book that lacks it is an error, not a no-op.

| Column | Present in | Missing from |
|---|---|---|
| `U_OcrCode5` | OIL, BEV | **MART** |

## Value vocabularies (OIL)

Columns holding a small closed set of values. These are the drop-downs and flags an operator picks from, so the list *is* the rule.

- **`TransId`** (5 values) — `1`×21,042, `2`×37, `3`×8, `4`×4, `5`×2
- **`Ref3Line`** (3 values) — `NULL`×20,896, `∅`×195, `11`×2
- **`TransType`** (1 values) — `-1`×21,093
- **`Ref2`** (5 values) — `∅`×21,085, `CCAG/DN/122`×2, `041/25-26`×2, `CCAG/DN/164`×2, `TSPL/2526/RN61`×2
- **`UserSign`** (19 values) — `39`×10,210, `13`×3,160, `11`×1,850, `10`×1,020, `17`×898, `16`×712, `53`×708, `48`×660, `15`×622, `14`×315, `12`×293, `18`×282, `20`×232, `1`×102, `27`×10, `47`×6, `24`×6, `46`×5, `22`×2
- **`FinncPriod`** (23 values) — `41`×1,488, `17`×1,385, `43`×1,330, `18`×1,186, `19`×1,176, `42`×1,169, `14`×1,125, `25`×1,039, `16`×1,014, `21`×1,005, `45`×1,004, `22`×982, `20`×959, `24`×951, `23`×902, `44`×873, `15`×856, `8`×742, `12`×652, `11`×435, `10`×411, `9`×318, `7`×91
- **`RelTransId`** (1 values) — `-1`×21,093
- **`RelLineID`** (1 values) — `-1`×21,093
- **`RelType`** (1 values) — `N`×21,093
- **`AdjTran`** (1 values) — `N`×21,093
- **`RevSource`** (1 values) — `N`×21,093
- **`ObjType`** (1 values) — `30`×21,093
- **`VatLine`** (1 values) — `N`×21,093
- **`Closed`** (1 values) — `N`×21,093
- **`DebCred`** (3 values) — `D`×10,744, `C`×10,091, `NULL`×258
- **`IsNet`** (1 values) — `Y`×21,093
- **`DunWizBlck`** (1 values) — `N`×21,093
- **`TaxPostAcc`** (1 values) — `N`×21,093
- **`ValidFrom`** (7 values) — `1900-01-01 00:00:00.0000000`×17,034, `2024-09-01 00:00:00.0000000`×2,247, `2000-01-01 00:00:00.0000000`×1,718, `2024-10-01 00:00:00.0000000`×45, `2024-09-24 00:00:00.0000000`×35, `2025-12-01 00:00:00.0000000`×11, `2025-01-01 00:00:00.0000000`×3
- **`OcrCode2`** (30 values) — `∅`×4,874, `03-2025`×1,535, `10-2025`×1,412, `03-2026`×1,006, `06-2025`×999, `07-2025`×879, `05-2025`×845, `02-2026`×823, `06-2026`×814, `08-2025`×785, `04-2025`×741, `12-2025`×712, `05-2026`×692, `07-2026`×669, `11-2025`×660, `01-2026`×655, `04-2026`×564, `10-2024`×430, `01-2025`×421, `12-2024`×398, `02-2025`×370, `11-2024`×303, `09-2025`×198, `09-2024`×121, `NULL`×99, `08-2024`×57, `04-2024`×11, `05-2024`×10, `07-2024`×4, `08-2026`×4
- **`OcrCode3`** (17 values) — `Sales`×6,962, `∅`×6,461, `BackOff`×2,809, `Factory`×2,624, `Med MKT`×422, `FACT_COM`×421, `Del Bkhp`×332, `NPD2`×236, `Interest`×196, `NULL`×159, `Sales RE`×140, `OTE`×108, `NPD1`×83, `Del Mayp`×45, `Sal CF`×39, `NPD3`×37, `Transprt`×19
- **`OcrCode4`** (25 values) — `∅`×9,950, `GT`×2,572, `MT`×1,663, `ROI`×1,540, `Accounts`×1,301, `NULL`×632, `Admin`×504, `IT`×467, `CSD`×447, `DIGTAL M`×311, `Legal`×269, `HR_DEPT`×232, `MIS`×215, `CAL CNTR`×212, `E-COM`×193, `HORECA`×175, `BankChgs`×117, `POP`×99, `CIVIL`×85, `CC Limit`×44, `EXPORT`×28, `Trm Loan`×15, `PVT LOAN`×15, `VHCLLOAN`×4, `TAXATION`×3
- **`OcrCode5`** (21 values) — `∅`×8,322, `DL`×6,061, `HR`×2,363, `PB`×1,364, `MH`×559, `WB`×439, `KN`×343, `TE`×292, `GJ`×264, `UP`×260, `UK`×198, `GO`×176, `JK`×138, `AP`×116, `KR`×60, `NULL`×57, `HP`×34, `CD`×20, `TN`×19, `RJ`×6, `CH`×2
- **`CenVatCom`** (1 values) — `-1`×21,093
- **`MatType`** (1 values) — `-1`×21,093
- **`ValidFrom2`** (1 values) — `1900-01-01 00:00:00.0000000`×21,093
- **`ValidFrom3`** (1 values) — `1900-01-01 00:00:00.0000000`×21,093
- **`ValidFrom4`** (1 values) — `1900-01-01 00:00:00.0000000`×21,093
- **`ValidFrom5`** (1 values) — `1900-01-01 00:00:00.0000000`×21,093
- **`Location`** (6 values) — `NULL`×17,002, `1`×2,478, `2`×1,477, `3`×115, `5`×15, `4`×6
- **`WTLiable`** (1 values) — `N`×21,093
- **`WTLine`** (1 values) — `N`×21,093
- **`PayBlock`** (1 values) — `N`×21,093
- **`Ordered`** (1 values) — `N`×21,093
- **`BPLId`** (7 values) — `1`×15,340, `2`×5,075, `3`×369, `5`×137, `6`×109, `7`×36, `4`×27
- **`BPLName`** (7 values) — `DELHI`×15,340, `FACTORY`×5,075, `PUNJAB`×369, `HARYANA SALES`×137, `DELHI ISD`×109, `DELHI INFO`×36, `HIMACHAL PRADESH`×27
- **`VatRegNum`** (5 values) — `07AACCJ4223F1ZY`×15,376, `06AACCJ4223F1Z0`×5,212, `03AACCJ4223F1Z6`×369, `07AACCJ4223F2ZX`×109, `02AACCJ4223F1Z8`×27
- **`U_OcrCode5`** (8 values) — `NULL`×18,548, `PROMOTER`×1,187, `SO/SR`×784, `ASM`×410, `∅`×153, `RSM`×6, `CALLER`×4, `MIS`×1
