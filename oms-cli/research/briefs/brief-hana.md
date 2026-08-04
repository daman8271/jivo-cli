# Domain brief: hana

14 paths. Live probe evidence and shipped command names are given per endpoint. Do not invent a command name for an endpoint that already has one.

## `/api/hana/address`

- harvested methods: `GET`  | GET-capable: **True**
- lenses: B-literal
- flags: branch-scoped
- **SHIPPED COMMAND (must not be renamed): `oms-pp-cli hana address`**

  shipped spec block:
  ```yaml
          path: "/api/hana/address/"
          description: "Addresses for a customer. Requires --card-code."
          params:
            - name: card_code
              type: string
              required: true
              description: "SAP card code"
          response:
            type: object
  ```

  live probe:
  - bare (no params) -> **HTTP 400**
    - server said: `{"error":"branch is required and must be one of: OIL, BEVERAGE"}`
  - branch=BEVERAGE -> **HTTP 400**
    - server said: `{"error":"card_code is required"}`
  - branch=OIL -> **HTTP 400**
    - server said: `{"error":"card_code is required"}`

## `/api/hana/all-customers`

- harvested methods: `GET`  | GET-capable: **True**
- lenses: B-literal
- flags: branch-scoped
- **SHIPPED COMMAND (must not be renamed): `oms-pp-cli hana all-customers`**

  shipped spec block:
  ```yaml
          path: "/api/hana/all-customers/"
          description: "All customers from SAP HANA"
          response:
            type: object
  ```

  live probe:
  - bare (no params) -> **HTTP 400**
    - server said: `{"error":"branch is required and must be one of: OIL, BEVERAGE"}`
  - branch=BEVERAGE -> **HTTP 200**, rows=1247, 185310 bytes, top-level JSON `list`
    - sample: `[{"U_Main_Group": "CSD", "CardCode": "CUSTA000636", "CardName": "THE AREA MANAGER CANTEEN STORE DEPARTMENT", "State1": "UP", "U_Chain": "RETAILER", "ListNum": 1, "OpenOrders": 41}, {"U_Main_Group": "STAFF", "CardCode": "ORGC000001", "CardName": "GAGANDEEP SINGH", "State1": "DL", "U_Chain": "INDIVIDU`
  - branch=OIL -> **HTTP 200**, rows=1172, 175076 bytes, top-level JSON `list`
    - sample: `[{"U_Main_Group": "CSD", "CardCode": "CUSTA000636", "CardName": "THE AREA MANAGER CANTEEN STORE DEPARTMENT", "State1": "UP", "U_Chain": "RETAILER", "ListNum": 1, "OpenOrders": 55}, {"U_Main_Group": "E-COMMERCE", "CardCode": "CUSTA000496", "CardName": "INNOVATIVE RETAIL CONCEPTS PVT LTD", "State1": "`

## `/api/hana/batch-details`

- harvested methods: `GET`  | GET-capable: **True**
- lenses: B-literal
- flags: branch-scoped
- **SHIPPED COMMAND (must not be renamed): `oms-pp-cli hana batch-details`**

  shipped spec block:
  ```yaml
          path: "/api/hana/batch-details/"
          description: "Batch details for an item in a warehouse. Requires --item-code and --whs-code."
          params:
            - name: item_code
              type: string
              required: true
              description: "SAP item code"
            - name: whs_code
              type: string
              required: true
              description: "Warehouse code"
          response:
            type: object
  ```

  live probe:
  - bare (no params) -> **HTTP 400**
    - server said: `{"error":"branch is required and must be one of: OIL, BEVERAGE"}`
  - branch=BEVERAGE -> **HTTP 400**
    - server said: `{"error":"item_code and whs_code are required"}`
  - branch=OIL -> **HTTP 400**
    - server said: `{"error":"item_code and whs_code are required"}`

## `/api/hana/customer-details`

- harvested methods: `GET`  | GET-capable: **True**
- lenses: B-literal
- flags: branch-scoped
- **SHIPPED COMMAND (must not be renamed): `oms-pp-cli hana customer-details`**

  shipped spec block:
  ```yaml
          path: "/api/hana/customer-details/"
          description: "Customer master detail. Requires --card-code."
          params:
            - name: card_code
              type: string
              required: true
              description: "SAP card code"
          response:
            type: object
  ```

  live probe:
  - bare (no params) -> **HTTP 400**
    - server said: `{"error":"branch is required and must be one of: OIL, BEVERAGE"}`
  - branch=BEVERAGE -> **HTTP 400**
    - server said: `{"error":"card_code is required"}`
  - branch=OIL -> **HTTP 400**
    - server said: `{"error":"card_code is required"}`

## `/api/hana/fg-items`

- harvested methods: `GET`  | GET-capable: **True**
- lenses: B-literal
- flags: branch-scoped
- **SHIPPED COMMAND (must not be renamed): `oms-pp-cli hana fg-items`**

  shipped spec block:
  ```yaml
          path: "/api/hana/fg-items/"
          description: "Finished-goods items"
          response:
            type: object
  ```

  live probe:
  - bare (no params) -> **HTTP 400**
    - server said: `{"error":"branch is required and must be one of: OIL, BEVERAGE"}`
  - branch=BEVERAGE -> **HTTP 200**, rows=336, 57606 bytes, top-level JSON `list`
    - sample: `[{"ItemCode": "FG0000328", "ItemName": "PET BOTTLE 250 ML JIVO NATURAL MINERAL SPECIAL EDITION ARSHDEEP  * (24 PCS)", "U_Brand": "JIVO", "U_Variety": "MINERAL WATER", "U_Sub_Group": "WATER", "U_SKU": "250 MLS", "TotalQty": 481779.0}, {"ItemCode": "FG0000314", "ItemName": "PET BOTTLE 160 MLS PUNJABI `
  - branch=OIL -> **HTTP 200**, rows=443, 75682 bytes, top-level JSON `list`
    - sample: `[{"ItemCode": "FG0000386", "ItemName": "CHAI 250 GMS 40 PCS", "U_Brand": "JIVO", "U_Variety": "TEA", "U_Sub_Group": "TEA", "U_SKU": "250 GMS", "TotalQty": 63501.0}, {"ItemCode": "FG0000150", "ItemName": "SANO POMACE OLIVE 1 LTR 16 PCS", "U_Brand": "SANO", "U_Variety": "POMACE", "U_Sub_Group": "OLIVE`

## `/api/hana/freight-masters`

- harvested methods: `GET`  | GET-capable: **True**
- lenses: B-literal
- flags: branch-scoped
- **SHIPPED COMMAND (must not be renamed): `oms-pp-cli hana freight-masters`**

  shipped spec block:
  ```yaml
          path: "/api/hana/freight-masters/"
          description: "Freight master records"
          response:
            type: object
  ```

  live probe:
  - bare (no params) -> **HTTP 400**
    - server said: `{"error":"branch is required and must be one of: OIL, BEVERAGE"}`
  - branch=BEVERAGE -> **HTTP 200**, rows=10, 438 bytes, top-level JSON `list`
    - sample: `[{"ExpnsCode": 2, "ExpnsName": "FREIGHT INWARD"}, {"ExpnsCode": 3, "ExpnsName": "FREIGHT OUTWARD"}, {"ExpnsCode": 8, "ExpnsName": "TCS"}, {"ExpnsCode": 4, "ExpnsName": "MARINE INSURANCE"}, {"ExpnsCode": 5, "ExpnsName": "OCEAN FREIGHT"}, {"ExpnsCode": 6, "ExpnsName": "OTHER CHARGES FA"}, {"ExpnsCode"`
  - branch=OIL -> **HTTP 200**, rows=11, 497 bytes, top-level JSON `list`
    - sample: `[{"ExpnsCode": 9, "ExpnsName": "BST"}, {"ExpnsCode": 2, "ExpnsName": "FREIGHT INWARD DRCT"}, {"ExpnsCode": 3, "ExpnsName": "FREIGHT OUTWARD"}, {"ExpnsCode": 4, "ExpnsName": "MARINE INSURANCE"}, {"ExpnsCode": 5, "ExpnsName": "OCEAN FREIGHT"}, {"ExpnsCode": 8, "ExpnsName": "TCS"}, {"ExpnsCode": 7, "Ex`

## `/api/hana/inventory-details`

- harvested methods: `GET`  | GET-capable: **True**
- lenses: B-literal
- flags: branch-scoped
- **SHIPPED COMMAND (must not be renamed): `oms-pp-cli hana inventory-details`**

  shipped spec block:
  ```yaml
          path: "/api/hana/inventory-details/"
          description: "Per-warehouse inventory for an item. Requires --item-code."
          params:
            - name: item_code
              type: string
              required: true
              description: "SAP item code"
          response:
            type: object
  ```

  live probe:
  - bare (no params) -> **HTTP 400**
    - server said: `{"error":"branch is required and must be one of: OIL, BEVERAGE"}`
  - branch=BEVERAGE -> **HTTP 400**
    - server said: `{"error":"item_code is required"}`
  - branch=OIL -> **HTTP 400**
    - server said: `{"error":"item_code is required"}`

## `/api/hana/item-price`

- harvested methods: `GET`  | GET-capable: **True**
- lenses: B-literal
- flags: branch-scoped
- **SHIPPED COMMAND (must not be renamed): `oms-pp-cli hana item-price`**

  shipped spec block:
  ```yaml
          path: "/api/hana/item-price/"
          description: "Price for an item on a price list. Requires --item-code and --price-list."
          params:
            - name: item_code
              type: string
              required: true
              description: "SAP item code"
            - name: price_list
              type: string
              required: true
              description: "Price list id"
          response:
            type: object
  ```

  live probe:
  - bare (no params) -> **HTTP 400**
    - server said: `{"error":"branch is required and must be one of: OIL, BEVERAGE"}`
  - branch=BEVERAGE -> **HTTP 400**
    - server said: `{"error":"item_code and price_list are required"}`
  - branch=OIL -> **HTTP 400**
    - server said: `{"error":"item_code and price_list are required"}`

## `/api/hana/next-doc-number`

- harvested methods: `GET`  | GET-capable: **True**
- lenses: B-literal
- flags: branch-scoped
- **SHIPPED COMMAND (must not be renamed): `oms-pp-cli hana next-doc-number`**

  shipped spec block:
  ```yaml
          path: "/api/hana/next-doc-number/"
          description: "Next document number for a document type. Requires --doc-type."
          params:
            - name: doc_type
              type: string
              required: true
              description: "Document type"
          response:
            type: object
  ```

  live probe:
  - bare (no params) -> **HTTP 400**
    - server said: `{"error":"branch is required and must be one of: OIL, BEVERAGE"}`
  - branch=BEVERAGE -> **HTTP 400**
    - server said: `{"error":"doc_type is required"}`
  - branch=OIL -> **HTTP 400**
    - server said: `{"error":"doc_type is required"}`

## `/api/hana/open-parties`

- harvested methods: `GET`  | GET-capable: **True**
- lenses: A-callsite
- **SHIPPED COMMAND (must not be renamed): `oms-pp-cli hana open-parties`**

  shipped spec block:
  ```yaml
          path: "/api/hana/open-parties/"
          description: "Parties with open transactions"
          response:
            type: object
  ```

  live probe:
  - bare (no params) -> **HTTP 400**
    - server said: `{"error":"branch is required and must be one of: OIL, BEVERAGE"}`
  - branch=BEVERAGE -> **HTTP 200**, rows=31, 2766 bytes, top-level JSON `list`
    - sample: `[{"CardCode": "CUSTA000636", "CardName": "THE AREA MANAGER CANTEEN STORE DEPARTMENT", "Num_of_Open_SalesOrder": 41}, {"CardCode": "ORGC000001", "CardName": "GAGANDEEP SINGH", "Num_of_Open_SalesOrder": 12}, {"CardCode": "CUSTA000538", "CardName": "SHRI RAM TRADERS", "Num_of_Open_SalesOrder": 8}, {"Ca`
  - branch=OIL -> **HTTP 200**, rows=58, 5389 bytes, top-level JSON `list`
    - sample: `[{"CardCode": "CUSTA000636", "CardName": "THE AREA MANAGER CANTEEN STORE DEPARTMENT", "Num_of_Open_SalesOrder": 55}, {"CardCode": "CUSTA000496", "CardName": "INNOVATIVE RETAIL CONCEPTS PVT LTD", "Num_of_Open_SalesOrder": 15}, {"CardCode": "CUSTA001041", "CardName": "HIMJYOTI TRADERS", "Num_of_Open_S`

## `/api/hana/product-so`

- harvested methods: `GET`  | GET-capable: **True**
- lenses: A-callsite
- params observed at the call site: `item_code`
- **SHIPPED COMMAND (must not be renamed): `oms-pp-cli hana product-so`**

  shipped spec block:
  ```yaml
          path: "/api/hana/product-so/"
          description: "Product sales-order data for an item. Requires --item-code."
          params:
            - name: item_code
              type: string
              required: true
              description: "SAP item code"
          response:
            type: object
  ```

  live probe:
  - bare (no params) -> **HTTP 400**
    - server said: `{"error":"branch is required and must be one of: OIL, BEVERAGE"}`
  - branch=BEVERAGE -> **HTTP 400**
    - server said: `{"error":"item_code is required"}`
  - branch=OIL -> **HTTP 400**
    - server said: `{"error":"item_code is required"}`

## `/api/hana/product-stock`

- harvested methods: `GET`  | GET-capable: **True**
- lenses: A-callsite
- **SHIPPED COMMAND (must not be renamed): `oms-pp-cli hana product-stock`**

  shipped spec block:
  ```yaml
          path: "/api/hana/product-stock/"
          description: "Live product stock from SAP HANA"
          response:
            type: object
  ```

  live probe:
  - bare (no params) -> **HTTP 400**
    - server said: `{"error":"branch is required and must be one of: OIL, BEVERAGE"}`
  - branch=BEVERAGE -> **HTTP 502**
    - server said: `{"error":"Unable to fetch product stock from HANA.","detail":"name 'unique_schemas' is not defined"}`
  - branch=OIL -> **HTTP 502**
    - server said: `{"error":"Unable to fetch product stock from HANA.","detail":"name 'unique_schemas' is not defined"}`

## `/api/hana/salesperson-details`

- harvested methods: `GET`  | GET-capable: **True**
- lenses: B-literal
- flags: branch-scoped
- **SHIPPED COMMAND (must not be renamed): `oms-pp-cli hana salesperson-details`**

  shipped spec block:
  ```yaml
          path: "/api/hana/salesperson-details/"
          description: "Salesperson detail. Requires --slp-code."
          params:
            - name: slp_code
              type: string
              required: true
              description: "Salesperson code"
          response:
            type: object
  
    invoices:
      description: "Sales invoices, invoice review, and SKU master/image data"
      endpoints:
  ```

  live probe:
  - bare (no params) -> **HTTP 400**
    - server said: `{"error":"branch is required and must be one of: OIL, BEVERAGE"}`
  - branch=BEVERAGE -> **HTTP 400**
    - server said: `{"error":"slp_code is required"}`
  - branch=OIL -> **HTTP 400**
    - server said: `{"error":"slp_code is required"}`

## `/api/hana/so`

- harvested methods: `GET`  | GET-capable: **True**
- lenses: A-callsite, B-literal
- params observed at the call site: `card_code`
- flags: branch-scoped
- **SHIPPED COMMAND (must not be renamed): `oms-pp-cli hana so`**

  shipped spec block:
  ```yaml
          path: "/api/hana/so/"
          description: "Sales orders for a party. Requires --card-code."
          params:
            - name: card_code
              type: string
              required: true
              description: "SAP party card code"
          response:
            type: object
  ```

  live probe:
  - bare (no params) -> **HTTP 400**
    - server said: `{"error":"branch is required and must be one of: OIL, BEVERAGE"}`
  - branch=BEVERAGE -> **HTTP 400**
    - server said: `{"error":"card_code is required"}`
  - branch=OIL -> **HTTP 400**
    - server said: `{"error":"card_code is required"}`
