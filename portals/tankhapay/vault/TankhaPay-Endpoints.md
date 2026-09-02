---
tags: [tankhapay, meta, index, coverage, source-of-truth]
---
# TankhaPay — Master Endpoint Index & Coverage Audit

Every endpoint across the four backends, grouped by the 14 studied sections. Each request is an AES-encrypted POST — the body is `{"encrypted": base64(AES-ECB(payload))}` and the reply carries `commonData` (AES-ECB, same key) — see [[Encryption-Scheme]] and [[Auth-and-Access]]. Reads are wired into the CLI; writes/unknowns are documented but never wired ([[Read-Only-Guardrails]]).

| Section | READ | WRITE | UNKNOWN | Note |
|---|--:|--:|--:|---|
| [[Dashboard]] | 11 | 1 | 0 | `Dashboard.md` |
| [[Employee-Management]] | 50 | 76 | 21 | `Employee-Management.md` |
| [[Attendance]] | 37 | 68 | 6 | `Attendance.md` |
| [[Leave-Management]] | 19 | 29 | 6 | `Leave-Management.md` |
| [[Payouts]] | 11 | 34 | 4 | `Payouts.md` |
| [[Approvals]] | 19 | 15 | 0 | `Approvals.md` |
| [[Accounts-Taxes]] | 9 | 13 | 0 | `Accounts-Taxes.md` |
| [[Reports]] | 59 | 0 | 0 | `Reports.md` |
| [[Recruit-ATS]] | 3 | 9 | 11 | `Recruit-ATS.md` |
| [[Masters-Config]] | 47 | 14 | 9 | `Masters-Config.md` |
| [[Org-User-Management]] | 28 | 51 | 7 | `Org-User-Management.md` |
| [[Broadcast-Visitor-Help]] | 12 | 11 | 1 | `Broadcast-Visitor-Help.md` |
| [[Contract-Labour-Inventory]] | 9 | 4 | 6 | `Contract-Labour-Inventory.md` |
| [[Training-Performance]] | 8 | 8 | 0 | `Training-Performance.md` |
| **TOTAL** | **322** | **333** | **71** | **726 endpoints** |

## Coverage audit

- **Total endpoints:** 726  (READ 322 · WRITE 333 · UNKNOWN 71)
- **Wired read commands:** 297  = 287 confirmed reads + 10 promoted from UNKNOWN (owner request). 35 extractor-mis-tagged reads were reclassified to write — see `../captures/reclassified-writes.tsv`.
- **Promoted-from-UNKNOWN (10):** path passes the read-only guardrail but behaviour is NOT live-verified — treat with caution (some `*Actions`/`manage_*` endpoints may dispatch mutations if given a write action). 61 UNKNOWNs were kept OUT (auth/session + write-verb paths) — see `../captures/unknown-excluded.tsv`.

**(a) Every endpoint in exactly one section**
- endpoints in zero sections: **0**
- endpoints in more than one section: **0**
- ✅ 0 gaps

**(b) Every wired READ documented in its section note**
- wired reads checked: **297**; undocumented: **0**
- ✅ 0 gaps — every wired read appears in its section note

**(c) Routes (pages + subpages)**
- routes enumerated in [[Pages-and-Routes]]: **325** (all mapped to a section there)

---
[[00-TankhaPay-Atlas]] · [[Encryption-Scheme]] · [[Auth-and-Access]] · [[Backends-and-Environment]] · [[Read-Only-Guardrails]] · [[Pages-and-Routes]]
