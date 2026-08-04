# Domain brief: orders

33 paths. Live probe evidence and shipped command names are given per endpoint. Do not invent a command name for an endpoint that already has one.

## `/api/orders/addresses`

- harvested methods: `GET`  | GET-capable: **True**
- lenses: A-callsite
- **SHIPPED COMMAND (must not be renamed): `oms-pp-cli orders addresses`**

  shipped spec block:
  ```yaml
          path: "/api/orders/addresses/"
          description: "Bill-to / ship-to addresses for a party. Requires --card-code."
          params:
            - name: card_code
              type: string
              required: true
              description: "SAP party card code"
            - name: category
              type: string
              description: "Optional category filter"
          response:
            type: object
  ```

  live probe:
  - bare (no params) -> **HTTP 400**
    - server said: `{"error":"card_code is required"}`

## `/api/orders/branch`

- harvested methods: `GET`  | GET-capable: **True**
- lenses: A-callsite
- **SHIPPED COMMAND (must not be renamed): `oms-pp-cli orders branch`**

  shipped spec block:
  ```yaml
          path: "/api/orders/branch/"
          description: "SAP branch / BPL list"
          response:
            type: object
  ```

  live probe:
  - bare (no params) -> **HTTP 200**, rows=1, 54 bytes, top-level JSON `list`
    - sample: `[{"bpl_id": "2", "bpl_name": "FACTORY", "category": "OIL"}]`

## `/api/orders/create`

- harvested methods: `POST`  | GET-capable: **False**
- lenses: A-callsite
- NEW — not in the shipped spec; needs a command name

  live probe: **not probed** (parameterised path, or write-intent — see WRITE_INTENT in probe.py)

## `/api/orders/create-scheme`

- harvested methods: `POST`  | GET-capable: **False**
- lenses: A-callsite
- NEW — not in the shipped spec; needs a command name

  live probe: **not probed** (parameterised path, or write-intent — see WRITE_INTENT in probe.py)

## `/api/orders/dashboardW`

- harvested methods: `GET`  | GET-capable: **True**
- lenses: A-callsite
- **SHIPPED COMMAND (must not be renamed): `oms-pp-cli dashboard summary`**

  shipped spec block:
  ```yaml
          path: "/api/orders/dashboardW/"
          description: "Dashboard KPI block (total orders, total sales, completion)"
          response:
            type: object
  ```

  live probe:
  - bare (no params) -> **HTTP 200**, 573 bytes, top-level JSON `dict`
    - sample: `{"filter": {"year": 2026, "month": 0}, "total_orders": 2163, "total_revenue": "14608501435.32", "completed_revenue": "1563368665.20", "rejected_revenue": "276814244.29", "pending_revenue": "12768318525.83", "today_orders": 9, "this_month_orders": 40, "status_counts": {"Order Created": 6, "Rate Appro`

## `/api/orders/dashboardW/charts`

- harvested methods: `GET`  | GET-capable: **True**
- lenses: A-callsite
- **SHIPPED COMMAND (must not be renamed): `oms-pp-cli dashboard charts`**

  shipped spec block:
  ```yaml
          path: "/api/orders/dashboardW/charts/"
          description: "Dashboard chart series (visual overview, statewise)"
          params:
            - name: status
              type: string
              description: "Optional status filter for the series"
          response:
            type: object
  
    sap:
      description: "SAP Business One sync — history logs and synced master data (branches, parties, products)"
      endpoints:
  ```

  live probe:
  - bare (no params) -> **HTTP 200**, 268382 bytes, top-level JSON `dict`
    - sample: `{"filter": {"year": 2026, "month": 0, "line_year": 2026}, "monthly_sales": [{"month": "2026-01", "label": "Jan", "revenue": 0, "count": 0}, {"month": "2026-02", "label": "Feb", "revenue": 0, "count": 0}, {"month": "2026-03", "label": "Mar", "revenue": 0, "count": 0}, {"month": "2026-04", "label": "A`

## `/api/orders/dispatches`

- harvested methods: `GET`  | GET-capable: **True**
- lenses: A-callsite
- **SHIPPED COMMAND (must not be renamed): `oms-pp-cli orders dispatches`**

  shipped spec block:
  ```yaml
          path: "/api/orders/dispatches/"
          description: "Dispatch-from locations"
          response:
            type: object
  ```

  live probe:
  - bare (no params) -> **HTTP 200**, rows=1, 58 bytes, top-level JSON `list`
    - sample: `[{"id": 4, "name": "Factory - Bahadurgarh", "code": "FAC-BGH"}]`

## `/api/orders/flow-config`

- harvested methods: `GET, POST`  | GET-capable: **True**
- lenses: A-callsite
- params observed at the call site: `flow_type`
- **SHIPPED COMMAND (must not be renamed): `oms-pp-cli orders flow-config`**

  shipped spec block:
  ```yaml
          path: "/api/orders/flow-config/"
          description: "Global order approval-flow configuration"
          response:
            type: object
  ```

  live probe:
  - bare (no params) -> **HTTP 200**, 808 bytes, top-level JSON `dict`
    - sample: `{"flow_type": "ASM", "flow_label": "ASM Order Flow", "flow_options": [{"code": "ASM", "label": "ASM Order Flow"}, {"code": "BILLING", "label": "Billing Orders Flow"}], "rate_approval_enabled": true, "billing_enabled": true, "auditor_enabled": true, "rate_conditions": ["BASIC_GT_MARKET", "BASIC_ZERO_`

## `/api/orders/list`

- harvested methods: `GET`  | GET-capable: **True**
- lenses: C-indirect
- params observed at the call site: `approval_pending, billing, status`
- **SHIPPED COMMAND (must not be renamed): `oms-pp-cli orders list`**

  shipped spec block:
  ```yaml
          path: "/api/orders/list/"
          description: "All orders (admin-wide). Filter by status/stage."
          params:
            - name: status
              type: string
              description: "Filter by status code (e.g. BILLING, AUDITOR_APPROVAL)"
            - name: billing
              type: bool
              description: "Only billing-stage orders"
            - name: approval_pending
              type: bool
              description: "Only approval-pending orders"
          response:
            type: object
  ```

  live probe:
  - bare (no params) -> **HTTP 200**, rows=263, 100435 bytes, top-level JSON `list`
    - sample: `[{"id": 2530, "order_number": "ORD-20260804-0009", "order_type": "PARTY", "employee_id": "", "card_code": "CUSTA000844", "card_name": "ILAHI CO. (BTCPN5063N)", "total_amount": "77487.40", "status": "BILLING", "status_display": "Billing", "sap_doc_number": "", "items_count": 3, "created_by": "Karande`

## `/api/orders/notifications`

- harvested methods: `GET, POST`  | GET-capable: **True**
- lenses: A-callsite
- **SHIPPED COMMAND (must not be renamed): `oms-pp-cli orders notifications`**

  shipped spec block:
  ```yaml
          path: "/api/orders/notifications/"
          description: "Order-status notifications for the current user"
          response:
            type: object
  ```

  live probe:
  - bare (no params) -> **HTTP 200**, rows=0, 2 bytes, top-level JSON `list`
    - sample: `[]`

## `/api/orders/notifications/history`

- harvested methods: `GET`  | GET-capable: **True**
- lenses: A-callsite
- params observed at the call site: `filter, limit, offset`
- NEW — not in the shipped spec; needs a command name

  live probe:
  - bare (no params) -> **HTTP 200**, rows=0, 60 bytes, top-level JSON `dict`
    - sample: `{"results": [], "count": 0, "unread_count": 0, "next_offset": null}`

## `/api/orders/notifications/{}`

- harvested methods: `PATCH`  | GET-capable: **False**
- lenses: A-callsite
- NEW — not in the shipped spec; needs a command name

  live probe: **not probed** (parameterised path, or write-intent — see WRITE_INTENT in probe.py)

## `/api/orders/orderdetailsbyid/{}`

- harvested methods: `GET`  | GET-capable: **True**
- lenses: A-callsite
- **SHIPPED COMMAND (must not be renamed): `oms-pp-cli orders detail`**

  shipped spec block:
  ```yaml
          path: "/api/orders/orderdetailsbyid/{id}/"
          description: "Full order with line items, addresses, rate approvals, SAP doc number"
          params:
            - name: id
              type: int
              required: true
              positional: true
              description: "Order id"
          response:
            type: object
  ```

  live probe: **not probed** (parameterised path, or write-intent — see WRITE_INTENT in probe.py)

## `/api/orders/ordersbyuser/{}`

- harvested methods: `GET`  | GET-capable: **True**
- lenses: A-callsite
- **SHIPPED COMMAND (must not be renamed): `oms-pp-cli orders by-user`**

  shipped spec block:
  ```yaml
          path: "/api/orders/ordersbyuser/{user_id}/"
          description: "Orders raised by a specific user (source for View Orders / Order Tracking)"
          params:
            - name: user_id
              type: int
              required: true
              positional: true
              description: "User id"
          response:
            type: object
  ```

  live probe: **not probed** (parameterised path, or write-intent — see WRITE_INTENT in probe.py)

## `/api/orders/parties`

- harvested methods: `GET`  | GET-capable: **True**
- lenses: A-callsite
- **SHIPPED COMMAND (must not be renamed): `oms-pp-cli orders parties`**

  shipped spec block:
  ```yaml
          path: "/api/orders/parties/"
          description: "Assigned-party dropdown (card_code -> card_name) for the current user"
          response:
            type: object
  ```

  live probe:
  - bare (no params) -> **HTTP 200**, rows=0, 2 bytes, top-level JSON `list`
    - sample: `[]`

## `/api/orders/party-flow-config`

- harvested methods: `DELETE, GET, POST`  | GET-capable: **True**
- lenses: A-callsite
- **SHIPPED COMMAND (must not be renamed): `oms-pp-cli orders party-flow-config`**

  shipped spec block:
  ```yaml
          path: "/api/orders/party-flow-config/"
          description: "Per-party approval-flow configuration"
          response:
            type: object
  
    quotations:
      description: "Sales quotations and their SAP push status"
      endpoints:
  ```

  live probe:
  - bare (no params) -> **HTTP 200**, rows=2, 1197 bytes, top-level JSON `dict`
    - sample: `{"success": true, "data": [{"card_code": "CUSTA000486", "category": "OIL", "flow_type": "BILLING", "flow_label": "Billing Orders Flow", "rate_approval_enabled": false, "billing_enabled": false, "auditor_enabled": true, "rate_conditions": ["BASIC_GT_MARKET"], "updated_at": "2026-06-24T05:32:30.172730`

## `/api/orders/party-products/{}`

- harvested methods: `GET`  | GET-capable: **True**
- lenses: A-callsite
- **SHIPPED COMMAND (must not be renamed): `oms-pp-cli orders party-products`**

  shipped spec block:
  ```yaml
          path: "/api/orders/party-products/{card_code}/"
          description: "Products (with rates) assigned to a party, for the order product selector"
          params:
            - name: card_code
              type: string
              required: true
              positional: true
              description: "SAP party card code"
          response:
            type: object
  ```

  live probe: **not probed** (parameterised path, or write-intent — see WRITE_INTENT in probe.py)

## `/api/orders/products`

- harvested methods: `GET`  | GET-capable: **True**
- lenses: A-callsite
- **SHIPPED COMMAND (must not be renamed): `oms-pp-cli orders products`**

  shipped spec block:
  ```yaml
          path: "/api/orders/products/"
          description: "Global product list"
          response:
            type: object
  ```

  live probe:
  - bare (no params) -> **HTTP 200**, rows=0, 2 bytes, top-level JSON `list`
    - sample: `[]`

## `/api/orders/quotation-overview`

- harvested methods: `GET`  | GET-capable: **True**
- lenses: A-callsite
- **SHIPPED COMMAND (must not be renamed): `oms-pp-cli quotations overview`**

  shipped spec block:
  ```yaml
          path: "/api/orders/quotation-overview/"
          description: "All quotations with SAP doc numbers and cancellation state"
          response:
            type: object
  ```

  live probe:
  - bare (no params) -> **HTTP 200**, rows=1898, 590698 bytes, top-level JSON `dict`
    - sample: `{"success": true, "data": [{"id": 2528, "order_number": "ORD-20260804-0007", "card_code": "CUSTA001216", "card_name": "SHRI SHYAM TRADERS (CUSTA001216)", "created_at": "2026-08-04T07:12:16.576456", "doc_num": null, "doc_entry": null, "quotation_cancelled": false, "quotation_cancelled_at": null, "quo`

## `/api/orders/quotation-status`

- harvested methods: `GET`  | GET-capable: **True**
- lenses: A-callsite
- params observed at the call site: `order_ids`
- **SHIPPED COMMAND (must not be renamed): `oms-pp-cli quotations status`**

  shipped spec block:
  ```yaml
          path: "/api/orders/quotation-status/"
          description: "Open/closed SAP status badges for specific quotations"
          params:
            - name: order_ids
              type: string
              description: "Comma-separated order ids, e.g. 1,2,3"
          response:
            type: object
  
    dashboard:
      description: "Dashboard KPIs and chart series"
      endpoints:
  ```

  live probe:
  - bare (no params) -> **HTTP 200**, 30 bytes, top-level JSON `dict`
    - sample: `{"success": true, "statuses": {}}`

## `/api/orders/schemes`

- harvested methods: `GET`  | GET-capable: **True**
- lenses: A-callsite
- **SHIPPED COMMAND (must not be renamed): `oms-pp-cli orders schemes`**

  shipped spec block:
  ```yaml
          path: "/api/orders/schemes/"
          description: "Sales schemes / promotions"
          response:
            type: object
  ```

  live probe:
  - bare (no params) -> **HTTP 200**, rows=72, 5338 bytes, top-level JSON `list`
    - sample: `[{"scheme_id": 76, "scheme_name": "( GN ) 1 LTR PER BOX PER 1 PCS CANOLA 1 LTR", "state_code": "UP"}, {"scheme_id": 80, "scheme_name": "(GN) 3 BOX PER 2 PCS GROUNDNUT 1 LTR", "state_code": "HR"}, {"scheme_id": 78, "scheme_name": "(GN) 5 LTR Per Box 1 PCS Canola 1 LTR", "state_code": "UP"}, {"scheme_`

## `/api/orders/schemes/manage`

- harvested methods: `GET`  | GET-capable: **True**
- lenses: A-callsite
- NEW — not in the shipped spec; needs a command name

  live probe:
  - bare (no params) -> **HTTP 200**, rows=72, 17823 bytes, top-level JSON `dict`
    - sample: `{"success": true, "data": [{"scheme_id": 76, "scheme_name": "( GN ) 1 LTR PER BOX PER 1 PCS CANOLA 1 LTR", "is_active": true, "state_name": "Uttar Pradesh", "state_code": "UP", "product_id": 3690, "item_code": "FG0000407", "item_name": "COLD PRESS 1 LTR (NIRMAL RISHI )20 PCS", "sal_factor2": 20.0, "`

## `/api/orders/schemes/{}`

- harvested methods: `DELETE, PATCH`  | GET-capable: **False**
- lenses: A-callsite
- NEW — not in the shipped spec; needs a command name

  live probe: **not probed** (parameterised path, or write-intent — see WRITE_INTENT in probe.py)

## `/api/orders/staff-products`

- harvested methods: `GET, POST`  | GET-capable: **True**
- lenses: A-callsite
- **SHIPPED COMMAND (must not be renamed): `oms-pp-cli orders staff-products`**

  shipped spec block:
  ```yaml
          path: "/api/orders/staff-products/"
          description: "Staff-assigned products"
          response:
            type: object
  ```

  live probe:
  - bare (no params) -> **HTTP 200**, rows=0, 2 bytes, top-level JSON `list`
    - sample: `[]`

## `/api/orders/status`

- harvested methods: `GET`  | GET-capable: **True**
- lenses: A-callsite
- **SHIPPED COMMAND (must not be renamed): `oms-pp-cli orders status`**

  shipped spec block:
  ```yaml
          path: "/api/orders/status/"
          description: "Order status master (id -> name)"
          response:
            type: object
  ```

  live probe:
  - bare (no params) -> **HTTP 200**, rows=11, 335 bytes, top-level JSON `list`
    - sample: `[{"id": 1, "name": "Order Created"}, {"id": 2, "name": "Rate Approval"}, {"id": 3, "name": "Billing"}, {"id": 4, "name": "Need Approval"}, {"id": 5, "name": "Billing Pending"}, {"id": 6, "name": "Approved"}, {"id": 7, "name": "Rejected"}, {"id": 8, "name": "Billing Rejected"}, {"id": 9, "name": "Com`

## `/api/orders/status-tracking`

- harvested methods: `GET`  | GET-capable: **True**
- lenses: A-callsite
- params observed at the call site: `mode`
- **SHIPPED COMMAND (must not be renamed): `oms-pp-cli orders status-tracking`**

  shipped spec block:
  ```yaml
          path: "/api/orders/status-tracking/"
          description: "Approval queue for a stage. Requires --mode."
          params:
            - name: mode
              type: string
              required: true
              description: "Approval stage"
              enum: [auditor, billing, rate_approver]
          response:
            type: object
  ```

  live probe:
  - bare (no params) -> **HTTP 400**
    - server said: `{"error":"mode must be auditor, billing, or rate_approver"}`

## `/api/orders/stock-check`

- harvested methods: `GET`  | GET-capable: **True**
- lenses: A-callsite
- **SHIPPED COMMAND (must not be renamed): `oms-pp-cli orders stock-check`**

  shipped spec block:
  ```yaml
          path: "/api/orders/stock-check/"
          description: "Per-order required-qty vs available-stock (legacy view)"
          response:
            type: object
  ```

  live probe:
  - bare (no params) -> **HTTP 200**, rows=1900, 1062456 bytes, top-level JSON `list`
    - sample: `[{"id": 2528, "order_number": "ORD-20260804-0007", "date": "2026-08-04T07:12:16.576456", "customer": "SHRI SHYAM TRADERS (CUSTA001216)", "order_type": "Party", "dispatch_from": "FACTORY", "status": "Completed", "items": [{"item_code": "FG0000328", "item_name": "PET BOTTLE 250 ML JIVO NATURAL MINERAL`

## `/api/orders/web-push/public-key`

- harvested methods: `GET`  | GET-capable: **True**
- lenses: A-callsite
- NEW — not in the shipped spec; needs a command name

  live probe:
  - bare (no params) -> **HTTP 200**, 104 bytes, top-level JSON `dict`
    - sample: `{"public_key": "BN-KZjxMcr9erUDbCi9gyoSh6tcS6WSzGpNDr8uzlUDIsUsSa7z2UjAQh6BeIOErhZJSNLnaEe-3OPqJi8PeBDo"}`

## `/api/orders/web-push/subscribe`

- harvested methods: `DELETE, POST`  | GET-capable: **False**
- lenses: A-callsite
- NEW — not in the shipped spec; needs a command name

  live probe: **not probed** (parameterised path, or write-intent — see WRITE_INTENT in probe.py)

## `/api/orders/{}/cancel-quotation`

- harvested methods: `POST`  | GET-capable: **False**
- lenses: A-callsite
- NEW — not in the shipped spec; needs a command name

  live probe: **not probed** (parameterised path, or write-intent — see WRITE_INTENT in probe.py)

## `/api/orders/{}/delete-draft`

- harvested methods: `DELETE`  | GET-capable: **False**
- lenses: A-callsite
- NEW — not in the shipped spec; needs a command name

  live probe: **not probed** (parameterised path, or write-intent — see WRITE_INTENT in probe.py)

## `/api/orders/{}/orderlogs`

- harvested methods: `GET`  | GET-capable: **True**
- lenses: A-callsite
- **SHIPPED COMMAND (must not be renamed): `oms-pp-cli orders logs`**

  shipped spec block:
  ```yaml
          path: "/api/orders/{id}/orderlogs/"
          description: "Status-change audit trail for an order (drives the tracking timeline)"
          params:
            - name: id
              type: int
              required: true
              positional: true
              description: "Order id"
          response:
            type: object
  ```

  live probe: **not probed** (parameterised path, or write-intent — see WRITE_INTENT in probe.py)

## `/api/orders/{}/update-status`

- harvested methods: `POST`  | GET-capable: **False**
- lenses: A-callsite
- NEW — not in the shipped spec; needs a command name

  live probe: **not probed** (parameterised path, or write-intent — see WRITE_INTENT in probe.py)
