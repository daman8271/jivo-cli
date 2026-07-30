# dsr — ask examples

Plain-English questions the DSR field-sales tool can answer, and the command to
run. Everything is **read-only** and pulled **live** from `DSR_V6`. Add `--json`
for machine output; `-n N` caps rows; dates are `YYYY-MM-DD` (`--from` inclusive,
`--to` exclusive).

> First time: `cp .env.example .env`, fill `DSR_USER/DSR_PASSWORD`, `go build -o dsr .`, then `./dsr doctor`.

## Sales (secondary — distributor → retailer)
| You want to know… | Run |
|---|---|
| Field visits by a salesperson last month | `dsr sales visits --salesperson 4927 --from 2026-07-01 --to 2026-08-01` |
| What products were sold on one visit | `dsr sales lines <salesId>` |
| Total sale value/pieces over a period | `dsr sales summary --from 2026-07-01 --to 2026-08-01` |
| Item-wise litres for a month (this is the number the portal dashboard shows) | see "worked example" below |
| Promoter in-store sales | `dsr promoters visits --from 2026-07-01 --to 2026-08-01` |

## Retailers / outlets
| … | Run |
|---|---|
| How many live retailers / distributors | `dsr retailers count` · `dsr retailers count --type Distributor` |
| List outlets in a state | `dsr retailers list --state 5 -n 50` |
| One outlet's full record | `dsr retailers get <id>` |
| Distributor's mapped shops | `dsr distributors shops <distId>` |

## People, beats & coverage
| … | Run |
|---|---|
| The field workforce | `dsr salespersons list` · `dsr salespersons get <id>` |
| A manager's team | `dsr salespersons subordinates <managerId>` |
| Which shops are on a beat | `dsr beats shops <beatId>` |
| Beat schedule for a period | `dsr beats assignments --from 2026-07-01 --to 2026-07-31` |

## Attendance & GPS
| … | Run |
|---|---|
| Who was present, by date | `dsr attendance list --salesperson 4927 --from 2026-07-01 --to 2026-07-31` |
| Present-day counts per person | `dsr attendance summary --from 2026-07-01 --to 2026-07-31` |
| One person's GPS track for a day (date window required) | `dsr geo track <personId> --from 2026-07-01 --to 2026-07-02` |

## Stock, targets, schemes, distributors, primary, ecom
| … | Run |
|---|---|
| A retailer's / distributor's stock | `dsr stock retailer <id>` · `dsr stock distributor <id>` |
| Monthly targets for a person | `dsr targets person <userId>` |
| Scheme products sold / gifts | `dsr schemes list-sold --from 2026-07-01 --to 2026-08-01` · `dsr schemes gifts` |
| Primary sales (JIVO → distributor) | `dsr primary list --from 2026-07-01 --to 2026-08-01` |
| Marketplace (Amazon/Flipkart) sales | `dsr ecom sales --from 2026-07-01 --to 2026-08-01` |

## Cross-check against the portal
| … | Run |
|---|---|
| The portal's own item-wise sale for a month | `dsr portal item-sale --month "July,2026"` |
| Portal monthly litres | `dsr portal monthly-sale --from 2026-07-01 --to 2026-07-31` |
| Unapproved-sales count the portal shows | `dsr portal unapproved-count` |

## Explore / raw SQL
| … | Run |
|---|---|
| What tables exist (biggest first) | `dsr schema tables` |
| Peek at any table | `dsr peek tbl_SalesReport -N 5` |
| Count anything | `dsr count tbl_salesPersonAttendance --where "..."` |
| Any read-only query | `dsr query "SELECT … "` (SELECT/WITH only; writes are rejected) |

## Worked example — item-wise litres for July (matches the portal exactly)
```bash
dsr query "SELECT ps.productName, SUM(ps.pieces) AS pieces, SUM(ps.totalQuantity) AS qty
  FROM tbl_ProductsSold ps JOIN tbl_SalesReport sr ON sr.salesId = ps.salesId
  WHERE sr.date >= '2026-07-01' AND sr.date < '2026-08-01'
    AND ISNULL(sr.deleted,0)=0 AND ps.productId > 0
  GROUP BY ps.productName ORDER BY SUM(ps.pieces) DESC"
```

## Gotchas (the tool handles most, but when writing raw SQL)
- Live rows only: `ISNULL(deleted,0)=0`. Drop sentinel product lines: `productId > 0`.
- Empty dates are `1899-12-30` — always bound date ranges.
- `-1` on an id means "all/unset". Distributors are `tbl_retailers` rows with `type='Distributor'`.
- Master keys are `tbl_salesperson.ID`, `tbl_retailers.Id`, `tbl_item.Id` (not the `personId`/`retailerId` alias). Full map: `study/vault/00-INDEX.md`.
