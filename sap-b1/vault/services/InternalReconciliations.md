---
entity: InternalReconciliations
domain: system-other-1
readable: true
methods: [GET, POST]
rows_oil: null
---
# InternalReconciliations
Internal reconciliation records matching open debits/credits on BP or G/L accounts. Live rows in JIVO_OIL_HANADB: unknown — the collection GET returned HTTP 502 during recon, so no count is available; only by-key GET is catalogued.

## Read it
```bash
cd ~/sap-b1/cli
# ⚠️ Collection GET 502s on this box — expect these to fail until the Service Layer behaves:
./sapb1 query InternalReconciliations --top 5
./sapb1 query InternalReconciliations --count
./sapb1 query InternalReconciliations --select "ReconNum,ReconDate,ReconType,Total" --top 10
# Narrowing server-side is the best shot at a working read (still a collection GET, may 502):
./sapb1 query InternalReconciliations --filter "ReconDate ge '2026-04-01'" --top 5
# Browse the catalogued operations offline instead:
./sapb1 ops InternalReconciliations
```

## Key fields
| Field | Meaning |
|---|---|
| ReconNum | Reconciliation number key |
| ReconDate | Reconciliation posting date |
| CardOrAccount | BP-based or G/L-account-based |
| ReconType | System/manual reconciliation type |
| Total | Reconciled amount total |
| InternalReconciliationRows | Matched transaction rows collection |

## Connections
- Domain: [[system-other-1]]
- [[BusinessPartners]] via ShortName on reconciliation rows — BP-side reconciliations (CardOrAccount = card)
- [[ChartOfAccounts]] via account code on reconciliation rows — G/L-side reconciliations (CardOrAccount = account)
- [[JournalEntries]] via TransId on reconciliation rows — the journal transactions being matched
