---
name: jivo-ap-draft
description: Use when an operator hands over a vendor's tax invoice (PDF, photo, scan, or typed details) and wants it entered in SAP B1 as an A/P invoice / purchase invoice / purchase bill — "make a draft of this", "enter this bill", "data entry for this invoice", "AP invoice draft". Also use when asked to check whether a vendor invoice is already in SAP, or why an A/P draft was rejected ("define the numbering series", -10, -4002, -5002 branch).
---

# A/P invoice draft from a vendor invoice (JIVO, SAP B1)

Internal skill for the jivo-cli toolkit. Everything here was learned on live data
on 2026-08-21: Frystal NINV/26-27/0826 turned out to be Neetu's existing Draft 54906;
SSY 26-27/1450 became Drafts 54937 **and** 54938 — the same document twice, under two
logins — which is exactly the duplicate this skill now prevents.

**Core principle: at JIVO the invoice is never keyed in — it is drawn from the
GRPO that the factory already made, and it may already exist. Find before you
make; read back after you make.** RULE 0 in `CLAUDE.md` governs the write itself.

**Many bills at once?** This skill is one bill at a time. For a pile of open
GRPOs — 50 at a time, reviewed in Excel before anything is sent — use
`acc batch` (see `acc/BATCH.md`). It shares these rules; the scripts here and
the batch both call `acc/apbatch`.

## The procedure

1. **Read the paper into facts.** Vendor name + GSTIN · invoice no. (exactly as
   printed → `NumAtCard`) · invoice date · **buyer name** (Jivo Wellness Pvt Ltd →
   `JIVO_OIL_HANADB`, the default; Jivo Mart → `JIVO_MART_HANADB`; Jivo Beverages →
   `JIVO_BEVERAGES_HANADB`) · buyer GSTIN (→ branch) · "Buyer's order no." (= JIVO
   PO DocNum) · item lines (qty, rate, taxable) · GST split (IGST vs CGST+SGST) ·
   round-off · grand total · **JIVO's gate stamp: G.No and date (= gate-in date)** ·
   every handwritten number (GE-2026-xxxx = gate entry; 5-digit = a Drafts
   DocEntry; 10-digit 2026xxxxxx = a GRPO DocNum).
2. **Run the pre-check** (read-only; it refuses to build if anything is off):
   ```bash
   python3 .claude/skills/jivo-ap-draft/bin/precheck.py \
     --ref "<invoice no>" --vendor "<name fragment or CardCode>" \
     --gstin <buyer GSTIN> --inv-date YYYY-MM-DD --gate-date YYYY-MM-DD \
     --qty <pieces> --total <grand total> --po <buyer's order no> [--grpo <DocNum>] \
     --item "<item description as printed>" \
     --note "GE-2026-xxxx | Veh … | e-Way … | <approvals written on the paper>" \
     [--company JIVO_MART_HANADB] [--env <operator>.env] --out /tmp/ap-draft.json
   ```
   - **Exit 2 = already in SAP.** Run the `readback.py` lines it prints, one per
     existing draft, and give the operator the paper-vs-record comparison and the
     draft number(s). Do not draft again. Two drafts on one invoice → a human
     removes the extra in the client.
   - **Exit 3** = it could not identify vendor / GRPO / branch / series — fix the
     inputs; never hand-edit facts it couldn't find.
   - **Exit 4** = SAP unreachable. Not a data answer. It prints the bridge fix.
3. **Show the operator** the dry-run, from `sap-b1/cli` with the operator's env
   sourced (`set -a; source <operator>.env; set +a`):
   `./sapb1 draft purchase-invoice --dry-run --data-file /tmp/ap-draft.json`.
   Wait for their go.
4. **Send** the same command with `--yes`. Note the DocEntry SAP returns.
5. **Read it back and compare**:
   `python3 .claude/skills/jivo-ap-draft/bin/readback.py <DocEntry> --expect-total … --expect-qty …`
   Report its flags as gaps, not as success. Give the operator the draft number
   and the click-path it prints.

## Rules the scripts encode (know them anyway)

| Field | Rule | Why |
|---|---|---|
| `DocDate` | **gate-in date** (JIVO stamp / GRPO date) | Daman's rule, harness C-0017 |
| `TaxDate` | vendor's invoice date | C-0017 |
| `DocDueDate` | omit — SAP applies the vendor's terms | it computes from doc date |
| `BPL_IDAssignedToInvoice` | branch whose `FederalTaxID` = buyer GSTIN; one GSTIN sits on several Oil branches (2 FACTORY, 5 HARYANA SALES, 8 …) — **the GRPO's branch decides** | -5002 without it |
| `Series` + `DocumentSubType` | the month's GST-tax-invoice series for that branch, e.g. Oil FACTORY Aug-26 = **3684 + `bod_GSTTaxInvoice`** | without both: `-10`/`-4002 define the numbering series` (C-0018) |
| `DocumentLines` | one per **open GRPO line**: `BaseType 20, BaseEntry, BaseLine`, qty = line's open qty | stock is not received twice; a 5,870-pc invoice can be two lines because the GRPO merged two POs — say so to the operator |
| `WTLiable` | **Ask the operator — precedent beats the master flag.** precheck defaults to `tYES` when the BP is TDS-liable, but show them the vendor's last 3 posted invoices first: if those are `tNO`/TDS 0, that is how JIVO books this vendor. TPAC 2026-08-22: master said 194Q 0.1% (₹214), last 3 all `tNO` → operator chose no TDS. Always check `WTAmount` on read-back | API drafts come out TDS 0 (C-0018); and once overruled, readback's "TDS is 0 but vendor is TDS-liable" flag is a false positive |
| `Comments` | `Based On Goods Receipt PO <n> \| PO <n> \| GATE ENTRY NO <n> \| <paper notes>` ≤ 254 chars | how Accounts searches |

## Attachments — the draft comes out with none, and that is fixable

An API-created A/P draft always has `AttachmentEntry: null`. A human-keyed one never does.
The B1 client copies the GRPO's attachment forward on copy-to-target; the Service Layer does not.

**You do not need to upload anything — the bill is already in SAP.** The factory attaches the
scanned vendor invoice to the GRPO at gate-in (623/623 GRPO-based Oil A/P drafts since 1 Jul 2026
had one). So the file exists and is registered; only the pointer is missing.

```bash
# find the bill the GRPO already carries
acc/_playbook/sap query PurchaseDeliveryNotes --filter "DocEntry eq <grpoEntry>" --select "AttachmentEntry"
acc/_playbook/sap query Attachments2 --filter "AbsoluteEntry eq <n>"      # name, size, path
# point the draft at it (dry-run first, then the operator's go)
acc/_playbook/sap patch "Drafts(<docEntry>)" --data '{"AttachmentEntry": <n>}' --dry-run
```

✅ **Proven 2026-08-24 on draft 54983 / GRPO 25714 (Oil, USER36):** `PATCH Drafts(N) {"AttachmentEntry": <n>}`
→ HTTP 204, draft reads back with the pointer, GRPO unchanged. Setting it back to `null` also
returns 204 (rollback works), and re-setting restores it. Still read back both the draft *and* the
GRPO afterwards — cheap, and it is the only proof the pointer landed. Not yet observed: whether the
borrowed pointer survives a human pressing Add on the draft (check the first converted one).

⚠ **Sharp edge:** draft and GRPO then share one `Attachments2` row. A file added later on the
draft's Attachments tab lands on that shared record and also shows on the GRPO.

**Do not try to upload the PDF through the Service Layer. It cannot, by design of this install.**
`POST /Attachments2` → `-5002 Attachments folder not defined`; `GET Attachments2(N)/$value` → 404
`Fail to get the LINUX mount point for AttachmentsFolderPath`. The SL runs on Linux; the attachment
folder is a Windows UNC. A CIFS mount of the share fixes the **download** path only — verified by
disassembly: `_FILE_GetMountPoint` has two call sites, both on download, and `SLFile::isFullPath`
accepts only a leading `/` or `smb:`. Mounting will not make uploads work. See SAP Note 3003664 and
KBA 3631883. For a bill with **no GRPO** (imprest, expenses, services) a person must attach it in
the client — there is no bill to borrow.

## Hard stops

- **Exit 2 from precheck means stop.** Accounts (Neetu/USER07 and others) key
  drafts in the SAP client the same afternoon the paper arrives; handwritten
  numbers on the scan are usually that draft. It checks by vendor ref **and** by
  GRPO, so a typo'd ref does not hide a duplicate. A second draft on the same
  GRPO is a duplicate.
- **"Put it in approval / make it pending" is a client action, not a CLI one.**
  The approval request is created when a person presses **Add** on the draft.
  `POST /PurchaseInvoices` to let the approval template intercept is refused by
  the server (`-5002 Attachments folder not defined [131-102]`) and, if it ever
  weren't, would post a live invoice. Never try it; say "open the draft → WTax
  Liable → Add".
- **A draft is owned by the login that made it.** The operator's Document Drafts
  Report defaults to their own user; a draft made as `manager` is invisible to
  them until they set User = manager/All. Use their per-operator env file
  (`sap-b1/cli/<name>.env`, 0600, gitignored) so it lands in their own list.
  precheck prints the login it will use.
- **Exit 7 from `sapb1 draft`** = sent, outcome unknown → run readback / query
  Drafts by `NumAtCard`; do not re-send.
- **SAP unreachable / timeouts** (`cannot reach SAP Service Layer`): the box only
  admits the office IP. `bash connections/sap-home-bridge.sh`, then
  `export SAPB1_HOST=127.0.0.1 SAPB1_PORT=15000 SAPB1_TIMEOUT=180 HANA_ENV=connections/hana-office-bridge.env`.
  Exported values beat `--env` files, so the operator's env still picks the login.
  `sap-office-bridge.sh` needs an office PC parked on the VPS and is often down;
  the home bridge is the durable one.

## If the draft is wrong: delete it

A draft this skill made is a draft this CLI made, so `sapb1 delete draft` will take
it without an override. Same env file as the draft (the login that owns it), and
show the operator the dry-run first — it reads the draft back, so they see the
vendor, the total and `NumAtCard` before they agree.

```bash
./sapb1 delete draft <DocEntry> --dry-run     # reads SAP, sends no DELETE
./sapb1 delete draft <DocEntry>               # then type yes at the prompt
```

- **Same day, no overrides needed.** Past 24 hours it asks for `--older-than <dur>`,
  and by then the answer is usually "leave it, Accounts will handle it in the
  client" — a day-old A/P draft may already be in someone's Document Drafts list.
- **If you patched `AttachmentEntry` onto it** (the GRPO's bill, above), the delete
  refuses until `--with-attachment` — the guard cannot tell a borrowed pointer from
  paper somebody attached. Setting the field back to `null` first is the cleaner
  route, and it keeps the question of the shared `Attachments2` row out of it; read
  the GRPO back either way and confirm it still carries its bill.
- **Once it has been sent for approval, it is not yours either.** A fresh draft reads
  `AuthorizationStatus dasWithout`; the moment Accounts presses **Add** it routes via
  "USER03 AP" and the row goes `dasPending` while still reading `bost_Open`, so the
  delete refuses it (`--in-approval`) and no other guard would have. Bhawani/USER03
  is looking at it — ask, don't override.
- **A duplicate keyed by a person is not yours to remove.** Precheck exit 2 means
  Neetu (or another operator) made that draft in the client; the delete will refuse
  it, and that refusal is correct. Tell the operator which two drafts exist and let
  them remove the extra in the client — unless they explicitly say to remove that
  DocEntry, which is the only thing `--not-created-here` means.
- **Never loop it.** `--not-created-here` takes one DocEntry, needs a person at the
  prompt, and refuses `--yes`. Every delete is logged under the operator's name; the
  snapshot of what was there stays on that machine and only its sha256 goes into the
  shared log, because this repo is public.

## Reference

`reference/series-and-errors.md` — how Oil numbers A/P invoices (branch × month ×
sub-type), the Aug-26 series table, SAP error codes seen and their fixes, and the
SAP-client click-paths for drafts and approvals.
