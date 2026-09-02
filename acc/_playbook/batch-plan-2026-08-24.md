# `acc batch` — batch A/P-invoice drafting from open GRPOs (Atlas plan, 2026-08-24)

Decided by Daman 2026-08-24: automation for Accounts starts with GRPO → A/P drafts, 50 at a time, Excel round-trip review. This is the implementation plan. Forge executes it in order; Cassius + Proof verify.

## 0. What exists and what this builds on (verified by reading)

| Thing | Where | What matters for this build |
|---|---|---|
| Single-bill pre-check | `.claude/skills/jivo-ap-draft/bin/precheck.py` | 450-line monolithic `main()`; all SAP reads go through `q()` = `subprocess.run([sapb1, "query", …, "--json"])` with `cwd=CLI.parent`; exit contract 0/2/3/4; payload shape proven (write log line 1 in `queries/USER36/sap-writes.jsonl` is the exact payload that created draft 54983). |
| Read-back | `…/jivo-ap-draft/bin/readback.py` | Same `q()` pattern; exit 0/1/3; flags TDS-0, qty/total, base-lines-closed. |
| Write contract | `sap-b1/cli/internal/cli/write.go`, `draft.go`, `patch.go`, `internal/client/write.go`, `exitcode.go` | `draft` splices `DocObjectCode` and POSTs to `Drafts`; refuses without `--yes` when stdin is not a TTY; exit 6 = SAP answered with an error envelope (nothing committed), exit 7 = `WriteOutcomeUnknownError` (sent, no answer — never replay); intent/outcome pair logged per attempt; `--json` returns SAP's created object on stdout. `patch "Drafts(N)"` proven (log lines 3–6). |
| Query contract | `internal/cli/listcmd.go`, `internal/client/query.go` | `--json` emits a bare rows array; `--all` follows nextLink (cap 200 pages); `--page-size` sets `Prefer: odata.maxpagesize`; `--count` is a separate mode. |
| Config precedence | `internal/config/config.go` | flag > env > `.env` in CWD; `SAPB1_WRITE_LOG` > `queries/<harness slug>/sap-writes.jsonl` > `~/.sapb1-writes.jsonl`. Session cache per company/host/user, so subprocess calls do not re-login. |
| Bridge/route | `acc/_playbook/connect.sh`, `acc/_playbook/sap` | Exported `SAPB1_HOST/PORT` win over `--env` files; `SAPB1_TIMEOUT=180`. |
| Demand | `acc/INVENTORY.md` | 609 open GRPOs (607 with attachment); **229 are service-type TRANSPORTER GRPOs** — a payload shape never sent live. 71 rows are older than 90 days, oldest Oct-2024. |
| Corrections | `harness/corrections/` C-0017/18/19/21/22 | DocDate = GRPO DocDate; Series + `bod_GSTTaxInvoice` mandatory; TDS comes out 0 unless asserted; C-0022: Bev follows the DocDate rule only 21% of the time. |
| Repo is public | `.gitignore` line 90, memory 2026-08-10 | Workbooks/sidecars hold vendor names, refs, amounts — must be ignored. |
| Python conventions | `harness/bin/setup.py` lines 40–44 | stdlib only, UTF-8 stream reconfigure guard for Windows consoles, `from __future__ import annotations`. No openpyxl anywhere in shipped code. |

### Two defects in the current precheck that the batch would hit on every row

1. **Series lookup has no upper month bound.** `precheck.py` line 353–354: `DocDate ge '{month_start}'` and no `lt next_month`. For a GRPO dated July scanned in August, the query returns August documents too and the most-common Series becomes August's — wrong series for a July posting.
2. **Duplicate check by GRPO only looks at drafts for the matched vendor** (line 304) and only after the vendor matched. For the batch, the GRPO-keyed check must be the primary one. The batch indexes every open A/P draft once by `BaseEntry`.

## 1. Design decisions (alternatives and why)

### D1. Reads and writes stay on `sapb1` via subprocess — no direct Service Layer from Python
The safety that makes writes trustworthy lives in `internal/client/write.go` (WroteRequest line between exit 5 and exit 7, intent/outcome audit pair, single 401 re-login, no idempotency header). Re-implementing in Python forks load-bearing code and bypasses the one sanctioned write path. Cost: per-call spawn over the bridge (~1–3 s); removed by changing query *shape*: ~5 bulk queries plus one per distinct vendor/branch-month instead of ~8 per row. Budget for 50 rows: ~40–60 calls ≈ 1–3 min scan; send ≈ 8 calls/row ≈ 5–10 min supervised.

### D2. Review surface: zero-dependency xlsx writer/reader — not openpyxl, not CSV
CSV: Excel mangles refs/dates, no yellow cells. openpyxl: not installed on operator boxes, pip/winget unreliable there. Zero-dep (`zipfile` + `xml.etree`): two fills, column widths, freeze pane, `yes/no` data validation, text-format (`@`) editable cells, sheet protection with editable cells unlocked, Indian-grouping number format — ~250 lines to write, ~120 to read. Reader must accept what Excel writes back (sharedStrings, numeric date serials).

### D3. Home for the shared code: `acc/apbatch/` package; the skill scripts become thin shims
The skill's `bin/precheck.py` / `bin/readback.py` keep argparse, print format and exit codes and import from `acc/apbatch` (they already have `find_repo()`; add one `sys.path.insert`). **Consequence:** `acc/apbatch/` must be committed to `main` by pathspec or every operator's skill breaks on the next pull. Gitignore `acc/_batches/` first.

### D4. Batch id travels in `Comments` — no Go change
Append ` | B240824-OIL-7F3A` to `Comments`. Write log records payloads verbatim, so `grep B240824-OIL-7F3A queries/*/sap-writes.jsonl` finds a run; the draft is searchable in SAP by the same token. 18 of 254 chars. Default on.

### D5. v1 sends item-type GRPOs only; service GRPOs are scanned, shown, and held
Service GRPO (`DocType dDocument_Service`, 229 of 609) has no ItemCode/Quantity; the draft needs `DocType: "dDocument_Service"` and lines with base keys only — untested live. Scan marks them `SERVICE-HOLD` with full detail; one supervised 1-row proof (step 12) flips `--allow-service` on.

### D6. Scan aborts (no workbook) when SAP becomes unreachable; send halts on exit 7
Scan retries a failed read 3× (2/4/8 s) then exits 4 with nothing written. Send: every row journaled before and after its write, exit 7 halts the run (remaining rows `NOT-ATTEMPTED`), `--resume` resolves the unknown row by looking for the draft by GRPO and ref before anything else is sent.

## 2. File layout

```
acc/
  acc.py                        entry point: python3 acc/acc.py batch {scan|send|status} …   (+ acc.cmd for Windows: python3 "%~dp0acc.py" %*)
  BATCH.md                      operator how-to (Windows + Mac), status legend, the resume rule
  apbatch/
    __init__.py
    sap.py                      SapCli (subprocess wrapper over sapb1: query/query_all/draft/patch; exit-code→exception map; company shorthand; env/--env precedence; read-only instance cannot write) + FakeSap for tests
    rules.py                    PURE functions, no I/O: inr(), fy_indicator(), month_bounds(), pick_series(), tds_proposal(), find_duplicates(), build_payload(), build_comments(), line_summary(), gross_of(), parse_sheet_date()
    context.py                  ScanContext: per-run caches (branches, BP groups, open A/P drafts indexed by BaseEntry and (CardCode,NumAtCard), vendor cards, last-3 invoices per vendor, WT rates, series per (bpl, month, subtype), PO DocNums)
    precheck.py                 precheck_grpo(sap, ctx, grpo) -> PrecheckResult  (status, reasons, payload, expect, tds, series, attachment)
    readback.py                 read_draft(sap, docentry) -> dict; readback_flags(draft, expect, tds_choice, attachment_entry) -> list[str]
    xlsx.py                     write_workbook(path, sheets: list[SheetSpec]) / read_workbook(path) -> {sheet: rows}; styles, validation, protection; handles inlineStr and sharedStrings, serial dates
    store.py                    new_batch_id(), batch_dir(), Sidecar (load/save/update_outcome), Journal (append-only JSONL), find_sidecar_for(workbook)
    batch_scan.py               run_scan(args) -> exit code
    batch_send.py               run_send(args) -> exit code; the state machine of section 5
    batch_status.py             print journal + outcomes for a workbook
  tests/
    fixtures/                   synthetic SAP JSON (shapes real, values fake), an Excel-resaved workbook, a sapb1 stub script
    test_rules.py  test_sap.py  test_precheck.py  test_xlsx.py  test_store.py  test_scan.py  test_send.py  test_skill_shims.py
  _batches/                     GITIGNORED — one folder per batch id (workbook, sidecar.json, payloads/, journal.jsonl, results-*.xlsx, dryrun-*.txt)
```

Refactored out of `.claude/skills/jivo-ap-draft/bin/`:
- `precheck.py` → keeps argparse, the `[1]…[6]` narrative prints, verdict and exit codes 0/2/3/4; all logic (`q`, `inr`, `fy_indicator`, `tokens`, series, TDS, duplicate, payload) comes from `acc.apbatch`. Paper-vs-GRPO checks (`--qty/--total/--po/--item` comparisons) stay in the shim.
- `readback.py` → shim over `apbatch.readback`; same prints, exit 0/1/3.
- `SKILL.md` gets one line: "Many bills from GRPOs → `acc batch` (see `acc/BATCH.md`)".

## 3. Workbook schema, sidecar, tamper detection

Workbook `acc/_batches/<id>/review-<id>.xlsx` (or `--out DIR`), three sheets.

**Sheet `Review`** — one row per GRPO, header row 1, frozen. Key = column C (`GRPO DocEntry`). Grey = locked, **yellow = editable only on READY rows** (grey and locked otherwise).

| Col | Header | Source | Edit |
|---|---|---|---|
| A | Row | 1..N | locked |
| B | GRPO DocNum | `PurchaseDeliveryNotes.DocNum` | locked |
| C | GRPO DocEntry | `DocEntry` (row key) | locked |
| D | Posting date (DocDate) | GRPO `DocDate` (C-0017) | locked |
| E | Vendor code | GRPO `CardCode` | locked |
| F | Vendor name | `CardName` | locked |
| G | Vendor group | `BusinessPartnerGroups.Name` | locked |
| H | Branch | `"{BPLID} {BPLName}"` | locked |
| I | Type | `Items` / `Service` | locked |
| J | Lines | `line_summary()`: `"0: PM0000851 … 42,900 @5.00"`, max 3 lines then `+n more`; partial lines marked `open 100/500` | locked |
| K | Open qty | sum of open-line `RemainingOpenQuantity` | locked, number |
| L | Taxable | sum `LineTotal` | locked, INR numFmt |
| M | Tax | sum `TaxTotal` | locked, INR numFmt |
| N | Gross | L+M | locked, INR numFmt |
| O | Series | resolved | locked |
| P | Sub-type | `bod_GSTTaxInvoice` / `bod_None` | locked |
| Q | TDS evidence | `TdsProposal.evidence` e.g. `last 3 posted: no/no/no (WTAmount 0/0/0) · master 1031 @0.1% → ₹214 if yes` | locked |
| R | Attachment | `yes (170187)` / `NONE` | locked |
| S | Bill date source | `GRPO TaxDate` / `= gate date (may be default) — check bill` | locked |
| T | Status | `READY` / `DUPLICATE` / `CANNOT-BUILD` / `SERVICE-HOLD` / `NEEDS-REF` / `INTERCOMPANY` | locked |
| U | Reason | problems + existing DocEntry/owner for duplicates | locked |
| **V** | **Approve? (yes/no)** | blank | **editable**, list validation `yes,no` |
| **W** | **TDS (yes/no)** | `TdsProposal.choice` | **editable**, list validation |
| **X** | **Vendor bill date (TaxDate)** | GRPO `TaxDate` | **editable**, text format `@` |
| **Y** | **Vendor ref (NumAtCard)** | GRPO `NumAtCard` | **editable**, text `@` |
| **Z** | **Note (goes to Remarks)** | blank | **editable** |

Indian grouping is a real number format on L–N (`[>=10000000]##\,##\,##\,##0.00;[>=100000]##\,##\,##0.00;##,##0.00`) so cells stay numeric; console output uses `inr()`.

**Sheet `Lines`** — locked detail: GRPO DocEntry, LineNum, ItemCode, Description, Open qty, Unit, UnitPrice, LineTotal, TaxCode, TaxTotal, Whs, CostingCode, base PO DocNum.

**Sheet `About`** — locked: `batch_id`, company, login (draft owner), host:port, scanned_at, scan args, counts per status, the legend, and the two rules in plain words ("only yellow cells; save as .xlsx; run `acc batch send <this file>`").

**Sidecar** `acc/_batches/<id>/sidecar.json` (schema 1):

```json
{"schema":1,"batch_id":"B240824-OIL-7F3A","company":"JIVO_OIL_HANADB","login":"USER36",
 "host":"127.0.0.1:15000","scanned_at":"2026-08-24T15:30:12+05:30","scan_args":{},
 "rows":{"25714":{"row":1,"status":"READY","reasons":[],
   "locked":{"B":2026086625,"C":25714,"D":"2026-08-14","U":""},
   "defaults":{"V":"","W":"no","X":"2026-08-13","Y":"2606000806","Z":""},
   "payload":{"CardCode":"VENDA000939","DocDate":"2026-08-14","BPL_IDAssignedToInvoice":2,"Series":3684,
              "DocumentSubType":"bod_GSTTaxInvoice","DocumentLines":[{"BaseType":20,"BaseEntry":25714,"BaseLine":0,
              "ItemCode":"PM0000851","Quantity":42900,"UnitPrice":5,"TaxCode":"IGST@18","WarehouseCode":"BH-PM","CostingCode":"MUSTARD"}]},
   "comments_base":"Based On Goods Receipt PO 2026086625 | PO 220726021 | GATE ENTRY NO 154",
   "expect":{"open_qty":42900,"taxable":214500.0,"tax":38610.0,"gross":253110.0,"lines":{"0":42900}},
   "attachment_entry":170187,
   "tds":{"choice":"no","basis":"PRECEDENT-NO","check":false,"master_liable":true,"wt_code":"1031","rate":0.1,"expected_amount":214,
          "precedent":[{"docentry":49158,"ref":"…","docdate":"…","wtamount":0,"withheld":false}]},
   "series":{"series":3684,"subtype":"bod_GSTTaxInvoice","source":"40 docs Aug-26 branch 2","nnm1":[[3684,"HR_G0826","GA"],[3732,"CNHR0826","GA"]]},
   "outcome":null}}}
```

`payload` deliberately excludes `NumAtCard`, `TaxDate`, per-line `WTLiable` and `Comments` — those four are finalized at send from the editable cells (Y, X, W, Z) and the batch tag. Everything else on the wire comes from the sidecar, never from the sheet.

**Tamper detection:** `send` reads `Review`, and for each row compares every locked column B–U against `locked` in the sidecar after normalization (strings stripped; numbers compared via `Decimal` rounded to 2 dp; dates as ISO). Any difference → row `TAMPERED` with the cell address and both values; not sent. The About sheet's `batch_id` must equal the sidecar's; the row-key set must match exactly. The sidecar is found next to the workbook, else at `acc/_batches/<batch_id>/sidecar.json`. Sheet protection (no password, `sort`/`autoFilter` allowed) makes locked cells physically hard to edit; the comparison is what enforces it.

## 4. Scan — query plan and row statuses

`acc batch scan --company Oil|Mart|Beverages|<DB> [--since YYYY-MM-DD | default today-90d] [--vendor CODE|name-fragment] [--group TRANSPORTER] [--limit 50 | 0=all] [--order oldest|newest (default oldest)] [--include-intercompany] [--env <operator>.env] [--out DIR]`

Read-only by construction: `SapCli(allow_writes=False)` has `draft()`/`patch()` raise; `test_scan.py` asserts FakeSap saw zero write calls.

Query plan (per company), all via `sapb1 query … --json`:
1. `PurchaseDeliveryNotes` — `DocumentStatus eq 'bost_Open' and Cancelled eq 'tNO' and DocDate ge '<since>'` [+ `and CardCode eq 'X'` when `--vendor` is a code] `--all --page-size 50 --orderby "DocDate asc,DocEntry asc"` (full rows; lines needed).
2. `BusinessPlaces` (once), `BusinessPartnerGroups` (once).
3. `BusinessPartners` for the distinct CardCodes, chunked `CardCode eq 'a' or CardCode eq 'b' …` (20 per call), select `CardCode,CardName,GroupCode,SubjectToWithholdingTax,BPWithholdingTaxCollection,Valid,Frozen`. Apply `--vendor` name fragment, `--group`, intercompany rule (C-0020: CardName contains `JIVO` → `INTERCOMPANY`, excluded unless flagged), then `--order` and `--limit`.
4. `Drafts` — `DocObjectCode eq 'oPurchaseInvoices' and DocumentStatus eq 'bost_Open'` `--all --page-size 50` → index by `BaseEntry` of lines with `BaseType 20`, and by `(CardCode, NumAtCard)`.
5. `PurchaseInvoices` by ref, chunked `NumAtCard eq '…' or …` (single quotes doubled), select `DocEntry,DocNum,CardCode,DocDate,DocTotal,Cancelled,NumAtCard`. Blank refs skip → `NEEDS-REF`.
6. Per distinct vendor: `PurchaseInvoices` `CardCode eq 'X' and Cancelled eq 'tNO'` `--orderby "DocEntry desc" --top 3` (full rows — lines' `WTLiable`). Subtype = most common `DocumentSubType` of those, default `bod_GSTTaxInvoice`.
7. Per distinct WT code: `WithholdingTaxCodes` rate.
8. Per distinct (BPLID, month, subtype): the two month-**bounded** series queries (section 6), plus NNM1 via `hana-sql` if reachable (optional, as today).
9. Per distinct PO `BaseEntry`: `PurchaseOrders` `DocEntry eq N` select `DocNum`, chunked with `or`.

Row status derivation (first match wins):
- `INTERCOMPANY` (excluded unless `--include-intercompany`)
- `DUPLICATE` — any live posted `PurchaseInvoices` with this ref (any vendor), or any open A/P draft with this ref, or any open A/P draft with a line `BaseType 20 and BaseEntry == GRPO.DocEntry`. Reason names DocEntry, owner `UserSign`, amount.
- `NEEDS-REF` — GRPO `NumAtCard` blank. Stays held; re-scan after the GRPO is fixed, or use the single-bill skill.
- `SERVICE-HOLD` — `DocType == dDocument_Service` and `--allow-service` absent.
- `CANNOT-BUILD` — no open lines; vendor `Frozen tYES`/`Valid tNO`; branch id not in `BusinessPlaces` or disabled; series unresolved; DocDate before current FY start (1 Apr) → "previous financial year, period closed — handle in the client"; DocDate month neither current nor previous month → note only (not a stop): "posting month <MMM-YY> — confirm the period is open".
- `READY` — payload built. Attachment `NONE` is a note, not a stop (2 of 609).

Scan exit: 0 workbook written; 0 with "0 GRPOs match" and no workbook; 2 usage; 3 config/auth; 4 SAP unreachable after retries (no workbook).

## 5. Send — state machine, re-validation, exit codes

`acc batch send <workbook.xlsx> [--dry-run] [--yes] [--resume] [--max-age-days 3] [--env …]`

Preconditions (any failure → exit 2, nothing contacted): workbook parses; `About.batch_id` found; sidecar found and ids match; row-key sets identical; sidecar `scanned_at` within `--max-age-days`; company in sidecar == company the CLI resolves to.

Per row, in sheet order, sequentially (never parallel):

```
V != "yes"                         -> SKIPPED
sidecar status != READY            -> REFUSED-STATUS
locked cells differ                -> TAMPERED
W not in {yes,no} | X unparseable | X > today | X < DocDate-120d | Y blank or >100 chars -> INVALID-INPUT
sidecar outcome == CREATED         -> ALREADY-CREATED (draft N)            [skip]
sidecar outcome == UNKNOWN         -> requires --resume (else halt, exit 7)
live re-validation:
  R5 GRPO by DocEntry: exists, Cancelled tNO, bost_Open, same CardCode,
     every payload line still bost_Open with RemainingOpenQuantity == sidecar qty (exact),
     AttachmentEntry read live (use live value; note if changed)              else -> STALE (reason)
  R6 PurchaseInvoices by ref (live, tNO) none; open A/P Drafts by ref none;
     open A/P Drafts for CardCode with BaseEntry == GRPO none                  else -> STALE-DUPLICATE (DocEntry)
  R7 vendor Valid/not Frozen (cached per vendor per run)                      else -> STALE
finalize payload: NumAtCard=Y, TaxDate=X(ISO), WTLiable=tYES/tNO per line from W,
  Comments=build_comments(base, note=Z, tag=batch_id) <= 254 with the tag guaranteed to survive
write payloads/<docentry>.json
sapb1 draft purchase-invoice --data-file payloads/<docentry>.json --dry-run --json  -> full text to dryrun-<run>.txt, one-line summary to console
if not --yes: -> PREVIEWED
else:
  journal {event:"draft", state:"sending"}
  sapb1 draft purchase-invoice --data-file … --yes --json
    exit 0  -> parse DocEntry/DocNum; journal; sidecar outcome CREATED
    exit 6  -> REJECTED (SAP's [code] message); journal; continue with next row (nothing committed)
    exit 7  -> UNKNOWN; journal; sidecar outcome UNKNOWN; HALT batch: remaining approved rows NOT-ATTEMPTED; exit 7
    exit 4/5 before sending -> UNREACHABLE; halt; exit 4
  sapb1 patch "Drafts(N)" --data '{"AttachmentEntry": <live entry>}' --yes   (skipped when attachment NONE)
    exit 0 -> attachment ok; exit 6 -> gap "attachment not set — attach in client"; exit 7 -> readback decides
  readback: read_draft(N); flags = readback_flags(draft, expect, tds_choice=W, attachment_entry)
    -> CREATED (no flags) or CREATED-WITH-GAPS (flags listed; e.g. C-0018 "TDS 0 — tick WTax Liable before Add" when W=yes and WTAmount==0)
```

`--resume` for a row with outcome `UNKNOWN` (or a journal `sending` with no outcome after a crash/Ctrl-C): run R6 only. Exactly one open draft found by GRPO or ref → adopt as `CREATED-RECOVERED` (then patch attachment if null, readback). None found → `UNKNOWN-UNRESOLVED`: never re-sent from this batch; the operator re-scans later. More than one → `DUPLICATE` report. Then continue with `NOT-ATTEMPTED` rows. `REJECTED` rows are retried on a later `send --yes` if still approved.

Outputs: `journal.jsonl` (append-only, one line per event, written before and after each write), `results-<run>.xlsx` (Row, GRPO DocNum, Vendor, Ref, Gross, Outcome, Draft DocEntry, Draft DocNum, Attachment, WTAmount on draft, Readback flags, Message) and a console summary with the Document Drafts click-path and the login the drafts are under.

Send exit codes: 0 all approved rows `CREATED` (or, without `--yes`, all `PREVIEWED`); 1 finished but some rows SKIPPED-for-cause/REJECTED/STALE/TAMPERED/WITH-GAPS; 2 usage/workbook/sidecar; 3 config/auth; 4 unreachable before any write; 7 halted on an unknown outcome — go look, then `--resume`.

Structural guarantee: `batch_send.py` passes `--yes` to `sapb1` only inside the `if args.yes:` branch; any other path runs `--dry-run`. `sapb1` itself refuses a non-TTY write without `--yes` (`write.go`), so the batch physically cannot write by accident. Unit test pins this.

## 6. The two resolution rules as code

### TDS precedent (`rules.tds_proposal`)

```python
def tds_proposal(bp, last_posted, wt_rate, taxable) -> TdsProposal:
    codes = [w["WTCode"] for w in (bp.get("BPWithholdingTaxCollection") or []) if w.get("WTCode")]
    master_liable = bp.get("SubjectToWithholdingTax") == "boYES" and bool(codes)
    prec = [{"docentry": i["DocEntry"], "ref": i.get("NumAtCard"), "docdate": i["DocDate"][:10],
             "wtamount": float(i.get("WTAmount") or 0),
             "withheld": float(i.get("WTAmount") or 0) > 0
                         or any(l.get("WTLiable") == "tYES" for l in i.get("DocumentLines") or [])}
            for i in last_posted[:3]]                 # PurchaseInvoices, Cancelled tNO, DocEntry desc, top 3
    n, k = len(prec), sum(p["withheld"] for p in prec)
    if not master_liable:      choice, basis, check = "no",  "MASTER-NOT-LIABLE", k > 0
    elif n == 0:               choice, basis, check = "yes", "NO-HISTORY->MASTER", True
    elif k == n:               choice, basis, check = "yes", "PRECEDENT-YES", False
    elif k == 0:               choice, basis, check = "no",  "PRECEDENT-NO", False           # TPAC 08-22
    else:                      choice, basis, check = "yes", "MIXED->MASTER", True
    expected = round(taxable * wt_rate / 100) if choice == "yes" and wt_rate else 0
```

`check=True` renders as `CHECK:` prefix in column Q. Payload: every line gets `WTLiable: "tYES"` or `"tNO"` explicitly. Readback: when W=`no`, suppress the "TDS is 0 but vendor is liable" flag; when W=`yes` and `WTAmount == 0`, flag it (C-0018).

### Series (`rules.month_bounds`, `rules.pick_series`)

```python
m0, m1 = month_bounds(docdate)      # '2026-07-01', '2026-08-01'
docs = q("PurchaseInvoices", f"DocDate ge '{m0}' and DocDate lt '{m1}' and BPL_IDAssignedToInvoice eq {bpl} and DocumentSubType eq '{subtype}'", "DocEntry,Series", orderby="DocEntry desc", top=20)
docs += q("Drafts", f"DocObjectCode eq 'oPurchaseInvoices' and DocDate ge '{m0}' and DocDate lt '{m1}' and BPL_IDAssignedToInvoice eq {bpl} and DocumentSubType eq '{subtype}'", "DocEntry,Series", orderby="DocEntry desc", top=20)
choice = pick_series(docs, nnm1_rows, subtype)
```
`pick_series`: most-common `Series` among docs → use. None → NNM1 rows (`ObjectCode 18`, `Indicator = fy_indicator(docdate)`, `BPLId`, `Locked='N'`) filtered to `{bod_GSTTaxInvoice: GA, bod_None: --, bod_GSTDebitMemo: GD}[subtype]`: exactly one → use; several → the one whose `SeriesName` matches `^[A-Z]{2,4}_G\d{4}$` if exactly one matches, else `CANNOT-BUILD "several GA series"`. Docs-derived series not in NNM1's set → warning in column U. No NNM1 and no docs → `CANNOT-BUILD "first document of the month for branch N — series unknown"`. Cached per (bpl, m0, subtype) per scan. The single-bill shim gets the month bound too.

## 7. Test plan

**Unit (stdlib `unittest`, `python3 -m unittest discover -s acc/tests`, no network).** Fixtures synthetic in values (public repo), real in shape.
- `test_sap.py`: stub `sapb1` script echoing argv and exiting with a chosen code → exit 0/2/3/4/5/6/7 map to `SapOK/SapUsage/SapConfig/SapAuth/SapUnreachable/SapRejected/SapUnknownOutcome`; `cwd` = CLI dir; `--company` passed; Windows picks `sap-b1/accounts-kit/sapb1.exe`; read-only instance raises on `draft()`.
- `test_rules.py`: TDS matrix (all 5 branches + TPAC); `month_bounds` incl. Dec→Jan; `pick_series` cases; `build_comments` keeps the batch tag under truncation; `build_payload` for the 08-22 GRPO fixture **equals the logged payload** from `queries/USER36/sap-writes.jsonl` line 1 (minus the four send-time fields); `inr()`; `parse_sheet_date` for four text formats and an Excel serial; duplicate detection by ref and by BaseEntry.
- `test_precheck.py`: FakeSap scripted → READY / DUPLICATE-by-ref / DUPLICATE-by-GRPO / NEEDS-REF / SERVICE-HOLD / CANNOT-BUILD variants / INTERCOMPANY.
- `test_xlsx.py`: write→read round trip; read a fixture re-saved by Excel (sharedStrings, `t="s"`, date serial); validation and protection elements present; INR numFmt present.
- `test_store.py`: batch id format `B<yymmdd>-<OIL|MART|BEV>-<4hex>`; sidecar round trip; journal append; `find_sidecar_for` both locations.
- `test_scan.py`: 3-GRPO FakeSap run → workbook + sidecar; zero write calls; statuses; `--limit`, `--order`, `--group`; unreachable → exit 4 and no file.
- `test_send.py`: SKIPPED/REFUSED/TAMPERED/INVALID/STALE/STALE-DUPLICATE; no `--yes` → every row PREVIEWED and no write call; `--yes` happy path; exit 6 on row 2 continues to row 3; exit 7 on row 2 halts, row 3 NOT-ATTEMPTED, exit 7, sidecar UNKNOWN; `--resume` found → CREATED-RECOVERED, not found → UNKNOWN-UNRESOLVED never re-sent; max-age refusal; company mismatch refusal; Comments tag in payload file.
- `test_skill_shims.py`: characterization — capture current `precheck.py`/`readback.py` stdout with `q` monkeypatched to fixtures **before** refactoring, assert identical after; exit codes pinned.

**Live read-only check (Proof, no send):** bridge up, then for each company `python3 acc/acc.py batch scan --company X --since 2024-01-01 --limit 0 --out <scratch>`. Evidence: row count vs INVENTORY (332/43/234 ± drift), status distribution, READY count, how many GRPOs have `TaxDate != DocDate`, series resolved for every READY row, wall time, and write-log line count unchanged. Open one workbook in Excel on a Windows box, edit three yellow cells, save, `send --dry-run` (round-trip proof); edit a grey cell → `TAMPERED`.

**First supervised send (Daman's go):** Oil, `--vendor` limited to vendors already drafted via this path (SSY VENDA000936, TPAC VENDA000939, Frystal VENDA000601) `--limit 5`; operator fills V/W/X; `send` → preview; `send --yes` under the operator's env; verify in the SAP client; then ask Accounts to Add one and check the attachment pointer survives draft→invoice. Record in `acc/_playbook/session-log.md`.

## 8. Risks, ranked, with the mitigation in the steps

1. Service GRPOs (38% of the pile) unproven payload → `SERVICE-HOLD`, 1-row supervised proof before `--allow-service`.
2. Series month bug → fixed in `rules.pick_series` with a test; pre-FY refused, off-month noted.
3. Exit 7 / Service Layer instability → halt-on-unknown, journal before/after, `--resume`, never re-send from same batch.
4. Human keys the same GRPO between scan and send → live R6 at send; sidecar max-age 3 days.
5. Excel round-trip → `@` on editable text cells, reader accepts both string forms and serials, Excel-resaved fixture.
6. Public repo leakage → `acc/_batches/` ignored first; fixtures synthetic.
7. Skill regression from the refactor → characterization golden before touching anything.
8. Draft ownership → login printed on scan, About sheet, send summary; `--env` per operator; company-mismatch refusal.
9. Beverages practice differs (C-0022: 21%) → start Oil.
10. Old GRPOs / closed periods → default `--since` 90d, pre-FY refused, off-month noted.
11. Intercompany GRPOs (C-0020) → excluded by default, explicit flag.

## 9. Step order for Forge

1. `.gitignore`: add `acc/_batches/`. Verify: `git check-ignore acc/_batches/x`.
2. `acc/apbatch/sap.py` + `tests/fixtures/sapb1_stub.py` + `test_sap.py`. Verify: `python3 -m unittest acc.tests.test_sap`.
3. `acc/apbatch/rules.py` (move `inr`, `fy_indicator`, `tokens` verbatim from `precheck.py`; write the rest) + `test_rules.py` including the golden against write-log line 1.
4. **Characterization first:** `test_skill_shims.py` captures current `precheck.py`/`readback.py` output on fixtures (monkeypatch `q`). Verify: passes against the unmodified scripts.
5. `acc/apbatch/context.py` + `precheck.py` + `readback.py` + `test_precheck.py`.
6. Refactor the two skill scripts into shims; re-run step 4's test. Then one live single-bill dry-run via the skill path (read-only: `precheck.py … --out`) against real SAP.
7. `acc/apbatch/xlsx.py` + `test_xlsx.py`. Open the produced file by eye.
8. `acc/apbatch/store.py` + `test_store.py`.
9. `acc/apbatch/batch_scan.py` + `acc/acc.py` + `acc.cmd` + `test_scan.py`. Then Proof's live read-only scan on all three companies.
10. Adjust defaults from what the live scan shows; record in `acc/BATCH.md`.
11. `acc/apbatch/batch_send.py` + `batch_status.py` + `test_send.py`. Then live `send` with **no flags** on a real scan workbook (previews only, zero writes — check the write log line count).
12. Supervised 5-row Oil send with Daman's go; session-log entry; then the 1-row service-GRPO proof (`--allow-service`, one TRANSPORTER row, dry-run shown, Daman's go).
13. Docs: `acc/BATCH.md`, one line in `SKILL.md`, row in `acc/README.md`. Commit **by pathspec** (`acc/apbatch acc/acc.py acc/acc.cmd acc/tests acc/BATCH.md .claude/skills/jivo-ap-draft .gitignore`).

## 10. Decisions for Daman (defaults stated; Forge proceeds on the defaults)

1. Batch tag in `Comments` (visible to approvers) vs a Go `--tag` flag and exe rebuild. **Default: Comments.**
2. `Approve?` defaults blank vs prefilled `yes`. **Default: blank** — the tick is the per-document okay RULE 0 asks for.
3. Whether a row with `TaxDate == DocDate` on the GRPO should be held until edited. **Default: not held, source noted in column S.**
4. Committing `acc/` to the public repo: code has no secrets; `acc/INVENTORY.md` and `_playbook/session-log.md` carry operator names, a vendor bill and a server path. **Default: commit only the paths in step 13.**
5. Beverages batches under the C-0017 DocDate rule despite C-0022's 21%. **Default: Oil only until confirmed.**
