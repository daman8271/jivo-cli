# Attaching the paper to a draft — `sapb1 attach` (2026-09-17)

Shared by `ap-rm-pm`, `jivo-ap-service-draft` and `jivo-ap-credit-memo`.
**Upload with `sapb1 attach`, and only with it** (C-0090, built 2026-09-17). It uploads
every file as a line of ONE `Attachments2` row, ticks **Copy to Target Document = `tYES`**
on every line, sets the Approve stamp where the book has it, reads the row back and exits
non-zero unless every line is `tYES` and every file it sent downloads back byte-identical.
The old route — `curl -X POST …/Attachments2`, then a
hand-written PATCH for the tick — is retired: an upload lands `tNO`, and a step in a recipe
is a step that gets skipped. Proven live 2026-09-17: Oil 177963 (1.8 MB + a second file,
both byte-identical on download), Mart 59373, Beverages 43331.

**Daman's rule (2026-08-24): a draft carries BOTH the operator's scan AND the base
document's file** (the GRPO's bill, the Goods Return's paper, …) — each as its own
line on the draft's OWN `Attachments2` row. Never point two documents at one
`Attachments2` row (a file added later on one then shows on both).

Upload works because hanadb now CIFS-mounts the attachment shares
(`sap-b1/attachments/MOUNT-RUNBOOK.md`, applied 2026-08-24, fstab-persistent). If a
mount ever drops, the POST fails loudly (shadow-write guard) with the old errors —
`-5002 Attachments folder not defined` / `404 Fail to get the LINUX mount point` —
and the fix is the runbook, not a retry.

```bash
R=/Users/damanpreetsingh/jivo-cli; S=<scratch dir>; H=https://127.0.0.1:15000   # bridge; or https://$SAPB1_HOST:$SAPB1_PORT
cd "$R"; set -a; source sap-b1/cli/<operator>.env; set +a                     # the login that owns the draft
```

**On a Windows operator box (Git bash), two things below bite before anything
reaches SAP — both measured on DESKTOP-EQ55Q8H, 2026-08-25:**

- **`$S` must be a Windows-visible directory**, e.g. `S=/c/Windows/Temp/attach`
  with `W='C:\Windows\Temp\attach'` for the Python calls. `mktemp -d` returns an
  MSYS path (`/tmp/tmp.XXXX`) that native Python cannot open, so every
  `python3 -c ... open("$S/...")` silently yields an empty value and the next
  curl is built with a blank AbsoluteEntry — which shows up as a puzzling 404
  on `$value`, not as a Python error. Pass the `C:\...` form to Python and the
  `/c/...` form to curl and `wc`.
- **`python3` may be the Microsoft Store stub.** Real CPython on Windows ships
  `python.exe` only, so bare `python3` falls through to
  `…\WindowsApps\python3.exe`, which prints "Python was not found" and exits.
  Fix once per box: `Copy-Item "C:\Program Files\Python312\python.exe" "C:\Program Files\Python312\python3.exe"`
  (Python312 sits ahead of WindowsApps on the Machine PATH, so `python3` then
  resolves to the real interpreter everywhere).

## 1. Upload — the operator's scan (and the base document's file) → one row

Rename first (`VENDOR-REF-DATE.pdf`) — it lands on
`\\10.10.101.52\Attachments_Oil\JIVO_OIL\Attachments` under exactly that name. SAP
auto-renames on a collision (name + ddmmyyyy + time); that is fine.

```bash
sapb1 attach "$S/VENDOR-REF-DATE.pdf" "$S/GRPO-<DocNum>-<FileName>.pdf" --company <DB> --dry-run
sapb1 attach "$S/VENDOR-REF-DATE.pdf" "$S/GRPO-<DocNum>-<FileName>.pdf" --company <DB> --yes
# → Attachments2 row N in <DB> — Copy to Target Document = tYES on all 2 line(s), read back:
#     line 1  VENDOR-REF-DATE.pdf  tYES  U_CHK2 OK
#     line 2  GRPO-<DocNum>-<FileName>.pdf  tYES  U_CHK2 OK
#   Point the document at it: "AttachmentEntry": N
```

The order of the files is the order of the lines. Add `--json` to get
`{"absoluteEntry": N, "lines": [...]}` for a script.

**What it sets, per book** (read off the row itself, not a company list):
- **Every book:** `CopyToTargetDoc = "tYES"` on every line — Daman, 2026-09-16: the file
  must follow the document when it is copied onward (GRPO → A/P, draft → posted).
- **Oil and Beverages:** `U_CHK = <size KB>`, `U_CHK2 = "OK"` where empty.
  `SBO_SP_TransactionNotification` refuses a draft pointing at a line whose `U_CHK2` is null
  (1120025). **Mart** has no such columns and would refuse the whole PATCH on an unknown
  field, so it gets the tick alone. Beverages also refuses a line over 1 MB (1120026) and a
  row over 5 MB (1120027) — at the pointer PATCH, not at the upload — so compress first.

**When it does not exit 0** — once a row exists it is never exit 5/6 ("nothing happened"):
- **Exit 8** — the row is there but not finished (a tick did not read back, a file did not
  come back byte-identical, or SAP refused a later file). The message names the fix, usually
  `sapb1 attach --row N --yes` (re-tick) or `sapb1 attach --row N <file> --yes` (add the rest).
- **Exit 7** — an answer never came back. Look first:
  `sapb1 query Attachments2 --filter "AbsoluteEntry eq N"`; then add only what is really
  missing. Never re-send blind — rows cannot be deleted.
- `--row N` reads and shows the row before you confirm, and refuses a row that does not exist.
- Two files with the same name, or a name with a line break in it, are refused before anything is sent.
- `-5002 Attachments folder not defined` / `404 Fail to get the LINUX mount point` — a CIFS
  mount on hanadb dropped: `sap-b1/attachments/MOUNT-RUNBOOK.md`, not a retry.

## 2. The base document's file — download it first (reads only)

```bash
sapb1 query PurchaseDeliveryNotes --filter "DocEntry eq <grpoEntry>" --select "DocEntry,DocNum,AttachmentEntry"   # or PurchaseReturns for a Goods Return
curl -sk -b "$S/ck" "$H/b1s/v1/Attachments2(<baseAE>)"                          # lines: FileName, FileExtension, FileSize
curl -sk -b "$S/ck" "$H/b1s/v1/Attachments2(<baseAE>)/\$value" -o "$S/GRPO-<DocNum>-<FileName>.pdf"; file "$S/GRPO-<DocNum>-<FileName>.pdf"   # must say "PDF document"
```

The session for those two GETs (never echo the password):

```bash
python3 -c 'import json,os;print(json.dumps({"CompanyDB":os.environ.get("SAPB1_COMPANYDB","JIVO_OIL_HANADB"),"UserName":os.environ["SAPB1_USER"],"Password":os.environ["SAPB1_PASSWORD"]}))' > "$S/login.json"
curl -sk -c "$S/ck" -H "Content-Type: application/json" --data-binary @"$S/login.json" "$H/b1s/v1/Login" -o "$S/loginresp.json"; rm "$S/login.json"
```

**Plain `$value` returns line 1 only.** Any other line needs the file name **with its
extension, quoted**: `…/Attachments2(N)/\$value?filename='332.pdf'` (200). Unquoted, or
without the extension, it is a 404 whose body lands in the output file — so a following
`cmp` "fails" for the wrong reason. Always check `file`.

## 3. Point the draft at the row

```bash
acc/_playbook/sap patch "Drafts(<DocEntry>)" --data '{"AttachmentEntry": N}' --dry-run
acc/_playbook/sap patch "Drafts(<DocEntry>)" --data '{"AttachmentEntry": N}' --yes      # HTTP 204
```

## 4. Verify — the only proof

`sapb1 attach` has already read every line back as `tYES` and every file back
byte-identical. What is left to prove is the pointer:

```bash
sapb1 query Drafts --filter "DocEntry eq <DocEntry>" --select "DocEntry,NumAtCard,AttachmentEntry" --json    # → N
# re-read the base document's AttachmentEntry: unchanged
curl -sk -b "$S/ck" -X POST "$H/b1s/v1/Logout" -o /dev/null; rm -f "$S/ck" "$S/loginresp.json" "$S/rb.pdf"
```

## Consequences

- `sapb1 delete draft` on a draft with `AttachmentEntry` set needs `--with-attachment`.
  Setting the pointer back to `null` first (PATCH, 204) is the cleaner route.
- **An attachment row can never be removed — orphans are permanent, and harmless.**
  Delete the draft and its `Attachments2` row survives, with the file still on the
  share. The catalog *lists* `DELETE Attachments2(id)`, so it looks available; the
  live server refuses every one (measured 2026-09-01 on Oil rows 173732/173733/173740,
  all `manager`, all unreferenced):

  ```
  DELETE /b1s/v1/Attachments2(173733) → 400 {"code": 220, "value": "Attachments2 is not allowed to remove."}
  ```

  Do not go delete the file off the CIFS share to "finish the job" either: the SAP row
  stays and would then point at a missing file, which is worse than the orphan. An
  unreferenced row costs nothing but disk.
- For a bill with no base document (fuel, expenses, services) the draft simply gets
  the scan alone — there is nothing to copy.
