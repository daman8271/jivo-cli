# `ITR1` — field profile

> Mined live from HANA. Recent window = last **120 days**. *Filled* means non-null **and** non-blank/non-zero — SAP stores `''` and `0` in fields nobody ever types in, so a NULL test alone calls every field 100% used.

| Book | Rows | Rows in window | Date column | Span |
|---|---:|---:|---|---|
| OIL | 123,136 | 0 | `—` | — |
| MART | 55,651 | 0 | `—` | — |
| BEV | 21,319 | 0 | `—` | — |

## Fields

Sorted as SAP stores them. **`—`** means the column exists in that book and is empty in every single row: SAP offers it, JIVO never fills it. **`n/a`** means the column does not exist in that book at all — a different fact entirely, and one that makes a write fail rather than merely do nothing.

| Field | Type | OIL all | MART all | BEV all | OIL 120d | MART 120d | BEV 120d | Distinct | Reads as |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| `ReconNum` | INTEGER | 100% | 100% | 100% | · | · | · | 30,085 | |
| `LineSeq` | INTEGER | 76% | 76% | 70% | · | · | · | 1,660 | |
| `ShortName` | NVARCHAR(15) | 100% | 100% | 100% | · | · | · | 1,733 | |
| `TransId` | INTEGER | 100% | 100% | 100% | · | · | · | 85,473 | |
| `TransRowId` | INTEGER | 48% | 29% | 43% | · | · | · | 146 | |
| `SrcObjTyp` | NVARCHAR(20) | 100% | 100% | 100% | · | · | · | 17 | |
| `SrcObjAbs` | INTEGER | 100% | 100% | 100% | · | · | · | 46,523 | |
| `ReconSum` | DECIMAL | 100% | 100% | 100% | · | · | · | 66,655 | |
| `ReconSumFC` | DECIMAL | <1% | <1% | — | · | · | · | 131 | |
| `ReconSumSC` | DECIMAL | 100% | 100% | 100% | · | · | · | 66,655 | |
| `FrgnCurr` | NVARCHAR(3) | <1% | <1% | — | · | · | · | 3 | |
| `SumMthCurr` | DECIMAL | 100% | 100% | 100% | · | · | · | 66,655 | |
| `IsCredit` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 2 | |
| `Account` | NVARCHAR(15) | 100% | 100% | 100% | · | · | · | 52 | |
| `ExpSum` | DECIMAL | <1% | — | <1% | · | · | · | 59 | |
| `ExpSumSC` | DECIMAL | <1% | — | <1% | · | · | · | 59 | |
| `InstID` | INTEGER | 57% | 85% | 71% | · | · | · | 3 | |
| `IntrsStat` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 1 | |

_**Reads as** is deliberately blank: fill it with what the field means in JIVO's terms, not SAP's. That column is the whole point of the note._

## Value vocabularies (OIL)

Columns holding a small closed set of values. These are the drop-downs and flags an operator picks from, so the list *is* the rule.

- **`SrcObjTyp`** (17 values) — `13`×25,801, `60`×21,173, `18`×20,922, `24`×11,725, `46`×11,309, `59`×8,291, `20`×7,077, `30`×6,433, `14`×5,217, `202`×2,363, `19`×1,425, `15`×729, `-3`×436, `21`×117, `16`×68, `321`×48, `69`×2
- **`FrgnCurr`** (4 values) — `NULL`×122,880, `USD`×168, `EUR`×87, `AUD`×1
- **`IsCredit`** (2 values) — `D`×68,724, `C`×54,412
- **`InstID`** (3 values) — `0`×53,337, `1`×46,760, `-99`×23,039
- **`IntrsStat`** (1 values) — `U`×123,136
