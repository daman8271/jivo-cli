---
name: jivo-tds
description: Not an entry skill. Every A/P entry skill runs `tds.py apply` on its payload before `sapb1 draft` and `tds.py check` on the new draft after it. Also use when asked why a bill does or doesn't carry TDS, or whether a draft's TDS is right.
---

# TDS on A/P bills: transporters and goods

Operators never work out TDS by hand. The rules below come from Daman and Divjot (Accounts), 17 Sept 2026, and they override anything in other skills. Every number is in `bin/tds_rules.json`. The rate always comes from SAP's own withholding table in that book.

## The two rules

**1. Transporters** (vendor group TRANSPORTER)
- **Declaration on file = no TDS:** PANs AGSPN9633Q (AIR TRANS), BZQPP0903H (BHARGAVE ROAD CARRIER), AANFD7642N (DELHI PUNJAB TRANSPORT CO), AAQCP4145A (PICK & SHIP), plus card VENDA000108 (DELHI PUNJAB CARRIER). This holds in all 3 books, even where the card sits in another group.
- **Every other transporter:** 2% on the whole bill from the first rupee, even if the card says 1%. The code is the card's 1024 or C194, otherwise 1024.

**2. Goods** (item bills from anyone who is not a transporter)
- Add up everything bought from the vendor this year (1 April up to the bill's date), before GST: posted A/P invoices minus A/P credit notes (a credit note against last year's invoice does not count), plus A/P drafts already with the approver (so bills entered together can't each slip under the limit). The vendor is found **by PAN** (the card's PAN, otherwise read from its GSTIN) in every book. Oil and Beverages count together; Mart counts alone.
- TDS is **0.1% only on the part of this bill above ₹50 lakh**. The code is the card's 1031 or TDS, otherwise 1031.
- Vendors in the IMPORT & EXPORT group get no TDS.

**Everything else** (service bills from non-transporters, credit notes): `apply` leaves the payload exactly as the skill built it.

## The two commands (run from the repo root; use `python` on Windows)

```
python3 .claude/skills/jivo-tds/bin/tds.py apply <payload.json> --company OIL|MART|BEV [--out FILE]
python3 .claude/skills/jivo-tds/bin/tds.py check <DocEntry> --company OIL|MART|BEV
```

- `apply` sets WTax Liable on every line and writes the withholding rows (code, taxable amount, TDS). It prints one line explaining why. A payload without `DocObjectCode` is treated as an A/P invoice (that is what `sapb1 draft purchase-invoice` sends).
- `check` reads the draft back from SAP and compares it with the rules, allowing ₹1 either way.
- Add `--json` for machine-readable output. **Never send a draft after a STOP**, and never pipe the output through `tail`.

## What the messages mean and who acts

| Message | Meaning | Who fixes |
|---|---|---|
| `PASS` (exit 0) | The TDS on the draft matches the rules (service bills: nothing half-done) | nobody |
| `… TDS left as the skill set it` (exit 0) | Service bill or credit note; not this calculator's job | the entry skill |
| `MISMATCH — TDS was calculated but not applied — open the draft in SAP B1 and save it once` (exit 3) | Lines are ticked or tax rows exist, but SAP's TDS total is still ₹0 | the operator: open the draft, save once, run `check` again |
| `MISMATCH — the rules say ₹X TDS …, the draft deducts ₹Y` (exit 3) | The draft carries the wrong TDS or none | whoever made the draft: set Withholding Tax in SAP B1, then run `check` again |
| `STOP — … not marked TDS-liable …` (exit 2) | TDS is due but SAP won't deduct it for this card | whoever keeps vendor masters ticks it on the card |
| `STOP — … more than one PAN …` (exit 2) | The vendor card is inconsistent | whoever keeps vendor masters |
| `STOP — … OWHT has code … but tds_rules.json says …` (exit 2) | SAP's rate differs from the rulebook | Divjot |
| `STOP — this bill is in EUR/USD …` (exit 2) | A foreign-currency bill | Divjot decides it |
| `STOP — SAP HANA unreachable / read failed` or `unexpected …` (exit 2) | SAP could not be read or the input broke the calculator, so nothing was decided | try again; tell Daman if it persists |
| `STOP — … no LineTotal …` / `not a vendor card` / `draft … not there` (exit 2) | Bad input: payload, CardCode, `--company` or DocEntry | the operator or the entry skill |
| exit 1 | The command was typed wrong | the operator |

## Notes

- A "no PAN" note means the vendor was counted by vendor code only. The same code in the other book is counted only when it is the same party (codes often mean different parties across books).
- Tests: `python3 .claude/skills/jivo-tds/bin/test_tds.py` (uses a fake SAP, no network).
