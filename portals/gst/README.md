# GST portal → read-only CLI (`gst-portal`)

> ## ⛔ READ-ONLY, AND THIS ONE IS STATUTORY
>
> `gst.gov.in` is not a seller portal — it is the government's live filing system
> for JIVO Wellness Pvt Ltd. A stray click there is a statutory event, and some of
> them cannot be undone by anybody at JIVO.
>
> **Nothing in this folder generates, saves, submits, files, resets, computes,
> amends, offsets or creates a challan.** The CLI's allowlist has exactly **33
> rows** — 30 GETs and 3 POSTs (the login, plus two searches the portal only
> answers to a POST) — and a deny-by-default guard refuses anything else *before a
> socket is opened*. **Logging in is the only sanctioned side effect** — see
> [`cli/README.md`](cli/README.md) for the three layers and the tests that pin
> them.

JIVO Wellness Pvt Ltd (PAN **AACCJ4223F** — the Oil books) holds **8 GST
registrations**. This folder is the study of the portal behind them and the
read-only CLI generated from it.

| | |
|---|---|
| Portal | `services.gst.gov.in` · `return.gst.gov.in` · `payment.gst.gov.in` · `gstr2b.gst.gov.in` |
| Entity | JIVO WELLNESS PRIVATE LIMITED, PAN AACCJ4223F |
| Auth | username + password + **6-digit image captcha**, one cookie jar (`AuthToken`) across all four hosts |
| Auth cracked & proven | **2026-08-21** — 10 live logins, no OTP ever demanded |
| Deliverable | [`cli/gst-portal`](cli/README.md) — **36 commands in 12 groups**, Go + cobra, stdlib only |
| Status | **v0.1 built.** 7 of 8 registrations log in; Punjab's password is wrong (below) |

## The 8 registrations

Verified live with a headless browser on **2026-08-21, 17:00–17:25 IST**. "OK" =
the portal accepted the credentials, the dashboard loaded, and
`GET /services/api/ustatus` answered with the GSTIN in the row.

Usernames and passwords are **not printed here** — this repo is public. They live
in `portals/gst/.env` (gitignored, mode 0600) and in the private `env-vault/`.
`gst-portal auth list` shows them masked on your own machine; the password is
never rendered at all, only `present` / `MISSING`.

| # | State | GSTIN | Login (2026-08-21) | e-invoicing |
|---|---|---|---|---|
| 01 | Haryana | `06AACCJ4223F1Z0` | OK | Y |
| 02 | Rajasthan | `08AACCJ4223F1ZW` | OK | Y |
| 03 | **Punjab** | `03AACCJ4223F1Z6` | **FAILED — "Invalid Username or Password"** (tried twice, both with an accepted captcha). Needs a corrected password from Accounts. **Do not retry it.** | — |
| 04 | Delhi | `07AACCJ4223F1ZY` | OK | Y |
| 05 | Himachal Pradesh | `02AACCJ4223F1Z8` | OK | Y |
| 06 | Uttar Pradesh | `09AACCJ4223F1ZU` | OK (2nd try — the first captcha was misread) | Y |
| 07 | Maharashtra (Mumbai) | `27AACCJ4223F2ZV` | OK | Y |
| 08 | Delhi **ISD** | `07AACCJ4223F2ZX` | OK | N — an ISD files **GSTR-6**, so it has no GSTR-1/3B calendar |

All 8 GSTINs pass the check-digit test. All 7 regular registrations show GSTR-1
and GSTR-3B **Filed** for Mar-26 … Jul-26 (`filingsnapshot`). Legal name on every
login: JIVO WELLNESS PRIVATE LIMITED.

**Punjab is a lockout risk, not a bug.** The CLI refuses to try it again: the
first credential rejection is written to `rejected-<GSTIN>.json` next to the
session files, and every later `auth login` for that GSTIN stops before the POST
until a human deletes it. Repeated attempts on a wrong password are how a GST
account gets locked, and only the department can unlock one.

## What works

Live-verified against Haryana (and, for the nil-filer shapes, UP and Rajasthan)
on 2026-08-21. Full contract with request/response shapes: [`API.md`](API.md).

| Area | Commands | Endpoint family |
|---|---|---|
| Filing calendar & ARN register | `returns calendar\|periods\|status\|filed` | `filingsnapshot`, `dropdown`, `rolestatus`, `formdetails`, `efiledReturns` |
| Ledgers | `ledger cash\|credit\|challans\|liability\|liability-other` | `cashbalance`/`cashdetls`, `itcbalance`/`itcdtls`, `searcharnusngdate`, `retdtl`, `liabdetails` |
| GSTR-3B | `gstr3b summary\|autopop\|status` | `gstr3b/summary`, `getr1r3bliab`, `formdetails` |
| GSTR-2B | `gstr2b summary` | `gstr2b/getdata`, `getuserdtls` |
| GSTR-1 | `gstr1 summary\|section\|docs` | `gstr1/totalsummarycount`, `gstr1/invoice` |
| GSTR-2A | `gstr2a suppliers\|docs\|status` | `gstr2a/ctin`, `gstr2a/b2b` |
| Reconciliation | `compare --fy 2026-27` | `gstr3bvs1/getdata` — the portal's own GSTR-1-vs-3B and 2A-vs-3B tables |
| Master data | `profile`, `masters …` | `profile/detail`, `/master/*` |
| Bulk pull | `snapshot --fy 2026-27 --out <dir>` | all of the above, raw + normalised, with a manifest |

## What is deferred, and why

- **`gstr2a amendments`** — the `b2ba` endpoint has never been replayed live. The
  command exists and says so; it does not guess a contract.
- **B2CL (`5 — B2C Large`)** — no current GSTIN has a document in it, so its
  section name is inferred, not observed.
- **`totalsummarycount?sec_name=B2B`** returns `GSTN-EXEC1003` (a server-side Java
  error, reproduced 3×). Per-counterparty B2B counts are unavailable until GSTN
  fixes it; the per-`ctin` document list itself works.
- **GSTR-2B "download" (`getjson`)** — proven to be a plain GET that assembles the
  file client-side (nothing is enqueued server-side), but it is **not wired**: the
  guard blocks any path containing `download`/`dwnld`, and `getdata` returns the
  same corpus anyway. Not worth a hole in the guard.
- **MCP** — reserved, not built. Port **7710**, tools `gst_*`. Phase 4.
- **Auto-OCR for the captcha** — measured at ~50% exact per attempt
  ([`docs/captcha-ocr.md`](docs/captcha-ocr.md)) and nobody has measured what the
  portal does after N bad logins. The operator types the six digits. See the gate
  in [`HANDOFF.md`](HANDOFF.md).
- **Session idle timeout (D9)** — not measured. The CLI assumes 15 minutes of idle
  and refreshes the window on every successful call.

## What was verified, and what was not

**Verified live on 2026-08-21** — 7 of 8 logins; all 33 endpoints in the
allowlist, each replayed as a plain HTTP request with only the cookie jar (so
they do not need a browser); the header rules the WAF enforces; the figures in
the table below.

**Not verified:**

- **`go test ./...` is currently RED** — 3 failures, all stale test expectations
  rather than production bugs (`auth list --all`, a fake-portal `ustatus` stub
  with no `gstin`, a test reading the pre-login jar from the wrong path). Each is
  a one-line fix; they are itemised in [`HANDOFF.md`](HANDOFF.md). Fix them before
  trusting a green run to mean anything.
- **Nothing has been run on Windows.** `gst-portal.exe` cross-compiles and is
  committed, but the captcha-image opener (`rundll32 url.dll,FileProtocolHandler`)
  has never been executed on a Windows box. Nothing on a Mac can test it.
- **Punjab has never logged in**, so nothing downstream of it is verified.
- **The session idle timeout is a guess** (15 minutes). D9 is open.
- **No end-to-end `snapshot --all` has been run.** Single-registration snapshots
  work; the estate-wide run has not been done by hand yet.

## The files

| Path | What |
|---|---|
| [`cli/`](cli/README.md) | the CLI — Go source, tests, `gst-portal` + `gst-portal.exe` |
| [`API.md`](API.md) | the verified endpoint contract (bodies, params, error codes, WAF rules) |
| [`RECON.md`](RECON.md) | the first pass: pages, cookies, WAF behaviour, discovery items |
| [`SETUP.md`](SETUP.md) | for an Accounts operator on Windows — 10 minutes, no Go needed |
| [`HANDOFF.md`](HANDOFF.md) | state of play, open items, what to do next |
| [`ASK-EXAMPLES.md`](ASK-EXAMPLES.md) | plain-English questions → the command that answers them |
| `docs/` | house conventions, the SAP↔portal comparison spec, the OCR study |
| `discovery/` | the XHR recorder and `scrub.py` (no data in either) |
| `.env` · `.env.example` | credentials (gitignored) · the empty template |
| `captures/` · `fixtures/` | raw live captures — **gitignored**, they hold real ARNs, balances and the signatory's phone/email |

## Numbers pulled on 2026-08-21 (Haryana `06AACCJ4223F1Z0`)

Each figure names the endpoint it came from. They are a snapshot of that
afternoon, not a standing fact — re-run the command before quoting one.

| Figure | Value | Endpoint |
|---|---|---|
| Electronic credit (ITC) ledger | ₹4,33,72,582 (SGST 1,92,62,335 · CGST 1,31,74,558 · IGST 1,08,67,113 · Cess 71,937) | `returns/auth/api/itcbalance` |
| Electronic cash ledger | ₹44,201 — almost all penalty (CGST 21,791 + SGST 21,791) | `payment/auth/api/cashbalance` |
| GSTR-3B Jul-26, outward taxable | ₹22,30,98,171.32 · IGST 60,86,669.17 · CGST = SGST 49,55,618.79 | `returns/auth/api/gstr3b/summary` |
| GSTR-3B Jul-26, inward RCM | ₹87,85,090 | same |
| GSTR-2B Jul-26, B2B ITC | taxable ₹31,22,54,425.59 · IGST ₹1,78,24,074.67 | `gstr2b/auth/api/gstr2b/getdata` |
| GSTR-1 Jul-26 document counts | B2B 878 · CDNR 111 · B2CS 18 · HSN 60 · DOC 2 | `returns/auth/api/gstr1/totalsummarycount` |

⚠️ **`itcbalance.dt` is garbage** — it came back `16/02/0027`. Ignore that field;
the `itcdtls` statement dates are sane `dd/mm/yyyy`.
