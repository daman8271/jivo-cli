# `ATC1` — field profile

> Mined live from HANA. Recent window = last **120 days**. *Filled* means non-null **and** non-blank/non-zero — SAP stores `''` and `0` in fields nobody ever types in, so a NULL test alone calls every field 100% used.

| Book | Rows | Rows in window | Date column | Span |
|---|---:|---:|---|---|
| OIL | 132,783 | 0 | `—` | — |
| MART | 39,193 | 0 | `—` | — |
| BEV | 38,703 | 0 | `—` | — |

## Fields

Sorted as SAP stores them. **`—`** means the column exists in that book and is empty in every single row: SAP offers it, JIVO never fills it. **`n/a`** means the column does not exist in that book at all — a different fact entirely, and one that makes a write fail rather than merely do nothing.

| Field | Type | OIL all | MART all | BEV all | OIL 120d | MART 120d | BEV 120d | Distinct | Reads as |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| `AbsEntry` | INTEGER | 100% | 100% | 100% | · | · | · | 78,342 | |
| `Line` | INTEGER | 100% | 100% | 100% | · | · | · | 34 | |
| `srcPath` | NCLOB | 100% | 100% | 100% | · | · | · | 0 | |
| `trgtPath` | NCLOB | 100% | 100% | 100% | · | · | · | 0 | |
| `FileName` | NVARCHAR(254) | 100% | 100% | 100% | · | · | · | 66,739 | |
| `FileExt` | NVARCHAR(8) | 100% | 100% | 100% | · | · | · | 26 | |
| `Date` | TIMESTAMP | 100% | 100% | 100% | · | · | · | 656 | |
| `UsrID` | INTEGER | 100% | 100% | 100% | · | · | · | 37 | |
| `Copied` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 1 | |
| `Override` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 2 | |
| `FreeText` | NVARCHAR(100) | <1% | <1% | — | · | · | · | 28 | |
| `CopyToTrgt` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 2 | |
| `CopyToProd` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 2 | |
| `EDocSign` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 1 | |
| `SendInMail` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 1 | |
| `FileSize` | INTEGER | 26% | 33% | 23% | · | · | · | 2,608 | |
| `CopyFile` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 1 | |
| `FileSuffix` | NVARCHAR(1) | 100% | 100% | 100% | · | · | · | 1 | |
| `U_CHK` | INTEGER | 60% | n/a | 13% | · | n/a | · | 1,743 | |
| `U_CHK2` | NVARCHAR(10) | 62% | n/a | 77% | · | n/a | · | 1 | |

_**Reads as** is deliberately blank: fill it with what the field means in JIVO's terms, not SAP's. That column is the whole point of the note._

## Columns that do not exist in every book (2)

A field present in one book and absent in another. Sending it to the book that lacks it is an error, not a no-op.

| Column | Present in | Missing from |
|---|---|---|
| `U_CHK` | OIL, BEV | **MART** |
| `U_CHK2` | OIL, BEV | **MART** |

## Value vocabularies (OIL)

Columns holding a small closed set of values. These are the drop-downs and flags an operator picks from, so the list *is* the rule.

- **`FileExt`** (26 values) — `pdf`×114,869, `jpeg`×9,216, `jpg`×4,520, `xlsx`×2,902, `png`×735, `PDF`×367, `docx`×59, `zip`×25, `xls`×25, `jfif`×12, `∅`×10, `JPG`×9, `txt`×7, `html`×4, `htm`×3, `eml`×3, `csv`×3, `doc`×2, `bmp`×2, `DOCX`×2, `mhtml`×2, `JPEG`×2, `XLSX`×1, `Pdf`×1, `rar`×1, `heic`×1
- **`Copied`** (1 values) — `Y`×132,783
- **`Override`** (2 values) — `Y`×114,355, `N`×18,428
- **`FreeText`** (29 values) — `NULL`×132,702, `OK`×31, `107`×3, `212`×3, `169`×3, `140`×3, `1032`×3, `118`×3, `1057`×3, `1204`×3, `999`×3, `91`×2, `6358`×2, `400`×2, `ok`×2, `+..050`×2, `97`×1, `593`×1, `388`×1, `837`×1, `850`×1, `415`×1, `119`×1, `42`×1, `1289`×1, `104`×1, `1390`×1, `49`×1, `532`×1
- **`CopyToTrgt`** (2 values) — `Y`×115,320, `N`×17,463
- **`CopyToProd`** (2 values) — `N`×132,236, `Y`×547
- **`EDocSign`** (1 values) — `N`×132,783
- **`SendInMail`** (1 values) — `N`×132,783
- **`CopyFile`** (1 values) — `N`×132,783
- **`FileSuffix`** (1 values) — `N`×132,783
- **`U_CHK2`** (2 values) — `OK`×82,516, `NULL`×50,267
