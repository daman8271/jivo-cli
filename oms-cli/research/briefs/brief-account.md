# Domain brief: account

29 paths. Live probe evidence and shipped command names are given per endpoint. Do not invent a command name for an endpoint that already has one.

## `/api/admin/devices`

- harvested methods: `GET`  | GET-capable: **True**
- lenses: A-callsite
- NEW — not in the shipped spec; needs a command name

  live probe:
  - bare (no params) -> **HTTP 200**, 17204 bytes, top-level JSON `dict`
    - sample: `{"success": true, "message": "Devices retrieved", "data": {"results": [{"id": 73, "device_id": "a9244663-59da-4b53-b5f1-61a51a0ca052", "user_id": 31, "username": "navi@2026", "user_name": "Navneet Singh", "email": "navneet@jivo.in", "role": "Manager", "status": "online", "platform": "WEB", "app_type`

## `/api/admin/devices/analytics`

- harvested methods: `GET`  | GET-capable: **True**
- lenses: A-callsite
- NEW — not in the shipped spec; needs a command name

  live probe:
  - bare (no params) -> **HTTP 200**, 2294 bytes, top-level JSON `dict`
    - sample: `{"success": true, "message": "Analytics retrieved", "data": {"cards": {"total_devices": 252, "active_devices": 252, "inactive_devices": 0, "mobile_devices": 72, "web_devices": 180, "android_devices": 47, "ios_devices": 25, "desktop_browsers": 177, "devices_active_today": 29, "status_counts": {"onlin`

## `/api/admin/devices/{}`

- harvested methods: `GET`  | GET-capable: **True**
- lenses: A-callsite
- NEW — not in the shipped spec; needs a command name

  live probe: **not probed** (parameterised path, or write-intent — see WRITE_INTENT in probe.py)

## `/api/auth/assign-parties`

- harvested methods: `POST`  | GET-capable: **False**
- lenses: A-callsite
- NEW — not in the shipped spec; needs a command name

  live probe: **not probed** (parameterised path, or write-intent — see WRITE_INTENT in probe.py)

## `/api/auth/assign-parties/bulk-upload`

- harvested methods: `POST`  | GET-capable: **False**
- lenses: A-callsite
- NEW — not in the shipped spec; needs a command name

  live probe: **not probed** (parameterised path, or write-intent — see WRITE_INTENT in probe.py)

## `/api/auth/bulk-party/assign-products`

- harvested methods: `POST`  | GET-capable: **False**
- lenses: A-callsite
- NEW — not in the shipped spec; needs a command name

  live probe: **not probed** (parameterised path, or write-intent — see WRITE_INTENT in probe.py)

## `/api/auth/categories`

- harvested methods: `GET`  | GET-capable: **True**
- lenses: A-callsite
- **SHIPPED COMMAND (must not be renamed): `oms-pp-cli account categories`**

  shipped spec block:
  ```yaml
          path: "/api/auth/categories/"
          description: "List product categories (e.g. OIL)"
          response:
            type: object
  ```

  live probe:
  - bare (no params) -> **HTTP 200**, rows=3, 86 bytes, top-level JSON `list`
    - sample: `[{"id": 2, "category": "BEVERAGES"}, {"id": 3, "category": "MART"}, {"id": 1, "category": "OIL"}]`

## `/api/auth/companies`

- harvested methods: `GET`  | GET-capable: **True**
- lenses: A-callsite
- **SHIPPED COMMAND (must not be renamed): `oms-pp-cli account companies`**

  shipped spec block:
  ```yaml
          path: "/api/auth/companies/"
          description: "List companies (Jivo Mart, Jivo Wellness)"
          response:
            type: object
  ```

  live probe:
  - bare (no params) -> **HTTP 200**, rows=2, 61 bytes, top-level JSON `list`
    - sample: `[{"id": 2, "name": "Jivo Mart"}, {"id": 1, "name": "Jivo Wellness"}]`

## `/api/auth/login`

- harvested methods: `POST`  | GET-capable: **False**
- lenses: A-callsite
- NEW — not in the shipped spec; needs a command name

  live probe: **not probed** (parameterised path, or write-intent — see WRITE_INTENT in probe.py)

## `/api/auth/logout`

- harvested methods: `POST`  | GET-capable: **False**
- lenses: A-callsite
- NEW — not in the shipped spec; needs a command name

  live probe: **not probed** (parameterised path, or write-intent — see WRITE_INTENT in probe.py)

## `/api/auth/mainGroup`

- harvested methods: `GET`  | GET-capable: **True**
- lenses: A-callsite
- **SHIPPED COMMAND (must not be renamed): `oms-pp-cli account main-groups`**

  shipped spec block:
  ```yaml
          path: "/api/auth/mainGroup/"
          description: "List main groups (ROI, GT, MT, BRANCH, ...)"
          response:
            type: object
  ```

  live probe:
  - bare (no params) -> **HTTP 200**, rows=27, 750 bytes, top-level JSON `list`
    - sample: `[{"id": 21, "name": "BRANCH"}, {"id": 13, "name": "BULK OIL"}, {"id": 8, "name": "CALL CENTER"}, {"id": 28, "name": "CALL CENTRE"}, {"id": 22, "name": "CASH SALE"}, {"id": 17, "name": "COMPANY UNIT"}, {"id": 24, "name": "CONSUMABLES"}, {"id": 14, "name": "CORPORATE"}, {"id": 11, "name": "CSD"}, {"id`

## `/api/auth/parties/{}/products`

- harvested methods: `GET`  | GET-capable: **True**
- lenses: A-callsite
- **SHIPPED COMMAND (must not be renamed): `oms-pp-cli account party-products`**

  shipped spec block:
  ```yaml
          path: "/api/auth/parties/{card_code}/products/"
          description: "Products assigned to a party (argument is the SAP card_code, not a numeric id)"
          params:
            - name: card_code
              type: string
              required: true
              positional: true
              description: "SAP party card code, e.g. CUSTA000596"
          response:
            type: object
  
    orders:
      description: "Orders: list, detail, status lifecycle, tracking, dispatch, approval-flow config, and the party/product lookups the order screens use"
      endpoints:
  ```

  live probe: **not probed** (parameterised path, or write-intent — see WRITE_INTENT in probe.py)

## `/api/auth/party-product/bulk-add`

- harvested methods: `POST`  | GET-capable: **False**
- lenses: A-callsite
- NEW — not in the shipped spec; needs a command name

  live probe: **not probed** (parameterised path, or write-intent — see WRITE_INTENT in probe.py)

## `/api/auth/party-product/remove`

- harvested methods: `POST`  | GET-capable: **False**
- lenses: A-callsite
- NEW — not in the shipped spec; needs a command name

  live probe: **not probed** (parameterised path, or write-intent — see WRITE_INTENT in probe.py)

## `/api/auth/party-product/update-rate`

- harvested methods: `POST`  | GET-capable: **False**
- lenses: A-callsite
- NEW — not in the shipped spec; needs a command name

  live probe: **not probed** (parameterised path, or write-intent — see WRITE_INTENT in probe.py)

## `/api/auth/profile`

- harvested methods: `GET`  | GET-capable: **True**
- lenses: A-callsite
- **SHIPPED COMMAND (must not be renamed): `oms-pp-cli account profile`**

  shipped spec block:
  ```yaml
          path: "/api/auth/profile/"
          description: "Show the authenticated user (role, company, main groups, states, category, page permissions)"
          response:
            type: object
  ```

  live probe:
  - bare (no params) -> **HTTP 200**, 3988 bytes, top-level JSON `dict`
    - sample: `{"success": true, "data": {"id": 62, "name": "Paramjot singh", "username": "paramjot", "email": "pramjot@jivo.in", "phone": "7418529637", "role": "admin", "role_display": "Admin", "company": {"id": 1, "name": "Jivo Wellness"}, "main_group": {"id": 21, "name": "BRANCH"}, "main_groups": [{"id": 1, "na`

## `/api/auth/refresh`

- harvested methods: `POST`  | GET-capable: **False**
- lenses: C-indirect
- flags: excluded:auth mutator — never published as a command, never probed
- NEW — not in the shipped spec; needs a command name

  live probe: **not probed** (parameterised path, or write-intent — see WRITE_INTENT in probe.py)

## `/api/auth/remove-party`

- harvested methods: `POST`  | GET-capable: **False**
- lenses: A-callsite
- NEW — not in the shipped spec; needs a command name

  live probe: **not probed** (parameterised path, or write-intent — see WRITE_INTENT in probe.py)

## `/api/auth/roles`

- harvested methods: `GET`  | GET-capable: **True**
- lenses: A-callsite
- **SHIPPED COMMAND (must not be renamed): `oms-pp-cli account roles`**

  shipped spec block:
  ```yaml
          path: "/api/auth/roles/"
          description: "List roles (admin, auditor, billing, rate approver, manager, etc.)"
          response:
            type: object
  ```

  live probe:
  - bare (no params) -> **HTTP 200**, rows=9, 488 bytes, top-level JSON `list`
    - sample: `[{"id": 1, "name": "admin", "display_name": "Admin"}, {"id": 3, "name": "approver", "display_name": "Approver"}, {"id": 5, "name": "auditor", "display_name": "Auditor"}, {"id": 4, "name": "billing", "display_name": "Billing"}, {"id": 9, "name": "legal", "display_name": "Legal"}, {"id": 2, "name": "m`

## `/api/auth/states`

- harvested methods: `GET`  | GET-capable: **True**
- lenses: A-callsite
- **SHIPPED COMMAND (must not be renamed): `oms-pp-cli account states`**

  shipped spec block:
  ```yaml
          path: "/api/auth/states/"
          description: "List states"
          response:
            type: object
  ```

  live probe:
  - bare (no params) -> **HTTP 200**, rows=27, 1149 bytes, top-level JSON `list`
    - sample: `[{"id": 29, "name": "Andaman and Nicobar Islands", "code": "AN"}, {"id": 10, "name": "Andhra Pradesh", "code": "AP"}, {"id": 15, "name": "Assam", "code": "AS"}, {"id": 16, "name": "Bihar", "code": "BH"}, {"id": 27, "name": "Chandigarh", "code": "CH"}, {"id": 26, "name": "Chhattisgarh", "code": "CT"}`

## `/api/auth/users/create`

- harvested methods: `POST`  | GET-capable: **False**
- lenses: A-callsite
- NEW — not in the shipped spec; needs a command name

  live probe: **not probed** (parameterised path, or write-intent — see WRITE_INTENT in probe.py)

## `/api/auth/users/list`

- harvested methods: `GET`  | GET-capable: **True**
- lenses: A-callsite
- **SHIPPED COMMAND (must not be renamed): `oms-pp-cli account users`**

  shipped spec block:
  ```yaml
          path: "/api/auth/users/list/"
          description: "List app users"
          response:
            type: object
  ```

  live probe:
  - bare (no params) -> **HTTP 200**, rows=52, 67540 bytes, top-level JSON `dict`
    - sample: `{"success": true, "data": [{"id": 2, "name": "Preshit", "username": "preshit", "email": "preshit@gmail.com", "phone": "9999999999", "role": "admin", "role_display": "Admin", "company": {"id": 1, "name": "Jivo Wellness"}, "main_group": {"id": 1, "name": "ROI"}, "main_groups": [], "state": {"id": 1, "`

## `/api/auth/users/{}`

- harvested methods: `PUT`  | GET-capable: **False**
- lenses: A-callsite
- NEW — not in the shipped spec; needs a command name

  live probe: **not probed** (parameterised path, or write-intent — see WRITE_INTENT in probe.py)

## `/api/auth/users/{}/page-permissions`

- harvested methods: `GET, PUT`  | GET-capable: **True**
- lenses: A-callsite
- **SHIPPED COMMAND (must not be renamed): `oms-pp-cli account user-page-permissions`**

  shipped spec block:
  ```yaml
          path: "/api/auth/users/{id}/page-permissions/"
          description: "Page-permission grants for a user"
          params:
            - name: id
              type: int
              required: true
              positional: true
              description: "User id"
          response:
            type: object
  ```

  live probe: **not probed** (parameterised path, or write-intent — see WRITE_INTENT in probe.py)

## `/api/auth/users/{}/parties`

- harvested methods: `GET`  | GET-capable: **True**
- lenses: A-callsite
- **SHIPPED COMMAND (must not be renamed): `oms-pp-cli account user-parties`**

  shipped spec block:
  ```yaml
          path: "/api/auth/users/{id}/parties/"
          description: "Parties (customers) assigned to a user"
          params:
            - name: id
              type: int
              required: true
              positional: true
              description: "User id"
          response:
            type: object
  ```

  live probe: **not probed** (parameterised path, or write-intent — see WRITE_INTENT in probe.py)

## `/api/devices/register`

- harvested methods: `POST`  | GET-capable: **False**
- lenses: A-callsite
- NEW — not in the shipped spec; needs a command name

  live probe: **not probed** (parameterised path, or write-intent — see WRITE_INTENT in probe.py)

## `/api/ui-config/admin/labels`

- harvested methods: `GET, POST`  | GET-capable: **True**
- lenses: A-callsite
- NEW — not in the shipped spec; needs a command name

  live probe:
  - bare (no params) -> **HTTP 200**, rows=1, 293 bytes, top-level JSON `dict`
    - sample: `{"success": true, "message": "UI labels fetched.", "data": [{"id": 1, "field_key": "price_list", "display_name": "Price List", "description": "Unified price list field label shown on web and mobile.", "is_active": true, "created_at": "2026-07-24T05:22:43.986703Z", "updated_at": "2026-07-29T10:08:08.`

## `/api/ui-config/admin/labels/{}`

- harvested methods: `DELETE, PUT`  | GET-capable: **False**
- lenses: A-callsite
- NEW — not in the shipped spec; needs a command name

  live probe: **not probed** (parameterised path, or write-intent — see WRITE_INTENT in probe.py)

## `/api/ui-config/labels`

- harvested methods: `GET`  | GET-capable: **True**
- lenses: C-indirect
- NEW — not in the shipped spec; needs a command name

  live probe:
  - bare (no params) -> **HTTP 200**, 27 bytes, top-level JSON `dict`
    - sample: `{"price_list": "Price List"}`
