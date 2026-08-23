# Things the Accounts team can ask (plain English)

## Balances / ledgers
- "What's the ledger balance of Ziyaul Haque?"
- "Is that a debit or credit balance?"
- "Show the open invoices behind customer ORGC000013's balance."
- "Which customers owe us the most right now (top 20 by balance)?"

## Turnover / sales
- "Total turnover April to today, month-wise, all 3 companies."
- "Mart's sales for June."
- "Top 10 customers by sales value this month in Oil."

## Documents
- "Open sales orders not yet delivered."
- "Today's invoices in Mart with totals."
- "Purchase orders raised this week."

## Inventory / items
- "Items below reorder level in Beverages."
- "Stock on hand for item <code>."

Tip: name the company if it's not Oil ("...in Mart", "...in Beverages"), and give a date range for sales questions.

## Creating a draft (not something you ask — something you run)

Claude can't change SAP; asking it to "create an order" won't work, by design.
When you actually need a document in SAP, you run one command yourself in
Command Prompt (`cd C:\jivo-sap`) and it creates a **draft**:

```
sapb1.exe draft order --data "{\"CardCode\":\"C0001\",\"DocumentLines\":[{\"ItemCode\":\"A0001\",\"Quantity\":10}]}"
```

It prints exactly what it will send and asks
`Type 'yes' to send this write to JIVO_OIL_HANADB:` — type the whole word `yes`
(`y` doesn't count; anything else cancels). Add `--dry-run` instead if you just
want to see what it would send. Then:

```
Draft created in JIVO_OIL_HANADB: DocEntry 4321, DocNum 99 (oOrders).
Open SAP B1 → Document Drafts → review → Add.
```

**Now open SAP B1 → Document Drafts, check it, and press Add.** Nothing is
posted until you do — no stock, no ledger. Same shape for `draft invoice`,
`draft purchase-order`, `draft delivery`, `draft credit-note`. Full steps and the
Windows quoting are in `SETUP.md`.

## Wrong draft? Remove it (also something you run)

Claude still can't do this for you — same reason. In Command Prompt:

```
sapb1.exe delete draft 4321
```

It shows you the draft first, asks you to type `yes`, deletes it, then reads it back
to prove it's gone. Several at once is fine — `sapb1.exe delete draft 4321 4322 4323`,
up to 50 — one confirmation for the lot, and `--dry-run` shows you what it would
remove without removing it (it reads SAP to do that, but sends no delete). **Drafts only**: anything already Added in SAP is untouchable
from here, and a draft *a person* keyed in SAP B1 is refused unless you explicitly
say it's yours to remove — so is one that has gone for approval, until you say so.
Payment drafts: `sapb1.exe delete payment-draft 77`.

Handy reads while you're at it: "what fields can I set on an order?" → ask Claude
for the Orders fields, or run `sapb1.exe fields Orders`.
