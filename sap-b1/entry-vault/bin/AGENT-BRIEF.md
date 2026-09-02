# Miner brief — read this before you write a single line

You are mining **JIVO's live SAP books** to write one note in the entry vault. The
vault's job is narrow and specific: *when someone sits down tomorrow to key an
entry, this vault tells them everything they need before they start.* Not what SAP
can do — what JIVO actually does.

## The tools (run them, don't guess)

All under `sap-b1/entry-vault/bin/`, all read-only, all through the guarded
`hana-sql` binary. Run from the repo root.

```bash
# What operators actually fill in — fill rates, distinct counts, value vocabularies
python3 sap-b1/entry-vault/bin/profile.py OPCH --days 120
python3 sap-b1/entry-vault/bin/profile.py PCH1 --co OIL --days 120 --vocab-max 40

# The journal a document type posts — accounts, sides, amounts, dimensions
python3 sap-b1/entry-vault/bin/gl.py 18 --co OIL --days 365 --memo

# Where a document comes from and what it feeds — copied-from vs keyed-from-scratch,
# drafted-first ratio, approval volume
python3 sap-b1/entry-vault/bin/flow.py OPCH --co OIL --days 120

# Real finished documents, header + lines + the journal they made
python3 sap-b1/entry-vault/bin/sample.py OPCH --n 3 --co OIL
python3 sap-b1/entry-vault/bin/sample.py ODRF --n 2 --where '"ObjType"=18'

# Anything else: raw read-only SQL
./hana-sql/hana-sql -env connections/hana-office-bridge.env "SELECT ..."
```

Schemas: `JIVO_OIL_HANADB`, `JIVO_MART_HANADB`, `JIVO_BEVERAGES_HANADB`. Always
double-quote SAP's mixed-case columns: `"DocDate"`, `"CardCode"`.

**If a query fails with connection refused / timeout:** run
`bash sap-b1/entry-vault/bin/bridge.sh` and retry. A watchdog also repairs it every
20s. Never conclude "no data" from a connection error.

## Non-negotiables

1. **Every number you write must come from a query you actually ran.** Put the SQL
   in the note. A figure without its query is somebody's memory, and this vault is
   read by people who will act on it.
2. **Mark what is inferred.** Fill rates and counts are measured. "This field means
   X" is usually an inference — say so, and say what would confirm it. Use
   *measured* / *inferred* / *unverified* explicitly. A thorough explanation is not
   evidence.
3. **The corrections in `harness/corrections/` are settled truth and outrank you.**
   Read `harness/corrections/INDEX.md`. If your data seems to contradict a
   correction, that is a finding worth reporting — do not quietly overwrite it.
4. **Never write to SAP.** You have read-only tools only. No `sapb1 draft`, `post`,
   `patch` or `delete`, not even a dry run.
5. **This repo is public.** Structural and statistical knowledge is fine (field
   names, fill rates, GL codes and names, series numbers, vendor *group* names,
   traps). Do **not** paste credentials, GSTINs, bank account numbers, individual
   employees' pay, or bulk customer contact lists.
6. **`_data/` is gitignored and stays that way.** The mined corpus contains real
   production rows — a scan on 2026-08-24 found 21 GSTINs and 26 account-number-shaped
   strings in it. Read from it freely; never copy an identifier out of it into a note, and
   never commit it. `OACT` in particular carries employee bank details in
   `U_Account_Number` / `U_IFSC` / `U_Bank_Name` on ~20% of Oil accounts.

7. **Say "I don't know."** An honest gap with the query that would close it is worth
   more than a confident guess. Add it to the note's **Open questions**.

## House style

- Obsidian: link with `[[Note-Name]]`, liberally. A `[[link]]` to a note that does
  not exist yet is a to-do marker, not an error.
- Plain language first, SAP jargon second. "GRNI — the account a receipt parks the
  cost in until the bill arrives (2140001)", not "the clearing account".
- Money in INR with Indian grouping; crores for anything large.
- Tables over prose. Give the list, not the rationale.
- Front-matter on every note:

```yaml
---
type: document | foundation | flow | playbook | trap
sap_tables: [OPCH, PCH1]
objtype: 18
companies: [OIL, MART, BEV]
mined: 2026-08-24
confidence: high | medium | low
---
```

## Deliverable

Write **one file** at the path you were given, following the matching template in
`sap-b1/entry-vault/_template/`. Then return a short report: the path, the 5 most
important things you learned that were *not* obvious from SAP's own documentation,
anything that contradicts an existing correction, and your open questions.
