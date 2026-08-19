---
title: JIVO CLI — Vision
created: 2026-07-30
updated: 2026-07-30
project: jivo-cli
type: vision
tags: [vision, strategy, sap, postgres, access]
---

# Vision — where this is going

> This folder is for **intent and direction**, not day-to-day work logs (those live in
> `chats/`) or system facts (those live in `connections/`, `README.md`, and memory).
> Seeded 2026-07-30 as a foundation; the actual tomorrow-intent gets filled in below.

## Where we are today (the honest baseline)

**The toolkit** — JIVO CLI is a read-only window into *every* JIVO business system: SAP
(3 companies), the app-layer CLIs (ecom/exim/factory/oms/jsap/control-panel), raw
Postgres, and the seller/HR portals (Blinkit/Zepto/TankhaPay). All strictly read-only.

**Access — solved from home (2026-07-30).** SAP HANA data (100%), the SAP Service Layer,
the ~105 GB of attachment files, and the Postgres server are all reachable off-office
through the goal-#96 reverse tunnel (`ssh jivo-sap-any`). Full runbook:
[`../connections/SAP-HOME-ACCESS.md`](../connections/SAP-HOME-ACCESS.md).

## The data landscape — two different worlds (and NO, one is not inside the other)

This is the thing to keep straight:

| | **SAP HANA** (the books) | **Postgres** (the apps) |
|---|---|---|
| What it is | The **financial system of record** — GL, journals, A/R & A/P invoices, ledgers, stock valuation, statutory books | The **operational databases under the day-to-day apps** — how work actually flows |
| Where | Linux box `jivo-dbsap` (138.252.101.222), HANA `:30015` | Postgres `103.89.45.76:5432` (via `postsql`) |
| Size | ~4.6 GB live books (Oil 3.11 / Mart 0.78 / Bev 0.68) | ~2.5 GB real data across 15 DBs |
| Holds data the other doesn't | detailed GL/journals, tax, cost valuation, posted accounting docs | `factory_flow` (gate→QC→production→dispatch steps), `order_management`/OMS, `jivo_ecom`, `CRM` (leads), `task` (tickets), `po_db`, `jivo_site` (website), `test_supabase` (app/auth) |

**They overlap only at the edges** (orders, invoices, parties exist on both sides — the
app records the *live workflow*, SAP records the *posted accounting entry*), and the app
side **syncs some things into SAP** (e.g. OMS pushes orders/invoices; ecom reads SAP
distribution). But most Postgres data — CRM leads, factory workflow granularity, tickets,
website, app users — **never lands in SAP**, and SAP's detailed accounting never lands in
Postgres. Mapping the joins between them is exactly what [`../connections/`](../connections/CONNECTIONS_MOC.md) is for.

**So: we do NOT "already have the Postgres data in SAP."** They are complementary systems,
partially synced, each large where the other is blind.

## What's solved · what's open

- ✅ Full read access to SAP (data + files) and Postgres, from anywhere.
- ✅ Credentials consolidated (`connections/*.env`, `chmod 600`, gitignored) + documented.
- 🔜 **The mirror** — pull HANA → our own Postgres on the VPS so SAP data survives an
  office-WAN outage (books ≈4.6 GB, trivial). Attachments = phase 2 (~105 GB). This is the
  next real move; approved direction.
- 🔜 Attachment bulk-pull into our own storage.

## Intent for tomorrow — (to be filled by Daman)

> _Empty — waiting on your direction. Tell me the goal and I'll turn it into a concrete plan here._
