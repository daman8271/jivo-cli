---
name: jivo-summary-pdf
description: Use when Daman or an operator wants one PDF of everything that was entered into SAP today (or on a date) so it can be forwarded to Divjot, Bhawani or a manager - "summary pdf", "compile all the draft numbers", "what did all those sessions make", "one report of today's entries", "send him the list", after a day of parallel A/P sessions, or when someone asks how many entries were made and how long it took.
---

# Summary PDF of a day's SAP entries

## Overview

Several Claude sessions enter bills in parallel. Each one reports only to its own tab, and a tab shows the last 35 lines. The person forwarding the work needs one page with every DocEntry, DocNum, amount, attachment row and approval request, plus every warning the sessions raised. **The source of truth is SAP and the shared write log, never the tab screens.** Screens are used only to see whether a session is still running.

## Steps

1. **Collect.** From the repo root:
   ```bash
   python3 .claude/skills/jivo-summary-pdf/bin/summary_pdf.py collect --out <scratchpad>/summary
   ```
   About 30 seconds, read-only. Reads `queries/*/sap-writes.jsonl` for the date, reads every touched draft back from all three companies, finds its `ApprovalRequests` row (Code = request number) and any invoice it posted as, resolves attachment-only touches and deleted drafts (with the rebuild, if any), pulls each session's final report from `~/.claude/projects/<repo>/*.jsonl`, and on a cmux box captures every tab. Writes `entries.json`, `skeleton.md` (all tables filled), `sessions.md`, `screens.md`. `--date YYYY-MM-DD` for another day.
2. **Read `sessions.md` end to end.** The final reports hold the warnings: TDS judgment calls, debit notes owed after posting, handwriting that could not be read, rate marks, why a draft was held. A session with no final report is still running: its facts are already in the skeleton from SAP; match it to a tab in `screens.md` by its first ask to see what it is still doing. A running session that wrote nothing changes no row; say so instead of hedging.
3. **`cp skeleton.md report.md` and edit `report.md`.** Keep both master tables as generated. Replace every `TODO`: who it is for, the action list grouped by book, per-bill open items, and the **Warnings and notices** table with one row per warning in the session's words condensed. Drop nothing a session flagged. A deleted-draft row shows what the log knows (time, user, rebuilt as); fill vendor and bill from the session report. Drafts a session verified but never wrote to are absent from the log; add them from `sessions.md`, marked as such.
4. **Render.**
   ```bash
   python3 .claude/skills/jivo-summary-pdf/bin/summary_pdf.py render <scratchpad>/summary/report.md
   ```
   Prints the PDF path in `~/Downloads` (`--pdf PATH` to choose). It leaves `report.html` and `report.pdf` beside the source. Supports headings, tables, bullets, `**bold**`, `` `code` ``, `~~struck~~`. Look at page 1 (`pdftoppm -r 70 -f 1 -l 1 -png`) before handing over.
5. **Hand over in three lines:** how many documents, the total, what the reader must do now. If sessions were still running, name the rows that may change and offer a re-run.

## What the reader must be told

- Find drafts by **DocEntry**. A draft's DocNum is provisional; several drafts share one until Added.
- Oil drafts go to Bhawani with `sapb1 add-draft <DocEntry>` run from `sap-b1/cli` under the operator's env (the same command the session used, whatever wrapper it went through). Mart and Beverages drafts must be Added from the SAP client: their DI approval switch is off (C-0074) and an API Add there posts live.
- Her approval does not post. A person presses Add a second time.
- Debit notes on the paper become A/P credit memos only after the parent invoice posts.

## Answering "how long did it take"

`entries.json` has `created_at` per draft and the skeleton prints first and last write. Scan files in `~/Downloads/DocScanner*.pdf` carry the hand-over time. State CLI timings as measured and any human comparison as an estimate with its confidence; the measured human pace is the gap between consecutive documents by one user in HANA (`OPCH.CreateDate/CreateTS`), not a guess.

## Common mistakes

| Mistake | What happens | Do instead |
|---|---|---|
| Building the list from tab screens | `cmux read-screen --scrollback` returns one frame (~37 lines); numbers get missed | Write log + SAP read-back; screens only for "still running?" |
| Trusting one session's summary of another | Tab 4 listed 55899 as "not read" while it was submitted | Every number from `entries.json` |
| Reporting only the tabs you were pointed at | Five other drafts were pending with Bhawani the same day | The write log covers every operator; include everything, mark what came from where |
| Using make-pdf for wide tables | Cells wrap one word per line, page 1 comes out blank | `render` (own CSS, nowrap master table, browse daemon) |
| Headless Chrome `--print-to-pdf` | Hung two minutes, left an orphan | `render` uses the gstack browse daemon; kill any `chrome-tmp` process you started |
| Output path outside `/private/tmp` or the repo | `browse pdf` refuses: "Path must be within" | `render` writes there and copies to Downloads |
| `--select WTSum` | SAP -1000 invalid property | TDS is the sum of `WithholdingTaxDataCollection[].WTAmount`; the script does it |
| Calling a draft "submitted" because the log has SaveDraftToDocument | In Mart/Bev that call posts the invoice | Trust `AuthorizationStatus` and `ApprovalRequests`; `bost_Close` on a draft means it posted |
| Editing `skeleton.md` in place | The next `collect` overwrites it | Copy to `report.md` first |
