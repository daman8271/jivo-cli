# GST portal CLI — setup on an office PC (Windows)

For Accounts. Ten minutes, no programming, nothing to install. You will end up
able to ask the GST portal questions from a terminal instead of clicking through
eight logins.

> ## ⛔ Before anything else
>
> This tool talks to **gst.gov.in**, the government's live filing system. It only
> ever **reads**. It cannot generate, save, submit, file, reset, compute, amend or
> create a challan — those buttons are not wired and cannot be reached.
>
> **The one thing it does that has an effect is log in.** The GST portal allows
> **one session per username**, so logging in from here **kicks out whoever is
> logged in as that user in a browser** — possibly in the middle of a filing.
> Check first on filing days.

## 1. Get the toolkit

If you already have `C:\jivo-cli`, just update it:

```
cd C:\jivo-cli
git pull
```

If not, follow `NEW-DEVICE.md` in the root of the repo first, then come back.

The program is `C:\jivo-cli\portals\gst\cli\gst-portal.exe`. It is committed —
there is nothing to build.

## 2. Put the credentials next to it

The passwords are **not** in the repo. Get the GST block from the env vault
(`env-vault\all-env.txt`, the section labelled `portals/gst/.env`) or from Daman,
and save it as:

```
C:\jivo-cli\portals\gst\.env
```

It looks like this — eight blocks, one per registration:

```
GST_01_STATE=Haryana
GST_01_GSTIN=06AACCJ4223F1Z0
GST_01_USER=<the portal username>
GST_01_PASS=<the portal password>
...
GST_08_STATE=Delhi ISD
```

`portals\gst\.env.example` is the empty template — copy it and fill in the USER
and PASS lines. **Never commit this file**; it is already in `.gitignore`, and
this repo is public.

If you keep the `.exe` somewhere else, put the `.env` **in the same folder as the
`.exe`** — that is one of the places it looks. The full search order is
`%GST_ENV%` → the current folder → its parent → the `.exe`'s folder → the `.exe`'s
parent → `%USERPROFILE%\jivo-cli\portals\gst\.env`.

## 3. Check it can see the credentials

Open **Command Prompt** (or PowerShell), then:

```
cd C:\jivo-cli\portals\gst\cli
gst-portal.exe doctor --offline
```

`--offline` opens no connection at all — it only checks that the `.env` is found
and readable. You should see all 8 registrations listed with their credentials
**masked**: usernames as first-four-`…`-last-four (short ones just say `present`), passwords only ever as `present`. The
password is never printed anywhere by this program.

Then the real check, which does one harmless read per registration:

```
gst-portal.exe doctor
```

The first time, every registration will say the session is missing. That is
expected — nothing has logged in yet.

## 4. Log in to one registration

```
gst-portal.exe auth login --state haryana
```

What happens:

1. It fetches a captcha and **saves it as a PNG, then opens it** in your default
   image viewer (Photos, usually). The file lands in
   `%APPDATA%\gst-portal\captcha-06AACCJ4223F1Z0.png` — outside the repo, so it
   never gets committed. The path is printed too, in case the viewer does not open.
2. It asks you for the six digits.
   - Type them and press Enter.
   - Can't read the image? Type **`r`** and press Enter for a fresh one. That is
     **free** — it does not count as a login attempt.
   - Press Enter on a blank line to abort. Nothing is sent.
3. It logs in **once**. There is no retry, ever, and no way to turn one on.

You can select a registration by state (`--state punjab`, `--state hr`,
`--state "delhi isd"`) or by GSTIN (`--gstin 06AACCJ4223F1Z0`). Run
`gst-portal.exe auth list` to see all eight.

Do this once per registration you need. Each has its own saved session.

## 5. Ask it something

```
gst-portal.exe ledger credit --state haryana
gst-portal.exe returns calendar --state haryana
gst-portal.exe gstr3b summary --state haryana --period 072026
```

`ASK-EXAMPLES.md` in the folder above has ten questions in plain English with the
command for each.

The best way to use it is one login, then pull everything at once:

```
gst-portal.exe snapshot --state haryana --fy 2026-27 --out C:\gst-snap
```

`--out` must be **outside** `C:\jivo-cli` — the program refuses to write JIVO's
financial data inside a git checkout, because this repo is public.

## What the exit codes mean

If a command fails, the number it exits with tells you who has to fix it. In
Command Prompt, `echo %ERRORLEVEL%` right after shows it.

| Code | Meaning | What to do |
|---|---|---|
| 0 | Fine. Including "no data for that period" — that is an answer, not an error | — |
| 2 | You asked for something it can't parse (bad flag, no registration picked) | Read the message; it lists the choices |
| 3 | It can't find or read the `.env` | Step 2 |
| **4** | **Auth.** No session, the session expired, or the portal refused the login | Usually: run `auth login` again. See below |
| 5 | Network failure, or the read-only guard refused | **Nothing was sent.** If it is the guard, tell Daman — a command tried to leave the allowlist |
| 6 | The portal answered, and its answer was an error | Read the portal's message; usually a wrong period or FY |

### Exit 4 in more detail

**Exit 4 is the normal one.** GST sessions expire after roughly fifteen minutes of
sitting idle, so most exit-4s just mean "log in again":

```
gst-portal.exe auth login --state haryana
```

Three exit-4s are *not* that:

- **"the portal already rejected the credentials for … refusing to try again"** —
  the password in the `.env` is wrong. **Punjab (`03AACCJ4223F1Z6`) is in exactly
  this state and has been since 2026-08-21.** Get a corrected password from
  Accounts. **Do not retry it by hand** — repeated attempts on a wrong password
  are how a GST account gets locked, and only the department can unlock one.
- **"portal asked for OTP"** — has never happened, but if it does, this tool stops.
  Log in once in a browser and use `auth import`, or ask Daman.
- **"that login belongs to <other GSTIN>, not <this one>"** — the username in that
  `GST_NN_` block is for a different registration. The session is discarded
  automatically. Check the `.env` block the message names.

## Never share the session file

After a login there is a file at
`%APPDATA%\gst-portal\session-<GSTIN>.json`. **It is the key to that
registration's GST account** — anyone holding it can act as you on a portal that
files statutory returns, without needing the password or a captcha.

- Never email it, never attach it to a ticket, never copy it to another PC.
- It is already outside the repo, so `git` cannot pick it up.
- If a PC is lost or handed over, delete the whole `%APPDATA%\gst-portal` folder
  and change the portal password.

The same goes for anything `snapshot` writes, and for the output of
`gst-portal.exe profile` — the profile carries the authorised signatory's name,
mobile number and email.

## When something looks wrong

| You see | It means |
|---|---|
| `no GST registrations configured` | The `.env` is missing or in the wrong folder — step 2 |
| Everything says "needs login" | Nothing has logged in yet, or every session has aged out |
| `read-only guard: …` | A command tried to reach something outside the allowlist. **Nothing was sent.** Report it |
| Rupee amounts show as `?` or boxes | Command Prompt's font, not a bug. Try Windows Terminal, or add `--json` |
| It logged you out of the portal in your browser | Expected — one session per username. See the banner at the top |
