---
type: document
sap_tables: [OBTF, BTF1, OJDT]
objtype: -1
companies: [OIL, MART, BEV]
mined: 2026-08-24
confidence: high
---

# Journal Voucher — the parked journal, and the main route into the ledger

> A journal entry saved but not posted, waiting for review. 4,933 across the books. And it
> turns out to be the **majority** path for manual journals, not the exception.

## At a glance

| | |
|---|---|
| SAP tables | `OBTF` batch header · `BTF1` lines · posts into `OJDT`/`JDT1` |
| Key | **`BatchNum`** — see the trap below |
| Volume | Oil 3,245 · Mart 791 · Bev 897 · **4,933** |
| Lines | 21,093 in Oil — about **6.5 lines per voucher** |
| Status | `BtfStatus` `C` posted 3,102 · **`O` unposted 143** |
| Oldest unposted | **2024-10-31** — nearly two years parked |
| Who keys them | Dolly 617 · Kamaljeet/HR 473 · Prashant 472 · Avtar 297 · Harsh 215 · Lovpreet 196 · Navdeep 191 · Neetu 189 · Ishwendra 145 · Taran 114 |

## It is the main road, not a siding

Oil has **5,235** manual journal entries (`OJDT."TransType"` = 30). Of those, **3,102 carry
a `BatchNum`** — exactly matching the 3,102 vouchers with `BtfStatus` = `C`.

| Route into the ledger | Journals | Share |
|---|---:|---:|
| **Posted from a parked voucher** | **3,102** | **59%** |
| Keyed directly as a journal entry | 2,133 | 41% |

So the normal way a manual journal reaches the books at JIVO is: **park it as a voucher, have
it reviewed, post it.** Anyone treating the voucher as an unusual "held for review" case has
it backwards. → [[Journal-Entry]]

## The trap: `TransId` is not the key, and joining on it explodes

`OBTF` and `BTF1` both have a `TransId` column. It looks like the obvious link. It is not.

| | Rows | Distinct `TransId` | Distinct `BatchNum` |
|---|---:|---:|---:|
| `OBTF` | 3,245 | **5** | 3,223 |
| `BTF1` | 21,093 | **5** | — |

**Five distinct values across 3,245 rows.** `TransId` on a voucher is effectively a constant
(*inferred:* a status or type code that SAP reuses, not an identifier).

The consequence:

```
BTF1 joined to OBTF on TransId   ->  67,818,963 rows
BTF1 joined to OBTF on BatchNum  ->      21,310 rows   (21,093 lines exist)
```

**A 3,200× cartesian explosion, and it does not error** — it returns tens of millions of
plausible-looking rows. Any total computed that way is garbage at a scale nobody would
notice from the shape of the result.

> **Use `BatchNum`.** And note it is not perfectly unique either: 21,310 joined rows against
> 21,093 real lines means ~217 duplicate matches. Verify with a count before trusting an
> aggregate.

This is the third distinct key-naming trap in this vault, after `VPM2`/`RCT2` where `DocNum`
holds the header's `DocEntry`. **Count your join before you trust it** is turning into a
house rule. → [[Field-Name-Rosetta]]

## Tracing a posted voucher to its journal

`OJDT` carries `BatchNum`, `BtfLine` and `BtfStatus` — so the link **does** exist, just not
through `TransId`:

```sql
-- the journal a voucher became
SELECT J."TransId", J."RefDate", J."Memo"
FROM "JIVO_OIL_HANADB"."OJDT" J
WHERE J."BatchNum" = <the voucher's BatchNum>;

-- and back the other way: which journals came from a voucher at all
SELECT COUNT(*) JOURNALS,
       SUM(CASE WHEN "BatchNum" IS NOT NULL AND "BatchNum"<>0 THEN 1 ELSE 0 END) FROM_VOUCHER
FROM "JIVO_OIL_HANADB"."OJDT" WHERE "TransType"=30;
-- 5,235 / 3,102
```

Note that `OBTF."TransId"` does **not** match any `OJDT."TransId"` — 0 of 3,245. Posting a
voucher creates a **new** journal with its own `TransId`; the voucher's is not carried over.
So `TransId` is useless in both directions here.

## The 143 unposted vouchers

`BtfStatus` = `O`, oldest dated **2024-10-31**. These are journals somebody wrote, parked for
review, and nobody ever posted — sitting for up to two years.

They have **no ledger effect**: an unposted voucher is not in `OJDT`, so it appears in no
balance, no ageing, no P&L. Which is exactly why it can sit for two years without anyone
noticing.

Worth a list at month-end. `143` is small enough to work through, and each one is either a
real entry someone forgot or a draft that should be deleted.

## Fields

| Field | Reads as |
|---|---|
| `BatchNum` | **The key.** Use this for every join |
| `BtfStatus` | `O` parked · `C` posted |
| `TransType` | The journal type it will become (30 for manual) |
| `RefDate` | The posting date it will use |
| `Memo` | What the entry is for — the operator's own words |
| `BaseRef`, `Ref1`, `Ref2` | References |
| `LocTotal` / `FcTotal` / `SysTotal` | The batch total, three currencies |
| `CreatedBy` | |
| `TransId` | **Ignore it.** 5 distinct values across 3,245 rows |

## Can the CLI make one?

**No.** `sapb1` has four write commands — `draft`, `post`, `patch`, `delete draft` — and
`draft` covers document types held in `ODRF`. A journal voucher lives in `OBTF`, which is not
a document draft and is not in the `draft` command's catalogue.

This is a statement about the code, not a policy: **nobody has written a write path for
journal vouchers.** Same for journal entries themselves. If that is needed, it would have to
be built. → [[Journal-Entry]]

## Traps

1. **Never join `OBTF` to `BTF1` on `TransId`** — 5 distinct values, 3,200× explosion, no
   error. Use `BatchNum`.
2. **`OBTF."TransId"` matches nothing in `OJDT`.** Posting creates a fresh `TransId`.
3. **59% of manual journals come through here.** Do not model the voucher as an edge case.
4. **An unposted voucher has zero ledger effect** and will not show up in any financial
   report — which is why 143 of them have gone unnoticed, one for nearly two years.
5. **`BatchNum` is nearly but not perfectly unique** (3,223 distinct for 3,245 rows). Count
   before aggregating.
6. **HR is a heavy user** — Kamaljeet/HR keys 473. So payroll and incentive entries route
   through vouchers, which means an Accounts person reviewing the parked queue is reviewing
   other departments' work too.

## Open questions

1. **What are the 5 `TransId` values?** If they are a status or type enum they are worth
   decoding; if they are junk, worth saying so.
2. Who **reviews and posts** a parked voucher? The creator is recorded (`UserSign` /
   `CreatedBy`); the poster may not be. If it is the same person, the review step is
   nominal.
3. The 143 unposted — cluster them by creator and date. Is this a backlog with an owner or
   abandoned work?
4. What are the ~217 duplicate `BatchNum` join matches?
5. Why do Mart (791) and Beverages (897) run comparable voucher volumes to Oil (3,245) when
   their manual-journal counts are much lower? Different review culture per book?
6. `BtfLine` on `OJDT` — presumably the voucher line a journal line came from. Unverified.

## Queries used

```sql
-- the key is BatchNum, not TransId
SELECT (SELECT COUNT(*) FROM "JIVO_OIL_HANADB"."OBTF") AS OBTF_ROWS,
       (SELECT COUNT(DISTINCT "TransId")  FROM "JIVO_OIL_HANADB"."OBTF") AS OBTF_DISTINCT_TRANSID,
       (SELECT COUNT(DISTINCT "BatchNum") FROM "JIVO_OIL_HANADB"."OBTF") AS OBTF_DISTINCT_BATCH,
       (SELECT COUNT(*) FROM "JIVO_OIL_HANADB"."BTF1") AS BTF1_ROWS,
       (SELECT COUNT(DISTINCT "TransId")  FROM "JIVO_OIL_HANADB"."BTF1") AS BTF1_DISTINCT_TRANSID
FROM DUMMY;
-- 3,245 / 5 / 3,223 / 21,093 / 5

-- the explosion, measured
SELECT (SELECT COUNT(*) FROM "JIVO_OIL_HANADB"."BTF1" L
          JOIN "JIVO_OIL_HANADB"."OBTF" O ON O."TransId"=L."TransId")  AS VIA_TRANSID,
       (SELECT COUNT(*) FROM "JIVO_OIL_HANADB"."BTF1" L
          JOIN "JIVO_OIL_HANADB"."OBTF" O ON O."BatchNum"=L."BatchNum") AS VIA_BATCHNUM
FROM DUMMY;
-- 67,818,963  vs  21,310

-- status and the parked backlog
SELECT "BtfStatus", COUNT(*) N, MIN("RefDate") OLDEST, MAX("RefDate") NEWEST
FROM "JIVO_OIL_HANADB"."OBTF" GROUP BY "BtfStatus";
-- O 143 (2024-10-31 -> 2026-08-19) | C 3,102

-- how many manual journals came from a voucher
SELECT COUNT(*) JOURNALS,
       SUM(CASE WHEN "BatchNum" IS NOT NULL AND "BatchNum"<>0 THEN 1 ELSE 0 END) FROM_VOUCHER
FROM "JIVO_OIL_HANADB"."OJDT" WHERE "TransType"=30;
-- 5,235 / 3,102 = 59%
```

Profile: `_data/profile-OBTF.md`, `profile-BTF1.md`.
