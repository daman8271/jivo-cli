# JIVO SAP — Claude Desktop setup (Windows, for the Accounts team)

Ask JIVO's SAP in plain English — "Ziyaul Haque's ledger balance?", "this month's turnover?",
"open POs for customer X?" — and get live answers. **Read-only: it can only read SAP, never change anything.**

Do this once per laptop (must be an office laptop that already reaches SAP):

## 1. Put the tool in place
- Create a folder `C:\jivo-sap`
- Copy `sapb1.exe` into it → `C:\jivo-sap\sapb1.exe`

## 2. Install Claude Desktop
- Download from https://claude.ai/download , install, sign in (needs a Claude account).

## 3. Connect SAP to Claude
- Open the config file (create if missing):
  `%APPDATA%\Claude\claude_desktop_config.json`  (paste `%APPDATA%\Claude\` in File Explorer)
- Paste the contents of `claude_desktop_config.json` from this kit.
- Replace `REPLACE_WITH_SAP_PASSWORD` with the SAP password.
- Save, then fully quit and reopen Claude Desktop.

## 4. Use it
- In Claude Desktop you'll see a tools icon (🔌). Ask questions like the ones in `ASK-EXAMPLES.md`.
- To switch company, just say "in Mart" / "in Beverages" (default is Oil / JIVO_OIL_HANADB).

## Companies
- `JIVO_OIL_HANADB` (Oil, default) · `JIVO_MART_HANADB` (Mart) · `JIVO_BEVERAGES_HANADB` (Beverages)

## Safety
- This is READ-ONLY by construction — no create/update/delete. It cannot damage SAP.
- Keep `claude_desktop_config.json` private (it holds the SAP password). Prefer a **read-only SAP user** over `manager` — ask IT/Basis to create one.
