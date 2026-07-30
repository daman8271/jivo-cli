# JIVO SAP — Claude Desktop setup (Windows, for the Accounts team)

Ask JIVO's SAP in plain English — "Ziyaul Haque's ledger balance?", "this month's turnover?",
"open POs for customer X?" — and get live answers. **Asking is read-only: Claude can only read SAP, never change it.**
(If you ever need to put a document *into* SAP, there's a separate command you
run yourself that creates a **draft** for a human to approve — see
"Creating a draft" below.)

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
  request : POST https://103.89.45.192:50000/b1s/v1/Drafts
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

## Safety
- **Asking questions in Claude Desktop is READ-ONLY** — the tools Claude can use are all reads. Claude cannot create, change, or delete anything in SAP.
- The only way anything gets written is you personally typing `draft` / `post` / `patch` in Command Prompt, and each of those shows the request and waits for you to type the full word `yes`. `draft` is the safe one — it needs a human to Add it in SAP.
- **The tool cannot delete or cancel anything.** It has no delete command, and it deliberately refuses SAP's cancel/close/"post this draft" operations — those you do in SAP B1 yourself. It also can't undo a `post` or `patch` it did perform; only SAP can.
- Every write you confirm is logged to `C:\Users\<you>\.sapb1-writes.jsonl` so it can always be traced.
- If a write ever ends with **"the outcome is unknown"**, do NOT run it again — check in SAP whether the document exists first, or you may end up with two.
- Keep `claude_desktop_config.json` private (it holds the SAP password). Prefer a **read-only SAP user** over `manager` — ask IT/Basis to create one; a read-only user makes the write commands fail safely too.
