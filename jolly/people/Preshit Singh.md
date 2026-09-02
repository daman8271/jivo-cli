---
name: Preshit Singh
aliases: ["Preshit", "Preshit Thakur", "Preshit Jivo"]
type: person
org: JIVO
title: "Monthly planning and billing head"
function: [planning, billing]
seniority: head
whatsapp: "+918178047679"
waid: "918178047679"
phone_display: "+91 81780 47679"
email: preshit@jivo.in
company: [Oil, Mart, Beverages]
emp_code: JWPL0030
reports_to: "[[Avtar Vg]]"
escalate_to:
approval_limit:
site:
language:
tone:
hours:
role_stated_by: "[[Gurvinderjeet Singh]]"
source: "WhatsApp — Gurvinderjeet Singh, 2026-08-11 18:23 IST"
verified_against: [JSAP, SAP B1, factory app, OMS, prior work]
last_verified: 2026-08-11
status: confirmed
tags: [jivo/person, jivo/planning, jivo/billing]
---

# Preshit Singh

*Real name: **Preshit Thakur***

> [!quote] Role, in Gurvinderjeet's exact words
> **"Monthly planning and billing head"**
> — WhatsApp, 11 Aug 2026, 18:23

> [!success] CONFIRMED — all four systems agree

## Why this person matters

Confirmed in every system, with the same employee code throughout — **JWPL0030** in JSAP, in the factory app and in SAP. He is **Sub-HOD of Accounts & Finance (Accounts Receivable) with 14 direct reports**, the largest team any of the ten runs.

**Billing checks out completely.** SAP puts his department as `BILLING`, he is the *sole* approver on the OMS invoice stage `cl oil int 1`, and he has his own named saved-query set inside SAP. **Monthly planning left no system trace — and Daman has explained why: he does it
by hand, in Excel.** So the absence was not a mistake in the search; it is the
finding. The single most important input to this whole pilot — the monthly plan —
exists only as a spreadsheet on somebody's PC.

> [!danger] The plan has no system source. This is the pilot's hardest dependency.
> The August workbook was authored on a Windows account `Jivo112`, saved to a
> `Downloads` folder, and pulls its e-commerce column via a `VLOOKUP` into
> *another* Excel file on *another* machine. There is no version, no date, no
> approver, no audit trail, and a missing SKU silently becomes zero.
>
> Anything the pilot computes downstream — what to produce, what to buy, whether
> it is feasible — inherits whatever is in that file. **Getting a reliable feed
> of Preshit's plan is step one, before any of the clever parts.**

## Verified identity

| | |
|---|---|
| **Real name** | **Preshit Thakur** on one SAP card, **Preshit Singh** on another — same phone, same user slot, one man |
| **Employee code** | **JWPL0030** — identical in JSAP, factory app and SAP |
| **JSAP** | emp 16 · **Sub-HOD, Accounts & Finance › A/R** · **14 direct reports** · reports to **Avtar Vg (JWPL0014, HOD Accounts & Finance)** |
| **SAP** | `USER11` (USERID 20, all three DBs) · dept **BILLING** · logged in 11 Aug |
| **factory app** | user 27 · preshit@jivo.in · active |
| **OMS** | 481 sales orders created · **sole approver on invoice stage `cl oil int 1`** |
| **control-panel** | logs in as `preshit` = Admin, but **explicitly denied COGS / margin data** (`can_cogs:false`) |

## OMS

| | |
|---|---|
| **Account** | `preshit` (id 2) — **`admin`, is_staff, is_superuser** |
| **Authority** | **He owns the global approval-flow config** (`orders flow-config.updated_by = "preshit"`, set 2026-06-25) — i.e. he decides whether the rate-approval, billing and auditor stages are switched on at all |
| **Activity** | only 2 orders raised, 2 log actions — his footprint is *configuration*, not volume |
| **Devices** | **49 registered devices** (Android + iOS + Web) — the most of any OMS user |
| **Last seen** | 11 Aug 2026, 12:29 |
| ⚠️ **Duplicate** | a second dormant account `preshit_singh` (id 51), `manager`, 27 main-groups, all 27 states, **never logged in** |

> [!note] This is the largest single piece of authority found on anyone
> He controls whether OMS's approval stages exist. That is a config switch over
> the whole order workflow, and it sits with one person.

## Reporting line

- **Reports to:** [[Avtar Vg]] — HOD, Accounts & Finance (JWPL0014)
- **Manages:** 14 people: Harpreet Singh, Sadaf Sartaj, Sumit Kumar Mehta, Mansi, Jaspal Singh, Paramjeet Kaur, Amandeep Singh, Krishan Preet, Gurleen Kaur, Jagpreet Singh, Gurpreet Kaur, Manpreet Kaur (+2)

> [!success] Both halves of his title are real — confirmed by Daman, 11 Aug
> **Billing:** SAP department `BILLING`, sole approver on the OMS invoice stage,
> his own SAP saved-query set. **Planning: yes, and he does it manually in Excel** —
> which is exactly why no system search found it. JSAP files him under Accounts › A/R
> because that is his *department*, not the whole of his job.

> [!danger] Traps — read before searching for this person
> ⚠️ The warehouses `BH-PS`, `DL-PS`, `PB-PS` contain "PRESHIT" and are **not his**. *Preshit* (प्रेषित) is the word for *dispatched/sent* — `DL-PS`'s address is Gurdwara Rakab Ganj Sahib. These are langar/samagam free-issue stock. ~30 rows will false-positive on any name search.

## Owns
<!-- The decisions this person can make ALONE, with no one else's sign-off.
     This is the single field that decides who gets a message. -->

- [ ] _to fill_

## Needs approval from

- [ ] _to fill_

## Escalate to
<!-- Provisional: [[Gurvinderjeet Singh]] — he owns the roster. NOT confirmed. -->

- [ ] _to fill_ — after _to fill_ hours of silence

## Message triggers
<!-- The operational core: what event makes the system message this person,
     what it says, and what happens when they don't reply. -->

| Trigger event | What we ask them | Reply we need | Chase after | Then escalate to |
|---|---|---|---|---|
| | | | | |

## How to talk to them

- **Language:** _unknown_ <!-- Hindi / Punjabi / English / mixed -->
- **Register:** _unknown_ <!-- formal, casual, respectful (veerji / ji) -->
- **Best hours:** _unknown_
- **Prefers:** _unknown_ <!-- text / voice note / call -->
- **Do not:** _unknown_

## Notes

_(free text — anything learned about how they actually work)_

## Open questions

- [ ] **Is "monthly planning" still current?** Every system says Accounts/AR and Billing.
- [ ] He runs 14 people — is that team relevant to this pilot?
- [ ] He is the *only* approver on OMS invoice stage `cl oil int 1`. What happens when he's away?
- [ ] He is walled off from COGS data in the control panel. Deliberate?
- [ ] Does his authority cover all three books, or only Wellness (Oil+Bev)?

## Log

- **2026-08-11 18:23** — contact card and role line from [[Gurvinderjeet Singh]] over WhatsApp.
- **2026-08-11 evening** — cross-checked against the JSAP org hierarchy, SAP B1 (all three
  company databases), the factory app, OMS and everything already written in the repo.
  Verdict: **CONFIRMED — all four systems agree**.
