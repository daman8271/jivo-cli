# Transporter-wise Details — JIVO Accounts

**Live:** https://jivo-transporter.vercel.app (public, no login)

One page, **two reports** (Daman's call, 2026-08-23): **Oil + Beverages combined**
(every combined figure carries its "Oil ₹X + Bev ₹Y" split — they are two SAP
books) and **Mart separate**, never mixed. The combined roster lists both books'
transporters in one table, each row badged with its book; drill-down (mapping,
tables) is per book because SAP keeps vendor codes and document numbers per
book — clicking a roster row opens the right book automatically. For each
transporter: every A/P invoice, every outgoing payment, and **the mapping
between them** (which payment settled which bill, and what was held back as
TDS / discount / unexplained residual). Built 2026-08-22 so Accounts stops
re-searching SAP for the same bill-to-payment question.

## What it answers

- Which bills has transporter X raised, and which of them are paid?
- Which bills did payment N cover, and how was the amount split?
- Was TDS deducted at payment, or was the bill paid at full gross?
- How much money has gone out **against no bill at all** (on-account)?
- What doesn't reconcile, and by how much?

## Reading the flags

Per invoice (`RESIDUAL_FLAG`), evaluated in this order:

| Flag | Meaning |
|---|---|
| `UNPAID` | no payment touches this bill |
| `OK` | paid = gross − TDS − discount (±₹1) — reconciles |
| `GROSS_PAID` | paid in full; the TDS on the bill was **not** deducted at payment (`OPCH.WTApplied = 0`) |
| `SHORT` | paid less than gross − TDS; the gap is an **unexplained residual** |
| `OVER` | genuinely paid above the bill (0 rows as of 2026-08-22) |
| `PART_TDS` | something deducted, but less than the TDS |

Per payment (`MATCH_FLAG`): `MATCHED` (allocations tie to the total ±₹1),
`PARTIAL` (they don't), `ON_ACCOUNT` (no allocation line at all).

`OTHER_DEDUCTION` is `GROSS − TDS − DISCOUNT − NET_PAID`. It is a balancing
figure, not a verified deduction, and the page says so.

## Data facts that make a naive version wrong

All verified live on 2026-08-22 — full record in `FACTS.md`.

- Transporters = vendor group `OCRG.GroupCode 102` in all three books.
- `VPM2` keys are named backwards: `VPM2.DocNum` is the **payment's** DocEntry,
  `VPM2.DocEntry` is the **invoice's**. A reversed join returns plausible wrong rows.
- TDS lives on the invoice (`OPCH.WTSum`), not the payment line (`VPM2.WtAppld`
  is 0 everywhere). Discount (`DcntSum`) is 0 everywhere.
- Payments settle invoices, credit notes (19), journal entries (30) and earlier
  on-account payments (46, negative). None are dropped.
- `CANCELED` is three-valued; filter `= 'N'` (C-0021). `DocStatus` is
  unreliable (C-0019) — status comes from the money, not the flag.
- Every transporter payment is a bank transfer; the bank reference is in
  `Comments`, never in `TrsfrRef`.

## Layout

```
transporter-dashboard/
  FACTS.md              verified data facts — binding on anyone changing the SQL
  pipeline/
    sql/                4 read-only HANA queries ({{SCHEMA}} substituted per book)
      transporter-master.sql        one row per transporter
      transporter-invoices.sql      one row per A/P invoice, with reconciliation
      transporter-payments.sql      one row per outgoing payment
      transporter-allocations.sql   one row per VPM2 line — the mapping itself
    build.py            runs the SQL through hana-sql, writes site/data/*.json
    live-refresh.sh     VPS loop: build → fingerprint rows → deploy only on change
    vercel-public.py    strips Vercel's SSO gate after every deploy
  site/
    index.html          the page (plain HTML + ES modules, no build step, no CDN)
    assets/             board.css · core.js · mapping.js (the SVG diagram) · views.js
    data/               generated — never hand-edit
```

## Refresh

```bash
# one-off, from the Mac (needs the home bridge / office IP)
python3 pipeline/build.py && (cd site && vercel deploy --prod --yes) \
  && python3 pipeline/vercel-public.py jivo-transporter

# continuous, on the VPS (cron, every 2 min; deploys only when rows change)
*/2 * * * * /root/jivo-cli/transporter-dashboard/pipeline/live-refresh.sh
```

Fetch window is FY25 onward (`DocDate >= 2025-04-01`) so FY26 payments can
resolve the prior-year bills they settle. Default view is FY26.

Read-only throughout: `hana-sql` accepts only `SELECT`/`WITH`. Nothing here
writes to SAP.
