# distribution/ — the JIVO kit bundle-builder

Tick the tools a colleague needs, pick Mac or Windows, get a zip with their
credentials already in the right places.

**Every zip this produces contains live production credentials.** They are
written only into `distribution/dist/`, and the builder refuses to run unless
git ignores that directory.

Design decisions: `PLAN.md`. Frontend contract: `API.md`.

## Run it

```bash
cd distribution/server && go build -o jivodist .

cd distribution
./server/jivodist                                       # UI on http://127.0.0.1:7788
./server/jivodist -list                                 # what can be bundled, per target
./server/jivodist -selection testdata/mac-min.json -o dist/test.zip
```

Flags: `-repo <path>` (default: walk up from the working directory to the
directory holding `distribution/manifest.json`), `-addr` (default
`127.0.0.1:7788`), `-keep-staging` (leave the staged tree under
`distribution/staging/` for inspection).

## Test it

```bash
cd distribution/server && go test ./...
go test ./internal/engine -update      # rewrite the golden ship lists + README
```

Regenerate the goldens only when a change to what ships is intended, and read
the diff before committing it — that diff is the review.

## Layout

```
distribution/
├── manifest.json     input: the 14-agent inventory of every CLI (committed)
├── overrides.json    hand-maintained warnings the manifest cannot know (committed)
├── PLAN.md           the implementation plan (Atlas)
├── API.md            the frontend contract
├── secrets.local.env GITIGNORED, operator-maintained: DSR_* keys (see below)
├── server/           the Go module (module jivodist, stdlib only)
│   ├── main.go       -serve (default) | -selection … -o … | -list
│   └── internal/
│       ├── manifest/ typed loader + live availability scan + overrides
│       ├── engine/   guard, ship-list resolver, env baker, README, zip, Build
│       └── httpapi/  the four endpoints + static serving of web/
├── web/              the frontend (built separately)
├── testdata/         selection fixtures + golden ship lists and README
├── dist/             GITIGNORED — output zips
└── staging/          GITIGNORED — only with -keep-staging
```

## How a bundle is put together

1. **Guard.** `git check-ignore` on `dist/` and `staging/`. If either has become
   committable the build stops with a `409` and says what to fix.
2. **Ship list.** For each picked component: its binaries **for that target
   only**, its companion files, its docs, and its credential files from the
   §5 table in `PLAN.md`. It is an allowlist — every file is named. A component
   with no binary for the target contributes nothing at all, not even its docs.
3. **Env baking.** A component's bundle carries only *its* credentials. Keys are
   lifted out of the repo-root `.env` by prefix (`JSAP_`, `OMS_`, `EXIM_`, …),
   so a jsap-only zip has no SAP or OMS password in it. Whole-file credentials
   (SAP, HANA, control-panel, TankhaPay) are copied to the path their tool
   actually reads.
4. **README.** Generated per bundle from `lessons.readme_must_say` plus a block
   per component: how to run it, what its credentials actually do, its offline
   check, and what behaves differently inside a standalone kit. CRLF for Windows
   bundles — and for that generated file only.
5. **Deny gate.** The finished staging tree is walked and refused if it contains
   anything on the deny list (`env-vault/`, `token.json`, `lovepreet-veerji.env`,
   `control-panel/recon/`, `captures/`, `.git/`, `__pycache__`, `*.pyc`,
   `.DS_Store`, `connections/fleet-access.env`). This is independent of the
   allowlist on purpose: it is what still holds if the resolver is ever replaced
   by a directory copy.
6. **Zip.** One `jivo-cli/` root mirroring the repo, forward-slash paths, unix
   modes preserved (0755 binaries, 0600 credentials, 0644 docs), then sha256.
   The archive is streamed to `<name>.zip.tmp` and renamed into place only when
   it is complete, so a crash never leaves a half-written credential zip sitting
   under a name that looks ready to send.

Output is named `jivo-kit-<target>-<YYYYMMDD-HHMM-xxxx>-<recipient>.zip`. The
bundle id is in the filename so same-day rebuilds cannot overwrite each other
and any zip on disk can be traced back to its build.

## Things that are easy to get wrong

- **Exec bits.** A plain `zip.Create()` writes mode-0 entries and every Mac
  binary lands non-executable. Modes are set with `FileInfoHeader`+`SetMode` and
  the tests re-read them from the **finished archive**, never from staging.
- **Never copy a folder.** One directory copy ships `lovepreet-veerji.env`, a
  live `exim/.secrets/token.json`, `control-panel/recon/` admin cookies, or 99 MB
  of Amazon captures. The golden ship lists exist to make that impossible to do
  quietly.
- **Tell the truth about credentials.** `auth_mode` is not decoration. Baking a
  `.env` that a binary never reads and calling it ready produces exactly the
  silent failure the lessons in `manifest.json` document.
- **product-identity is hash-pinned.** Those JSON files are copied byte-for-byte.
  No re-encoding, no line-ending translation, or every `product` command fails
  closed with exit 6.
- **NTFS.** A Windows bundle is refused, loudly, if any staged path contains
  `: * ? " < > |`. It never silently drops the file.
- **Empty is an error.** If nothing the operator picked has a binary for the
  chosen target, the build fails. A zip containing only a README is not a kit,
  and handing one over is worse than saying no.
- **No silent auth default.** A component with no row in `envPlan` is
  `unconfigured`: it cannot be bundled and the board shows the gap. Defaulting
  it to `baked-env` would print "ready to use" for credentials nobody has
  thought about.
- **The server is loopback-only and browser-hardened** (Host allowlist, JSON
  required on state-changing methods, no CORS headers, `Sec-Fetch-Site`
  checked). That is anti-drive-by protection for the operator's machine, not
  authentication — see `API.md`.

## `secrets.local.env`

Gitignored, operator-maintained, and the one thing you may need to create by
hand. No DSR credential exists anywhere in this repo or in the env vault, so
`dsr-cli/.env` is generated from here:

```
DSR_HOST=…
DSR_PORT=…
DSR_DATABASE=…
DSR_USER=…
DSR_PASSWORD=…
DSR_PORTAL_URL=…
```

Without it the builder ships a blank template and says so, loudly, in the build
result and in the recipient's README. It never invents a value.

## `overrides.json`

Warnings the manifest cannot know — a stale exe, a dead password, credentials
awaiting rotation. Keyed by `global`, by component id, or by binary path (which
fires only when that artefact actually ships). A warning may be scoped to one
target with a `[windows] ` / `[mac-arm64] ` prefix. **Date every entry**: an
undated warning goes stale without anyone noticing.
