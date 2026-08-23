# JIVO SAP — Claude Desktop setup (Windows, for the Accounts team)

Ask JIVO's SAP in plain English — "Ziyaul Haque's ledger balance?", "this month's turnover?",
"open POs for customer X?" — and get live answers. **Asking is read-only: Claude can only read SAP, never change it.**
(If you ever need to put a document *into* SAP, there's a separate command you
run yourself that creates a **draft** for a human to approve — see
"Creating a draft" below. If one of those drafts turns out wrong, there's a command
to remove it too — see "Deleting a draft you created".)

Do this once per laptop (must be an office laptop that already reaches SAP):

## 1. Put the tool in place
- Create a folder `C:\jivo-sap`
- Copy `sapb1.exe` into it → `C:\jivo-sap\sapb1.exe`

## 2. Install Claude Desktop
- Download from https://claude.ai/download , install, sign in (needs a Claude account).

## 3. Connect SAP to Claude
- Open the config file (create if missing):
  `%APPDATA%\Claude\claude_desktop_config.json`  (paste `%APPDATA%\Claude\` in File Explorer)
- Paste the contents of `claude_desktop_config.json` from this kit.
- Replace `REPLACE_WITH_SAP_PASSWORD` with the SAP password.
- Save, then fully quit and reopen Claude Desktop.

## 4. Use it
- In Claude Desktop you'll see a tools icon (🔌). Ask questions like the ones in `ASK-EXAMPLES.md`.
- To switch company, just say "in Mart" / "in Beverages" (default is Oil / JIVO_OIL_HANADB).

## Companies
- `JIVO_OIL_HANADB` (Oil, default) · `JIVO_MART_HANADB` (Mart) · `JIVO_BEVERAGES_HANADB` (Beverages)

## Creating a draft (optional — only if you were asked to)

Asking Claude Desktop **cannot** change SAP; it can only read. If you need to get
a document *into* SAP, you type one command yourself in Command Prompt, and it
creates a **draft** — nothing is posted until a person adds it in SAP.

Open Command Prompt, `cd C:\jivo-sap`, then:

```
sapb1.exe draft order --data "{\"CardCode\":\"C0001\",\"DocumentLines\":[{\"ItemCode\":\"A0001\",\"Quantity\":10}]}"
```

It shows you exactly what it will send and waits:

```
About to WRITE to SAP:
  company : JIVO_OIL_HANADB
  user    : manager
  request : POST https://138.252.101.222:50000/b1s/v1/Drafts
  payload :
    {
      "DocObjectCode": "oOrders",
      "CardCode": "C0001",
      "DocumentLines": [
        {
          "ItemCode": "A0001",
          "Quantity": 10
        }
      ]
    }
Type 'yes' to send this write to JIVO_OIL_HANADB:
```

Type the whole word `yes` — just `y` does **not** count, and anything else
cancels with nothing sent. You get back:

```
Draft created in JIVO_OIL_HANADB: DocEntry 4321, DocNum 99 (oOrders).
Open SAP B1 → Document Drafts → review → Add.
```

**Then open SAP B1 → Sales (or Purchasing) → Document Drafts, find it, check it,
and press Add.** Until someone does that, the draft affects nothing — no stock,
no ledger, no customer. Other document types work the same way:
`draft invoice`, `draft purchase-order`, `draft delivery`, `draft credit-note`.

Not sure about a command? Add `--dry-run` and it prints exactly what it *would*
send and stops, without touching SAP:

```
sapb1.exe draft order --dry-run --data "{\"CardCode\":\"C0001\"}"
```

In Windows Command Prompt the quotes have to be escaped as above (`\"`). Easier
route for a long document: put the JSON in a file and use
`sapb1.exe draft order --data-file order.json`.

## Deleting a draft you created

If a draft you made with `sapb1.exe draft` is wrong, you can remove it from the same
Command Prompt. **Drafts only** — a document that has been Added in SAP is not
touchable from here, and there is no way to point this command at one.

```
sapb1.exe delete draft 54990
```

It reads the draft first and shows you what you are about to destroy — vendor,
total, invoice reference, whether it is still open — then asks:

```
Type 'yes' to DELETE 1 draft(s) from JIVO_OIL_HANADB (this cannot be undone):
```

Type the whole word `yes`, same as before. After it deletes, it reads the draft back
to confirm it is really gone and tells you so. If it says it deleted the draft but
**could not verify** it, the draft is almost certainly gone — look in Document
Drafts, and running the same command again is safe (a delete cannot delete twice).
You get the same message if the tool could not print its report — for example when
the output was piped into something that stopped reading. It stops there rather than
carrying on through the rest of your list.

A whole bad batch goes in one command (up to 50 at a time), with one confirmation:

```
sapb1.exe delete draft 54990 54991 54992
```

Add `--dry-run` to see the drafts and exactly what would be deleted **without
deleting anything**. Unlike the other commands, this one does read SAP so you can
see the real documents.

**It refuses drafts it did not create.** If a person keyed the draft in SAP B1
itself, the tool stops and says so — because deleting it means they key it again
from scratch. Same if the draft is more than a day old, has a file attached, is no
longer open, was created by a colleague, or **has gone into an approval workflow**
(someone has it in their Approval Status Report — ask them before removing it; it
still shows as open, so nothing else would have caught it). Six checks, each with a
flag that says "I know, do it anyway", and every one of them is written into the log
with your name against it. The hand-keyed one (`--not-created-here`) is deliberately awkward: one
number at a time, and you have to be there to type `yes` — it will not run from a
script. **If you are not sure, don't override it — delete it in SAP B1 instead,
or ask.** Payment drafts use `sapb1.exe delete payment-draft <number>`.

**If a draft you made a minute ago is refused as "no record that this CLI created
it",** you are not registered in this folder — the tool is writing its log somewhere
it does not read back. Run `python3 harness/bin/setup.py` once from the top of the
JIVO folder (the refusal message says so too) and it works from then on. Don't
reach for the override to get past that.

## Safety
- **Asking questions in Claude Desktop is READ-ONLY** — the tools Claude can use are all reads. Claude cannot create, change, or delete anything in SAP.
- The only way anything gets written is you personally typing `draft` / `post` / `patch` / `delete` in Command Prompt, and each of those shows the request and waits for you to type the full word `yes`. `draft` is the safe one — it needs a human to Add it in SAP.
- **The tool can only delete drafts, and only ones it made itself.** `sapb1.exe delete draft <number>` removes a draft; it refuses a draft that a person keyed in SAP B1 unless you explicitly override it, and it records what it deleted. **Nothing else can be deleted** — not an invoice, not an order, nothing that has been Added. It also deliberately refuses SAP's cancel/close/"post this draft" operations — those you do in SAP B1 yourself — and it can't undo a `post` or `patch` it did perform, or bring back a draft it deleted; only SAP can, and for a deleted draft not even SAP can.
- Every write you confirm is logged to `queries\<your-name>\sap-writes.jsonl` inside the JIVO folder, which syncs to the team — so every write by every operator ends up in one shared history. (Outside a registered folder it falls back to `C:\Users\<you>\.sapb1-writes.jsonl`, which nobody else can see.)
- A delete also keeps **what the draft held** — vendor, bill number, totals, line prices — in `C:\Users\<you>\.sapb1-delete-snapshots.jsonl` on your PC only. The shared log gets a fingerprint of it, not the contents, because that folder is public. Don't move that file into the JIVO folder.
- If a write ever ends with **"the outcome is unknown"**, do NOT run it again — check in SAP whether the document exists first, or you may end up with two.
- Keep `claude_desktop_config.json` private (it holds the SAP password). Prefer a **read-only SAP user** over `manager` — ask IT/Basis to create one; a read-only user makes the write commands fail safely too.
