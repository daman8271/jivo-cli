---
title: "GST portal cracked and turned into a read-only CLI"
created: 2026-08-21
project: jivo-cli
type: worklog
tags: [gst, portals, gst-portal, read-only, accounts, reconciliation]
---

# GST portal → `gst-portal`, 2026-08-21

Studied `gst.gov.in` live, captured the API contract, and built a read-only Go
CLI over it for JIVO Wellness's **8 GST registrations** (PAN AACCJ4223F — the Oil
books). One day, from nothing to a working binary. Uncommitted at time of writing.

## Result

**33 endpoints proven live on 4 hosts · 36 commands in 12 groups · 7 of 8 logins
verified · 3 POSTs in the whole binary, one of which is the login.**

Nothing was filed, generated, saved, submitted, reset, computed or paid. This is
a statutory portal; the guard refuses those paths before a socket opens.

## What was done

1. **Recon** (`RECON.md`) — the AngularJS SPA, the four hosts, the F5/ASM WAF, the
   cookie set, the page map.
2. **Logins verified** for all 8 registrations with a headless browser,
   17:00–17:25 IST. 7 OK, Punjab refused (below). No OTP was ever demanded, across
   10 successful logins.
3. **API contract captured** (`API.md`) — request bodies, query params, response
   shapes, error codes, and the header rules a plain HTTP client needs. Everything
   marked **replayed** was re-issued as a bare `fetch` with only the cookie jar,
   proving it does not need a browser.
4. **CLI built** (`portals/gst/cli/`) — cobra + stdlib, deny-by-default allowlist,
   3-layer guard, per-GSTIN session jars, two-step captcha login, `snapshot`.
5. **Docs written** — `README.md`, `cli/README.md`, `SETUP.md` (Windows operator),
   `HANDOFF.md`, `ASK-EXAMPLES.md`; root `README.md` grid row and `NEW-DEVICE.md`
   line; harness hook + `TOOL_ALIASES` alias `gst`.

## Figures pulled, with the endpoint each came from

Haryana `06AACCJ4223F1Z0`, 2026-08-21 afternoon. These are that day's snapshot,
not standing facts.

| Figure | Value | Endpoint |
|---|---|---|
| Electronic credit (ITC) ledger | **₹4,33,72,582** — SGST 1,92,62,335 · CGST 1,31,74,558 · IGST 1,08,67,113 · cess 71,937 | `return…/returns/auth/api/itcbalance` |
| Electronic cash ledger | **₹44,201**, almost all penalty (CGST 21,791 + SGST 21,791 + fee 1,200 + interest 7) | `payment…/payment/auth/api/cashbalance` |
| GSTR-3B Jul-26 outward taxable | **₹22,30,98,171.32** · IGST 60,86,669.17 · CGST = SGST 49,55,618.79 | `return…/returns/auth/api/gstr3b/summary` |
| GSTR-3B Jul-26 inward RCM | **₹87,85,090** (IGST 3,64,515 · CGST = SGST 38,605) | same |
| GSTR-2B Jul-26 B2B ITC | taxable **₹31,22,54,425.59** · IGST 1,78,24,074.67 · CGST = SGST 13,54,491.23 | `gstr2b…/gstr2b/auth/api/gstr2b/getdata` |
| GSTR-1 Jul-26 document counts | B2B **878** · CDNR 111 · B2CS 18 · HSN 60 · DOC 2 | `return…/returns/auth/api/gstr1/totalsummarycount` |
| GSTR-2A Jul-26 suppliers | **353** in one response, no paging params | `return…/returns/auth/api/gstr2a/ctin` |
| Filing status | GSTR-1 + GSTR-3B **Filed** Mar-26 … Jul-26 on all 7 regular registrations | `services…/returns/auth/api/filingsnapshot` |

## Decisions

- **No auto-OCR for the captcha.** Measured ~50% exact per attempt, ~83–88% per
  digit (`docs/captcha-ocr.md`, n=4), and it degrades further on the real 182×50
  input. At that rate auto-OCR burns roughly one failed `authenticate` POST per
  login on a statutory account whose lockout behaviour nobody has measured. The
  operator types six digits; a re-roll (`r`) is free and is not a login attempt.
- **One login POST per process,** as a constant, not a flag. And a **credential
  rejection is recorded to disk** — every later `auth login` for that GSTIN
  refuses before the POST until a human deletes the record. That is what turns
  "never retry a wrong password" from advice into a mechanism.
- **`generate` / `download` stay unwired even where they are provably harmless.**
  GSTR-2B's "GENERATE JSON FILE TO DOWNLOAD" was traced into the app bundle and
  replayed: it is a plain `GET .../getjson` that assembles the file client-side,
  nothing is enqueued. It is still not wired — `getdata` returns the same corpus,
  and a hole in the guard costs more than the convenience is worth.
- **Login is never exposed over MCP.** MCP (port 7710) stays read-only forever. An
  agent that can log in can end an accountant's browser session mid-filing and, on
  a wrong password, walk an account toward a lockout.
- **`snapshot` is the primary operator verb.** A login costs a hand-typed captcha
  and the session is short, so the useful shape is one login → pull the whole
  financial year. It never prompts and never aborts on one registration.
- **`--all` is not a global flag.** Only `doctor`, `auth status` and `snapshot`
  can act on more than one registration. A flag that three commands honour and
  eleven reject is a flag that lies.
- **Snapshot output refuses to land inside a git checkout.** This repo is public
  and `.gitignore` only covers the literal `out/`.
- **Usernames are not printed in any tracked file.** `LOGIN-STATUS.md` is
  gitignored for exactly this reason; the public `README.md` carries the
  registration table with GSTINs (public on every invoice) and no credentials.

## Traps found, worth remembering

- **Never fetch `/services/login` with a live session.** It replaces `AuthToken`
  with a pre-auth placeholder and logs you straight out. Three logins were burned
  discovering this.
- **The WAF keys on Referer and User-Agent, not on being a browser.** A plain Go
  client with the cookie jar reaches every JSON API. But `services.gst.gov.in`
  **TCP-resets a branded desktop-Chrome UA** (reproduced 6×) and ASM-rejects a
  bare `Mozilla/5.0`; `return`/`payment`/`gstr2b` **302 to `accessdenied`** without
  their own host's dashboard Referer. An `accessdenied` is a header bug, not an
  expired session — re-logging in is the wrong reflex.
- **`filingsnapshot` only answers on the `services.` host.** The identical path on
  `return.` is an ASM block for a plain client.
- **`itcbalance.dt` is garbage** — `16/02/0027`. The `itcdtls` statement dates are
  fine.
- **`efiledReturns` wants the literal word** `Monthly`/`Quarterly`/`Annual`/`Half
  Yearly` in `rfp`. `"M"` returns `RET11403 Invalid API Request`.
- **The GST portal is one session per username.** A CLI login ends whoever is
  logged in as that user in a browser, possibly mid-filing.
- **The ISD registration files GSTR-6**, not GSTR-1/3B — the form list has to come
  from `ustatus`, not be hardcoded.
- **`totalsummarycount?sec_name=B2B` returns `GSTN-EXEC1003`** — a server-side
  error on GSTN's side, reproduced 3×. Not us.

## Open items

- **Punjab (`03AACCJ4223F1Z6`) has a wrong password.** Refused twice on 2026-08-21,
  both times with a captcha the portal had accepted. **Accounts task:** get a
  corrected password. Do not retry it by hand — that is how an account gets locked,
  and only the department can unlock one.
- **Test suite is red: 3 failures, all stale test expectations**, none a production
  bug (`auth list --all`, a fake-portal `ustatus` stub with no `gstin`, and a test
  looking for the pre-login jar at the wrong path). Detailed in `HANDOFF.md`.
- **D9 — the session idle timeout is unmeasured.** 15 minutes is a conservative
  guess, refreshed on every successful call.
- **D1b** — the credential-rejection `errorCode` is unknown (only the page text was
  seen). Needs a deliberately wrong password, never on a live JIVO credential.
- **The Windows captcha-open path has never been executed on Windows.**
  `rundll32 url.dll,FileProtocolHandler`, chosen over `cmd /c start` because cmd.exe
  re-parses `& | ^ >` before dequoting. Needs a walk-through on VICTUS 23001.
- **`docs/comparison-spec.md` has no consumer yet.** The portal↔SAP reconciliation
  script is unwritten — that is the actual point of this CLI.
- **The GST passwords should be rotated.** They sat in `env-vault/all-env.txt`,
  which was publicly readable (2026-08-05).
- **MCP is not built.** Port 7710 reserved, tools `gst_*`, read-only surface only.

## Next

Fix the three stale tests → run `snapshot --all --fy 2026-27` once by hand →
write the SAP reconciliation against `docs/comparison-spec.md` → then MCP.
