I have what I need. Three findings from the reads change the plan relative to the brief, so I'll state them first, then the plan.

# GST portal CLI — implementation plan (v0.1)

## 0. What I found that the brief didn't say

1. **Part of Phase 2 has already been executed.** `/Users/damanpreetsingh/jivo-cli/portals/gst/fixtures/` holds 16 live captures made via `gst-prep.sh` + an injected XHR recorder (format `{m,u,h,req,st,res}`). They settle: **D4** (`POST /returns/auth/api/efiledReturns`, body `{fy,rfp,qtr,mth,rtntp}`; response array `[{rtntype,fy,taxp,arn,dof,mof,filedBy,dg}]`; `rtntp:null` → `RET13510`), **D5 cash+credit** (`GET /payment/auth/api/cashdetls?fdate=dd/mm/yyyy&tdate=…`, `GET /returns/auth/api/itcdtls?fdate=&tdate=` — full `tr[]` shapes with `ref_no`, `tr_typ`, `ret_period`, per-head `*TaxAmt`/`*TaxBal`), and **D8 partially** (GSTR-3B summary body, the auto-populated "r1r3bliab" body, `formdetails` with `arn/fil_dt/status`, GSTR-2B `userdtls`). Five fixtures (`gstr3b-*`, `formdetails-*`, `gstr2b-*`) are bare bodies with **no URL recorded**, `profile/liability/comparison.rec.json` are empty, and every capture is from **UP (09…), a nil filer** — all amounts are zero, `itc_elg`/`inward_sup` are absent. Discovery below is re-scoped to exactly the gaps.
2. **Those fixtures contain live business data in a public repo**: real ARNs, ledger balances, and the filer's name. `portals/gst/.gitignore` ignores `captures/` but not `fixtures/`. I could not run git to see if they are tracked; either way Step 0 moves them to `captures/` (ignored) and the tests use scrubbed copies.
3. **Punjab (03…) login fails** with "Invalid Username or Password" (`LOGIN-STATUS.md:9`). That is a credential problem for Accounts, not a CLI item; v0.1 acceptance is 7/8 unless the password is fixed.

Two more facts that shape decisions: the OCR study measured **~50% exact per attempt** on n=4 with a fragile pipeline, and nobody has confirmed whether a wrong captcha counts toward the GST lockout counter. And the `dt` field on `itcbalance` is garbage ("16/02/0027", `RECON.md:43`) while `itcdtls` dates are sane `dd/mm/yyyy`.

## 1. Decisions (recommendation first, alternatives after)

| Decision | Recommendation | Why / what I rejected |
|---|---|---|
| Language, packaging | Go 1.25+, cobra, stdlib only, flat `package main` in `portals/gst/cli/`, binary `gst-portal` + `gst-portal.exe` both committed | House convention (zepto/blinkit/dsr all do this; `.exe` tracked because office PCs have no Go). Rejected Python: the one place Python helps (OCR) is optional and stays external. |
| Session model | One persisted cookie jar **per GSTIN** at `os.UserConfigDir()/gst-portal/session-<GSTIN>.json` (0700 dir, 0600 file); `{gstin, username, saved_at, cookies:[{name,value,domain,path,expires}]}`; loaded into `cookiejar` for all three hosts; reused until a 401/403/accessdenied redirect or `saved_at + lifetime` (lifetime from D9) | Go's `cookiejar` doesn't persist and `Jar.Cookies()` drops attributes, so the client records every `resp.Cookies()` into its own map alongside the jar. TS* (F5) cookies are persisted and resent too — that's what the WAF keys on (`RECON.md:18-21`). |
| Login | Username/password from `.env`; **captcha typed by the operator by default**; OCR is an opt-in pluggable solver (`--captcha auto` / `GST_CAPTCHA_CMD`), Phase 3; **exactly one `POST /services/authenticate` per GSTIN per process**; OTP detection → clear message, exit 4, never loop | Inverts the brief's "OCR-with-retry then prompt". At 50% exact, auto-OCR burns one failed authenticate per login on average and lockout semantics are unknown (D1). The operator path is faster today and every typed answer becomes a labelled sample for a later CNN. The solver interface costs nothing and keeps the door open. |
| Multi-GSTIN | Registry from `GST_NN_*` blocks; select with `--gstin 06AACCJ4223F1Z0`, `--state haryana` (case-insensitive, also accepts `hr`/`06`/`delhi-isd`), or `--all` (sequential); no selector and no `GST_DEFAULT` → exit 2 listing the 8 | blinkit's fixed-map "unknown value is a clear error" pattern. Sequential because each cold login is a captcha. |
| Command output | stdout = pretty JSON (raw portal body) by default; `--json` identical (kept for uniformity); `--agent` = `{ok,command,endpoint,gstin,count,data\|error}`; one human INR summary line on **stderr** (`logf`) for ledger/calendar commands, suppressed under `--agent` | House (`zepto/cli/output.go`). Adds `gstin` to the envelope because every call is per-registration. |
| Read-only guard | **Deny-by-default exact allowlist** (`endpoints.go` table) + `forbidden()` before any socket + no mutating code path + an **AST test** over the whole package + a **string-literal test** (any literal starting `/services/ /returns/ /payment/ /master/` outside the table fails) + POST body-key allowlist | Amazon's allowlist model, strengthened. GST's paths don't carry verbs (`efiledReturns`, `cashdetls`), so verb-scanning alone is insufficient — the allowlist is the real guarantee. |
| Sanctioned side effect | The **only** POSTs in the table: `/services/authenticate` (login) and `/returns/auth/api/efiledReturns` (read-shaped, body keys pinned). "Generate-then-download" (GSTR-1/2B zip) is **excluded from v0.1**; view APIs only | RULE 0 and the blinkit/zepto `--export` precedent; decide in Phase 3 once D8 shows whether "generate" enqueues server-side work. |
| Exit codes | 0 ok, 1 generic, 2 usage, 3 config, 4 auth (incl. OTP, captcha refused, GSTIN mismatch), 5 guard/network ("nothing was sent"), 6 portal API error; typed errors + `exitCodeFor(err)` in `main.go` | sapb1 table (`sap-b1/cli/internal/cli/exitcode.go:10-20`). No 7: this CLI never writes. |
| Empty-result codes | `RET13510` (no record), `LG9221` (no data), `GTR2B-002` (2B not generated) → **ok, `data: null`, `count: 0`**, exit 0, with the portal message in `note` | These are answers, not failures; treating them as exit 6 would make `snapshot --all` abort on nil filers (RJ/UP/MH). |
| MCP | **Phase 4, out of v0.1.** Reserved: tools `gst_*`, port **7710** (verified free in `mcp-gateway/internal/gateway/config.go:111-139`), `Prefix=StripPrefix="gst_"` | Keeps v0.1 small; gateway rule says no over-privileged backend until the guard is proven. |
| Snapshot | `gst-portal snapshot --all --fy 2026-27 --out <dir>` writes the comparison spec's envelope as `.jsonl` + raw JSON + `manifest.json`; `out/` gitignored | v0.1 normalises what the captured shapes support (FILING, LEDGER_CASH, LEDGER_CREDIT, GSTR3B tables). GSTR-1/2B/2A document normalisers wait for D8 (Phase 3); raw bodies are still saved so no re-login is needed later. |

**Alternatives considered for the session model**: (b) consume a browser-minted session only (`auth import` from `$B cookies`) — kept as a secondary command for agents/dev, not the operator path, because Accounts PCs have no cookie exporter. (c) Playwright-in-Go — rejected: a Chromium dependency on office PCs for a JSON API.

**Assumptions I am making** (each named so Forge can check): the `AuthToken` cookie is opaque (no client-side expiry to decode) until D9 says otherwise; the authenticate body is plain JSON with no client-side encryption (D1 decides — if the password is RSA-encrypted in the browser, Step 6 grows by a `crypto/rsa` step and needs the public key capture); the APIs under `return.` and `payment.` work from a plain client once cookies + Referer are right (D3 decides; if a per-host HTML "warm-up" GET is required, `client.warm(host)` does it once per session).

## 2. Module layout

```
/Users/damanpreetsingh/jivo-cli/portals/gst/
  README.md  HANDOFF.md  ASK-EXAMPLES.md  SETUP.md        (docs, Step 9)
  RECON.md                                                 (exists; extended by Phase 2)
  .env  .env.example  .gitignore                           (exist; add out/ captcha-labels/ fixtures-raw rule)
  captures/            gitignored — raw live captures (moved from fixtures/) + D-item recordings
  discovery/recorder.js  discovery/scrub.py                (tracked; no data)
  cli/
    go.mod main.go root.go registry.go exitcode.go
    config.go        Registration{Idx,State,GSTIN,User,Pass}, loadRegistrations, selectRegistrations(flags)
    endpoints.go     hostServices/hostReturn/hostPayment consts; type Endpoint{Name,Method,Host,Path,Query,Body,Referer}; var endpoints []Endpoint; lookup(name)
    guard.go         forbidden(method, host, path string, query, body []string) error; sessionMutatingPaths
    session.go       type session; sessionPath(gstin); load/save; applyTo(jar)
    client.go        type Client; newClient(cfg, reg); doRead(ep Endpoint, q url.Values, body []byte) (json.RawMessage, error); classify(resp)
    captcha.go       type captchaSolver interface{ Solve(png []byte) (string, error) }; promptSolver; execSolver
    login.go         (c *Client) login() error — the single sanctioned non-read; ensureSession(); detectOTP()
    output.go        App{JSON,Agent,Sel}, emit/emitError/logf, inr()/groupIndian(), bestEffortCount, emptyCodes
    dates.go         period MMYYYY parse/format, fy "2026-27" → months, ddmmyyyy ↔ ISO, IST
    doctor.go        cmd_auth.go cmd_returns.go cmd_ledger.go cmd_gstr3b.go cmd_gstr2b.go
    cmd_gstr1.go cmd_gstr2a.go cmd_compare.go cmd_profile.go cmd_masters.go   (deferred leaves print "capture live first")
    normalise.go     envelope builder + per-form normalisers (spec §3–§4)
    snapshot.go      iterate registrations, write out/<gstin>/…, manifest
    wired-reads.tsv  tracked: method\thost\tpath\tcommand — the guard-coverage truth
    testdata/        scrubbed, shape-only fixtures + golden jsonl
    *_test.go        see §5
    gst-portal  gst-portal.exe   (committed)
    README.md
```

Contracts that matter:

- `Endpoint.Query`/`Endpoint.Body` are the **only** keys the client will send; unknown key → guard error (exit 5). This is what stops a future "helpful" `action=submit`.
- `doRead` is the single network path. `login()` is the only other caller of `http.NewRequest`, and the AST test pins both to `client.go`/`login.go`.
- Every emitted record is the spec's envelope: `{src:"gst-portal", gstin, state_code, period, fy, form, section, record_kind, pulled_at, filing|null, portal_ref:{endpoint, raw_id}}` with amounts as numbers (2 dp), dates ISO, `taxable_value,igst,cgst,sgst,cess` keys.

## 3. Command tree v0.1

| Command | Endpoint (allowlist row) | Status |
|---|---|---|
| `doctor [--offline]` | config → session → `GET services /services/api/ustatus` | wired |
| `auth list` | none (prints 8 registrations, creds masked `s[:4]+"…"+s[-4:]`) | wired |
| `auth login` | `POST services /services/authenticate` then `ustatus` must return the selected GSTIN | wired after D1 |
| `auth status` / `auth whoami` | session file age / `ustatus` | wired |
| `auth import <cookies.json>` | none (Playwright-style `[{name,value,domain}]`, as `$B cookies` emits) | wired |
| `returns calendar` | `GET services /returns/auth/api/filingsnapshot` | wired |
| `returns periods` | `GET return /returns/auth/api/dropdown` | wired |
| `returns status --period 072026` | `GET return /returns/auth/api/rolestatus?rtn_prd=` | wired |
| `returns filed --fy 2026-27 [--form GSTR1] [--freq Monthly]` | `POST return /returns/auth/api/efiledReturns` body keys `{fy,rfp,qtr,mth,rtntp}` | wired after D4 confirms the working body |
| `ledger cash [--from --to]` | `GET payment /payment/auth/api/cashbalance`; with range `GET payment /payment/auth/api/cashdetls?fdate=&tdate=` | wired |
| `ledger credit [--from --to]` | `GET return /returns/auth/api/itcbalance`; with range `GET return /returns/auth/api/itcdtls?fdate=&tdate=` | wired |
| `ledger liability --from --to` | D5 | deferred |
| `ledger challans --from --to` | `GET payment /payment/auth/api/searcharnusngdate?fromdate=&todate=` | wired (shape with data pending D5) |
| `gstr3b summary --period` / `status --period` / `autopop --period` | D8 (bodies captured, URLs not) | wired after D8 |
| `gstr2b summary --period` | D8 (`getdata`/`userdtls` URLs) | wired after D8 |
| `gstr1 summary --period`, `gstr2a summary --period` | D8 | deferred |
| `compare --period` | D7 | deferred |
| `profile` | D6 | deferred |
| `masters forms\|fy\|quarters\|states` | `GET return /master/gstrs/A`, `/master/fy/<fy>`, `/master/qtrs/<fy>`, `/master/allstates` | wired |
| `snapshot --all --fy 2026-27 [--out DIR]` | composes the above | wired |

Global flags: `--gstin`, `--state`, `--all`, `--json`, `--agent`, `--period MMYYYY` (where relevant), `--from/--to YYYY-MM-DD` (inclusive/exclusive, IST; converted to the portal's `dd/mm/yyyy`).

## 4. Phase 2 — discovery, sequential, one browse session

Executor: one agent, `$B=~/.claude/skills/gstack/browse/dist/browse`. Prep per GSTIN with the existing `gst-prep.sh <NN>` (logout → login page → fill creds → captcha PNG), then the agent reads the PNG, `$B fill "#captcha" NNNNNN`, `$B press Enter`, `$B wait --networkidle`. Use **Haryana (01)** for everything with amounts; UP (06) only for the one deliberately-wrong-captcha test. Every capture goes to `/Users/damanpreetsingh/jivo-cli/portals/gst/captures/` (gitignored); only shapes and rules go into `RECON.md`.

Recorder: save this once as `portals/gst/discovery/recorder.js` (tracked, no data) and run `$B eval portals/gst/discovery/recorder.js` **after every full navigation** (SPA hops between the three hosts are full loads and kill the hook): wrap `XMLHttpRequest.prototype.open/setRequestHeader/send` and `window.fetch`, push `{m,u,h,req,st,res,t}` to `window.__rec`; dump with `$B js "JSON.stringify(window.__rec)"` > file. Cross-check with `$B network` (URL/method/status only).

| Item | What to capture | How (browse) | Save to |
|---|---|---|---|
| **D1** login body | Inject recorder on `/services/login` *before* pressing Enter. Capture: request headers (any CSRF/token header?), the exact JSON body keys and which value is the password or a transform of it (plain / md5 / sha256 / RSA-base64 — compare against the `.env` value and its digests), the 80-byte success body, `Set-Cookie` names; `$B cookies` right after. Then, once only, on **UP**: correct creds + wrong captcha → record the error JSON and whether it mentions attempts/lockout. Then a correct login. | `gst-prep.sh 01`; `$B eval recorder.js`; fill captcha; `$B press Enter`; `$B wait --networkidle`; `$B js …__rec`; `$B cookies` | `captures/D1-authenticate.rec.json` with the password and every digest of it replaced by `<REDACTED>` (post-process with `discovery/scrub.py` before saving); `captures/D1-wrong-captcha.rec.json`; `captures/cookies-06.json` |
| **D2** logout | href of the "Logout" link and the request it fires. Record only; never wired. | `$B links \| grep -i logout`; then `gst-prep.sh` already clicks it with the recorder active | `captures/D2-logout.rec.json`; one line in RECON |
| **D3** plain-client WAF rules | With `captures/cookies-01.json` from a fresh login, run a `curl -s -o /dev/null -w '%{http_code} %{redirect_url}'` matrix: {`services…/ustatus`, `return…/itcbalance`, `payment…/cashbalance`} × {no headers; browser UA only; UA+Referer=that host's dashboard page; UA+Referer+`Accept: application/json, text/plain, */*`} × {all cookies; without TS*}. Also: does `return.` API succeed if the client never fetched `return…/returns/auth/dashboard` HTML first? | Bash `curl` (GET only) using the dumped cookie header | `captures/D3-waf-matrix.md` (24 rows), rule summary into RECON |
| **D4** filed-returns | The working request body for Monthly GSTR1, Monthly GSTR3B, and Annual GSTR9 (FY 2025-26 returned `RET11403` — capture what the UI sends). Confirm `rfp` vocabulary and whether `qtr/mth` ever fill. | On `return…/returns/auth/efiledReturns`: `$B eval recorder.js`; `$B select select:nth-of-type(1) 2026-27`; `…(2) Monthly`; `…(3) GSTR1`; `$B click` Search; dump | `captures/D4-efiled-*.rec.json` |
| **D5** ledgers | (a) liability: open `return…/returns/auth/ledger/taxledger`, pick a range, capture the API + response; (b) Haryana `itcdtls` and `cashdetls` over `01/04/2026–today` to see **real entries** (utilisation debits with 3B ARN, a challan deposit, the `pen`/`fee` debits); (c) `searcharnusngdate` on Haryana (has penalty payments); (d) the **max range** per call: try `01/04/2025–today` and record the error text. | `$B goto` each ledger page; recorder; `$B fill` the date inputs (`$B forms` to find them); click Go; dump | `captures/D5-liability.rec.json`, `D5-itcdtls-01.rec.json`, `D5-cashdetls-01.rec.json`, `D5-searcharn-01.rec.json`, `D5-range-limit.md` |
| **D6** profile | API(s) behind `services…/services/auth/dashboard/profile` (legal name, addresses, authorised signatories, registration date — useful for the envelope's `state_code` and for ISD scope). | `$B goto`; recorder; dump | `captures/D6-profile.rec.json` |
| **D7** comparison | API + params behind `return…/returns/auth/comparison` for FY 2026-27 (GSTR-1 vs 3B liability, 2B vs 3B ITC). This is the cheapest SAP cross-check — capture every tab. | `$B goto`; recorder; select FY; click each tab; dump | `captures/D7-comparison.rec.json` |
| **D8** return views | On the returns dashboard for Haryana **072026**: recorder, then click GSTR-1 VIEW (capture per-table GETs: b2b, b2cs, cdnr, hsn, docs…), GSTR-3B VIEW (the URL that produced `gstr3b-summary` + `r1r3bliab` + `formdetails`), GSTR-2B VIEW (URLs behind `getdata`/`userdtls`), GSTR-2A VIEW. For each **DOWNLOAD** button: record the request it fires **without clicking "generate"** if a generate step is offered — classify as read vs side-effect. Also the non-nil 3B body must show `itc_elg`/`inward_sup` (absent on the UP nil sample). | `$B goto return…/returns/auth/dashboard`; `$B select select[name=fin] 2026-27`; quarter/month selects; Search; recorder; click each VIEW; `$B back`; repeat | `captures/D8-gstr1-view.rec.json`, `D8-gstr3b-view.rec.json`, `D8-gstr2b-view.rec.json`, `D8-gstr2a-view.rec.json`, `D8-download-buttons.md` (classification) |
| **D9** session lifetime | From `$B cookies`: `expires` on `AuthToken`/TS*. Then leave the Haryana session idle while doing D6/D7 on it is not possible — so: save the cookie header at login time, do ~20 min of other work, `curl …/ustatus` with the saved header every 5 min and log the first failure. Also record any "session about to expire" modal text. | `$B cookies`; timed `curl` loop (GET) | `captures/D9-session-lifetime.md` |
| **D10** OTP | In the D6 profile/settings pages look for a 2FA/OTP-on-login setting; note the dashboard "Currently logged in from IP" line; record the literal text the SPA shows if OTP is demanded (search the login page JS for the OTP route name so the CLI can recognise the response). Do **not** try to trigger it. | `$B html` on profile; `$B text` on login page after D1 | `captures/D10-otp-notes.md` |

Also record for Accounts (not discovery): Punjab password is wrong; fix in `.env` then re-verify with `gst-prep.sh 03`.

## 5. Build steps (dependency order; steps marked ∥ can run in parallel — they touch disjoint files)

0. **Housekeeping.** Move `portals/gst/fixtures/*` → `portals/gst/captures/`; add `out/`, `captcha-labels/`, `*.png` to `portals/gst/.gitignore`; add `discovery/scrub.py` (replaces GSTINs with `06AAAAA0000A1Z5`-style test values, ARNs/names with synthetic ones, keeps keys and types, zeroes are kept). *Proof:* `git check-ignore -v portals/gst/captures/x.json` matches; `git status --porcelain portals/gst` shows no `.rec.json`; scrubbed copies land in `cli/testdata/`.
1. **Skeleton.** `go.mod`, `main.go`, `root.go`, `registry.go`, `exitcode.go`, `output.go` (copy zepto's emit/envelope + dsr's `inr()`/`groupIndian()` verbatim), `dates.go`. *Proof:* `go build ./... && go vet ./...`; `TestInr` (₹4,33,72,582.27 → "(4.34 Cr)"), `TestExitCodeFor` (each typed error → its code), `TestPeriodParse` (`072026`, `--fy 2026-27` → 12 periods, `dd/mm/yyyy` and `dd-mm-yyyy` both parse).
2. **Config + registry.** `config.go`: `.env` search order per house (`$GST_ENV` → `./.env` → `../.env` → exe dir → `~/jivo-cli/portals/gst/.env`), hand parser, `loadRegistrations() ([]Registration, error)` requiring all four keys per block, `selectRegistrations(gstin, state string, all bool) ([]Registration, error)`. *Proof:* `TestLoadRegistrationsFromTempEnv`, `TestSelectByStateAliases` (`haryana`, `HR`, `06`, `Delhi ISD`, unknown → usage error), `TestNoSelectorIsUsageError`, `TestMaskedNeverEchoesPassword`.
3. **Allowlist + guard (∥ with 2).** `endpoints.go` table (one row per endpoint in §3 plus login), `wired-reads.tsv`, `guard.go`. *Proof:* `guardrail_test.go` (blocked: PUT/PATCH/DELETE, `/services/logout`, `…/save`, `…/submit`, `…/file`, `…/setoff`, `…/challan/create`, unknown path, extra query key, extra body key; allowed: every table row), `guardrail_coverage_test.go` (table == `wired-reads.tsv` 1:1; every row passes `forbidden`), `readonly_ast_test.go` (walk all non-test `.go`: no `http.MethodPut/Patch/Delete`, `http.Post`, `http.PostForm`; `http.NewRequest*` only in `client.go`+`login.go`; `os.WriteFile/Create/MkdirAll` only in `session.go`, `snapshot.go`, `captcha.go`; every string literal matching `^/(services|returns|payment|master)/` is a table path).
4. **Session persistence (∥ with 2, 3).** `session.go`. *Proof:* `TestSessionRoundTripThreeHosts`, `TestSessionFileIs0600`, `TestSessionExpiredByAge`, `TestImportPlaywrightCookies`.
5. **Client.** `client.go`: `doRead` = guard → ensureSession → headers (browser UA, `Accept`, per-host `Referer` from the table, D3 rules) → `Do` with `CheckRedirect` refusing `/services/error/accessdenied` and `/services/login` → classify: 401/403/redirect/"Request Rejected" HTML → `authError`; `{"status":0,"error":{errorCode}}` and `{"status_cd":"0","error":{error_cd}}` → `apiError{Code}` unless in `emptyCodes`; 200 HTML → `authError`. Test harness `fakeportal_test.go`: `httptest.Server` + a transport that rewrites the three hosts to it, serving `testdata/`. *Proof:* `TestDoReadHeaders`, `TestAccessDeniedRedirectIsAuthError`, `TestRequestRejectedHTMLIsAuthError`, `TestPortalErrorEnvelopeToExit6`, `TestEmptyCodesAreOkCountZero`, `TestUnknownQueryKeyNeverOpensSocket` (server records zero hits).
6. **Captcha + login (after D1).** `captcha.go`, `login.go`: GET login page → GET `/services/captcha?rnd=` (allowlisted) → solver → POST authenticate (body keys pinned from D1) → `ustatus` must equal `reg.GSTIN` else `authError` and the session is discarded → save session → append `captcha-labels/<ts>-<digits>-<ok|fail>.png`. `maxLoginAttempts = 1` (constant, raised only if D1 proves wrong-captcha is lockout-free). OTP: if the authenticate response or the next `ustatus` matches the D10 signature → `authError("portal asked for OTP for <gstin>; this CLI never handles OTP — complete the login once in a browser, then `auth import`, or ask Accounts to disable OTP-on-login")`, exit 4, no retry. *Proof:* `TestLoginPostsOnceEvenOnFailure`, `TestLoginRejectsGSTINMismatch`, `TestLoginStopsOnOTP`, `TestPromptSolverRequiresSixDigits`, `TestExecSolverUsesStdoutOnly`.
7. **Commands (∥, one file each, all via `registerSection`).** `cmd_auth.go`, `doctor.go`, `cmd_returns.go`, `cmd_ledger.go`, `cmd_masters.go` now; `cmd_gstr3b.go`, `cmd_gstr2b.go` after D8; `cmd_gstr1.go`, `cmd_gstr2a.go`, `cmd_compare.go`, `cmd_profile.go` as `deferred(...)` leaves until their D-item lands. *Proof per file:* argv → exact URL/query/body asserted against the fake portal; `TestDeferredLeavesNeverHitNetwork`.
8. **Normalise + snapshot (after 5, 7).** `normalise.go`: `normFiling(efiled, formdetails)`, `normCreditLedger(itcbalance, itcdtls)` (opening/closing rows → `balance`; `tr_typ Cr/Dr` → `txn_type`; `entry_class` from `desc` with raw kept; `ret_period` kept), `normCashLedger(cashbalance, cashdetls)`, `normGSTR3B(summary)` (3.1 rows, 4 when present, 5.1, 6.1/`tt_val`). `snapshot.go`: sequential over selections, `out/<gstin>/manifest.json` with `pulled_at`, endpoint, status, error per artefact; never aborts the run on one GSTIN's `authError` — records it and continues. *Proof:* golden tests `testdata/golden/*.jsonl` from scrubbed Haryana captures; `TestSnapshotContinuesPastAuthFailure`; `TestSnapshotWritesOnlyUnderOut`; `TestEnvelopeFieldsAlwaysPresent`.
9. **Live smoke, binaries, docs, harness.** `live_test.go` gated by `GST_LIVE=1` + an existing session (it never logs in): `doctor`, `returns calendar`, `ledger credit` for one GSTIN, asserts `ustatus.gstin` matches. Build `go build -o gst-portal .` and `GOOS=windows GOARCH=amd64 go build -o gst-portal.exe .`. Docs: `portals/gst/README.md` (banner, auth table "verified 2026-08-21", 8-GSTIN table from `LOGIN-STATUS.md`, deliverable, status), `cli/README.md` (house shape: read-only law in 3 layers, auth, build, quick start, flags, command table, deferred list, files), `SETUP.md` (Windows: copy `.env` from env-vault next to the `.exe`, `gst-portal.exe doctor --state haryana`, `auth login`, where the captcha PNG opens, what exit 4 means), `HANDOFF.md`, `ASK-EXAMPLES.md`; root `README.md` grid row; `NEW-DEVICE.md` "not automatic" line; `chats/2026-08-21-gst-portal.md`. Harness: add `gst` to the regex at `harness/hooks/post-tool-use.sh:42` and `"gst-portal": "gst", "gst": "gst"` to `TOOL_ALIASES` at `harness/bin/patterns.py:367`.

Phase 3 (not v0.1): `--captcha auto` via `execSolver` + `portals/gst/tools/captcha_ocr.py` (copied from the scratchpad, no secrets), gated on ≥80% exact over ≥100 labelled samples from `captcha-labels/`; GSTR-1/2B/2A document normalisers (C1, C2, C4); `compare`; `profile`; liability ledger. Phase 4: `gst-portal mcp` in `cli/internal/mcp/` copying `dsr-cli/internal/mcp/readonly_guard_test.go`, port 7710.

## 6. Risks flagged

- **D1 may reveal client-side encryption of the password** (common on Indian gov portals). Then `login.go` needs the public key or the JS transform replicated; budget one extra step and re-verify the redaction rule.
- **WAF may require a warm-up HTML GET per host or short-lived TS cookies** (D3/D9). The client design absorbs both, but if TS cookies rotate per request the session-reuse window shrinks and `snapshot --all` may need a login per run.
- **Lockout semantics unknown.** Until D1's one deliberate failure is recorded, every automated retry is off. The CLI's hard cap of one authenticate per GSTIN per process is the protection.
- **Fixtures are all nil-filer shapes.** Normalisers written against them will be wrong about optional sections (`itc_elg`, `inward_sup`, `b2b[]`). Golden tests must be regenerated from Haryana captures before Step 8 is called done.
- **Public repo.** `captures/`, `out/`, `captcha-labels/`, session files and the `.env` must all be ignored; Step 0's `git status` check is the gate, and the D1 recording must be scrubbed before it touches disk under the repo.

## 7. Acceptance checklist, v0.1

- `go test ./...` green with no network; `readonly_ast_test.go`, `guardrail_test.go`, `guardrail_coverage_test.go` present and passing; `wired-reads.tsv` equals the table.
- `gst-portal doctor --all` reaches 7/8 registrations (Punjab until its password is fixed), prints masked creds only.
- `auth login` performed once per GSTIN with a typed captcha; a second `doctor` run uses the cached session with zero prompts; `auth status --all` shows session age for each.
- `returns calendar`, `returns status --period 072026`, `returns filed --fy 2026-27 --form GSTR1`, `ledger cash`, `ledger credit`, `ledger credit --from 2026-04-01 --to 2026-08-22`, `masters forms` each return 200 JSON for Haryana, and `--agent` output validates against the envelope; RJ/UP/MH nil answers exit 0 with `count: 0`.
- `gstr3b summary --period 072026` returns the non-nil Haryana body (after D8).
- `snapshot --all --fy 2026-27 --out /tmp/gst-out` produces `manifest.json` + jsonl for every reachable GSTIN, continues past the Punjab failure, and every record carries the spec envelope.
- Scrubbed fixtures in `cli/testdata/`; raw captures only under gitignored `captures/`; `git status --porcelain` shows no session, captcha, `.env`, or capture files.
- `gst-portal` and `gst-portal.exe` committed; `SETUP.md` walked once on a Windows fleet box (VICTUS 23001) — `doctor --offline` then a live `doctor` with a copied `.env`.
- Harness hook + alias edits in; `RECON.md` updated with D1–D10 outcomes tagged VERIFIED / NOT_REACHABLE; `chats/` entry written.

Confidence: high (~90%) on layout, guard, session, output, and test design — all grounded in tracked precedents I read. Medium (~60%) on the login step's size until D1 is captured. Low confidence that auto-OCR belongs in the product at all; the operator-typed path is the correct v0.1.

Hand-off to **Forge**: start at Step 0 and Steps 1–4 (they need no discovery); Steps 6 and the `gstr3b/gstr2b` leaves wait on D1/D8 from the discovery agent.