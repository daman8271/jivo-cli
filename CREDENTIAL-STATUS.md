# Credential status — every JIVO CLI

Live-tested 2026-08-29 from the Mac Air. **No passwords in this file** — this repo is
public. Each row says *where* the credential lives, never what it is.

Re-run the sweep any time: each CLI has a `doctor` command.

## ✅ Working — nothing to do (10)

| System | Account | Credential lives in | Proof |
|---|---|---|---|
| **SAP B1** (3 companies) | `manager` | `sap-b1/cli/.env` | Oil 3,416 BPs · Mart 2,192 · Bev 2,969 |
| **HANA** | `ZIA` | `connections/hana-office-bridge.env` | `SELECT CURRENT_USER` |
| **ecom.jivo.in** | `ecom6@jivo.in` (id 13, "Simran") | `~/.config/jivo-ecom-pp-cli/` | live Blinkit Aug DRR |
| **OMS** | `paramjot` → `pramjot@jivo.in` (id 62, **admin**) | `.env` `OMS_*` | re-logged in, doctor green |
| **Factory / ji.jivo.in** | `test@jivo.in` (all 3 companies) | `.env` `JIVO_FACTORY_*` | re-logged in, doctor green |
| **exim** | env token | `~/.config/exim-pp-cli/config.toml` | 139 parties live |
| **ARY** (FusionERP8) | `sa` | `ary-cli` config | 1.09 M bills, today's data |
| **TankhaPay** | `shunty@jivo.in` | `.env` `TPAY_*` | token valid, dashboard read |
| **jmail** | `logistics@jivo.in` | `.env` `ZOHO_MAIL_*` | 40,219 msgs |
| **Control Panel** | Django session | `~/.config/jivo-pp-cli/config.toml` | live Aug sales rows |

## ❌ Genuinely need a credential from IT (3)

| System | Failure | What's needed |
|---|---|---|
| **postsql** | `28P01 password authentication failed for user "postgres"` @ 103.89.45.76:5432 | New Postgres password → `~/.postsql/config.toml`. Dead fleet-wide since ~6 Aug |
| **DSR** | `no database user configured` | `DSR_USER` / `DSR_PASSWORD` — never set on this Mac |
| **JSAP** | HTTP 401 on the live box | A working account. `nirmalkaur` is rejected (identical response to a bogus user) |

## ⚠️ Session expiry, not a lost password (1)

| System | State | Fix |
|---|---|---|
| **GST portal** (8 GSTINs) | every cached session ~100 h old, all expired | Relogin per GSTIN — captcha/OTP each. Passwords are still in `portals/gst/.env` |

## Notes worth keeping

- **`ji.jivo.in` and `factory.jivo.in` are the same box** — both resolve to `138.252.101.117`.
  The factory CLI logs in at `ji.jivo.in`, calls the API at `factory.jivo.in/api/v1`.
- **JSAP moved boxes.** `103.89.45.75:5001` is dead (no TCP at all). Live box is
  `138.252.101.118:5001` — `.env` `JSAP_URL` updated 2026-08-29. Login shape confirmed:
  `POST /api/auth/Login` with flat `{"loginUser": ..., "password": ...}`.
- **OMS and Factory were never missing credentials** — both had valid logins sitting in
  `.env`; only their cached JWTs had expired (access 12 Aug, refresh 18 Aug). A plain
  `auth login` fixed both. Check `.env` before asking IT for a password.
- **SAP is unreachable *directly* from home** (`138.252.101.222:50000`) — office-IP filter,
  expected, not a credential problem. Run `connections/sap-home-bridge.sh`, then
  `SAPB1_HOST=127.0.0.1 SAPB1_PORT=15000 sapb1 ...`.
- **A stale `token_expiry` field in a config.toml means nothing** — ecom, OMS and Factory
  all show `2026-08-12`. The real expiry is inside the JWT.
- **ecom's refresh token is single-use and rotates.** Never copy it between machines; the
  second box to use it gets locked out. The VPS keeps its own separate lineage on purpose.
