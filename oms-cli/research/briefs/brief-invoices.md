# Domain brief: invoices

17 paths. Live probe evidence and shipped command names are given per endpoint. Do not invent a command name for an endpoint that already has one.

## `/api/invoice/all`

- harvested methods: `GET`  | GET-capable: **True**
- lenses: shipped-only
- flags: NOT called by the current SPA
- **SHIPPED COMMAND (must not be renamed): `oms-pp-cli invoices all`**

  shipped spec block:
  ```yaml
          path: "/api/invoice/all/"
          description: "Invoice review queue (all invoices). Optionally filter by status."
          params:
            - name: status
              type: string
              description: "Status filter"
          response:
            type: object
        # NOTE (Phase-3 verify 2026-07-19): the live backend has NO /api/invoice/history/{id}/
        # route (only log/create, all, refLogs exist) — deployed API is out of sync with the
        # SPA bundle. This command is unregistered in the CLI until the backend confirms the route.
  ```

  live probe:
  - bare (no params) -> **HTTP 400**
    - server said: `{"error":"Warehouse Code is a required parameter."}`

## `/api/invoice/credit-limit/cards`

- harvested methods: `GET`  | GET-capable: **True**
- lenses: B-literal
- NEW — not in the shipped spec; needs a command name

  live probe:
  - bare (no params) -> **HTTP 200**, rows=1172, 176607 bytes, top-level JSON `dict`
    - sample: `{"success": true, "data": [{"cardCode": "CUSTA000025", "cardName": "HARPREET SINGH CASH SALE", "cardType": "CASH SALE", "balance": "15051.139800", "debtLine": "25000.000000", "creditLine": "25006.000000"}, {"cardCode": "CUSTA000017", "cardName": "FAIRDEAL MARKETING", "cardType": "ROI", "balance": "-`

## `/api/invoice/credit-limit/flow`

- harvested methods: `GET`  | GET-capable: **True**
- lenses: B-literal
- NEW — not in the shipped spec; needs a command name

  live probe:
  - bare (no params) -> **HTTP 400**
    - server said: `{"error":"invoice_id is a required parameter."}`

## `/api/invoice/credit-limit/request`

- harvested methods: `POST`  | GET-capable: **False**
- lenses: B-literal
- flags: multipart-upload, write-intent-keyword
- NEW — not in the shipped spec; needs a command name

  live probe: **not probed** (parameterised path, or write-intent — see WRITE_INTENT in probe.py)

## `/api/invoice/history/{}`

- harvested methods: `GET`  | GET-capable: **True**
- lenses: B-literal
- **SHIPPED COMMAND (must not be renamed): `oms-pp-cli invoices history`**

  shipped spec block:
  ```yaml
          path: "/api/invoice/history/{id}/"
          description: "Status-history timeline for an invoice (BACKEND ROUTE MISSING — unregistered)"
          params:
            - name: id
              type: int
              required: true
              positional: true
              description: "Invoice id"
          response:
            type: object
  ```

  live probe: **not probed** (parameterised path, or write-intent — see WRITE_INTENT in probe.py)

## `/api/invoice/logs/all`

- harvested methods: `GET`  | GET-capable: **True**
- lenses: B-literal
- NEW — not in the shipped spec; needs a command name

  live probe:
  - bare (no params) -> **HTTP 200**, rows=23, 37207 bytes, top-level JSON `list`
    - sample: `[{"id": 44, "supersedes_so_number": null, "supersedes_status": null, "supersedes_rejection_reason": null, "superseded_by_id": null, "fg_stock": [{"line_num": 0, "item_code": "FG0000032", "item_name": "COLD PRESS 1 LTR 20 PCS", "quantity": 60.0, "warehouse_code": "BH-PS", "warehouse_stock": 0.0}], "s`

## `/api/invoice/pending`

- harvested methods: `POST`  | GET-capable: **False**
- lenses: B-literal
- flags: write-intent-keyword
- NEW — not in the shipped spec; needs a command name

  live probe: **not probed** (parameterised path, or write-intent — see WRITE_INTENT in probe.py)

## `/api/invoice/{}/update-status`

- harvested methods: `PATCH`  | GET-capable: **False**
- lenses: B-literal
- NEW — not in the shipped spec; needs a command name

  live probe: **not probed** (parameterised path, or write-intent — see WRITE_INTENT in probe.py)

## `/api/legal/item`

- harvested methods: `GET, UNKNOWN`  | GET-capable: **True**
- lenses: B-literal, C-indirect
- flags: url-constant-only, write-intent-keyword
- NEW — not in the shipped spec; needs a command name

  live probe:
  - bare (no params) -> **HTTP 200**, rows=1, 97 bytes, top-level JSON `list`
    - sample: `[{"id": 1, "item_name": "Kachi Ghani Mustard Oil Pouch", "created_at": "2026-07-27T09:35:48.484272Z"}]`

## `/api/legal/item-nutrition`

- harvested methods: `GET`  | GET-capable: **True**
- lenses: C-indirect
- NEW — not in the shipped spec; needs a command name

  live probe:
  - bare (no params) -> **HTTP 200**, 24 bytes, top-level JSON `dict`
    - sample: `{"nutritional_facts": []}`

## `/api/legal/nutrition`

- harvested methods: `GET`  | GET-capable: **True**
- lenses: C-indirect
- NEW — not in the shipped spec; needs a command name

  live probe:
  - bare (no params) -> **HTTP 200**, rows=0, 2 bytes, top-level JSON `list`
    - sample: `[]`

## `/api/legal/uom`

- harvested methods: `GET`  | GET-capable: **True**
- lenses: C-indirect
- NEW — not in the shipped spec; needs a command name

  live probe:
  - bare (no params) -> **HTTP 200**, rows=0, 2 bytes, top-level JSON `list`
    - sample: `[]`

## `/api/legal/upload`

- harvested methods: `UNKNOWN`  | GET-capable: **False**
- lenses: B-literal
- flags: url-constant-only, write-intent-keyword
- NEW — not in the shipped spec; needs a command name

  live probe: **not probed** (parameterised path, or write-intent — see WRITE_INTENT in probe.py)

## `/api/sku/all`

- harvested methods: `GET`  | GET-capable: **True**
- lenses: B-literal
- **SHIPPED COMMAND (must not be renamed): `oms-pp-cli invoices skus`**

  shipped spec block:
  ```yaml
          path: "/api/sku/all/"
          description: "All SKUs"
          response:
            type: object
  ```

  live probe:
  - bare (no params) -> **HTTP 200**, rows=0, 2 bytes, top-level JSON `list`
    - sample: `[]`

## `/api/sku/pending`

- harvested methods: `GET`  | GET-capable: **True**
- lenses: B-literal
- **SHIPPED COMMAND (must not be renamed): `oms-pp-cli invoices skus-pending`**

  shipped spec block:
  ```yaml
          path: "/api/sku/pending/"
          description: "SKUs pending review"
          response:
            type: object
  ```

  live probe:
  - bare (no params) -> **HTTP 500**
    - server said: `TypeError at /api/sku/pending/
SalesOrderService.getFGItems() missing 1 required positional argument: 'branch'

Request Method: GET
Request URL: http://127.0.0.1:8001/api/sku/pending/
Django Version: 5.2.10
Python Executable: C:\LiveProjects\OMS\Backend\.venv\Scripts\python.exe
Python Version: 3.14.`
  - branch=BEVERAGE -> **HTTP 500**
    - server said: `TypeError at /api/sku/pending/
SalesOrderService.getFGItems() missing 1 required positional argument: 'branch'

Request Method: GET
Request URL: http://127.0.0.1:8001/api/sku/pending/?branch=BEVERAGE
Django Version: 5.2.10
Python Executable: C:\LiveProjects\OMS\Backend\.venv\Scripts\python.exe
Pytho`
  - branch=OIL -> **HTTP 500**
    - server said: `TypeError at /api/sku/pending/
SalesOrderService.getFGItems() missing 1 required positional argument: 'branch'

Request Method: GET
Request URL: http://127.0.0.1:8001/api/sku/pending/?branch=OIL
Django Version: 5.2.10
Python Executable: C:\LiveProjects\OMS\Backend\.venv\Scripts\python.exe
Python Ver`

## `/api/sku/upload`

- harvested methods: `UNKNOWN`  | GET-capable: **False**
- lenses: B-literal
- flags: url-constant-only, write-intent-keyword
- NEW — not in the shipped spec; needs a command name

  live probe: **not probed** (parameterised path, or write-intent — see WRITE_INTENT in probe.py)

## `/api/sku/{}`

- harvested methods: `UNKNOWN`  | GET-capable: **False**
- lenses: B-literal
- flags: url-constant-only, write-intent-keyword
- **SHIPPED COMMAND (must not be renamed): `oms-pp-cli invoices sku`**

  shipped spec block:
  ```yaml
          path: "/api/sku/{item_code}/"
          description: "Per-SKU detail"
          params:
            - name: item_code
              type: string
              required: true
              positional: true
              description: "SKU item code"
          response:
            type: object
  
    tracker:
      description: "Invoice-tracker sub-app (access-gated: returns 403 for non-tracker roles). Read endpoints for a tracker-enabled account."
      endpoints:
  ```

  live probe: **not probed** (parameterised path, or write-intent — see WRITE_INTENT in probe.py)
