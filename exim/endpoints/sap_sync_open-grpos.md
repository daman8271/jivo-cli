---
title: "EXIM endpoint — GET /sap_sync/open-grpos/"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: endpoint
tags: [jivogpt, exim, api, endpoint]
method: GET
path: /sap_sync/open-grpos/
category: sap-sync
kind: sync
resource: open_grpos
auth: bearer
---

# `GET /sap_sync/open-grpos/`

> Open goods-receipt POs (SAP). **Sole GRPO source.**

## Request

| | |
|---|---|
| Method | `GET` |
| URL | `https://eximbe.jivo.in/sap_sync/open-grpos/` |
| Auth | `Authorization: Bearer <access_token>` |

## Namespace note (why tooling excludes it)

It sits in the `/sap_sync/` (underscore) namespace and its permission is
`open_grpos:[sync]`. Even though the response contains GRPO data, the request may
refresh SAP as a side effect. [[HARD-RULE]] therefore classifies it as a sync
operation and excludes it from both the generated CLI and the raw wrapper.

## Tooling status

Do not call this route from JivoGPT tooling. Use an already-synced safe source
when one becomes available; until then, GRPO freshness is unavailable through
the read-only connector.

## Response — real sample (trimmed)

```json
{
  "open_grpos": [
    {
      "GRPO Number": 2026076640,
      "Vendor Ref No": "190826018899",
      "User Name": "KULBIR SINGH",
      "Vendor Name": "AWL AGRI BUSINESS LIMITED",
      "Warehouse": "BH-GJ",
      "Pending Days": 4
    },
    {
      "GRPO Number": 2026076649,
      "Vendor Ref No": "VARPL/2627/01869",
      "User Name": "KULBIR SINGH",
      "Vendor Name": "VAISHNODEVI AGRO RESOURCES PRIVATE LIMITED",
      "Warehouse": "BH-GJ",
      "Pending Days": 3
    },
    "...(+3 more of 5)"
  ]
}
```

## Notes
- Powers [[pages/open-grpos|Open GRPOs]]. Part of [[API-INVENTORY]] · [[HARD-RULE]] · [[INDEX]]

Linked: [[API-INVENTORY]] · [[INDEX]]
