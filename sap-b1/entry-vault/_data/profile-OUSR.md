# `OUSR` — field profile

> Mined live from HANA. Recent window = last **3650 days**. *Filled* means non-null **and** non-blank/non-zero — SAP stores `''` and `0` in fields nobody ever types in, so a NULL test alone calls every field 100% used.

| Book | Rows | Rows in window | Date column | Span |
|---|---:|---:|---|---|
| OIL | 55 | 0 | `—` | — |
| MART | 53 | 0 | `—` | — |
| BEV | 52 | 0 | `—` | — |

## Fields

Sorted as SAP stores them. **`—`** means the column exists in that book and is empty in every single row: SAP offers it, JIVO never fills it. **`n/a`** means the column does not exist in that book at all — a different fact entirely, and one that makes a write fail rather than merely do nothing.

| Field | Type | OIL all | MART all | BEV all | OIL 3650d | MART 3650d | BEV 3650d | Distinct | Reads as |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| `USERID` | SMALLINT | 100% | 100% | 100% | · | · | · | 55 | |
| `PASSWORD` | NVARCHAR(254) | 100% | 100% | 100% | · | · | · | 53 | |
| `INTERNAL_K` | SMALLINT | 100% | 100% | 100% | · | · | · | 55 | |
| `USER_CODE` | NVARCHAR(25) | 100% | 100% | 100% | · | · | · | 55 | |
| `U_NAME` | NVARCHAR(155) | 100% | 100% | 100% | · | · | · | 54 | |
| `GROUPS` | SMALLINT | 9% | 2% | 6% | · | · | · | 2 | |
| `ALLOWENCES` | NCLOB | 100% | 100% | 100% | · | · | · | 0 | |
| `SUPERUSER` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 2 | |
| `DISCOUNT` | DECIMAL | 60% | 38% | 73% | · | · | · | 2 | |
| `Info1File` | NVARCHAR(4) | 4% | 2% | 2% | · | · | · | 1 | |
| `Info1Field` | SMALLINT | 4% | 2% | 2% | · | · | · | 2 | |
| `Info2File` | NVARCHAR(4) | 4% | 2% | — | · | · | · | 1 | |
| `Info2Field` | SMALLINT | 4% | 2% | — | · | · | · | 2 | |
| `Info3File` | NVARCHAR(4) | 4% | 2% | — | · | · | · | 1 | |
| `Info3Field` | SMALLINT | 4% | 2% | — | · | · | · | 2 | |
| `dType` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 1 | |
| `E_Mail` | NVARCHAR(100) | 80% | 75% | 81% | · | · | · | 40 | |
| `PortNum` | NVARCHAR(50) | 76% | 72% | 79% | · | · | · | 41 | |
| `OutOfOffic` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 1 | |
| `SendEMail` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 1 | |
| `SendSMS` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 1 | |
| `CashLimit` | NVARCHAR(1) | 2% | 100% | 100% | · | · | · | 1 | |
| `SendFax` | NVARCHAR(1) | — | 100% | 100% | · | · | · | 0 | |
| `Locked` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 1 | |
| `Department` | SMALLINT | — | 98% | 100% | · | · | · | 0 | |
| `Branch` | SMALLINT | — | 98% | 100% | · | · | · | 0 | |
| `UserPrefs` | BLOB | 85% | 77% | 87% | · | · | · | 0 | |
| `Language` | INTEGER | 4% | — | 2% | · | · | · | 1 | |
| `OpenCdt` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 1 | |
| `CdtPrvDays` | INTEGER | 100% | 100% | 100% | · | · | · | 1 | |
| `DsplyRates` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 1 | |
| `AuImpRates` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 1 | |
| `OpenDps` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 1 | |
| `RcrFlag` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 1 | |
| `CheckFiles` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 2 | |
| `OpenCredit` | NVARCHAR(1) | 89% | 91% | 88% | · | · | · | 1 | |
| `CreditDay1` | SMALLINT | 100% | 100% | 100% | · | · | · | 1 | |
| `CreditDay2` | SMALLINT | 100% | 100% | 100% | · | · | · | 1 | |
| `WallPaper` | NCLOB | 4% | — | — | · | · | · | 0 | |
| `ContactLog` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 2 | |
| `LastWarned` | TIMESTAMP | 82% | 74% | 83% | · | · | · | 17 | |
| `AlertPolFr` | SMALLINT | 100% | 100% | 100% | · | · | · | 1 | |
| `ScreenLock` | SMALLINT | 100% | 100% | 100% | · | · | · | 1 | |
| `ShowNewMsg` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 1 | |
| `GENDER` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 1 | |
| `EnbMenuFlt` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 1 | |
| `objType` | NVARCHAR(20) | 100% | 100% | 100% | · | · | · | 1 | |
| `userSign` | SMALLINT | 100% | 100% | 100% | · | · | · | 4 | |
| `createDate` | TIMESTAMP | 89% | 89% | 88% | · | · | · | 16 | |
| `userSign2` | SMALLINT | 91% | 100% | 92% | · | · | · | 10 | |
| `updateDate` | TIMESTAMP | 91% | 100% | 92% | · | · | · | 23 | |
| `OneLogPwd` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 2 | |
| `lastLogin` | TIMESTAMP | 89% | 92% | 90% | · | · | · | 17 | |
| `LastPwds` | NCLOB | 82% | 77% | 79% | · | · | · | 0 | |
| `LastPwdSet` | TIMESTAMP | 100% | 100% | 100% | · | · | · | 45 | |
| `FailedLog` | INTEGER | 11% | 19% | 15% | · | · | · | 5 | |
| `PwdNeverEx` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 2 | |
| `SalesDisc` | DECIMAL | 58% | 36% | 77% | · | · | · | 3 | |
| `PurchDisc` | DECIMAL | 55% | 40% | 77% | · | · | · | 3 | |
| `LstLogoutD` | TIMESTAMP | 89% | 81% | 88% | · | · | · | 29 | |
| `LstLoginT` | INTEGER | 89% | 92% | 90% | · | · | · | 49 | |
| `LstLogoutT` | INTEGER | 89% | 81% | 88% | · | · | · | 49 | |
| `LstPwdChT` | INTEGER | 100% | 100% | 100% | · | · | · | 52 | |
| `LstPwdChB` | NVARCHAR(25) | 93% | 92% | 92% | · | · | · | 29 | |
| `RclFlag` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 1 | |
| `MobileUser` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 2 | |
| `MobileIMEI` | NVARCHAR(64) | 9% | 4% | — | · | · | · | 4 | |
| `PrsWkCntEb` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 1 | |
| `STData` | NVARCHAR(40) | 95% | 94% | 96% | · | · | · | 52 | |
| `SupportUsr` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 1 | |
| `NoSTPwdNum` | SMALLINT | 2% | 8% | 2% | · | · | · | 2 | |
| `TPLId` | SMALLINT | 85% | 64% | 87% | · | · | · | 47 | |
| `ShowNewTsk` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 1 | |
| `IntgrtEb` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 1 | |
| `AllBrnchF` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 2 | |
| `EvtNotify` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 1 | |
| `IgnDtOwn` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 1 | |
| `EnterAsTab` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 1 | |
| `DotAsSep` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 1 | |
| `MouseOnly` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 1 | |
| `Color` | SMALLINT | 20% | 6% | 8% | · | · | · | 5 | |
| `SkinType` | NVARCHAR(254) | 85% | 92% | — | · | · | · | 1 | |
| `Font` | NVARCHAR(50) | 20% | 2% | 10% | · | · | · | 8 | |
| `FontSize` | INTEGER | 51% | 28% | 42% | · | · | · | 5 | |
| `NaturalPer` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 1 | |
| `DPPStatus` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 1 | |
| `AutoAsnBPL` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 2 | |
| `HandleEDoc` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 2 | |
| `ShowLicBal` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 1 | |
| `LicBaHDate` | TIMESTAMP | 89% | 89% | 88% | · | · | · | 19 | |
| `ShowFstMsg` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 1 | |
| `ShowMsgNum` | INTEGER | 100% | 100% | 100% | · | · | · | 1 | |
| `CleanChb` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 1 | |
| `CleanIbx` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 1 | |
| `CleanObx` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 1 | |
| `CleanSnt` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 1 | |
| `validFor` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 2 | |
| `frozenFor` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 1 | |
| `U_UTL_ST_StaAdmin` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 2 | |
| `U_UTL_ST_UWISE` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 2 | |
| `U_U_Role` | NVARCHAR(20) | 13% | — | — | · | · | · | 4 | |
| `U_DEPT` | NVARCHAR(20) | 69% | — | 65% | · | · | · | 5 | |

_**Reads as** is deliberately blank: fill it with what the field means in JIVO's terms, not SAP's. That column is the whole point of the note._

## Value vocabularies (OIL)

Columns holding a small closed set of values. These are the drop-downs and flags an operator picks from, so the list *is* the rule.

- **`GROUPS`** (2 values) — `0`×50, `99`×5
- **`SUPERUSER`** (2 values) — `N`×44, `Y`×11
- **`DISCOUNT`** (2 values) — `100.000000`×33, `0.000000`×22
- **`Info1File`** (2 values) — `NULL`×53, `DLN1`×2
- **`Info1Field`** (3 values) — `0`×45, `NULL`×8, `24`×2
- **`Info2File`** (2 values) — `NULL`×53, `DLN1`×2
- **`Info2Field`** (3 values) — `0`×45, `NULL`×8, `24`×2
- **`Info3File`** (2 values) — `NULL`×53, `DLN1`×2
- **`Info3Field`** (3 values) — `0`×45, `NULL`×8, `24`×2
- **`dType`** (1 values) — `S`×55
- **`OutOfOffic`** (1 values) — `N`×55
- **`SendEMail`** (1 values) — `N`×55
- **`SendSMS`** (1 values) — `N`×55
- **`CashLimit`** (2 values) — `NULL`×54, `N`×1
- **`Locked`** (1 values) — `N`×55
- **`Language`** (2 values) — `NULL`×53, `8`×2
- **`OpenCdt`** (1 values) — `N`×55
- **`CdtPrvDays`** (1 values) — `1`×55
- **`DsplyRates`** (1 values) — `N`×55
- **`AuImpRates`** (1 values) — `N`×55
- **`OpenDps`** (1 values) — `N`×55
- **`RcrFlag`** (1 values) — `N`×55
- **`CheckFiles`** (2 values) — `N`×54, `Y`×1
- **`OpenCredit`** (2 values) — `N`×49, `NULL`×6
- **`CreditDay1`** (1 values) — `1`×55
- **`CreditDay2`** (1 values) — `15`×55
- **`ContactLog`** (2 values) — `Y`×49, `N`×6
- **`LastWarned`** (18 values) — `2026-08-24 00:00:00.0000000`×25, `NULL`×10, `2026-08-17 00:00:00.0000000`×2, `2024-09-16 00:00:00.0000000`×2, `2026-08-01 00:00:00.0000000`×2, `2026-08-22 00:00:00.0000000`×2, `2026-01-20 00:00:00.0000000`×1, `2026-03-21 00:00:00.0000000`×1, `2026-07-20 00:00:00.0000000`×1, `2026-08-07 00:00:00.0000000`×1, `2026-08-21 00:00:00.0000000`×1, `2025-11-11 00:00:00.0000000`×1, `2025-10-17 00:00:00.0000000`×1, `2026-08-04 00:00:00.0000000`×1, `2025-07-01 00:00:00.0000000`×1, `2025-12-04 00:00:00.0000000`×1, `2026-07-18 00:00:00.0000000`×1, `2025-10-16 00:00:00.0000000`×1
- **`AlertPolFr`** (1 values) — `5`×55
- **`ScreenLock`** (1 values) — `30`×55
- **`ShowNewMsg`** (1 values) — `Y`×55
- **`GENDER`** (1 values) — `F`×55
- **`EnbMenuFlt`** (1 values) — `N`×55
- **`objType`** (1 values) — `12`×55
- **`userSign`** (4 values) — `1`×52, `40`×1, `47`×1, `38`×1
- **`createDate`** (17 values) — `2024-09-17 00:00:00.0000000`×31, `NULL`×6, `2024-12-05 00:00:00.0000000`×2, `2024-11-13 00:00:00.0000000`×2, `2024-09-07 00:00:00.0000000`×2, `2026-02-06 00:00:00.0000000`×1, `2024-11-29 00:00:00.0000000`×1, `2024-11-11 00:00:00.0000000`×1, `2025-01-28 00:00:00.0000000`×1, `2025-12-24 00:00:00.0000000`×1, `2025-10-13 00:00:00.0000000`×1, `2026-01-12 00:00:00.0000000`×1, `2025-04-18 00:00:00.0000000`×1, `2025-10-29 00:00:00.0000000`×1, `2025-11-20 00:00:00.0000000`×1, `2025-07-16 00:00:00.0000000`×1, `2024-09-12 00:00:00.0000000`×1
- **`userSign2`** (11 values) — `40`×29, `1`×13, `NULL`×5, `52`×1, `12`×1, `15`×1, `38`×1, `32`×1, `31`×1, `49`×1, `36`×1
- **`updateDate`** (24 values) — `2026-06-19 00:00:00.0000000`×24, `NULL`×5, `2026-07-24 00:00:00.0000000`×2, `2026-06-24 00:00:00.0000000`×2, `2026-08-05 00:00:00.0000000`×2, `2024-09-24 00:00:00.0000000`×2, `2026-07-06 00:00:00.0000000`×1, `2026-08-17 00:00:00.0000000`×1, `2026-08-24 00:00:00.0000000`×1, `2026-08-14 00:00:00.0000000`×1, `2024-09-12 00:00:00.0000000`×1, `2025-12-15 00:00:00.0000000`×1, `2026-07-14 00:00:00.0000000`×1, `2026-04-21 00:00:00.0000000`×1, `2026-08-18 00:00:00.0000000`×1, `2026-04-09 00:00:00.0000000`×1, `2026-08-07 00:00:00.0000000`×1, `2024-11-05 00:00:00.0000000`×1, `2026-07-28 00:00:00.0000000`×1, `2026-06-27 00:00:00.0000000`×1, `2026-07-04 00:00:00.0000000`×1, `2026-06-22 00:00:00.0000000`×1, `2026-07-10 00:00:00.0000000`×1, `2025-08-25 00:00:00.0000000`×1
- **`OneLogPwd`** (2 values) — `N`×51, `Y`×4
- **`lastLogin`** (18 values) — `2026-08-24 00:00:00.0000000`×29, `NULL`×6, `2026-08-22 00:00:00.0000000`×3, `2026-08-17 00:00:00.0000000`×2, `2024-09-16 00:00:00.0000000`×2, `2026-08-07 00:00:00.0000000`×1, `2026-07-20 00:00:00.0000000`×1, `2026-07-27 00:00:00.0000000`×1, `2026-01-20 00:00:00.0000000`×1, `2026-02-24 00:00:00.0000000`×1, `2026-07-18 00:00:00.0000000`×1, `2026-08-21 00:00:00.0000000`×1, `2025-12-15 00:00:00.0000000`×1, `2026-08-04 00:00:00.0000000`×1, `2026-05-21 00:00:00.0000000`×1, `2026-08-01 00:00:00.0000000`×1, `2026-08-08 00:00:00.0000000`×1, `2026-07-28 00:00:00.0000000`×1
- **`FailedLog`** (5 values) — `0`×49, `1`×2, `3`×2, `2`×1, `5`×1
- **`PwdNeverEx`** (2 values) — `Y`×43, `N`×12
- **`SalesDisc`** (3 values) — `100.000000`×29, `0.000000`×23, `0.500000`×3
- **`PurchDisc`** (3 values) — `100.000000`×29, `0.000000`×25, `1.000000`×1
- **`LstLogoutD`** (30 values) — `2026-08-24 00:00:00.0000000`×13, `NULL`×6, `2026-08-19 00:00:00.0000000`×3, `2026-08-18 00:00:00.0000000`×3, `2026-08-22 00:00:00.0000000`×2, `2026-08-11 00:00:00.0000000`×2, `2026-07-31 00:00:00.0000000`×2, `2026-08-21 00:00:00.0000000`×2, `2024-09-16 00:00:00.0000000`×1, `2026-05-23 00:00:00.0000000`×1, `2026-08-08 00:00:00.0000000`×1, `2026-08-06 00:00:00.0000000`×1, `2026-07-08 00:00:00.0000000`×1, `2025-10-16 00:00:00.0000000`×1, `2026-08-13 00:00:00.0000000`×1, `2025-05-23 00:00:00.0000000`×1, `2025-12-14 00:00:00.0000000`×1, `2025-11-17 00:00:00.0000000`×1, `2026-08-20 00:00:00.0000000`×1, `2026-06-03 00:00:00.0000000`×1, `2025-10-30 00:00:00.0000000`×1, `2026-01-20 00:00:00.0000000`×1, `2026-03-21 00:00:00.0000000`×1, `2024-09-14 00:00:00.0000000`×1, `2026-08-14 00:00:00.0000000`×1, `2026-06-05 00:00:00.0000000`×1, `2026-08-12 00:00:00.0000000`×1, `2026-08-17 00:00:00.0000000`×1, `2026-08-01 00:00:00.0000000`×1, `2025-10-17 00:00:00.0000000`×1
- **`LstPwdChB`** (29 values) — `manager`×14, `USER31`×7, `USER29`×5, `∅`×4, `USER15`×1, `USER04`×1, `USER18`×1, `USER13`×1, `USER32`×1, `admin`×1, `USER35`×1, `USER17`×1, `USER06`×1, `USER08`×1, `USER24`×1, `USER27`×1, `USER25`×1, `USER07`×1, `USER22`×1, `USER19`×1, `USER43`×1, `USER21`×1, `USER38`×1, `USER23`×1, `USER37`×1, `USER10`×1, `USER11`×1, `USER09`×1, `USER39`×1
- **`RclFlag`** (1 values) — `N`×55
- **`MobileUser`** (2 values) — `N`×52, `Y`×3
- **`PrsWkCntEb`** (1 values) — `Y`×55
- **`SupportUsr`** (1 values) — `N`×55
- **`NoSTPwdNum`** (2 values) — `0`×54, `1`×1
- **`ShowNewTsk`** (1 values) — `N`×55
- **`IntgrtEb`** (1 values) — `N`×55
- **`AllBrnchF`** (2 values) — `Y`×51, `N`×4
- **`EvtNotify`** (1 values) — `Y`×55
- **`IgnDtOwn`** (1 values) — `N`×55
- **`EnterAsTab`** (1 values) — `N`×55
- **`DotAsSep`** (1 values) — `N`×55
- **`MouseOnly`** (1 values) — `N`×55
- **`Color`** (6 values) — `NULL`×44, `1`×4, `9`×3, `2`×2, `3`×1, `8`×1
- **`SkinType`** (2 values) — `Belize Deep`×47, `NULL`×8
- **`Font`** (9 values) — `NULL`×44, `Arial`×3, `Cambria`×2, `Ebrima`×1, `AvantGarde`×1, `Nirmala UI`×1, `Yu Gothic UI Semibold`×1, `Times New Roman`×1, `Calibri`×1
- **`FontSize`** (6 values) — `NULL`×27, `12`×12, `11`×9, `14`×3, `10`×2, `9`×2
- **`NaturalPer`** (1 values) — `N`×55
- **`DPPStatus`** (1 values) — `N`×55
- **`AutoAsnBPL`** (2 values) — `Y`×34, `N`×21
- **`HandleEDoc`** (2 values) — `Y`×53, `N`×2
- **`ShowLicBal`** (1 values) — `Y`×55
- **`LicBaHDate`** (20 values) — `2024-09-17 00:00:00.0000000`×28, `NULL`×6, `2024-09-07 00:00:00.0000000`×2, `2024-11-13 00:00:00.0000000`×2, `2024-12-05 00:00:00.0000000`×2, `2025-11-20 00:00:00.0000000`×1, `2025-04-18 00:00:00.0000000`×1, `2024-10-15 00:00:00.0000000`×1, `2024-11-29 00:00:00.0000000`×1, `2026-02-06 00:00:00.0000000`×1, `2024-10-05 00:00:00.0000000`×1, `2024-10-09 00:00:00.0000000`×1, `2024-11-11 00:00:00.0000000`×1, `2025-01-28 00:00:00.0000000`×1, `2024-09-12 00:00:00.0000000`×1, `2025-07-16 00:00:00.0000000`×1, `2025-10-29 00:00:00.0000000`×1, `2026-01-12 00:00:00.0000000`×1, `2025-10-13 00:00:00.0000000`×1, `2025-12-24 00:00:00.0000000`×1
- **`ShowFstMsg`** (1 values) — `N`×55
- **`ShowMsgNum`** (1 values) — `100`×55
- **`CleanChb`** (1 values) — `N`×55
- **`CleanIbx`** (1 values) — `N`×55
- **`CleanObx`** (1 values) — `N`×55
- **`CleanSnt`** (1 values) — `N`×55
- **`validFor`** (2 values) — `Y`×45, `N`×10
- **`frozenFor`** (1 values) — `N`×55
- **`U_UTL_ST_StaAdmin`** (2 values) — `N`×50, `Y`×5
- **`U_UTL_ST_UWISE`** (2 values) — `N`×50, `Y`×5
- **`U_U_Role`** (5 values) — `NULL`×48, `GENERAL`×4, `TRACKER`×1, `SUPPORT`×1, `ADMIN`×1
- **`U_DEPT`** (6 values) — `NULL`×17, `ACCOUNTS`×12, `FACTORY`×11, `BILLING`×10, `SAP`×4, `IMPORT/EXPORT`×1
