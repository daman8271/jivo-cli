# Domain brief: tracker

22 paths. Live probe evidence and shipped command names are given per endpoint. Do not invent a command name for an endpoint that already has one.

## `/api/tracker/actions/bulk`

- harvested methods: `POST`  | GET-capable: **False**
- lenses: A-callsite
- NEW — not in the shipped spec; needs a command name

  live probe: **not probed** (parameterised path, or write-intent — see WRITE_INTENT in probe.py)

## `/api/tracker/admin/lookups/{}`

- harvested methods: `GET, POST`  | GET-capable: **True**
- lenses: A-callsite
- **SHIPPED COMMAND (must not be renamed): `oms-pp-cli tracker admin-lookups`**

  shipped spec block:
  ```yaml
          path: "/api/tracker/admin/lookups/{type}/"
          description: "Tracker admin: lookup set by type"
          params:
            - name: type
              type: string
              required: true
              positional: true
              description: "Lookup type"
          response:
            type: object
  ```

  live probe: **not probed** (parameterised path, or write-intent — see WRITE_INTENT in probe.py)

## `/api/tracker/admin/lookups/{}/{}`

- harvested methods: `DELETE, PATCH`  | GET-capable: **False**
- lenses: A-callsite
- NEW — not in the shipped spec; needs a command name

  live probe: **not probed** (parameterised path, or write-intent — see WRITE_INTENT in probe.py)

## `/api/tracker/admin/stages`

- harvested methods: `GET, POST`  | GET-capable: **True**
- lenses: A-callsite
- **SHIPPED COMMAND (must not be renamed): `oms-pp-cli tracker admin-stages`**

  shipped spec block:
  ```yaml
          path: "/api/tracker/admin/stages/"
          description: "Tracker admin: stage definitions"
          response:
            type: object
  ```

  live probe:
  - bare (no params) -> **HTTP 403**
    - server said: `{"detail":"Tracker administration is restricted to tracker admins."}`

## `/api/tracker/admin/stages/{}`

- harvested methods: `DELETE, PATCH`  | GET-capable: **False**
- lenses: A-callsite
- NEW — not in the shipped spec; needs a command name

  live probe: **not probed** (parameterised path, or write-intent — see WRITE_INTENT in probe.py)

## `/api/tracker/admin/tracker-users`

- harvested methods: `GET, POST`  | GET-capable: **True**
- lenses: A-callsite
- **SHIPPED COMMAND (must not be renamed): `oms-pp-cli tracker admin-tracker-users`**

  shipped spec block:
  ```yaml
          path: "/api/tracker/admin/tracker-users/"
          description: "Tracker admin: tracker-role users"
          response:
            type: object
  ```

  live probe:
  - bare (no params) -> **HTTP 403**
    - server said: `{"detail":"Tracker administration is restricted to tracker admins."}`

## `/api/tracker/admin/tracker-users/{}`

- harvested methods: `DELETE, PATCH`  | GET-capable: **False**
- lenses: A-callsite
- NEW — not in the shipped spec; needs a command name

  live probe: **not probed** (parameterised path, or write-intent — see WRITE_INTENT in probe.py)

## `/api/tracker/admin/users`

- harvested methods: `GET`  | GET-capable: **True**
- lenses: A-callsite
- **SHIPPED COMMAND (must not be renamed): `oms-pp-cli tracker admin-users`**

  shipped spec block:
  ```yaml
          path: "/api/tracker/admin/users/"
          description: "Tracker admin: users"
          response:
            type: object
  ```

  live probe:
  - bare (no params) -> **HTTP 403**
    - server said: `{"detail":"Tracker administration is restricted to tracker admins."}`

## `/api/tracker/admin/users/{}/stages`

- harvested methods: `PUT`  | GET-capable: **False**
- lenses: A-callsite
- NEW — not in the shipped spec; needs a command name

  live probe: **not probed** (parameterised path, or write-intent — see WRITE_INTENT in probe.py)

## `/api/tracker/alerts`

- harvested methods: `GET`  | GET-capable: **True**
- lenses: A-callsite
- **SHIPPED COMMAND (must not be renamed): `oms-pp-cli tracker alerts`**

  shipped spec block:
  ```yaml
          path: "/api/tracker/alerts/"
          description: "Tracker alerts"
          response:
            type: object
  ```

  live probe:
  - bare (no params) -> **HTTP 403**
    - server said: `{"detail":"You do not have access to this tracker page."}`

## `/api/tracker/all-invoices`

- harvested methods: `GET`  | GET-capable: **True**
- lenses: A-callsite
- **SHIPPED COMMAND (must not be renamed): `oms-pp-cli tracker all-invoices`**

  shipped spec block:
  ```yaml
          path: "/api/tracker/all-invoices/"
          description: "All tracker invoices"
          response:
            type: object
  ```

  live probe:
  - bare (no params) -> **HTTP 403**
    - server said: `{"detail":"Tracker administration is restricted to tracker admins."}`

## `/api/tracker/all-invoices/export`

- harvested methods: `GET`  | GET-capable: **True**
- lenses: A-callsite
- **SHIPPED COMMAND (must not be renamed): `oms-pp-cli tracker all-invoices-export`**

  shipped spec block:
  ```yaml
          path: "/api/tracker/all-invoices/export/"
          description: "Export of all tracker invoices"
          response:
            type: object
  ```

  live probe:
  - bare (no params) -> **HTTP 403**
    - server said: `{"detail":"Tracker administration is restricted to tracker admins."}`

## `/api/tracker/invoices`

- harvested methods: `GET, POST`  | GET-capable: **True**
- lenses: A-callsite
- **SHIPPED COMMAND (must not be renamed): `oms-pp-cli tracker invoices`**

  shipped spec block:
  ```yaml
          path: "/api/tracker/invoices/"
          description: "Tracker invoices"
          response:
            type: object
  ```

  live probe:
  - bare (no params) -> **HTTP 403**
    - server said: `{"detail":"You do not have access to this tracker page."}`

## `/api/tracker/invoices/{}`

- harvested methods: `DELETE, GET, PATCH`  | GET-capable: **True**
- lenses: A-callsite
- **SHIPPED COMMAND (must not be renamed): `oms-pp-cli tracker invoice-detail`**

  shipped spec block:
  ```yaml
          path: "/api/tracker/invoices/{id}/"
          description: "Single tracker invoice"
          params:
            - name: id
              type: int
              required: true
              positional: true
              description: "Tracker invoice id"
          response:
            type: object
  ```

  live probe: **not probed** (parameterised path, or write-intent — see WRITE_INTENT in probe.py)

## `/api/tracker/invoices/{}/jsap`

- harvested methods: `GET`  | GET-capable: **True**
- lenses: A-callsite
- NEW — not in the shipped spec; needs a command name

  live probe: **not probed** (parameterised path, or write-intent — see WRITE_INTENT in probe.py)

## `/api/tracker/invoices/{}/payment`

- harvested methods: `PATCH`  | GET-capable: **False**
- lenses: A-callsite
- NEW — not in the shipped spec; needs a command name

  live probe: **not probed** (parameterised path, or write-intent — see WRITE_INTENT in probe.py)

## `/api/tracker/jsap/sync`

- harvested methods: `POST`  | GET-capable: **False**
- lenses: A-callsite
- NEW — not in the shipped spec; needs a command name

  live probe: **not probed** (parameterised path, or write-intent — see WRITE_INTENT in probe.py)

## `/api/tracker/lookups`

- harvested methods: `GET`  | GET-capable: **True**
- lenses: A-callsite
- **SHIPPED COMMAND (must not be renamed): `oms-pp-cli tracker lookups`**

  shipped spec block:
  ```yaml
          path: "/api/tracker/lookups/"
          description: "Tracker lookup reference data"
          response:
            type: object
  ```

  live probe:
  - bare (no params) -> **HTTP 403**
    - server said: `{"detail":"You do not have access to this tracker page."}`

## `/api/tracker/my-queue`

- harvested methods: `GET`  | GET-capable: **True**
- lenses: A-callsite
- **SHIPPED COMMAND (must not be renamed): `oms-pp-cli tracker my-queue`**

  shipped spec block:
  ```yaml
          path: "/api/tracker/my-queue/"
          description: "Current user's tracker work queue"
          response:
            type: object
  ```

  live probe:
  - bare (no params) -> **HTTP 403**
    - server said: `{"detail":"You do not have access to this tracker page."}`

## `/api/tracker/reports`

- harvested methods: `GET`  | GET-capable: **True**
- lenses: A-callsite
- **SHIPPED COMMAND (must not be renamed): `oms-pp-cli tracker reports`**

  shipped spec block:
  ```yaml
          path: "/api/tracker/reports/"
          description: "Tracker reports"
          response:
            type: object
  ```

  live probe:
  - bare (no params) -> **HTTP 403**
    - server said: `{"detail":"You do not have access to this tracker page."}`

## `/api/tracker/stage-advanced`

- harvested methods: `GET`  | GET-capable: **True**
- lenses: A-callsite
- params observed at the call site: `stage`
- **SHIPPED COMMAND (must not be renamed): `oms-pp-cli tracker stage-advanced`**

  shipped spec block:
  ```yaml
          path: "/api/tracker/stage-advanced/"
          description: "Advanced stage view"
          response:
            type: object
  ```

  live probe:
  - bare (no params) -> **HTTP 403**
    - server said: `{"detail":"You do not have access to this tracker page."}`

## `/api/tracker/vendors`

- harvested methods: `GET`  | GET-capable: **True**
- lenses: A-callsite
- **SHIPPED COMMAND (must not be renamed): `oms-pp-cli tracker vendors`**

  shipped spec block:
  ```yaml
          path: "/api/tracker/vendors/"
          description: "Tracker vendors"
          response:
            type: object
  ```

  live probe:
  - bare (no params) -> **HTTP 403**
    - server said: `{"detail":"You do not have access to this tracker page."}`
