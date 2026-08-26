# Attaching the paper to a draft — the proven recipe (2026-08-24)

Shared by `jivo-ap-draft`, `jivo-ap-service-draft` and `jivo-ap-credit-memo`.
Every command below was run live on 2026-08-24 against drafts 55126 / 55128 / 55130.

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

## 1. Session (never echo the password)

```bash
python3 -c 'import json,os;print(json.dumps({"CompanyDB":os.environ.get("SAPB1_COMPANYDB","JIVO_OIL_HANADB"),"UserName":os.environ["SAPB1_USER"],"Password":os.environ["SAPB1_PASSWORD"]}))' > "$S/login.json"
curl -sk -c "$S/ck" -H "Content-Type: application/json" --data-binary @"$S/login.json" "$H/b1s/v1/Login" -o "$S/loginresp.json"; rm "$S/login.json"
```

## 2. The operator's scan → a new row

Rename the file first (`VENDOR-REF-DATE.pdf`) — it lands on
`\\10.10.101.52\Attachments_Oil\JIVO_OIL\Attachments` under exactly that name.

```bash
curl -sk -b "$S/ck" -X POST "$H/b1s/v1/Attachments2" -F "files=@$S/VENDOR-REF-DATE.pdf;type=application/pdf"
# → HTTP 201, {"AbsoluteEntry": N, "Attachments2_Lines": [{"LineNum": 1, "FileSize": <KB>, ...}]}
```

## 3. The base document's file(s) → extra lines on the same row

```bash
acc/_playbook/sap query PurchaseDeliveryNotes --filter "DocEntry eq <grpoEntry>" --select "DocEntry,DocNum,AttachmentEntry"   # or PurchaseReturns for a Goods Return
curl -sk -b "$S/ck" "$H/b1s/v1/Attachments2(<baseAE>)"                     # lines: FileName, FileExtension, FileSize
curl -sk -b "$S/ck" "$H/b1s/v1/Attachments2(<baseAE>)/\$value" -o "$S/GRPO-<DocNum>-<FileName>.pdf"; file "$S/GRPO-<DocNum>-<FileName>.pdf"   # must say "PDF document"
curl -sk -b "$S/ck" -X PATCH "$H/b1s/v1/Attachments2(N)" -F "files=@$S/GRPO-<DocNum>-<FileName>.pdf;type=application/pdf"
# → HTTP 204; the row now has LineNum 2
```

Rename before re-uploading so it cannot collide with the original file name on the
share. A base row with several lines needs one `$value` call per file (the SL takes a
file-name selector for that — not exercised yet; verify on the first multi-file row).

## 4. Stamp every line — JIVO guard 1120025 "Select OK in Approve Column"

`SBO_SP_TransactionNotification` refuses a draft that points at an attachment line
whose `U_CHK2` is null. Human-keyed rows carry `U_CHK = <size KB>`, `U_CHK2 = 'OK'`.

```bash
acc/_playbook/sap patch "Attachments2(N)" --data '{"Attachments2_Lines":[{"AbsoluteEntry":N,"LineNum":1,"U_CHK":<KB1>,"U_CHK2":"OK"},{"AbsoluteEntry":N,"LineNum":2,"U_CHK":<KB2>,"U_CHK2":"OK"}]}' --yes
```

## 5. Point the draft at the row

```bash
acc/_playbook/sap patch "Drafts(<DocEntry>)" --data '{"AttachmentEntry": N}' --dry-run
acc/_playbook/sap patch "Drafts(<DocEntry>)" --data '{"AttachmentEntry": N}' --yes      # HTTP 204
```

## 6. Verify — the only proof

```bash
acc/_playbook/sap query Drafts --filter "DocEntry eq <DocEntry>" --select "DocEntry,NumAtCard,AttachmentEntry" --json    # → N
curl -sk -b "$S/ck" "$H/b1s/v1/Attachments2(N)"     # every line: TargetPath = \\10.10.101.52\Attachments_Oil\JIVO_OIL\Attachments (Windows UNC → the client opens it), U_CHK2 OK
curl -sk -b "$S/ck" "$H/b1s/v1/Attachments2(N)/\$value" -o "$S/rb.pdf" -w "%{http_code}\n"; cmp "$S/rb.pdf" "$S/VENDOR-REF-DATE.pdf" && echo byte-identical
# re-read the base document's AttachmentEntry: unchanged
curl -sk -b "$S/ck" -X POST "$H/b1s/v1/Logout" -o /dev/null; rm -f "$S/ck" "$S/loginresp.json" "$S/rb.pdf"
```

## Consequences

- `sapb1 delete draft` on a draft with `AttachmentEntry` set needs `--with-attachment`.
  Setting the pointer back to `null` first (PATCH, 204) is the cleaner route.
- The physical files stay on the share even if the draft is deleted (the SL has no
  DELETE for `Attachments2`) — harmless orphans.
- For a bill with no base document (fuel, expenses, services) the draft simply gets
  the scan alone — there is nothing to copy.
