---
name: jivo-banking
description: Use when a bank statement arrives and its lines must be entered in SAP B1 — "bank entry", "put this statement in SAP", "make drafts for these bank lines", an HSBC/ICICI/Indian Bank export (.xlsx/.csv/PDF), or a screenshot of a bank ledger. Covers all three shapes a statement contains: customer receipts, vendor payments, and transfers between JIVO's own bank accounts. Also use to reconcile a bank account against SAP, or to work out why a payment draft opens blank in the SAP B1 client.
---

# Bank statement → SAP B1 (JIVO)

Internal skill for the jivo-cli toolkit. Built 2026-08-31 from a live HSBC
statement (a/c 166-79XXXX-001, 7 lines, ₹5.45 Cr) whose every line turned out to
be **already keyed** — and from the four drafts SAP then rejected outright.
Worked example: `reference/worked-example.md`.

**Sibling skill:** `jivo-outgoing-payment` handles ONE payment sourced from ONE
approval mail. This one handles a STATEMENT — many lines, mixed direction, no
approval thread. The write mechanics are shared; read that skill's §3 (clone the
precedent) and §7 (deleting a payment draft) rather than duplicating them here.

RULE 0 in `CLAUDE.md` governs the write.

---

## RULE ZERO — a statement records money that has ALREADY MOVED

Every other entry skill starts from a request for something to happen. **This one
starts from something that has already happened.** The bank has moved the money;
the only question is whether SAP knows.

> **So the default hypothesis is "already entered", and the tool must prove
> otherwise before you build a single payload.**
>
> Live, 2026-08-31: an operator handed over a 7-line HSBC statement and asked for
> drafts. All 7 were already posted — 4 receipts by USER11 (Preshit) and 3
> payments by USER05 (Taran), the same morning. Building from the paper without
> checking would have created ₹5.45 Cr of duplicates.

The failure mode here is **duplicating real money**, not missing a record. That
inverts the usual caution: being slow to write costs nothing, being quick costs
crores.

---

## 1. Tie the statement's own arithmetic first

Before believing any line, prove the export is complete:

```
opening balance  +  all credits  −  all debits  =  closing balance
```

If it doesn't tie, the file is filtered or truncated — stop and ask for a clean
export. Bank exports are usually **newest-first**, so the running balance column
descends as you read down. A statement carries both an opening figure
("closing ledger brought forward from <prev date>") and a current balance; use
the brought-forward one as the opening.

---

## 2. Resolve every account number to a GL code — including the ones in the narrative

A statement talks in account numbers. SAP talks in GL codes. Map both the
**statement's own account** and any account number **inside a narrative**:

```bash
# strips dashes and spaces, so "166-79XXXX-001" finds "16679XXXX001"
./hana-sql/hana-sql 'SELECT "AcctCode","AcctName" FROM "JIVO_OIL_HANADB"."OACT"
 WHERE REPLACE(REPLACE("AcctName",'"'"'-'"'"','"'"''"'"'),'"'"' '"'"','"'"''"'"') LIKE '"'"'%16679XXXX001%'"'"''
```

Live result: `2201105 = HSBC BANK A/C - 16679XXXX001`, and the `/70072XXX27` in a
narrative resolved to `2201101 = INDIAN BANK CC A/C 70072XXX27`.

> ### ⚠️ A narrative naming JIVO itself is a TRANSFER, not a payment
> `JIVO WELLNESS PVT LTD 83457J300TFC /70072XXX27` reads like a payment to a
> party called Jivo Wellness. It is JIVO moving ₹1.7 Cr from its own HSBC account
> to its own Indian Bank CC account. Key it as a vendor payment and you invent a
> creditor. **Always check a counterparty name against JIVO's own legal entities
> and own bank accounts before mapping it to a business partner.**

Company: `JIVO WELLNESS PRIVATE LTD` = Oil, `JIVO MART PRIVATE LIMITED` = Mart,
Beverages is its own entity. A transfer *between* two JIVO companies is a real
intercompany receipt in the receiving company's book (C-0005).

---

## 3. Three shapes, not one

| | **Receipt** | **Own-bank transfer** | **Vendor payment** |
|---|---|---|---|
| Money | in | out | out |
| Command | `draft payment incoming` | `draft payment outgoing` | `draft payment outgoing` |
| `DocType` | `rCustomer` | **`rAccount`** | `rSupplier` |
| `CardCode` | customer code | **omit** — SAP fills at Add | vendor code |
| Contents | `PaymentInvoices`, or none | **`PaymentAccounts`** row | `PaymentInvoices`, or none |
| `TransferAccount` | the statement's bank GL | the statement's bank GL (**source**) | the statement's bank GL |
| Series (Oil, Aug-26) | 2564 | 2600 | 2600 |
| `BPLID` | per precedent | 1 DELHI | per precedent |

`TransferAccount` is always the bank the statement belongs to — the account the
money left or arrived in. For a transfer the **destination** goes in the
`PaymentAccounts` line, never in `TransferAccount`.

**Own-bank transfer payload** (verified live, draft 2185):

```json
{ "DocType": "rAccount", "TransferAccount": "2201105", "TransferSum": 17000000,
  "Series": 2600, "BPLID": 1, "U_Pymnt_Mode": "RTGS",
  "PaymentAccounts": [ { "LineNum": 0, "AccountCode": "2201101",
    "GrossAmount": 17000000, "SumPaid": 17000000,
    "ProfitCenter": "CANOLA", "ProfitCenter2": "08-2026" } ] }
```

`ProfitCenter2` is the period as `MM-YYYY`. Both are on every JIVO bank line.

---

## 4. Match EVERY line against SAP before building anything

One query does it — all SAP movement on that bank GL for that date, both
directions:

```bash
./hana-sql/hana-sql 'SELECT '"'"'IN '"'"' AS "Dir","DocEntry","DocNum","CardCode","CardName","TrsfrSum"
 FROM "JIVO_OIL_HANADB"."ORCT" WHERE "TrsfrAcct"='"'"'2201105'"'"' AND "DocDate"='"'"'2026-08-31'"'"' AND "Canceled"='"'"'N'"'"'
UNION ALL
SELECT '"'"'OUT'"'"',"DocEntry","DocNum","CardCode","CardName","TrsfrSum"
 FROM "JIVO_OIL_HANADB"."OVPM" WHERE "TrsfrAcct"='"'"'2201105'"'"' AND "DocDate"='"'"'2026-08-31'"'"' AND "Canceled"='"'"'N'"'"'
ORDER BY "Dir","TrsfrSum"'
```

Match on **amount + date + bank GL**. Not on document number — a bank reference
never appears in SAP, and `DocNum` is unusable on drafts (§6).

Report the result as a two-way diff, because both sides matter:

- **statement line with no SAP row** → this is what you actually key.
- **SAP row with no statement line** → a payment SAP thinks left this bank but the
  bank has not shown. Live: three ARORA AGRI payments (₹1,90,15,748) sat in SAP
  against HSBC and were absent from the statement. That is either same-day timing
  or a payment keyed to the wrong bank — always surface it, never silently ignore
  the extra rows.

---

## 5. A precedent proves what SAP STORED — not what SAP will ACCEPT

Clone the matching posted document (`jivo-outgoing-payment` §3 has the six
per-vendor fields). But do not read a blank field in the precedent as permission
to leave yours blank.

> **Live trap.** All four Mart receipts were rejected:
> `[SAP -1116] (46000071) Please select Payment Mode` — a JIVO validation on the
> `U_Pymnt_Mode` UDF. Yet **14,195 posted ORCT rows have it NULL**, including the
> four keyed in the SAP client that same morning. The client path does not
> enforce it; the Service Layer path does. Two write paths, two rule sets.

So read the UDF's own valid-value list rather than copying a precedent's blank:

```bash
./hana-sql/hana-sql 'SELECT f."TableID", f."AliasID", v."FldValue" FROM "JIVO_OIL_HANADB"."CUFD" f
 JOIN "JIVO_OIL_HANADB"."UFD1" v ON v."TableID"=f."TableID" AND v."FieldID"=f."FieldID"
 WHERE f."AliasID"='"'"'Pymnt_Mode'"'"' AND f."TableID" IN ('"'"'ORCT'"'"','"'"'OVPM'"'"')'
```

`U_Pymnt_Mode` takes **NEFT / RTGS / FT** only. RTGS above ₹2 lakh, NEFT below.
Set it on every payment and every receipt.

---

## 6. Why the draft opens blank — check before you hand it over

An **on-account** payment has no `PaymentInvoices` and no `PaymentAccounts`, so
its Contents grid is empty and the SAP B1 form looks blank. The amount is in the
**Payment Means** sub-window, not the grid. That is a correct, faithful clone —
posted `OVPM 27993` has no `VPM2` and no `VPM4` rows either.

It cost an operator a confused afternoon, so **say it before they open it**:

```bash
./hana-sql/hana-sql 'SELECT d."DocEntry", d."DocType", d."TrsfrSum",
  (SELECT COUNT(*) FROM "JIVO_OIL_HANADB"."PDF4" a WHERE a."DocNum"=d."DocEntry") AS "GL_ROWS",
  (SELECT COUNT(*) FROM "JIVO_OIL_HANADB"."PDF2" i WHERE i."DocNum"=d."DocEntry") AS "INV_ROWS"
 FROM "JIVO_OIL_HANADB"."OPDF" d WHERE d."DocEntry" IN (<drafts>) ORDER BY d."DocEntry"'
```

Zero on both counts = it will open with an empty grid. Tell the operator that,
and that it matches the precedent.

Things that are **not** the cause, all checked live and all red herrings:
`OpenBal` is 0 on *every* draft including human-made ones (SAP computes it at
Add); `DataSource` is `S` for Service Layer vs `I` for client and changes
nothing.

⚠️ **`PDF2`/`PDF4`/`VPM2`/`VPM4` column names are backwards** — `"DocNum"` holds
the *payment's DocEntry*. Joining on the obvious reading returns zero rows.

### `DocNum` on a draft is meaningless — identify by `DocEntry`

A draft's `DocNum` is a provisional reservation off the series, not consumed
until Add. Live: drafts 2183, 2185 and 2186 **all** showed `826467038`, and
2191–2194 **all** showed `826246813`. Searching Payment Drafts by that number
returns several different documents. Always quote `DocEntry` to an operator.

---

## 7. Write it

```bash
cd sap-b1/cli
set -a; source <operator>.env; set +a     # the login whose entry it is
./sapb1 doctor                            # settles company + login in one line
./sapb1 draft payment incoming --dry-run --data-file line.json   # show the operator
./sapb1 draft payment incoming --yes     --data-file line.json
```

One draft per statement line, so the operator can tick the statement off against
SAP. `UserSign` is stamped at creation and can never be patched — settle the
login *before* writing. Nothing posts until a human opens **Banking → Payment
Drafts** and presses Add.

Deleting: `sapb1 delete payment-draft <DocEntry> [...]`, up to 50 at a time, and
it needs no override flag for drafts this checkout created.

---

## 8. Reconcile, and report the difference itemised

The statement's real question is whether the bank and the books agree:

```bash
./hana-sql/hana-sql 'SELECT SUM("Debit")-SUM("Credit") AS "SAP_BALANCE" FROM "JIVO_OIL_HANADB"."JDT1"
 WHERE "Account"='"'"'2201105'"'"' AND "RefDate"<='"'"'2026-08-31'"'"''
```

Then state it as a bridge, never as a bare gap — an unexplained difference is not
a finding, it is an unfinished one:

```
SAP ledger 2201105 at 31-Aug            8,57,64,570.39
add back: in SAP, not yet at the bank  +1,90,15,748.00   (3 ARORA payments)
                                       ───────────────
                                       10,47,80,318.39
statement closing                      10,49,22,908.76
still unexplained                          1,42,590.37   ← predates this statement
```

Check whether a residue predates the statement by comparing SAP's balance at the
*previous* date against the statement's opening figure. If it matches, the
residue is old and is not this statement's problem — say so.

---

## Checklist

- [ ] Statement arithmetic ties: opening + credits − debits = closing
- [ ] Statement's bank account resolved to a GL code via `OACT`
- [ ] Every narrative account number resolved too
- [ ] Counterparties checked against JIVO's own entities and own bank accounts
- [ ] Company decided; `--company` on every command
- [ ] `doctor` green for that company + login before any payload
- [ ] **Every line matched against `ORCT` + `OVPM` on amount + date + bank GL**
- [ ] Two-way diff reported: unmatched statement lines AND unmatched SAP rows
- [ ] Shape chosen per line: `rCustomer` / `rAccount` / `rSupplier`
- [ ] Transfer lines carry a `PaymentAccounts` row with `ProfitCenter` + period
- [ ] `U_Pymnt_Mode` set from `UFD1` valid values, not copied blank from precedent
- [ ] `--dry-run` shown to the operator before `--yes`
- [ ] Contents-row count checked; operator warned if a draft will open blank
- [ ] Drafts reported by `DocEntry`, never by `DocNum`
- [ ] Reconciliation reported as an itemised bridge, residue aged
