---
name: jivo-invoice-sweep
description: Use when an operator wants the invoices that arrived in a MAILBOX pulled out and saved - "check today's emails for invoices", "download all the invoices from my mail", "which mails today had a tax invoice", "aaj ki mail ke bills nikalo", "invoices from yesterday's mail", or a daily routine that files the day's invoices into Documents. Reads the mailbox read-only over IMAP, classifies every attachment on its CONTENT (not the filename), and saves tax invoices / credit notes / other bills into ~/Documents/JIVO-Invoices/<date>/. NOT for entering a bill into SAP - that is jivo-ap-draft, and this skill never touches SAP.
---

# Invoice sweep of a mailbox

## What it answers

Four numbers, then the files:

1. how many emails came in that day
2. how many of them carried attachments
3. how many of those attachments are invoice documents at all
4. how many are genuine **tax invoices** - and those are saved to Documents

Filenames are never trusted. On 2026-09-03 the security contractor's tax invoice arrived
as `1.png` and a mail titled "Bills-26-08-2026" carried a handwritten attendance register.
Everything is decided by reading the file: PDF text, OCR for scans, spreadsheet cells.

## Run it

```bash
python3 mail-cli/invoice_sweep.py --env-prefix NAVDEEP                  # today
python3 mail-cli/invoice_sweep.py --env-prefix NAVDEEP --date 2026-09-01
python3 mail-cli/invoice_sweep.py --env-prefix NAVDEEP --days 3          # last 3 days, one folder each
```

On Windows: `python mail-cli\invoice_sweep.py --env-prefix NAVDEEP`.

`--env-prefix X` reads `ZOHO_MAIL_X_USER` / `ZOHO_MAIL_X_APP_PASSWORD` from the repo-root
`.env`. Mailboxes already there: `NAVDEEP` (navdeep@jivo.in), `ACCOUNTS007`, `ACCOUNT003`,
and the default `ZOHO_MAIL_*` block (logistics@jivo.in). For a mailbox not in `.env`,
pass `--user` and `--password` (the app password; spaces are fine) or set
`JIVO_MAIL_USER` / `JIVO_MAIL_PASSWORD`.

Takes 3-6 minutes for a 100-email day; the slow part is OCR. It prints one line per
file it keeps and ends with the funnel and the folder.

## What lands where

```
~/Documents/JIVO-Invoices/<YYYY-MM-DD>/
    <uid>__<file>              tax invoices  (TAX INVOICE header, or invoice number + GST)
    credit-notes/              credit notes  (GST documents but not invoices - do not count them as invoices)
    other-invoices/            invoices with no GST on them (cash memos, receipts, foreign bills)
    needs-a-look/              document-sized scans the box could not read (no OCR), inline
                               screenshots that duplicate a PDF in the same mail, and very
                               long filings that merely quote invoices - open these by eye
    INDEX.csv                  every file -> email uid, sender, subject, why it was bucketed, sha256
    SUMMARY.txt                the four numbers + which tools were available on this box
```

Each saved file is prefixed with the email uid so it can be traced back:
`mail-cli/jmail-navdeep show <uid>` opens the mail.

## Report back

Give the four numbers as a short table, the folder path, and then the judgment calls
the operator should know about - read `INDEX.csv` and `SUMMARY.txt` for them:

- **JIVO's own outgoing AR invoices** (stock transfers, sales) are tax invoices too and
  will be in the folder. Say how many of the count are JIVO's own, not vendor bills.
- **Credit notes are not tax invoices.** They are filed separately; mention the count.
- **`needs-a-look/` is not empty** means the box has no OCR (SUMMARY says
  `tesseract(OCR)=no`) or a screenshot duplicated a PDF. Name the files; do not
  guess what is in them.
- **Duplicates** (same bytes sent twice, or a PDF plus a pasted screenshot of it) are
  skipped and listed in INDEX.csv as `duplicate` - the count is invoices, not files.

Nothing here writes to SAP or to the mailbox. If the operator then wants a bill
**entered**, that is a new ask: hand the file to `jivo-ap-draft` (goods) or
`jivo-ap-service-draft` (services) per bill.

## If the box has no OCR

The script still runs: text PDFs are read (via `pdftotext`, or `pypdf` if installed -
`pip install pypdf`), scans go to `needs-a-look/`. To read scans, install Tesseract
(Windows: `winget install -e --id UB-Mannheim.TesseractOCR`, then add its folder to
PATH) and Poppler for `pdftoppm`. SUMMARY.txt line 2 shows what the box had.
