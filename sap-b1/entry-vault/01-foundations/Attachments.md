---
type: foundation
sap_tables: [OATC, ATC1, ODRF, OPCH, OPDN, ORPC, OINV]
objtype: null   # no single document type — this is the last step of every entry
companies: [OIL, MART, BEV]
mined: 2026-08-24
confidence: high
---

# Attachments — getting the paper onto the document

> The last step of every purchase entry, and the one that stops the entry dead. A draft
> with no scan gets rejected by the approver; a draft with the **wrong kind** of scan
> cannot be saved at all, and SAP's error message does not say why. Two of today's
> twelve drafts were believed to be un-addable for exactly that reason — see the
> correction immediately below: they are not.

---

> [!danger] CORRECTION, verified 2026-08-24 after this note was written
> **The per-line 1 MB rule (`1120026`) is COMMENTED OUT in the live procedure** and does not
> fire. Read the raw text: the `IF EXISTS … 'Attachment Size Should be Less Than 1 MB' … END
> IF;` block is wrapped in `/*` … `*/`. Only two attachment guards are live on an Oil draft:
>
> | Code | Rule | Status |
> |---|---|---|
> | `1120025` | an `ATC1` line has `U_CHK2 IS NULL` | **LIVE** |
> | `1120026` | `U_CHK > 1024` or `U_CHK IS NULL` (1 MB per line) | **COMMENTED OUT — does not fire** |
> | `1120027` | `SUM(U_CHK) > 10240` (10 MB per document) | **LIVE** |
>
> **Consequence: no draft made today is un-addable.** Checked all 19 CLI drafts
> (`DocEntry` ≥ 55120) against the live rules — `U_CHK2` is set on every line of every one
> (0 nulls), and the largest total is 1,537 KB against a 10,240 KB cap. Drafts **55167**
> (max line 1,402 KB) and **55168** (1,032 KB) are **fine**: they would only fail under the
> disabled rule.
>
> Everything else in this note stands — the `U_CHK2` requirement, the per-book differences,
> the `Expect: 100-continue` cause of the `400`, and the row-cloning finding were all
> verified independently. Treat the per-line size statements below as describing a rule that
> is *present but disabled*: still worth compressing scans (the 10 MB total is real), but not
> a blocker.
>
> *Lesson for anyone mining stored procedures: `/*` and `*/` are easy to miss in a
> single-line `SUBSTRING` dump, and a disabled guard reads exactly like a live one.*

---

## The short version

1. Every file lives in **`ATC1`**, grouped under one id in **`OATC`**. The document
   points at that id through one field: `AtcEntry` (API name `AttachmentEntry` →
   [[Field-Name-Rosetta]]).
2. **One document = one attachment row of its own.** Never point two documents at the
   same row. Measured: 74,795 of Oil's 75,522 referenced rows belong to exactly one
   document, and when a draft is Added SAP **clones** the row rather than sharing it
   (14,238 of 14,267 posted-A/P-to-draft pairs carry two different `AtcEntry` values,
   **zero** share one).
3. JIVO added its own rules on top of SAP, in `SBO_SP_TransactionNotification`. On a
   **draft** (any type, Oil): every file needs `U_CHK2` filled ("OK") **and** `U_CHK`
   filled and **≤ 1024**, total ≤ 10,240. Break any of the three and the save is refused.
   **(C-0026)**
4. **`U_CHK` / `U_CHK2` exist only on `ATC1`, and only in Oil and Beverages.**
   They do **not** exist in Mart, and they do **not** exist on `PCH1` or `DRF1` —
   they are attachment-line fields, not document-line fields.
5. The "1 MB limit" is a rule about **the number you type**, not about the file. Oil
   stores files up to 36 MB happily. What the guard reads is `U_CHK`.

## What actually holds the file

| Piece | Table / field | What it is |
|---|---|---|
| The id | `OATC.AbsEntry` | **The whole table.** `OATC` has exactly **one column** in all three books — verified against `SYS.TABLE_COLUMNS`. It exists only to hand out numbers |
| The files | `ATC1` | One row per file. `AbsEntry` + `Line`. Up to **34** lines seen on one row |
| The link | `<document>.AtcEntry` | One integer on the document header. Set it, and the SAP client shows the Attachments tab |

Row counts, all history: `OATC` **78,342** Oil · 32,118 Mart · 19,965 Bev.
`ATC1` **132,783** Oil · 39,193 Mart · 38,703 Bev. Earliest file 2024-10-04 (Oil),
i.e. attachments predate the 2025-04-01 cutover → [[Opening-Balance-and-Cutover]].

Files per row (Oil): 45,252 rows hold one file, 24,675 hold two, 5,379 hold three,
the rest more.

## `ATC1` — every field, and who fills it

Fill rates all-history, from `_data/profile-ATC1.md` and the queries at the foot of this
note. **Filled = non-null, non-blank, non-zero.**

| Field | Type | OIL | MART | BEV | Distinct | Reads as |
|---|---|---:|---:|---:|---:|---|
| `AbsEntry` | INTEGER | 100% | 100% | 100% | 78,342 | The number the document points at |
| `Line` | INTEGER | 100% | 100% | 100% | 34 | File 1, 2, 3… on the same row |
| `srcPath` | NCLOB | 100% | 100% | 100% | — | Where the file came **from**. Human rows: `C:\Users\USER<nn>\Desktop`. API rows: `/tmp/sap_b1_b1service0/ServiceLayer/Attachments2/` |
| `trgtPath` | NCLOB | 100% | 100% | 100% | — | The Windows share it was copied **to** (one value per book) → `sap-b1/attachments/MOUNT-RUNBOOK.md` |
| `FileName` | NVARCHAR(254) | 100% | 100% | 100% | 66,739 | Name **without** the extension. 34,330 name+ext combinations are reused — see Traps |
| `FileExt` | NVARCHAR(8) | 100% | 100% | 100% | 26 | `pdf` 87% of Oil. Case is not normalised (`pdf`, `PDF`, `Pdf` all exist) |
| `Date` | TIMESTAMP | 100% | 100% | 100% | 656 | When it was attached, not the bill date |
| `UsrID` | INTEGER | 100% | 100% | 100% | 37 | Who attached it (`OUSR.USERID`) |
| `Copied` | NVARCHAR(1) | 100% | 100% | 100% | 1 | Always `Y`. Carries no information |
| `Override` | NVARCHAR(1) | 100% | 100% | 100% | 2 | `Y` on 114,355 / `N` on 18,428 — overwrite a same-named file on the share. **API rows get `N`** |
| `FreeText` | NVARCHAR(100) | <1% | <1% | — | 28 | Nobody uses it. The 28 values are mostly `OK` and bare numbers — people typing the tick or the size into the wrong column |
| `CopyToTrgt` | NVARCHAR(1) | 100% | 100% | 100% | 2 | `Y` 115,320 / `N` 17,463 |
| `CopyToProd` | NVARCHAR(1) | 100% | 100% | 100% | 2 | `N` almost always. **`Y` is the fingerprint of an API upload** (see below) |
| `EDocSign` | NVARCHAR(1) | 100% | 100% | 100% | 1 | Always `N` |
| `SendInMail` | NVARCHAR(1) | 100% | 100% | 100% | 1 | Always `N` |
| `FileSize` | INTEGER | 26% | 33% | 23% | 2,608 | **The real size in KB**, written by SAP. Empty on everything before 2025; 77% filled in 2026 |
| `CopyFile` | NVARCHAR(1) | 100% | 100% | 100% | 1 | Always `N` |
| `FileSuffix` | NVARCHAR(1) | 100% | 100% | 100% | 1 | Always `N` |
| **`U_CHK`** | INTEGER | **60%** | *absent* | **13%** | 1,743 | JIVO UDF. "Size in KB" **as declared by the operator**. The guard reads this |
| **`U_CHK2`** | NVARCHAR(10) | **62%** | *absent* | **77%** | 1 | JIVO UDF. The Approve tick. Only ever `OK` |

### The dash trap in the profile corpus

`_data/profile-ATC1.md` shows a **dash** for Mart's `U_CHK` / `U_CHK2`, which reads as
"the field exists and Mart never uses it". It is worse than that: **the columns do not
exist in Mart at all.** The profiler takes its column list from the first book with rows
(Oil) and reports 0 for any book where the lookup misses. Confirmed:

```
SELECT SCHEMA_NAME, TABLE_NAME, COLUMN_NAME FROM SYS.TABLE_COLUMNS
WHERE COLUMN_NAME LIKE 'U_CHK%'
-- → ATC1 in JIVO_OIL_HANADB and JIVO_BEVERAGES_HANADB only. Two tables, four rows.
```

That is why a Mart stamp comes back **`[SAP -1000] Property 'U_CHK' of 'Attachments2_Line'
is invalid`** — measured twice today (`queries/manager/sap-writes.jsonl`, AE 56509 and
56511) — and why the Mart pointer PATCH then succeeded (204) with no stamp at all.

**A dash in any profile in `_data/` may mean "column absent in that book".** Check
`SYS.TABLE_COLUMNS` before writing "SAP offers it, JIVO never uses it".

## The guard, decoded

Not documentation — the procedure text itself, read out of `SYS.PROCEDURES`. On a draft,
Oil enforces:

```sql
-- Oil, SBO_SP_TRANSACTIONNOTIFICATION, verbatim
IF EXISTS(SELECT * FROM ATC1 A INNER JOIN ODRF B on A."AbsEntry"=B."AtcEntry"
          Where B."DocEntry"=:list_of_cols_val_tab_del and B."CANCELED"='N'
          And A."U_CHK2" is NULL )
   THEN Select 1120025, 'Select "OK" in Approve Column After Adding Attachment ' ...
IF EXISTS(... And ("U_CHK">1024 or "U_CHK" is null))
   THEN Select 1120026, 'Attachment Size Should be Less Than 1 MB' ...
IF EXISTS(... Having Sum(A."U_CHK")>10240 )
   THEN Select 1120027, 'Attachment Size Should be Less Than 10 MB for compelete Entry' ...
```

Three separate refusals, and the `ODRF` block carries **no `ObjType` filter** — it applies
to every draft of every type.

| Rule | Oil draft (`ODRF`) | Bev draft (`ODRF`) | Mart |
|---|---|---|---|
| `U_CHK2` must be non-null | yes — **1120025** | yes — 1120025 | **no rule; no column** |
| `U_CHK` must be non-null | **yes** — 1120026 fires on `is null` too | **no** — null passes | no |
| `U_CHK` ≤ 1024 per file | yes — 1120026 | yes — 1120026 | no |
| Total `SUM(U_CHK)` | ≤ **10,240** | ≤ **5,120** | no |

The guard only checks `is NULL`, so any non-blank value satisfies the tick. `OK` is the
only value that has ever been used — 82,516 times in Oil.

### Which document types the guard covers, per book

Measured by reading each book's procedure and counting the `ATC1`↔table joins.

| Table | Document | OIL | MART | BEV |
|---|---|---|---|---|
| `ODRF` | any [[Document-Drafts]] | **guarded** | — | **guarded** |
| `OPCH` | [[AP-Invoice]] | **guarded** (block appears twice) | — | **guarded** |
| `OPDN` | [[GRPO]] | **guarded** | — | **guarded** |
| `ORIN` | [[AR-Credit-Memo]] | **guarded** | — | **guarded** |
| `ODLN` | [[Delivery]] | **guarded** | — | **guarded** |
| `ORDN` | [[AR-Return]] | **guarded** | — | **guarded** |
| `OINV` | [[AR-Invoice]] | not guarded | — | **guarded** (block appears twice) |
| `ORPC` | [[AP-Credit-Memo]] | not guarded | — | **guarded** |
| `OPOR` | [[Purchase-Order]] | not guarded | — | **guarded** |
| `ORDR` | [[Sales-Order]] | not guarded | — | **guarded** (a duplicate block sits commented out) |

And the books agree with their own procedures — 2026 attachment lines on live documents:

| Book · table | Lines | No tick | Over 1 MB |
|---|---:|---:|---:|
| Oil `OPCH` (guarded) | 9,541 | **0** | **0** |
| Oil `OPDN` (guarded) | 3,316 | 13 | **0** |
| Oil `ORPC` (**not** guarded) | 1,237 | 1 | **127** |
| Oil `OINV` (**not** guarded) | 2,493 | **336** | **150** |
| Bev `OPCH` (guarded) | 2,991 | 0 | 0 |
| Bev `OPDN` (guarded) | 1,803 | 0 | 0 |

Zero exceptions in 9,541 lines on guarded Oil A/P invoices, and 150 exceptions on the
unguarded sales invoices right beside them. **The guard blocks the Add.** A draft that
breaks it is not "untidy" — it is a document nobody can post.

In 2025 the same query returns 138 over-1MB lines and 4,138 missing ticks on Oil `OPCH`,
and 2024 has no ticks at all: the rule was switched on during 2025.

## Is there a size ceiling? Yes, and it is not the one it looks like

| Question | Answer | How |
|---|---|---|
| Biggest file that exists | **37,103 KB (≈36 MB)** in Oil; 24,614 KB Mart; 35,877 KB Bev | `MAX("FileSize")` — measured |
| Files over 10 MB | 97 Oil · 46 Mart · 56 Bev | measured |
| SAP / share ceiling | **Unknown.** Nothing in the books suggests one below 36 MB | not established |
| The ceiling that bites | **1,024 in `U_CHK`**, per file, plus a 10,240 total on an Oil draft | read out of the procedure |
| Was the 2026-08-24 `400` a size limit? | **No** — see below | measured |

So the honest statement: **the enforced limit is a JIVO business rule on a typed number,
and the platform limit is unmeasured.** The two get confused constantly because the
message says "1 MB".

### What the office actually types

Of 24,700 Oil lines in 2026 with both numbers present, 4,042 sit on a file that is
genuinely bigger than 1 MB — and **3,826 of those carry a `U_CHK` of 1024 or less**.
Only 216 declare the real size, and those documents cannot be added.

The most common values typed against an over-1 MB file: **999** (1,344 times), 990 (577),
780 (248), 105 (237), 1024 (217).

That is a measured fact about the books, not a recommendation. `U_CHK` equals `FileSize`
exactly on 21,750 of the 26,542 Oil lines where both are set (82%), so most of the time
it *is* the size — right up to the point where the truth would fail the guard.

**Consequence for anything automated:** a tool that sets `U_CHK = FileSize` honestly
(which is what `attach_all.py` does today) produces an un-addable draft for every scan
over 1 MB. Compress the scan under 1 MB and the honest number passes. Whether typing 999
instead is acceptable is Daman's call, not the AI's — do not adopt it silently.

## What went wrong on 2026-08-24 — all four incidents

| # | Symptom | Real cause | Fix | Evidence |
|---|---|---|---|---|
| 1 | `POST /Attachments2` → **400, code 206, "Bad Post content."** | **curl's `Expect: 100-continue`** header (added automatically for any body over ~1 KB) breaks the Service Layer multipart through the home bridge. **Not a size limit** | add **`-H 'Expect:'`** to the `curl -F` POST **and** PATCH → 201/204 | Found independently on two bills. A 1,402 KB file uploaded fine with the header suppressed — larger than the 1,056 KB file that failed without it |
| 2 | Draft 55177's scan only went in after the PDF was re-rendered 1.03 MB → 286 KB (**−73%**) | The compression was **necessary for the guard** either way — 1,056 KB would have tripped 1120026 at Add. Why the smaller file then also got past the `400` on plain `curl -F` is **not explained**: curl sends `Expect:` for any body over ~1 KB, so size alone should not have fixed it | compress **and** suppress `Expect:` — treat them as two separate fixes | Entry note filed with the draft blames the size alone; that is half the story. `U_CHK` = 279 on AE 172366 |
| 3 | Draft 55175: base attachment **AE 170926 "not a PDF"** | **The warning was correct.** `ATC1` says `FileExt` = **`jpeg`** — the GRPO's bill was a WhatsApp photo. The defect is in the uploader, which accepts only PDFs and hard-codes `type=application/pdf`, so it skipped a perfectly good file | upload it as what it is; AE 172356 line 3 is now that `jpeg`, 195 KB, ticked | `SELECT "FileExt" ... WHERE "AbsEntry"=170926` → `jpeg` |
| 4 | Batch upload died with **`KeyError: 'AbsoluteEntry'`** | `attach_all.py` does `json.loads(r)["AbsoluteEntry"]` on the POST body **without checking the HTTP status**. On the 400 the body is `{"error":{"code":206,...}}` — no such key. The KeyError *is* the 400, wearing a Python traceback | check the status code first and surface SAP's message | `curl -sk` hides the status; the error body is still on disk in the batch work dir |

Nothing in incidents 1–4 was a mount problem, and nothing was SAP refusing a big file.

### The 2026-08-24 memory note, checked

The memory says the API attach path works after the CIFS mount fix, and that Mart's 404s
are legacy missing source files rather than a mount fault.

- **API upload works in all three books — measured, and only ever on 2026-08-24.**
  `srcPath LIKE '%ServiceLayer%'` returns **28 files / 13 rows in Oil, 4 files / 2 rows in
  Mart, 1 file / 1 row in Beverages**, every one dated today. Confirmed, including
  Beverages, which the memory left open.
- **Mart's upload path is fine** — four files landed. So a Mart `404` is not the write
  mount. Whether the specific old rows that 404 are missing source files is **still
  unverified**: SQL can see the row, not the file. Closing it needs a directory listing on
  the share.

An API row is identifiable: `CopyToProd='Y'` with `Override='N'` and `CopyToTrgt='N'` —
28 such rows exist in Oil, all today. Human rows are `Y/Y/N`.

## One document, one row — and SAP makes the copy for you

| Finding | Measured |
|---|---|
| Rows referenced by exactly one document | **74,795** of 75,522 (Oil, 23 document tables) |
| Rows referenced by two documents | **727** |
| Posted A/P invoice sharing its draft's row | **0** of 14,267 pairs. 14,238 hold two **different** ids |
| Drafts sharing their base GRPO's row | **1** in all of Oil's history — draft **54983**, and it was **this CLI** on 2026-08-24 |

So SAP **clones** the attachment row when a draft is Added: the posted invoice gets a new
`OATC` id and its own copies of the files. Nothing is lost (0 pairs where the draft had an
attachment and the posted document did not), and the physical file is duplicated on the
share.

It also means the shared-pointer shortcut has no precedent in the books. **C-0026's "never
a shared pointer" is not a preference — it is what 14,267 posted invoices already do.**

⚠️ **`acc/apbatch/batch_send.py` still does the opposite.** `_attach_and_read_back()`
patches the draft with the GRPO's own `AttachmentEntry`:

```python
attachment = res.attachment or None          # = the GRPO's AttachmentEntry
sap.patch(f"Drafts({int(res.draft_entry)})", {"AttachmentEntry": int(attachment)}, yes=True)
```

That is the one row in Oil's history. It also has no stamp step, so in Oil it will fail
1120025 unless the GRPO's row happens to be ticked already. Not fixed here — reported.

## Which documents carry a scan

Draft attachment rate, 90 days to 2026-08-24, by `ODRF."ObjType"`:

| ObjType | Document | OIL | MART | BEV |
|---:|---|---|---|---|
| 18 | [[AP-Invoice]] | **1,700/1,708 (99.5%)** | **450/451** | **308/308 (100%)** |
| 19 | [[AP-Credit-Memo]] | **209/209 (100%)** | 75/79 | **21/21** |
| 20 | [[GRPO]] | 362/421 (86%) | 348/356 (98%) | 32/42 (76%) |
| 14 | [[AR-Credit-Memo]] | 117/126 | 130/141 | 51/55 |
| 16 | [[AR-Return]] | 15/158 | 12/80 | 1/17 |
| 15 | [[Delivery]] | 0/30 | 9/11 | — |
| 13 | [[AR-Invoice]] | 4/1,934 | 4/709 | 3/1,307 |
| 22 | [[Purchase-Order]] | 0/402 | 1/12 | 2/92 |
| 67 | [[Stock-Transfer]] | 0/1,630 | 0/213 | 1/372 |
| 1250000001 | [[Inventory-Transfer-Request]] | 0/150 | 0/7 | — |

Posted documents, same window:

| Table | OIL | MART | BEV |
|---|---|---|---|
| `OPDN` [[GRPO]] | **1,421/1,421 (100%)** | **439/439 (100%)** | **917/917 (100%)** |
| `OPCH` [[AP-Invoice]] | 1,456/1,474 (99%) | 663/705 (94%) | 261/268 (97%) |
| `ORPC` [[AP-Credit-Memo]] | 182/182 | 64/66 | 20/20 |
| `OINV` [[AR-Invoice]] | 778/1,918 (41%) | 2,302/3,228 (71%) | 835/1,323 (63%) |
| `OVPM` [[Outgoing-Payment]] | 1,103/1,761 (63%) | 231/402 (57%) | 176/199 (88%) |
| `OJDT` manual [[Journal-Entry]] | 30/324 (9%) | 28/206 (14%) | 8/112 (7%) |

Read that pair of tables together: **A/R invoice drafts almost never carry a file, but
41–71% of posted A/R invoices do** — the e-way bill and LR copy go on *after* posting.
On the purchase side the scan is on the document from the start.

Files per Oil A/P draft (90 days): 1 file **417**, **2 files 1,021 (61%)**, 3 files 171,
more 77. The two-file habit — own scan plus the base document's bill — is already what
most operators do by hand.

## How it differs across the three books

| | OIL | MART | BEV |
|---|---|---|---|
| `U_CHK` / `U_CHK2` columns | yes | **absent** | yes |
| Draft needs the tick | **yes** (1120025) | **no** | yes |
| Draft needs a size number | **yes** — null fails | no | **no** — null passes |
| Total size rule on a draft | ≤ 10,240 | none | ≤ 5,120 |
| Guard covers `OINV`/`ORPC`/`OPOR` | **no** | — | **yes** |
| Tick actually used | 62% of all lines, 84% in 2026 | never | 77% of all lines, 90% in 2026 |
| Size number actually used | 60% / 81% in 2026 | never | **13% / 22% in 2026** — Bev skips it, and its guard lets it |
| Spreadsheets | 2,902 `xlsx` of 132,783 (2%) | **9,967 of 39,193 (25%)** | 251 of 38,703 |
| `pdf` share | 87% | 69% | **91%** |

Mart being spreadsheet-heavy is not noise — a quarter of everything attached in Mart is an
`xlsx`. Do not assume "the attachment is the bill" in Mart.

**A figure from Oil asserted for Beverages is the classic mistake here.** In Oil the size
number is mandatory; in Beverages it is optional; in Mart the field does not exist. The one
API-uploaded Beverages row (AE 41019) has `U_CHK2='OK'` and `U_CHK` **null** — and it was
accepted.

## Attaching a bill scan to a draft — the procedure

### In the SAP B1 client (what Accounts does all day)

1. Open the draft → **Attachments** tab → **Browse**, pick the file. `srcPath` shows
   almost everyone works from `C:\Users\USER<nn>\Desktop`.
2. **Tick the Approve column on every line.** That is `U_CHK2`. Miss it and Add is refused
   with *Select "OK" in Approve Column After Adding Attachment*.
3. **Fill the size column (`U_CHK`) on every line, Oil only** — a blank fails, and a value
   over 1024 fails. Beverages needs only the tick. Mart has neither column.
4. Add the base document's bill as a **second line on this document's own row** — never by
   pointing at the GRPO's row. **(C-0026)**

*(Steps 1–3 are inferred from `srcPath`, the UDF names and the guard text; the grid layout
itself has not been seen. Steps 3 and 4 are measured rules.)*

### From the CLI (`jivo-ap-draft` and friends)

Full recipe: `.claude/skills/jivo-ap-draft/reference/attachments-upload.md`. **It needs two
amendments as of today, and neither is in the file yet:**

| Step | Amendment |
|---|---|
| POST and PATCH `Attachments2` | add **`-H 'Expect:'`** to every `curl -F`, or you get 400 "Bad Post content" |
| Stamp | `U_CHK` must be **≤ 1024**. Compress the scan first. Do **not** send `U_CHK` at all to Mart (`-1000`); Beverages accepts the tick alone |
| Base file | send it with **its own** MIME type and extension — the GRPO's bill is a `jpeg` about as often as it is a `pdf` (Oil: 9,216 `jpeg` + 4,520 `jpg` of 132,783) |
| Error handling | check the **HTTP status** before reading `AbsoluteEntry` out of the body |

Order matters: **upload → stamp → point the draft.** Pointing first fails; that is
literally how C-0026 was found (`Drafts(55126/55128/55130)` each 400'd on 1120025, then
204'd after the stamp — `queries/USER36/sap-writes.jsonl`).

## The read-back that proves it worked

```sql
-- one draft: the pointer, every file, and every guard in one row
SELECT d."DocEntry", d."ObjType", d."AtcEntry",
       COUNT(a."Line")                                     AS FILES,
       SUM(CASE WHEN a."U_CHK2" IS NULL THEN 1 ELSE 0 END) AS NO_TICK,     -- must be 0
       SUM(CASE WHEN a."U_CHK"  IS NULL THEN 1 ELSE 0 END) AS NO_SIZE,     -- must be 0 in Oil
       MAX(a."U_CHK")                                      AS MAX_KB,      -- must be <= 1024
       SUM(a."U_CHK")                                      AS TOTAL_KB     -- <= 10240 Oil, 5120 Bev
FROM "JIVO_OIL_HANADB"."ODRF" d
JOIN "JIVO_OIL_HANADB"."ATC1" a ON a."AbsEntry" = d."AtcEntry"
WHERE d."DocEntry" = <DocEntry>
GROUP BY d."DocEntry", d."ObjType", d."AtcEntry";
```

Four things must all be true, and `AttachmentEntry` coming back non-null proves only the
first:

- [ ] the draft's `AtcEntry` is set (`sapb1 query Drafts --select "DocEntry,AttachmentEntry"`)
- [ ] `NO_TICK` = 0 and, in Oil, `NO_SIZE` = 0
- [ ] `MAX_KB` ≤ 1024 and `TOTAL_KB` within the book's limit
- [ ] the file reads back: `GET Attachments2(<AE>)/$value` byte-identical to what you sent,
      and `trgtPath` is the book's share

Run against today's twelve CLI drafts, that query says:

| Draft | Files | Max KB | Total KB | Verdict |
|---:|---:|---:|---:|---|
| 55126, 55128, 55130, 55165, 55166, 55174, 55175, 55176, 55177, 54983 | 1–3 | 279–857 | 304–1,537 | clean |
| **55167** (D.D. Motors) | 2 | **1,402** | 1,430 | **blocked — 1120026 at Add** |
| **55168** (Om Sai 2496) | 2 | **1,032** | 1,061 | **blocked — over by 8 KB** |

Both need the scan re-rendered under 1 MB, the row re-stamped, and then they can be Added.
Nobody would have found that by looking at the draft: SAP said 204 to every write.

## Traps

1. **`AttachmentEntry` set ≠ attachment accepted.** The pointer PATCH returns 204 while
   the guard still refuses the Add. The pointer is the *first* of four checks.
2. **The guard fires on save, not on the row.** **34** live Oil drafts dated this August
   already violate it — they were saved before the file was attached or re-stamped, so the
   procedure never re-ran. Their Add will fail.
3. **Mart is a different world.** No `U_CHK` columns, no guard, and a stamp attempt errors
   `-1000`. Code written against Oil breaks there, and code written against Mart produces
   un-addable Oil drafts.
4. **Beverages looks like Oil and is not.** Null `U_CHK` passes in Bev, fails in Oil.
   Total cap 5 MB, not 10.
5. **"1 MB" is about `U_CHK`, not the file.** 4,698 Oil files attached in 2026 are over
   1 MB; 3,826 of them carry a declared size under the limit.
6. **`U_CHK`/`U_CHK2` are not on `PCH1` or `DRF1`.** They are attachment-line fields. A
   search of document lines for them finds nothing and proves nothing — the same
   name-mismatch failure mode as [[Field-Name-Rosetta]].
7. **A dash in `_data/profile-*.md` can mean "column absent in that book."**
8. **File names collide.** 34,330 name+extension combinations in Oil are used more than
   once, one of them 188 times, and 86% of rows carry `Override='Y'`. Rename to
   `VENDOR-REF-DATE.pdf` before uploading.
9. **The `$value` of a base attachment is often not a PDF.** Check with `file` and upload
   it as what it is.
10. **`FreeText` is where the tick goes when someone misreads the grid** — 31 rows say
    `OK` there and nowhere else.
11. **Deleting a draft with an attachment** needs `sapb1 delete draft --with-attachment`,
    or set `AttachmentEntry` back to null first. The files stay on the share either way —
    the Service Layer has no DELETE for `Attachments2`. → [[Document-Drafts]]
12. **~2,800 Oil `OATC` rows are referenced by no document** in the 23 tables checked.
    Uploading and then failing to point a document at the row leaves exactly that.

## Open questions

- **Is there a real platform ceiling?** 36 MB exists in the books; nothing shows where the
  Service Layer or the share gives up. Would need a deliberate test upload, which is a
  write — not done.
- **Why does `Expect: 100-continue` break the multipart?** The bridge, the Service Layer or
  something between. Only observed from home through `127.0.0.1:15000`. Untested from an
  office PC. And why a 286 KB body then succeeded **without** the header suppressed is
  unexplained — the failure may be timing-sensitive rather than a clean threshold.
- **Is typing `999` for an oversized file acceptable practice?** It is what the books do
  (1,344 times in 2026). Documented, not endorsed — Daman's call.
- **Do the Mart `404`s on old rows mean the source files are gone?** SQL sees the row, not
  the file. Needs a listing on the share.
- **Does SAP copy `U_CHK`/`U_CHK2` when it clones the row at Add, or does the client
  re-tick?** The outcome is measured (0 untick'd lines on 2026 Oil `OPCH`); the mechanism
  is not.
- **What are `CopyToTrgt` / `CopyToProd` for?** Values measured, meanings inferred. The
  useful fact — `CopyToProd='Y'` marks an API upload — is measured.
- **Does the guard block an Add whose total lands between 5,120 and 10,240?** The draft
  rule allows it and the `OPCH` rule does not. Not observed.

## Queries used

```sql
-- the UDFs exist in two books and on one table
SELECT SCHEMA_NAME, TABLE_NAME, COLUMN_NAME, DATA_TYPE_NAME FROM SYS.TABLE_COLUMNS
WHERE SCHEMA_NAME IN ('JIVO_OIL_HANADB','JIVO_MART_HANADB','JIVO_BEVERAGES_HANADB')
  AND COLUMN_NAME LIKE 'U_CHK%';

-- OATC is one column
SELECT SCHEMA_NAME, COLUMN_NAME FROM SYS.TABLE_COLUMNS WHERE TABLE_NAME='OATC';

-- rows, tick, size, span per book
SELECT COUNT(*), COUNT(DISTINCT "AbsEntry"),
       SUM(CASE WHEN "U_CHK">0 THEN 1 ELSE 0 END),
       SUM(CASE WHEN "U_CHK2"='OK' THEN 1 ELSE 0 END),
       SUM(CASE WHEN "FileSize">0 THEN 1 ELSE 0 END), MIN("Date"), MAX("Date")
FROM "JIVO_OIL_HANADB"."ATC1";          -- and MART, BEV

-- the guard, read from the database
SELECT SCHEMA_NAME, PROCEDURE_NAME, LENGTH(DEFINITION),
       LOCATE(DEFINITION,'Approve Column'), LOCATE(DEFINITION,'U_CHK2')
FROM SYS.PROCEDURES WHERE UPPER(PROCEDURE_NAME) LIKE 'SBO_SP%'
  AND SCHEMA_NAME IN ('JIVO_OIL_HANADB','JIVO_MART_HANADB','JIVO_BEVERAGES_HANADB');
SELECT SUBSTRING(DEFINITION, 152900, 1500) FROM SYS.PROCEDURES
WHERE SCHEMA_NAME='JIVO_OIL_HANADB' AND PROCEDURE_NAME='SBO_SP_TRANSACTIONNOTIFICATION';

-- the ceiling that exists vs the ceiling that is enforced
SELECT MIN("FileSize"), MAX("FileSize"), ROUND(AVG("FileSize")),
       SUM(CASE WHEN "FileSize">1024  THEN 1 ELSE 0 END),
       SUM(CASE WHEN "FileSize">10240 THEN 1 ELSE 0 END)
FROM "JIVO_OIL_HANADB"."ATC1" WHERE "FileSize">0;

SELECT COUNT(*), SUM(CASE WHEN "FileSize">1024 AND "U_CHK"<=1024 THEN 1 ELSE 0 END),
       SUM(CASE WHEN "FileSize"="U_CHK" THEN 1 ELSE 0 END)
FROM "JIVO_OIL_HANADB"."ATC1" WHERE "U_CHK">0 AND "FileSize">0 AND YEAR("Date")=2026;

SELECT "U_CHK", COUNT(*) FROM "JIVO_OIL_HANADB"."ATC1"
WHERE "FileSize">1024 AND "U_CHK" BETWEEN 1 AND 1024 AND YEAR("Date")=2026
GROUP BY "U_CHK" ORDER BY 2 DESC;

-- does the guard actually bite: guarded vs unguarded tables, 2026
SELECT COUNT(a."Line"), SUM(CASE WHEN a."U_CHK2" IS NULL THEN 1 ELSE 0 END),
       SUM(CASE WHEN a."U_CHK">1024 THEN 1 ELSE 0 END)
FROM "JIVO_OIL_HANADB"."OPCH" p JOIN "JIVO_OIL_HANADB"."ATC1" a ON a."AbsEntry"=p."AtcEntry"
WHERE p."CANCELED"='N' AND YEAR(p."DocDate")=2026;      -- and OPDN, ORPC, OINV; and BEV

-- one document, one row
SELECT USERS, COUNT(*) FROM (SELECT AE, COUNT(*) AS USERS FROM (
  SELECT "AtcEntry" AS AE FROM "JIVO_OIL_HANADB"."OPCH" WHERE "AtcEntry">0
  UNION ALL SELECT "AtcEntry" FROM "JIVO_OIL_HANADB"."ODRF" WHERE "AtcEntry">0
  UNION ALL SELECT "AtcEntry" FROM "JIVO_OIL_HANADB"."OPDN" WHERE "AtcEntry">0
  -- … 20 more document tables …
) GROUP BY AE) GROUP BY USERS;

-- SAP clones the row at Add
SELECT COUNT(*), SUM(CASE WHEN p."AtcEntry"<>d."AtcEntry" THEN 1 ELSE 0 END),
       SUM(CASE WHEN p."AtcEntry"=d."AtcEntry" THEN 1 ELSE 0 END)
FROM "JIVO_OIL_HANADB"."OPCH" p JOIN "JIVO_OIL_HANADB"."ODRF" d ON d."DocEntry"=p."draftKey"
WHERE p."draftKey">0;

-- the one shared draft→GRPO pointer in Oil history
SELECT d."DocEntry", d."AtcEntry", g."DocNum", d."UserSign"
FROM "JIVO_OIL_HANADB"."ODRF" d JOIN "JIVO_OIL_HANADB"."OPDN" g ON g."AtcEntry"=d."AtcEntry"
WHERE d."AtcEntry">0;

-- has the API ever written into this book
SELECT COUNT(*), COUNT(DISTINCT "AbsEntry"), MIN("Date"), MAX("Date")
FROM "JIVO_MART_HANADB"."ATC1" WHERE TO_VARCHAR("srcPath") LIKE '%ServiceLayer%';

-- attachment discipline by draft type, 90 days
SELECT "ObjType", COUNT(*), SUM(CASE WHEN "AtcEntry">0 THEN 1 ELSE 0 END)
FROM "JIVO_OIL_HANADB"."ODRF" WHERE "DocDate">='2026-05-25' GROUP BY "ObjType";

-- who attaches
SELECT u."USER_CODE", u."U_NAME", COUNT(*) FROM "JIVO_OIL_HANADB"."ATC1" a
JOIN "JIVO_OIL_HANADB"."OUSR" u ON u."USERID"=a."UsrID"
WHERE a."Date">='2026-05-25' GROUP BY u."USER_CODE", u."U_NAME" ORDER BY 3 DESC;
```

Also read, not re-derived: `_data/profile-ATC1.md`, `_data/profile-OATC.md`,
`_data/profile-OPCH.md`, `_data/profile-ODRF.md`, `_data/profile-OPDN.md`,
`_data/sample-OPCH-OIL.md`, `_data/sample-ODRF-OIL.md`,
`queries/USER36/sap-writes.jsonl`, `queries/manager/sap-writes.jsonl`,
`acc/INVENTORY.md`, `acc/apbatch/batch_send.py`,
`.claude/skills/jivo-ap-draft/reference/attachments-upload.md`.

## See also

[[Document-Drafts]] · [[AP-Invoice]] · [[AP-Credit-Memo]] · [[GRPO]] ·
[[Purchase-to-Pay]] · [[Field-Name-Rosetta]] · [[Approval-Workflow]] ·
[[Add-on-Tables-and-UDFs]]
