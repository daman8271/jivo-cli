---
type: document
sap_tables: []
objtype:
companies: []
mined:
confidence:
---

# <Document name> — <plain-English one-liner>

> One sentence an operator would recognise: what this document *is* in the
> business, not in SAP.

## At a glance

| | |
|---|---|
| SAP tables | `OXXX` header, `XXX1` lines |
| ObjType | |
| Volume (last 120d) | Oil / Mart / Bev |
| Who keys it | |
| Drafted first? | |
| Needs approval? | |
| Comes from paper? | |

## Where it sits in the chain

What must exist before this document can be made, and what it feeds. Link the
neighbours: `[[GRPO]]` → **this** → `[[Outgoing-Payment]]`.

## Before you start — the pre-flight list

Everything you need in your hand or decided *before* opening the screen. This is
the part that makes tomorrow faster.

- [ ] …

## Fields that matter

Only the fields a human decides. Measured fill rates, and what each one means
here. Mark required / conditional / optional, and say what breaks without it.

| Field | Reads as | Filled | Required? | Notes |
|---|---|---:|---|---|

### Fields SAP offers that JIVO never uses

Worth stating — it stops the next person wondering.

## Dimensions

Branch, series, warehouse/location, cost centres, budget, project — with the
actual values in play.

## Tax

GST (which codes, which side), RCM, TDS/withholding: what appears, when, and what
SAP fills in versus what you must.

## The journal it posts

The GL fingerprint from `gl.py`. Then: how to tell a *correct* posting from a
plausible-but-wrong one.

## Real examples

Two or three genuine documents, trimmed to the fields that matter, showing the
common shape and at least one awkward variant.

## Traps

Numbered, concrete, each with the evidence. Cross-reference `harness/corrections/`
by ID where one applies.

## How to create it from the CLI

Payload skeleton and the pre-checks worth running first. Draft-first. If this
document type cannot be created from the CLI today, say so plainly.

## Verify after saving

The read-back checklist — what SAP silently left blank or filled differently from
what you sent.

## Open questions

What is still unknown, and the query or the person that would settle it.

## Queries used

```sql
```
