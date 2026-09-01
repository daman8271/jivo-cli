# saphist — setup (Windows and Mac)

`saphist` reads JIVO's **old SAP books** (2014 → Oct-2024) off the SQL Server at
`138.252.101.118:1433`. It never writes.

## 1. You need two things

- **the program** — `saphist.exe` (Windows) or `saphist` (Mac/Linux)
- **a `.env` file next to it** with the SQL Server login

That is all. No install, no VPN, no tunnel — this server is reachable from the
office, from home and from the VPS (unlike the live SAP HANA box, which is
filtered to the office IP).

## 2. The `.env`

Create a file called `.env` **in the same folder as the program**:

```
SAPHIST_HOST=138.252.101.118
SAPHIST_PORT=1433
SAPHIST_USER=sa
SAPHIST_PASSWORD=<ask IT — never type it into a chat or commit it>
```

If you already have `connections\ary.env` from the jivo-cli kit, saphist reads
that too — same server, same login, nothing to copy.

**Never commit a `.env`.** This repository is public. `.gitignore` already covers
`*.env`, but check with `git check-ignore -v .env` before any `git add`.

## 3. Check it works

```
saphist doctor
```

You should see `reachable: yes`, the SQL Server build, and a coverage table for
each of the three books. If it says `no SQL Server login configured`, the `.env`
is not where the program is looking — run `saphist doctor` from the folder that
contains it.

## 4. Windows notes (learned the hard way on the fleet)

- **SSH lands you in PowerShell, not `cmd`.** PowerShell eats parentheses, so a
  query with `CONVERT(date, …)` sent over ssh needs the SQL passed as a single
  quoted argument — or just run the domain commands, which build the SQL for you.
- **Pass SQL as an argument, not on a pipe**, when you are inside a `.cmd`
  wrapper.
- **Do not nest `\"` quotes** in a command sent over ssh to a Windows box — it
  fails silently rather than erroring.

## 5. First things to run

```
saphist books                                  which books exist, and what each covers
saphist books which --year 2016                which book holds 2016
saphist sales summary --fy 2016                that year's turnover
saphist party search <name>                    find a customer or vendor by name
saphist party statement <CardCode> --fy 2021   their ledger with a running balance
```

More: **ASK-EXAMPLES.md**.

## 6. What it cannot do

- **It cannot write.** Not a policy — there is no write command in the program,
  and every statement runs inside a transaction that is always rolled back.
- **It cannot see anything after October 2024.** That is the live SAP system:
  use `sapb1` in `sap-b1/`.
- **It is not the ARY retail system** (`FR8HODBNEW`, same server): that is the
  `ary` CLI.
