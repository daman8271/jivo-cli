---
title: "EXIM endpoint — GET /director-inventorty/"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: endpoint
tags: [jivogpt, exim, api, endpoint]
method: GET
path: /director-inventorty/
category: director-inventorty
kind: read
resource: director_report
auth: bearer
---

# `GET /director-inventorty/`

> Director rollup: finished + at-factory + in-transit inventory by litre/MT.

## Request

| | |
|---|---|
| Method | `GET` |
| URL | `https://eximbe.jivo.in/director-inventorty/` |
| Auth | `Authorization: Bearer <access_token>` |
| Query params | — |
| Path params | — |

## Response — real sample (trimmed)

```json
{
  "finished": {
    "total": {
      "liter": 577771.0,
      "mts": 526
    },
    "BH-EC": {
      "liter": 12714.0,
      "mts": 12
    },
    "GP-FG": {
      "liter": 565057.0,
      "mts": 514
    }
  },
  "at_factory": {
    "total": {
      "total_lts": 1007088.0,
      "total_mts": 916.0
    },
    "in_tank": {
      "liter": {
        "total_liter": 892500.0
      },
      "mts": 812
    },
    "outside_factory": {
      "liter": 114588.0,
      "mts": 104.0
    }
  },
  "otw": {
    "liter": 266588.0,
    "mts": 243.0
  },
  "under_loading": {
    "liter": 46154.0,
    "mts": 42.0
  },
  "at_refinery": {
    "liter": 171933.0,
    "mts": 156.0
  },
  "mundra_port": {
    "liter": 0.0,
    "mts": 0.0
  },
  "on_the_sea": {
    "liter": 48352.0,
    "mts": 44.0
  },
  "in_contract": {
    "liter": 797560.0,
    "mts": 726.0
  }
}
```

## Field reference

Every leaf carries the same pair: `liter` (litres) and `mts` (metric tonnes).

- `finished` — finished-goods stock: `total` plus a breakdown by SAP warehouse code (`BH-EC`, `GP-FG`).
- `at_factory` — raw stock at the factory: `total` (`total_lts` litres / `total_mts` MT), split into `in_tank` (bulk oil in storage tanks; litres nested as `liter.total_liter`) and `outside_factory` (tankers parked outside, status OUT_SIDE_FACTORY).
- `otw` — stock ON_THE_WAY from port to factory.
- `under_loading` — stock at status UNDER_LOADING.
- `at_refinery` — stock at status AT_REFINERY.
- `mundra_port` — stock landed at MUNDRA_PORT (0 in sample).
- `on_the_sea` — shipments at status ON_THE_SEA.
- `in_contract` — quantity still at IN_CONTRACT (booked, not yet shipped).

## Used by pages

- [[pages/director-dashboard|Director Dashboard]]

## Related endpoints

- _(none)_

## Notes

- Kind: **read**. Resource permission group: `director_report`.
- Read-only GET; safe to call repeatedly.


Linked: [[API-INVENTORY]] · [[INDEX]]
