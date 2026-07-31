# Setting up a new device

Everything in this repo is in git **except credentials**. So a new machine is
always the same two jobs: **clone the code**, then **restore the secrets**.
Nothing here will log in until you do the second part.

This guide gets a fresh machine to the point where it can read SAP and — if you
want it to — create SAP drafts.

---

## What you need before you start

- **Git**, and access to `github.com/daman8271/jivo-cli`.
- **Go 1.25.5 or newer** — only if you want to rebuild the binaries. If the
  committed binaries run on your platform, you can skip Go entirely.
- **Network reach to SAP.** SAP (`103.89.45.192:50000`) is only reachable from
  the office network, over the VPN, or from a whitelisted IP. A machine that
  can't reach it will fail at `doctor` no matter how correct the setup is.
  From home, see `connections/SAP-HOME-ACCESS.md`.
- **The SAP password.** It is not in this repo and never will be. Get it from
  Daman or copy `sap-b1/cli/.env` off a machine that already works.

---

## 1. Clone

```bash
git clone https://github.com/daman8271/jivo-cli.git
cd jivo-cli
```

## 2. Restore the credentials

The repo ships with **no** `.env` files — `.gitignore` blocks `.env`, `*.env`,
`*.token` and friends, which is why a clone is safe to put on a new box but
useless until you do this step.

Create `sap-b1/cli/.env`:

```bash
cat > sap-b1/cli/.env <<'EOF'
SAPB1_HOST=103.89.45.192
SAPB1_PORT=50000
SAPB1_COMPANYDB=JIVO_OIL_HANADB
SAPB1_USER=manager
SAPB1_PASSWORD=<the SAP password>
SAPB1_INSECURE=true
EOF
chmod 600 sap-b1/cli/.env
```

`SAPB1_INSECURE=true` is needed because SAP's Service Layer uses a self-signed
certificate. The other CLIs (ecom, exim, factory, oms, jsap) read the root
`.env` — copy that too if you need them; the root `README.md` lists what goes
in it.

## 3. Build (skip if the committed binary runs)

```bash
cd sap-b1/cli
go build -o sapb1 ./cmd/sapb1
```

For the Accounts team's Windows laptops, cross-compile from any machine:

```bash
GOOS=windows GOARCH=amd64 go build -o ../accounts-kit/sapb1.exe ./cmd/sapb1
```

## 4. Prove it works

```bash
./sapb1 doctor
```

You want all three green — configuration, network, login. If network fails
you're not on a network that can see SAP; if login fails the password is wrong.

Then a real read:

```bash
./sapb1 query BusinessPartners --select "CardCode,CardName" --top 3 --json
```

---

## Reading vs writing

**Reads need nothing extra.** Every command except the three below only reads.

**Writes are opt-in and explicit.** The same binary can create SAP drafts, but
only when a person runs one of these on purpose:

| Command | What it does |
|---|---|
| `sapb1 draft <doctype>` | Creates a **draft** document. A human opens SAP → Document Drafts → reviews → Add. This is the intended way to put data into SAP. |
| `sapb1 post <Entity>` | Direct create, for master data that can't be drafted (Business Partners, Items). |
| `sapb1 patch <Entity(key)>` | Direct update. |

Try one safely — `--dry-run` shows the exact request and sends nothing:

```bash
./sapb1 draft order \
  --data '{"CardCode":"CUSTA000619","BPL_IDAssignedToInvoice":1,"DocumentLines":[{"ItemCode":"FG0000011","Quantity":1}]}' \
  --dry-run
```

Drop `--dry-run` and it previews the payload and waits for you to type `yes`.
Add `--yes` to skip the prompt in a script.

### Two things that will bite you on a first write

1. **Every JIVO document needs a branch.** Without
   `BPL_IDAssignedToInvoice`, SAP rejects the write with
   `-5002 Specify an active branch`. Valid branches in Oil: `1`=DELHI,
   `2`=FACTORY, `3`=PUNJAB, `4`=HIMACHAL PRADESH, `5`=HARYANA SALES,
   `6`=DELHI ISD.
2. **Exit code 7 means "unknown, go look".** If a write times out, the document
   may or may not have been created. Never blind-retry — query SAP first.
   Exit 5 means the request never left your machine and is safe to retry.

### Where writes are recorded

Every attempt is appended twice — one line when the request is sent, one when it
comes back — so an ambiguous failure still tells you exactly what was attempted
and against which host.

The log lands in **`queries/<operator>/sap-writes.jsonl`** inside the checkout,
which syncs to `main` with the rest of that operator's session log. That is
deliberate: a write log that only ever sat in the writer's home directory was
readable by exactly the one person it exists to hold accountable. In the repo,
**every write by every operator converges into one shared history.**

Precedence, highest first:

| | Path |
|---|---|
| `$SAPB1_WRITE_LOG` | wherever you point it |
| registered operator | `queries/<operator>/sap-writes.jsonl` |
| fallback | `~/.sapb1-writes.jsonl` (mode 0600) |

The fallback only applies to a binary run outside a registered checkout — run
`python3 harness/bin/setup.py` and it resolves to the repo path instead.

---

## Optional: ask SAP in plain English

Two ways, both read-only:

- **Claude Desktop on Windows** (what the Accounts team uses) —
  `sap-b1/accounts-kit/SETUP.md`. Question examples in `ASK-EXAMPLES.md`.
- **MCP from a terminal or phone** — `sap-b1/cli/MCP.md`.

Both surfaces expose **only the read tools**. Writing to SAP is deliberately
terminal-only: you cannot create a draft by asking Claude, on any device. That
is enforced by a test, not by convention.

---

## What is NOT automatic on a new device

Cloning does not give you these — set them up only if that machine needs them:

- **Other systems' credentials** — the root `.env` (ecom/exim/factory/oms/jsap),
  `control-panel/.env`, `~/.postsql/config.toml`, portal tokens.
- **Portal logins** that mint JWTs on a schedule (Blinkit, Zepto) —
  those run off LaunchAgents on the Mac that owns them; don't duplicate them on
  a second box or they'll fight over the same session.
- **Fleet SSH access** — `~/.ssh/config` aliases and keys are per-machine.

---

## Troubleshooting

| Symptom | Cause |
|---|---|
| `network` fails in doctor | Not on office network/VPN, or IP not whitelisted. |
| `login` fails in doctor | Wrong password, or `.env` not being read — check you're running from `sap-b1/cli/`. |
| `x509: certificate signed by unknown authority` | `SAPB1_INSECURE=true` missing from `.env`. |
| A write says exit 7 | Outcome unknown. Query SAP to see whether it landed before doing anything else. |
| `Specify an active branch` | Add `BPL_IDAssignedToInvoice` to the payload. |
