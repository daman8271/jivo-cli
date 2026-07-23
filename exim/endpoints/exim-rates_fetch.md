---
title: "EXIM endpoint — GET /exim-rates/fetch/"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: endpoint
tags: [jivogpt, exim, api, endpoint]
method: GET
path: /exim-rates/fetch/
category: exim-rates
kind: read
resource: exim_rates
auth: bearer
---

# `GET /exim-rates/fetch/`

> Fetch/refresh custom exchange (EXIM) rates.

## Request

| | |
|---|---|
| Method | `GET` |
| URL | `https://eximbe.jivo.in/exim-rates/fetch/` |
| Auth | `Authorization: Bearer <access_token>` |
| Query params | — |
| Path params | — |

## Response — real sample (trimmed)

```json
{
  "data": [
    {
      "currency": "Australian Dollar",
      "import": "66.50 ",
      "export": "63.60",
      "date": "2026-07-15T00:00:00.000Z",
      "notification_no": "20/2026"
    },
    {
      "currency": "Bahraini Dinar",
      "import": "266.20 ",
      "export": "236.30",
      "date": "2026-07-15T00:00:00.000Z",
      "notification_no": "20/2026"
    },
    "...(+21 more of 23)"
  ]
}
```

## Field reference

- `data` — array of customs exchange rate rows, one per currency:
  - `currency` — currency name (e.g. "Australian Dollar", "Bahraini Dinar").
  - `import` — customs exchange rate for imports, ₹ per unit of the currency (string, may carry a trailing space, e.g. "66.50 ").
  - `export` — customs exchange rate for exports, ₹ per unit of the currency (string, e.g. "63.60").
  - `date` — effective date of the rate, ISO 8601 timestamp (e.g. "2026-07-15T00:00:00.000Z").
  - `notification_no` — CBIC customs notification number the rates were published under (e.g. "20/2026").

## Used by pages

- [[pages/exim-rates|Exchange Rates]]

## Related endpoints

- _(none)_

## Notes

- Kind: **read**. Resource permission group: `exim_rates`.
- Read-only GET; safe to call repeatedly.


Linked: [[API-INVENTORY]] · [[INDEX]]
