# TankhaPay portal — handoff (VPS → Mac Air, 2026-07-25)

Paste the block below into a Claude Code session started in `~/jivo-cli/portals/tankhapay` on the Mac.

---

You are picking up a **finished** project: a read-only CLI + Obsidian study vault for
**business.tankhapay.com** (JIVO's TankhaPay HR/payroll SaaS by Akal Information Systems). It was
built and verified on a Linux VPS and transferred here. Everything is on disk in this folder
(`~/jivo-cli/portals/tankhapay`). **It is strictly READ-ONLY** — the golden rule: never call, build,
wrap, or suggest any write/mutation against any JIVO backend. The only non-read call allowed is the
login token exchange.

## What exists (done + verified)
- **`cli/`** — Go CLI `tankhapay-portal` (cobra, stdlib only). **297 read commands** across 14 section
  groups, generated from `captures/wired-reads.tsv`. AES-128-ECB body cipher + bearer JWT, headless
  login from `.env`, 24h token cache, 3-layer read-only guardrail, `go test` green (coverage + guardrail).
- **`vault/`** — Obsidian vault: 5 `_meta` docs + `00-TankhaPay-Atlas.md` + `Pages-and-Routes.md` (325
  routes) + `TankhaPay-Endpoints.md` (master index + coverage audit, **0 gaps**) + 14 section notes.
- **`captures/`** — inventory (`endpoints-raw.tsv` = 726 endpoints), per-section splits, the 20 MB JS
  corpus (`captures/js/`), and the partition manifests (`wired-reads.tsv`, `reclassified-writes.tsv`,
  `unknown-promoted.tsv`, `unknown-excluded.tsv`).
- **`scripts/`** — `gen_commands.py` (regenerates the command tree), `build_index.py` (coverage audit),
  `section_pack.py`, `promote_unknown.py`.

## First steps on the Mac
```sh
cd ~/jivo-cli/portals/tankhapay/cli
go build -o ~/go/bin/tankhapay-portal .        # rebuild native (Linux binary was not shipped)
tankhapay-portal doctor                         # confirms .env + login + one live read (593 employees)
tankhapay-portal auth whoami
tankhapay-portal dashboard tpay-dashboard-data --set action=get_employee_list
```
`.env` (your creds, gitignored) is already here. If `doctor` can't find creds, it needs
`TPAY_USERNAME`, `TPAY_PASSWORD`, `TPAY_BODY_KEY=0123456789abcdef`.

## Auth/crypto — ALREADY CRACKED, do not re-derive
- Body cipher: **AES-128-ECB + PKCS7, base64**, static key `0123456789abcdef`. Request body =
  `{"encrypted": base64(AES(JSON))}`; reply carries `commonData` (same cipher). A few endpoints return
  `commonData` already-plain — the client handles both.
- Login: POST `…/api/login` with AES-wrapped `{email, password: md5(pw) lowercase, recaptchaToken:"",
  localhost:true, action:"check_login_by_emailid1"}`. reCAPTCHA bypassed by `localhost:true`; the action
  MUST be `…emailid1`. Reply `{status:"True", token}`. JWT `data` field is AES-ECB (same key) → account
  ctx `tp_account_id=2719, geo_location_id=37, ouIds="37,2211,38,40,31,1925"`, user "ravinder singh"
  (Employer). One JWT authorizes all 4 backends: business / mobapi / tpPay / tnd.
- **JWT gotcha:** `aud` is a JSON array — decode only `exp`/`iat`/`data`.

## Read shaping
The CLI auto-injects `accountId`/`geo_location_id`/`ouIds` from the JWT. Add per-endpoint params with
`--set k=v` (values may be `@accountId @geo @ouIds @productType @userid`) or `--body '{...}'`; `--no-ctx`
to disable injection. **Do NOT auto-add `customerAccountId`** — it breaks the dashboard read; add it only
where a note says to. `TP_DEBUG=1` prints the outgoing payload. Exact per-endpoint payloads are in each
`vault/<Section>.md`.

## Coverage (audit: 0 gaps)
726 endpoints, all documented, each in exactly one section. **297 reads wired** = 287 confirmed + 10
hand-vetted reads promoted from UNKNOWN. Documented-but-never-wired: 333 writes + 35 extractor-mis-tagged
writes + **61 UNKNOWN held out** (`captures/unknown-excluded.tsv`) — these are behavioral writes/auth/
dual-mode `manage_*` endpoints whose read/write couldn't be confirmed; wiring them would risk a write, so
per the read-only vow they were left out. To wire any of them: add its URL to `captures/wired-reads.tsv`,
run `python3 scripts/gen_commands.py`, rebuild, `go test`. ONLY do this for endpoints you've confirmed
are reads from the JS corpus — never guess.

## Regenerate / re-verify
```sh
python3 scripts/gen_commands.py && (cd cli && go build -o ~/go/bin/tankhapay-portal . && go test ./...)
python3 scripts/build_index.py            # rebuilds the coverage audit (expect 0 gaps)
```

## Optional next steps (all READ-ONLY)
- Wire specific vetted reads from the 61 held-out UNKNOWNs after confirming behavior in `captures/js/`.
- Add richer default payloads / typed flags to high-value reads (reports, attendance) from the vault docs.
- Open the vault in Obsidian; start at `vault/00-TankhaPay-Atlas.md`.
- (Later) `git init` + push if desired — `.gitignore` already excludes `.env`, `.token`, the binary,
  and `captures/js/`.
