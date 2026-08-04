# Domain brief: sap

11 paths. Live probe evidence and shipped command names are given per endpoint. Do not invent a command name for an endpoint that already has one.

## `/api/sap/addresses`

- harvested methods: `GET`  | GET-capable: **True**
- lenses: A-callsite
- **SHIPPED COMMAND (must not be renamed): `oms-pp-cli sap addresses`**

  shipped spec block:
  ```yaml
          path: "/api/sap/addresses/"
          description: "SAP addresses"
          response:
            type: object
  ```

  live probe:
  - bare (no params) -> **HTTP 200**, rows=35722, 11798113 bytes, top-level JSON `list`
    - sample: `[{"id": 12220, "card_code": "CUSTA000001", "address_name": "BHARTI MACHINERY TOOLS DELHI", "address_type": "S", "gst_number": "07AGTPB8563G1Z1", "full_address": "1ST FLOOR HOUSE NO L-835 836 885 886 JJ COLONY VILLAGE BAWANA NEW DELHI DL IN 110039", "state": "DL", "city": "NEW DELHI", "zip_code": "11`

## `/api/sap/approve-sales-order`

- harvested methods: `POST`  | GET-capable: **False**
- lenses: A-callsite
- NEW — not in the shipped spec; needs a command name

  live probe: **not probed** (parameterised path, or write-intent — see WRITE_INTENT in probe.py)

## `/api/sap/branches`

- harvested methods: `GET`  | GET-capable: **True**
- lenses: A-callsite
- **SHIPPED COMMAND (must not be renamed): `oms-pp-cli sap branches`**

  shipped spec block:
  ```yaml
          path: "/api/sap/branches/"
          description: "SAP branches"
          response:
            type: object
  ```

  live probe:
  - bare (no params) -> **HTTP 200**, rows=22, 3666 bytes, top-level JSON `list`
    - sample: `[{"id": 9, "bpl_id": 1, "bpl_name": "DELHI", "category": "BEVERAGES", "is_active": false, "created_at": "2026-03-03T12:42:40.149149Z", "updated_at": "2026-08-04T05:54:06.112584Z"}, {"id": 10, "bpl_id": 2, "bpl_name": "FACTORY", "category": "BEVERAGES", "is_active": false, "created_at": "2026-03-03T1`

## `/api/sap/logs`

- harvested methods: `GET`  | GET-capable: **True**
- lenses: A-callsite
- **SHIPPED COMMAND (must not be renamed): `oms-pp-cli sap logs`**

  shipped spec block:
  ```yaml
          path: "/api/sap/logs/"
          description: "SAP sync history (sync_type, status, records processed/created/updated, duration)"
          response:
            type: object
  ```

  live probe:
  - bare (no params) -> **HTTP 200**, rows=50, 13592 bytes, top-level JSON `list`
    - sample: `[{"id": 846, "sync_type": "PARTY_ADDRESS", "status": "SUCCESS", "records_processed": 35721, "records_created": 2, "records_updated": 35719, "error_message": null, "started_at": "2026-08-04T06:42:29.575225Z", "completed_at": "2026-08-04T06:44:20.668423Z", "triggered_by": "manual", "duration": 111.093`

## `/api/sap/parties`

- harvested methods: `GET`  | GET-capable: **True**
- lenses: A-callsite
- params observed at the call site: `search`
- **SHIPPED COMMAND (must not be renamed): `oms-pp-cli sap parties`**

  shipped spec block:
  ```yaml
          path: "/api/sap/parties/"
          description: "SAP parties (business partners)"
          response:
            type: object
  ```

  live probe:
  - bare (no params) -> **HTTP 200**, rows=3358, 620913 bytes, top-level JSON `list`
    - sample: `[{"id": 5408, "card_code": "CUSTA000001", "card_name": "JIVO WELLNESS PVT LTD - DL", "state": "DL", "main_group": "BRANCH", "card_type": "C", "category": "BEVERAGES", "synced_at": "2026-08-04T06:38:32.796644Z"}, {"id": 4231, "card_code": "CUSTA000001", "card_name": "JIVO WELLNESS PVT LTD - DL", "sta`

## `/api/sap/parties/category`

- harvested methods: `GET`  | GET-capable: **True**
- lenses: A-callsite
- params observed at the call site: `category`
- **SHIPPED COMMAND (must not be renamed): `oms-pp-cli sap party-categories`**

  shipped spec block:
  ```yaml
          path: "/api/sap/parties/category/"
          description: "SAP parties filtered by category"
          params:
            - name: category
              type: string
              description: "Category filter"
          response:
            type: object
  ```

  live probe:
  - bare (no params) -> **HTTP 400**
    - server said: `{"success":false,"message":"category query parameter is required"}`

## `/api/sap/product-varieties`

- harvested methods: `GET`  | GET-capable: **True**
- lenses: A-callsite
- **SHIPPED COMMAND (must not be renamed): `oms-pp-cli sap product-varieties`**

  shipped spec block:
  ```yaml
          path: "/api/sap/product-varieties/"
          description: "SAP product varieties"
          response:
            type: object
  ```

  live probe:
  - bare (no params) -> **HTTP 200**, rows=114, 3898 bytes, top-level JSON `dict`
    - sample: `{"category": "", "count": 114, "varieties": ["1109005-PREPAID - REPAIR AND MAINTENANCE (SIDEL)", "1204007-BLOWING MACHINE (SIDEL) (FA0000025)", "1204019-INSTALLATION-CONTAINER 20 FEET", "1204022 - GAS DISTRIBUTION PANEL (FA0000354)", "1205009- AGILENT 8860 GC SYSTEM CUSTOM", "1212013 - BUILDINGS WIP`

## `/api/sap/products`

- harvested methods: `GET`  | GET-capable: **True**
- lenses: A-callsite
- **SHIPPED COMMAND (must not be renamed): `oms-pp-cli sap products`**

  shipped spec block:
  ```yaml
          path: "/api/sap/products/"
          description: "SAP products"
          response:
            type: object
  ```

  live probe:
  - bare (no params) -> **HTTP 200**, rows=2637, 1010130 bytes, top-level JSON `list`
    - sample: `[{"id": 4090, "item_code": "CG0000001", "item_name": "TAPE ROLL", "category": "MART", "sal_factor2": "1.000000", "tax_rate": "18.00", "is_deleted": "N", "variety": "PACKAGING MATERIAL EXPENSES", "type": "OTHERS", "sub_group": "PACKAGING MATERIAL EXPENSES", "sal_pack_unit": "1.000000", "brand": "JIVO`

## `/api/sap/quotation-log/{}`

- harvested methods: `GET`  | GET-capable: **True**
- lenses: A-callsite
- **SHIPPED COMMAND (must not be renamed): `oms-pp-cli sap quotation-log`**

  shipped spec block:
  ```yaml
          path: "/api/sap/quotation-log/{id}/"
          description: "Per-order SAP quotation push record"
          params:
            - name: id
              type: int
              required: true
              positional: true
              description: "Order id"
          response:
            type: object
  
    hana:
      description: "Live SAP HANA queries — product stock, sales orders, customers, and the order-creation wizard lookups"
      endpoints:
  ```

  live probe: **not probed** (parameterised path, or write-intent — see WRITE_INTENT in probe.py)

## `/api/sap/sync/{}`

- harvested methods: `POST`  | GET-capable: **False**
- lenses: A-callsite
- NEW — not in the shipped spec; needs a command name

  live probe: **not probed** (parameterised path, or write-intent — see WRITE_INTENT in probe.py)

## `/api/service-layer/invoice`

- harvested methods: `POST`  | GET-capable: **False**
- lenses: B-literal
- flags: branch-scoped, write-intent-keyword
- NEW — not in the shipped spec; needs a command name

  live probe: **not probed** (parameterised path, or write-intent — see WRITE_INTENT in probe.py)
