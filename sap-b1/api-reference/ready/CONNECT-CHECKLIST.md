# First 5 minutes once you're connected

The moment you're on the company **VPN** (or your IP is whitelisted) **and** you
have the **CompanyDB name**, do this in order. Everything else is already built.

## 1. Fill in the one blank
Open `~/sapb1-cli/.env` and set the company database name:
```
SAPB1_COMPANYDB=<the name the SAP admin gives you>
```
(Host, user, password, and `SAPB1_INSECURE=true` are already filled in.)

## 2. Prove the connection
```
cd ~/sapb1-cli
./sapb1 doctor
```
`doctor` runs a ✓/✗ checklist: config present → server reachable (TCP) → login works.
- All ✓  → you're in, go to step 3.
- ✗ at "reachable" → you're not on the whitelisted network yet (VPN/whitelist).
- ✗ at "login" → wrong CompanyDB name or password; re-check with the admin.

## 3. Explore what exists (works offline too)
```
./sapb1 entities                 # all 498 APIs
./sapb1 entities --search invoice
./sapb1 ops Orders               # operations on an entity
```

## 4. Fetch real data
```
./sapb1 orders list --open
./sapb1 invoices list --top 20
./sapb1 items list --low-stock 5
./sapb1 partners list --customers
./sapb1 query BusinessPartners --select CardCode,CardName,CurrentAccountBalance --top 50 --json
```
Add `--json` to pipe into anything (jq, an AI agent). Add `--csv` to export.
See `docs/00-READ-PLAYBOOK.md` for the full business-question → command cheat-sheet.

## Remote Desktop (the human GUI, separate from the CLI)
Double-click `~/SAP Remote Desktop.rdp` → Windows App opens aimed at the box →
enter the password. Also only works once you're on the VPN/whitelist.

## Dry-run the whole flow tonight (no real server needed)
```
python3 ~/sapb1-api-reference/mock/serve.py --port 50000 &   # local fake SAP
cd ~/sapb1-cli
./sapb1 --host 127.0.0.1 --port 50000 --company TESTDB --insecure orders list --open
```
Proves the login → fetch → render path works before the real connection.
