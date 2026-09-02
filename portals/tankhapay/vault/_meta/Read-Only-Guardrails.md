---
tags: [tankhapay, meta, guardrails, safety]
---
# TankhaPay — Read-Only Guardrails

> This is a **READ-ONLY study of a live production HR/payroll system holding real employee data
> for JIVO (593 employees).** The same discipline as [[feedback_sap_readonly|SAP]] applies:
> **only ever READ. Never write.** No create / update / delete / approve / reject / pay / disburse /
> upload / import / send / punch / schedule / relieve / onboard — ever.

## Why this is high-stakes
- The account (`shunty@jivo.in`, role 2 "Business") can see and modify payroll, attendance, payouts,
  approvals for real employees. A stray write could disburse money, alter attendance, or fire someone.
- 333 of 726 endpoints are writes. They are **documented for understanding, never wired into the CLI.**

## Three-layer guardrail (mirrors the zepto/blinkit portal CLIs)
1. **Allowlist at the command layer** — the CLI only ever registers commands that map to a `READ`
   row in the endpoint inventory. Write endpoints have no command, no flag, no code path.
2. **Verb denylist in the HTTP client** — `client.go` refuses to send any request whose path matches
   the write-verb regex (`save|add|create|insert|update|edit|delete|remove|set|submit|approve|reject|
   assign|upload|import|register|send|verify|generate|process|pay|cancel|apply|revoke|reset|change|
   mark|initiate|release|disburse|deactivate|activate|enable|disable|store|renew|revert|withdraw|
   resend|allot|allocate|migrate|push|book|raise|settle|payout|deduct|terminate|relieve|onboard|
   punch|checkin`), regardless of how it was reached. Fails closed with an error.
3. **HTTP-method floor** — the client only issues the calls needed for reads (the login POST + the
   encrypted read POSTs). No PUT/PATCH/DELETE verbs are implemented at all.

## Classification method
- First pass: regex heuristic over the endpoint path (`get/fetch/list/view/report/…` = READ;
  `save/add/update/approve/…` = WRITE). Saved in `captures/endpoints-raw.tsv`.
- Second pass (Phase 2, per section): read the actual service call site in the JS to confirm the verb
  and payload, and **downgrade any ambiguous endpoint to out-of-scope rather than guess**. A few
  heuristic labels are wrong (e.g. `insert_birthday_wishes`, `send_wishes_email` are WRITES that the
  READ-regex mislabels) — the section notes are the source of truth, not the raw TSV.
- Probing: only ever `GET`-equivalent read POSTs against the **live** API, one at a time, and stop
  immediately on any 4xx/5xx/WAF signal. Never probe a write endpoint to "see what it does."

## Login hammering
Login attempts risk account lockout. During study, cap login probes to a handful; the CLI caches the
24h token and re-logs in **at most once per day** (or on 401), never in a loop.

See [[Auth-and-Access]] · [[Encryption-Scheme]] · [[Backends-and-Environment]]
