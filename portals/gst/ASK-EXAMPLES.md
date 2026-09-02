# GST portal — ask examples

Ten things Accounts actually asks about JIVO's GST registrations, and the command
that answers each. Everything is **read-only** and pulled **live** from
`gst.gov.in`. Nothing here files, generates, saves or pays anything.

> **First time:** see [`SETUP.md`](SETUP.md). Short version — put the `.env` next
> to `gst-portal.exe`, run `gst-portal doctor --offline`, then
> `gst-portal auth login --state haryana` and type the six digits from the captcha
> image it opens. On Windows use `gst-portal.exe` wherever this says `./gst-portal`.

**Pick a registration every time** with `--state <name|code>` or
`--gstin <GSTIN>` — `./gst-portal auth list` shows all eight. Periods are
`MMYYYY` (`--period 072026` = July 2026); financial years are `--fy 2026-27`;
dates are `YYYY-MM-DD` and `--to` is **inclusive**. Add `--json` for machine
output, `--agent` for a stable envelope.

## The ten

| You want to know… | Run |
|---|---|
| **1. How much ITC are we sitting on?** — the electronic credit ledger balance, split IGST / CGST / SGST / cess | `./gst-portal ledger credit --state haryana` |
| **2. Where did that ITC go?** — every credit-ledger movement this financial year, with the return period and ARN that consumed it | `./gst-portal ledger credit --state haryana --from 2026-04-01 --to 2026-08-21` |
| **3. Have we filed everything?** — GSTR-1 and GSTR-3B for the last five periods, filed or not, with the filing date | `./gst-portal returns calendar --state haryana` |
| **4. What is the ARN for July's 3B?** — the acknowledgement number and filing date for one form in one period | `./gst-portal returns status --state haryana --period 072026 --form GSTR3B` |
| **5. What did we declare in July?** — the filed GSTR-3B: outward taxable value, tax by head, RCM, ITC claimed, tax paid | `./gst-portal gstr3b summary --state haryana --period 072026` |
| **6. What ITC can we legally claim for July?** — GSTR-2B, summary **and** every supplier document behind it | `./gst-portal gstr2b summary --state haryana --period 072026` |
| **7. Which suppliers did not file?** — everyone who filed against us in a period, with their own GSTR-1 filing date and 3B status (a blank one is a supplier to chase) | `./gst-portal gstr2a suppliers --state haryana --period 072026` |
| **8. Does GSTR-1 agree with 3B?** — the portal's own comparison: declared vs actual liability, month by month, plus 2A/2B vs 3B ITC, for the whole year in one call | `./gst-portal compare --state haryana --fy 2026-27` |
| **9. Have we paid any interest or penalty?** — the cash ledger by head (`intr`, `pen`, `fee`), then the challans behind it | `./gst-portal ledger cash --state haryana` then `./gst-portal ledger challans --state haryana --from 2026-04-01 --to 2026-08-21` |
| **10. Give me everything for the year so I can tie it to SAP** — one login, one pull: every period's returns and ledgers, raw plus normalised, with a manifest | `./gst-portal snapshot --state haryana --fy 2026-27 --out ~/gst-snap` |

## Two more that come up

| … | Run |
|---|---|
| Every return we have ever filed this year, with who filed it | `./gst-portal returns filed --state haryana --fy 2026-27 --form GSTR1` |
| Our own registration details — legal name, jurisdiction, signatory | `./gst-portal profile --state haryana` ⚠️ contains the signatory's mobile and email; do not paste it into a shared ticket |
| The invoices behind a GSTR-1 section (878 B2B documents in Jul-26) | `./gst-portal gstr1 docs --state haryana --period 072026 --section B2B --ctin <customer GSTIN>` |
| Which state is which | `./gst-portal auth list` |

## Reading the answers

- **"No record found" is an answer, not a failure.** Exit code 0, `count: 0`.
  Rajasthan, UP and Maharashtra are nil filers — an empty GSTR-2B for them is
  correct, not a bug.
- **The ISD registration (Delhi ISD, `07AACCJ4223F2ZX`) files GSTR-6**, not
  GSTR-1/3B. Asking it for a 3B gets you an error, and `snapshot` skips those
  pulls for it on purpose.
- **Ignore `itcbalance.dt`.** It comes back as `16/02/0027` — a portal quirk. The
  statement dates from `ledger credit --from --to` are correct.
- **"session expired"** just means the fifteen-minute idle window closed. Run
  `auth login` again for that registration.
- **Punjab (`03AACCJ4223F1Z6`) will refuse to run.** Its password is wrong and the
  CLI will not retry it — that is deliberate. Get a corrected password from
  Accounts; do not try it by hand.
- One login per username: logging in here **ends any browser session** logged in
  as that user. Don't do it while somebody is filing.
