# Domain study: `account`

29 paths across `/api/auth/`, `/api/admin/devices/`, `/api/devices/` and
`/api/ui-config/`. **15 published (all GET), 14 excluded.** Two published paths
also serve a write verb on the same URL; the write is excluded verb-by-verb, not
path-by-path.

Everything below was measured live on 2026-08-04 with the `paramjot` token
(`role=admin`, `company=Jivo Wellness`, `category=OIL`). Where a fact came from
the SPA bundle instead of a live call, it says so.

> ⚠️ **Read `## Domain summary → Backend defects` before shipping anything.**
> `GET /api/auth/users/list/` serves **54 users' full PBKDF2 password hashes to
> an unauthenticated caller**. Verified from two independent hosts. That is a
> live production credential-disclosure, not a CLI concern.

---

### `/api/admin/devices/`

- **command**: `account devices`  (NEW)
- **verdict**: publish
- **description**: The device registry — every browser and phone that has logged
  into OMS, who was on it, and when it was last seen. This is how you find out
  which app build a salesperson is actually running before you believe a bug
  report from the field.
- **params**:
  - `search` — string, optional, query. Free text. Server-side matches user name
    / app version / build. Source: the app's own filter state
    `rge={search:'',build_number:'',status:''}` (bundle @1996009) and the search
    box's own placeholder "Search by name, version or build…". Verified live:
    `?search=Navneet` → 4 rows, all `user_name = "Navneet Singh"`.
  - `status` — string, optional, query. Enum **`online` | `idle` | `offline` |
    `inactive`**. Source: the bundle's own status map
    `Zhe={online:'Online',idle:'Idle',offline:'Offline',inactive:'Inactive'}`
    *and* the live `status_counts` object on `devices/analytics/`. Verified
    live: `?status=offline` → `total: 249`, which equals the analytics
    `status_counts.offline` exactly.
  - `build_number` — int, optional, query. Verified live: `?build_number=3` →
    `total: 46`.
  - `ordering` — string, optional, query. Django-style; prefix `-` for
    descending. Fields observed in the app's sortable column headers:
    `user__name`, `app_type`, `app_version`, `build_number`, `last_active`.
    Server default is **`-last_active`** (the app sends it explicitly;
    `tge='-last_active'` @1996009). Verified live: `?ordering=user__name`
    returns Abhijit first; `?ordering=-last_active` returns today's timestamps
    descending. Note the **double underscore** in `user__name` — it is a Django
    relation traversal, not a typo.
  - `page` — int, optional, query, default 1.
  - `page_size` — int, optional, query, default 25 (`ege=25` in the bundle),
    **server caps it at 100**. Verified live: `?page_size=500` came back with
    `page_size: 100` and 100 rows.
- **response**: `object`.
  `{success, message:"Devices retrieved", data:{results:[…], pagination:{page,
  page_size, total, total_pages}}}`.
  Row fields (27): `id`, `device_id` (client-generated UUID), `user_id`,
  `username`, `user_name`, `email`, `role`, `status`, `platform`
  (`WEB`|`ANDROID`|`IOS`), `app_type` (`WEB`|`MOBILE`), `app_version`,
  `build_number`, `device_name`, `manufacturer`, `device_model`, `browser_name`,
  `browser_version`, `os_name`, `os_version`, `language`, `timezone`,
  `first_login`, `last_login`, `last_active`, `is_active`, `created_at`,
  `updated_at`.
  **This is the only paginated endpoint in the whole account domain.** Every
  other list here returns everything in one shot.
- **evidence**: HTTP 200 bare (brief) and six live parameterised calls today.
- **traps**:
  - It is **paginated and defaults to 25 rows** while `total` is 253. A command
    that prints `results` without following `pagination` silently shows 10% of
    the fleet. Needs an `--all` that walks `total_pages`.
  - One human = many rows. "Navneet Singh" holds 4 devices (2 WEB, 2 IOS).
    252 devices vs 54 users — never treat a device count as a user count.
  - `status` is **derived from `last_active`, not stored**: the analytics
    endpoint publishes the thresholds — online ≤5 min, idle ≤30 min, inactive
    after 30 days. So the same row's `status` changes between two calls with no
    write in between.
  - Returns 401 unauthenticated (checked).

---

### `/api/admin/devices/analytics/`

- **command**: `account device-analytics`  (NEW)
- **verdict**: publish
- **description**: One-screen rollout health for the OMS apps — how many devices
  are on each Android/iOS/web build, and how many have been seen recently. Use
  it to answer "has everyone updated?" before blaming the backend.
- **params**:
  - `days` — int, optional, query, **default 14**. Controls only the length of
    the `devices_by_last_seen` series. Source: `getAnalytics(e)` sends
    `{days:e}` (bundle @1994907). Verified live: `?days=7` → 7 buckets,
    `?days=30` → 30 buckets, no param → 14 buckets.
- **response**: `object`.
  `data.cards`: `total_devices`, `active_devices`, `inactive_devices`,
  `mobile_devices`, `web_devices`, `android_devices`, `ios_devices`,
  `desktop_browsers`, `devices_active_today`, `status_counts{online,idle,
  offline,inactive}`, `status_thresholds{online_within_minutes:5,
  idle_within_minutes:30, inactive_after_days:30}`.
  `data.charts`: `version_distribution[]` (platform/app_type/app_version/
  build_number/count), `platform_distribution[]`, `app_type_distribution[]`,
  `browser_distribution[]`, `os_distribution[]`, `devices_by_last_seen[]`
  (date/count).
- **evidence**: HTTP 200 bare + three live `days` calls today.
- **traps**:
  - `active_devices` is **not** "currently online". Live today:
    `active_devices: 252` while `status_counts.online: 0`. `active` means
    `is_active=true` (the row has not been retired); "online" is the 5-minute
    window. Two different questions, adjacent field names.
  - `browser_distribution` contains an empty-string bucket of 72 — those are the
    mobile apps, which have no browser. Don't render it as "unknown browser".
  - Counts drift within a session; the numbers here were 252 total at 14:5x and
    253 a few minutes later.

---

### `/api/admin/devices/{id}/`

- **command**: `account device`  (NEW)
- **verdict**: publish
- **description**: Full record for one enrolled device — model, OS, app build,
  first and last login — for when you need to confirm exactly what a specific
  user was running.
- **params**:
  - `id` — int, required, positional. The registry row id, **not** `device_id`
    and **not** `user_id`. Source: `getDevice(e)` → `/admin/devices/${e}/`
    (bundle @1994907), with ids taken from the live list.
- **response**: `object`. `{success, message:"Device retrieved", data:{…}}` —
  `data` is a **single row with exactly the same 27 fields** as one element of
  the list's `results`. No extra detail is returned; the list already contains
  everything.
- **evidence**: **live `GET /api/admin/devices/11/` → HTTP 200, 727 bytes**, id
  sourced from the live list. Field-for-field identical to that row in the list.
- **traps**:
  - Because the detail adds nothing over the list row, a bulk question should be
    answered from `account devices` with a filter, not by looping this.
  - The path takes the numeric `id`. Operators will have the UUID `device_id`
    (the UI has a "Copy device ID" button that copies the UUID). Passing the
    UUID here will not work; resolve it via `account devices --search` first.
  - I did **not** probe a non-existent id — that value would have been invented,
    which rule 2 forbids — so the 404 shape is unverified.

---

### `/api/auth/assign-parties/`

- **command**: —
- **verdict**: exclude
- **exclusion reason**: write verb (POST `{user_id, card_codes[], category?}` —
  bundle @805272)

### `/api/auth/assign-parties/bulk-upload/`

- **command**: —
- **verdict**: exclude
- **exclusion reason**: write verb (POST `{rows:[…]}` from an uploaded sheet)

### `/api/auth/bulk-party/assign-products/`

- **command**: —
- **verdict**: exclude
- **exclusion reason**: write verb (POST `{card_codes[], party_selections[],
  products[]}` — bundle @1558488)

---

### `/api/auth/categories/`

- **command**: `account categories`  (shipped)
- **verdict**: publish
- **description**: JIVO's three product categories inside OMS — which of the
  three businesses a party, a product, or a user belongs to.
- **params**: none.
- **response**: **`array`** (the shipped spec says `object`; it is a bare JSON
  list). 3 rows. The key is **`category`, not `name`** — this list is the one
  exception to the `{id,name}` shape every other reference list uses.

  | id | category | what it means at JIVO |
  |---|---|---|
  | 1 | `OIL` | the edible-oils business — SAP company `JIVO_OIL_HANADB` |
  | 2 | `BEVERAGES` | drinks/water — SAP company `JIVO_BEVERAGES_HANADB` |
  | 3 | `MART` | JIVO Mart — SAP company `JIVO_MART_HANADB` |

- **evidence**: live GET → HTTP 200, 3 rows, 86 bytes (re-fetched in full today).
- **traps**:
  - **`category` is not `branch`.** `branch` (on every `hana/*` and
    `service-layer/*` endpoint) is `OIL` | `BEVERAGE` — **singular**, and it has
    **no MART value at all**. Sending `BEVERAGES` where `branch` is wanted, or
    `MART` anywhere near a `hana/*` call, fails. See API-FACTS §2.
  - Three categories but only **two** companies (below). Category is the finer
    grain and it is the one that partitions data.
  - The list comes back sorted alphabetically, so `BEVERAGES` (id 2) is first
    and `OIL` (id 1) is last. Do not assume id order.
  - Served **200 with no Authorization header** (checked). Harmless — it is
    static reference data — but it confirms the auth gap below is a class of
    problem in this app, not one bad decorator.

---

### `/api/auth/companies/`

- **command**: `account companies`  (shipped)
- **verdict**: publish
- **description**: The two legal entities a user account can be attached to.
- **params**: none.
- **response**: **`array`**, 2 rows, `{id, name}`.

  | id | name | what it means |
  |---|---|---|
  | 1 | `Jivo Wellness` | Jivo Wellness Pvt Ltd — the entity behind both the OIL and BEVERAGES categories. 42 of 52 users sit here. |
  | 2 | `Jivo Mart` | the Mart entity. **Zero users are assigned to it** in today's data. |

- **evidence**: live GET → HTTP 200, 2 rows, 61 bytes.
- **traps**:
  - **Two companies, three categories, three SAP company databases.** They do
    not line up. `Jivo Wellness` covers OIL *and* BEVERAGES; `MART` is a
    category with a company nobody uses. Never map company → SAP DB 1:1.
  - The shipped description says "Jivo Mart, Jivo Wellness" — correct, but the
    ordering is alphabetical by name, not by id.
  - 10 of 52 users have `company: null` (all the `tracker_*` roles). A join on
    company drops them.
  - Served 200 unauthenticated (checked).

---

### `/api/auth/login/`

- **command**: —
- **verdict**: exclude
- **exclusion reason**: auth mutator. **Never published and never probed.**
  Its response body is the origin of the password-hash leak documented below.

### `/api/auth/logout/`

- **command**: —
- **verdict**: exclude
- **exclusion reason**: auth mutator. Never published, never probed.

---

### `/api/auth/mainGroup/`

- **command**: `account main-groups`  (shipped)
- **verdict**: publish
- **description**: JIVO's 27 sales channels / customer segments — the field that
  says whether a party is General Trade, Modern Trade, e-commerce, CSD, export,
  a branch transfer, or staff. It is the primary way sales get sliced.
- **params**: none.
- **response**: **`array`**, 27 rows, `{id, name}`.

  Live values, with what they mean at JIVO:

  | id | name | meaning |
  |---|---|---|
  | 1 | `ROI` | Rest of India — the distributor/general trade base outside the focus states |
  | 2 | `GT` | General Trade — traditional kirana/distributor channel |
  | 3 | `MT` | Modern Trade — organised retail chains |
  | 4 | `STAFF` | staff sales |
  | 5 | `E-COMMERCE` | Amazon/Flipkart/q-commerce accounts |
  | 6 | `PURCHASE OIL` | oil purchase counterparties |
  | 7 | `HORECA` | hotels, restaurants, caterers |
  | 8 | `CALL CENTER` | tele-sales |
  | 9 | `TRANSPORT` | transporters |
  | 10 | `WEBSITE` | D2C web orders |
  | 11 | `CSD` | Canteen Stores Department (defence) |
  | 12 | `EXPORT` | export customers |
  | 13 | `BULK OIL` | bulk/tanker oil |
  | 14 | `CORPORATE` | corporate gifting / institutional |
  | 15 | `REFERENCE` | reference accounts |
  | 16 | `SANGAT` | community/gurdwara sales |
  | 17 | `COMPANY UNIT` | internal units |
  | 18 | `FIXED ASSETS` | fixed-asset counterparties (not a sales channel) |
  | 19 | `JOB WORK` | third-party job work |
  | 20 | `EVENTS & EXHIBITIONS` | event sales |
  | 21 | `BRANCH` | **inter-branch / intercompany transfers** |
  | 22 | `CASH SALE` | counter cash sales |
  | 23 | `STAFF CUSTOMER` | staff-as-customer accounts |
  | 24 | `CONSUMABLES` | consumables |
  | 25 | `PVT` | private-label |
  | 26 | `GOVT` | government |
  | 28 | `CALL CENTRE` | **duplicate of id 8** — see traps |

- **evidence**: live GET → HTTP 200, 27 rows, 750 bytes; every row printed and
  read today.
- **traps**:
  - **`CALL CENTER` (8) and `CALL CENTRE` (28) are the same channel entered
    twice.** Any group-by on `main_group` splits tele-sales across two buckets.
    This is a live master-data defect, not a naming choice.
  - **id 27 does not exist** — ids run 1–28 with 27 missing. Never iterate ids.
  - `BRANCH` (21) is intercompany, and `FIXED ASSETS` (18) is not a sales
    channel at all. Both must be excluded from any channel-mix number, the same
    way correction **C-0005** excludes the 23 intercompany card codes in SAP.
  - `main_group` is a **string name** on `/api/sap/parties/` rows and an
    **`{id,name}` object** on user rows. Same concept, two shapes.

---

### `/api/auth/parties/{card_code}/products/`

- **command**: `account party-products`  (shipped)
- **verdict**: publish
- **description**: The SKUs a specific customer is allowed to be sold, with the
  party-specific basic rate. This is what constrains the item dropdown when
  someone raises an order for that party.
- **params**:
  - `card_code` — string, required, positional. The SAP card code, e.g.
    `CUSTA000593`. Source: live `GET /api/sap/parties/` (3358 rows) and the
    `card_codes[]` array returned by `account user-parties`.
  - `category` — string, optional, query. Enum `OIL` | `BEVERAGES` | `MART`
    from `/api/auth/categories/`. Source: the app's own call —
    `getPartyProducts:(e,t)=>Y.get('/auth/parties/'+e+'/products/',
    {params:t?{category:t}:undefined})` (bundle @805272).
- **response**: `object`.
  `{success, data:{party:{card_code, card_name, state, main_group},
  products:[…], total_assigned}}`.
  Product fields: `id` (the assignment-row id, **not** an item id), `item_code`
  (SAP `FG…`), `item_name`, `category`, `brand` (`JIVO` / `SANO`), `variety`,
  `sub_group`, `sal_pack_unit`, `basic_rate`, `assigned_at`.
- **evidence**: **six live calls today, all HTTP 200**:
  - `CUSTA001139` → 13 products (`AMAR CHAND GUPTA OILS MILLS`)
  - `CUSTA000593` → 12 (`SS AGRO PRODUCTS`)
  - `CUSTA001094` → 17 (`GRACIOUS EMPIRE HOSPITALITIES LLP`)
  - `CUSTA000001` → 23 (`JIVO WELLNESS PVT LTD - DL`, intercompany)
  - `CUSTA001139?category=OIL` → 1 · `?category=BEVERAGES` → 12 · no param → 13
    — **the `category` filter demonstrably works here**
  - `CUSTA000502/3/4/5/6/7` → HTTP 200, `total_assigned: 0`, `products: []`,
    **but `party` still resolves with the real `card_name`** — a valid card code
    with no assignments is a 200-with-zero, not a 404.
- **traps**:
  - **`variety` and `sub_group` mean the opposite of what they read like.**
    Live rows: `variety:"EXTRA LIGHT", sub_group:"OLIVE"` and
    `variety:"COLD PRESS", sub_group:"CANOLA"`. So **`sub_group` is the oil
    variety** (OLIVE/CANOLA/MUSTARD/SUNFLOWER/RICE BRAN) and **`variety` is the
    grade within it** (EXTRA LIGHT/EXTRA VIRGIN/POMACE/COLD PRESS). They mirror
    SAP's `OITM.U_Sub_Group` and `OITM.U_Variety` faithfully — the field names
    are right and the English is misleading. Answering "how much olive did we
    sell" off `variety` gives the wrong number. Matches corrections C-0003 and
    the `sap-olive-grade-field` note.
  - **A party's product list crosses categories.** `CUSTA001139` is an *oils*
    party whose 13 assigned SKUs are 12 BEVERAGES and 1 OIL; `CUSTA000001`
    carries OIL + BEVERAGES + MART rows in one response. Never infer the party's
    category from its products, and pass `--category` when you want one book.
  - **`basic_rate` is a configured field, not a verified price.** It is the
    "Price List (Basic)" the order form pre-fills (bundle: `a.priceListBasic =
    String(t.basic_rate ?? '')`; the bulk sheet accepts the column under
    `Basic Rate` / `Price List (Basic)` / `Rate`). Observed values run 0.0–27.32
    and **most are 0.0**; one row prices a 15 LTR canola tin at ₹2.00. Some of
    those are plausible per-piece ex-tax rates (₹6.35 on a 1 L water bottle),
    some are clearly placeholders. **Do not present `basic_rate` as a selling
    price without checking it against `hana/item-price/`.** Medium confidence at
    best — I did not cross-check a single row against HANA.
  - `sal_pack_unit` is a **string** (`"15.000000"`), not a number, and it is
    litres per piece — so it is the multiplier for the tonnage conversion, not a
    carton count.
  - `products[].id` is the assignment row. Two parties assigned the same item
    have different `id`s for it.

---

### `/api/auth/party-product/bulk-add/`

- **command**: —
- **verdict**: exclude
- **exclusion reason**: write verb (POST `{card_codes[], products[]}`)

### `/api/auth/party-product/remove/`

- **command**: —
- **verdict**: exclude
- **exclusion reason**: write verb (POST `{card_code, item_code, category}`)

### `/api/auth/party-product/update-rate/`

- **command**: —
- **verdict**: exclude
- **exclusion reason**: write verb (POST `{card_code, item_code, category,
  basic_rate}` — this is the endpoint that sets the `basic_rate` above)

---

### `/api/auth/profile/`

- **command**: `account profile`  (shipped)
- **verdict**: publish
- **description**: Who the token belongs to and exactly what it can see —
  role, company, every main group, every state, every category, and the extra
  pages granted. **This is the health check.** Run it first whenever another
  command returns 0 rows or 403; nine times out of ten the answer is in here.
- **params**: none.
- **response**: `object`. `{success, data:{…}}` with 23 fields:

  | field | type | what it means |
  |---|---|---|
  | `id`, `name`, `username`, `email`, `phone` | scalars | identity |
  | `role` | string | machine name, e.g. `admin` — matches `auth/roles[].name` |
  | `role_display` | string | UI label, e.g. `Admin` |
  | `company` | `{id,name}` | one of the two companies |
  | `main_group` | `{id,name}` | **legacy singular — do not use, see traps** |
  | `main_groups` | `[{id,name}]` | **the real channel scope.** 27 for this token |
  | `state` | `{id,name,code}` | legacy singular — do not use |
  | `states` | `[{id,name,code}]` | **the real geographic scope.** 27 for this token |
  | `category` | `{id,category}` | primary category — `{id:1,category:"OIL"}` here |
  | `categories` | `[{id,category}]` | full category scope — `[OIL]` here |
  | `sub_group` | string \| null | free-text CSV of SAP sub-groups the user is scoped to |
  | `is_active`, `is_superuser`, `is_staff` | bool | Django flags. This admin is `is_superuser:false` |
  | `last_login`, `date_joined`, `created_at` | ISO 8601 | |
  | `extra_pages` | `[string]` | **the page permissions.** `[]` for this token |
  | `password` | string | **the caller's full PBKDF2 hash — see the security finding** |

- **evidence**: live GET → HTTP 200, 3988 bytes, every field enumerated today.
  Returns **401** unauthenticated (checked).
- **traps**:
  - The shipped description promises "page permissions". The field is called
    **`extra_pages`**, and for an `admin` it is **`[]`** — admins get every page
    implicitly (`_7 = e => String(e||'').trim().toLowerCase()==='admin'` in the
    bundle gates the sidebar). **An empty `extra_pages` on an admin does not
    mean "no access".** Only the five non-admin users with grants have entries.
  - **`main_group` (singular) is not `main_groups[0]`.** For this token the
    singular is `BRANCH` while the plural is all 27, and across the 52-user
    table the singular disagrees with `main_groups[0]` for 1 user and `state`
    disagrees with `states[0]` for 2. They are separate legacy columns. **Scope
    questions must read the plural.**
  - `category` is an object keyed `category`, not `name` — `{id:1,
    category:"OIL"}`. Every other reference object uses `name`.
  - `sub_group` is a comma-joined **string**, not a list, and it is polluted:
    this admin's value opens with `1204019-INSTALLATION-CONTAINER 20 FEET,
    1204022 - GAS DISTRIBUTION PANEL (FA0000354)…` — SAP fixed-asset codes
    sitting in the item sub-group master. Only 5 of 52 users have it set. It
    corroborates the "fixed assets carried as stock" finding from the godown
    board; do not parse it as a clean variety list.
  - **`password` is present in the response.** See the security finding.

---

### `/api/auth/refresh/`

- **command**: —
- **verdict**: exclude
- **exclusion reason**: auth mutator. Never published, never probed. (Refresh
  rotation is ON — see API-FACTS §6; that is a token-rotator concern, not a
  command.)

### `/api/auth/remove-party/`

- **command**: —
- **verdict**: exclude
- **exclusion reason**: write verb (POST `{user_id, card_codes[]}`)

---

### `/api/auth/roles/`

- **command**: `account roles`  (shipped)
- **verdict**: publish
- **description**: The nine job types an OMS account can hold. This is what
  decides which screens a person sees and where they sit in the order-approval
  chain.
- **params**: none.
- **response**: **`array`**, 9 rows, `{id, name, display_name}`.

  | id | name | display | what the person does |
  |---|---|---|---|
  | 1 | `admin` | Admin | full app access; bypasses `extra_pages` entirely |
  | 2 | `manager` | Manager | the sales manager who raises orders for assigned parties — **30 of 52 users** |
  | 3 | `approver` | Approver | approves orders/rates in the flow |
  | 4 | `billing` | Billing | raises the invoice after approval |
  | 5 | `auditor` | Auditor | one of the three `orders/status-tracking/` modes |
  | 6 | `tracker_admin` | Tracker Admin | administers the separate invoice-tracker module |
  | 7 | `tracker_entry` | Tracker Entry | data entry into the tracker |
  | 8 | `tracker_user` | Tracker User | reads the tracker |
  | 9 | `legal` | Legal | legal/label module |

  Live distribution across the 52 users: manager 30, tracker_user 6, billing 4,
  tracker_admin 4, admin 3, approver 3, auditor 1, legal 1, tracker_entry 0.
- **evidence**: live GET → HTTP 200, 9 rows, 488 bytes.
- **traps**:
  - **`role` is not the tracker grant.** API-FACTS §3 records all 12
    `/api/tracker/*` endpoints returning 403 to a global `admin`. The three
    `tracker_*` roles are a separate access system; holding `admin` buys you
    nothing there. Do not tell an operator "you're an admin so tracker will
    work".
  - `auditor` | `billing` | `rate_approver` is the `mode` enum on
    `orders/status-tracking/`. **`rate_approver` is not a role here** — the role
    is `approver`. Two overlapping vocabularies; don't cross them.
  - The 10 users with `company: null` and `category: null` are exactly the
    `tracker_*` accounts. Tracker users live outside the company/category model.
  - Sorted alphabetically by `name`, not by id.
  - Served 200 unauthenticated (checked).

---

### `/api/auth/states/`

- **command**: `account states`  (shipped)
- **verdict**: publish
- **description**: The 27 states/UTs JIVO actually sells into, with the state
  code the rest of the system uses. Not a list of Indian states — a list of
  JIVO's territories.
- **params**: none.
- **response**: **`array`**, 27 rows, `{id, name, code}`.
  Live set (id · code · name): 1·DL Delhi, 2·PB Punjab, 3·WB West Bengal,
  4·HR Haryana, 5·UP Uttar Pradesh, 6·MH Maharashtra, 7·KR Kerala,
  8·GJ Gujarat, 9·KA Karnataka, 10·AP Andhra Pradesh, 11·JK Jammu Kashmir,
  12·MP Madhya Pradesh, 13·GO Goa, 14·UK Uttarakhand, 15·AS Assam,
  16·BH Bihar, 17·RJ Rajasthan, 21·MZ Mizoram, 22·HP Himachal Pradesh,
  23·DB Dadra and Nagar Haveli and Daman and Diu, 24·OD Odisha,
  25·TE Telangana, 26·CT Chhattisgarh, 27·CH Chandigarh, 28·TN Tamil Nadu,
  29·AN Andaman and Nicobar Islands, 30·MN Manipur.
- **evidence**: live GET → HTTP 200, 27 rows, 1149 bytes; every row printed.
- **traps**:
  - **These are JIVO's own codes, not the ISO/GST ones.** Bihar is `BH` (ISO
    `BR`), Kerala `KR` (ISO `KL`), Goa `GO` (ISO `GA`), Telangana `TE` (ISO
    `TS`). Joining to a GST state code table on `code` will silently drop rows.
  - Only 27 of India's 36 states/UTs. A missing state is "we don't sell there",
    not a data gap.
  - **ids 18, 19, 20 do not exist** — the id range is 1–30 with three holes.
    Never iterate ids.
  - `state` on a `/api/sap/parties/` row is the **code string** (`"DL"`); on a
    user row it is an `{id,name,code}` object. Same concept, two shapes.
  - Sorted alphabetically by name.
  - Served 200 unauthenticated (checked).

---

### `/api/auth/users/create/`

- **command**: —
- **verdict**: exclude
- **exclusion reason**: write verb (POST — creates an OMS login)

---

### `/api/auth/users/list/`

- **command**: `account users`  (shipped)
- **verdict**: publish
- **description**: Every OMS login — who they are, what role they hold, and
  which company/category/channels/states they are scoped to. The starting point
  for "why can't so-and-so see this order".
- **params**: none observed. The app calls it bare
  (`getUsers: async()=>Y.get('/auth/users/list/')`, bundle @804434). No filter,
  no pagination, no `search`. **Unproven resolves to excluded** — do not add
  params that were not observed.
- **response**: `object` — **`{success: true, data: [ … ]}`**, i.e. the rows are
  an array *nested under* `data`. (The shipped spec's `type: object` is right
  about the envelope and unhelpful about the payload; the sibling reference
  endpoints are bare arrays, so a generic "unwrap `data` if present" rule is
  needed, not a per-endpoint guess.)
  52 rows at 14:5x today; **54 a few minutes later** (two `tracker_user`
  accounts created at 09:16 and 09:17 UTC). Each row carries the **same 23
  fields as `/api/auth/profile/`** — same serializer, `password` included.
- **evidence**: live GET → HTTP 200, 52 rows, 67540 bytes, every field
  enumerated and every row's role/company/category tallied today.
- **traps**:
  - **It leaks all 54 users' password hashes, and it does so without
    authentication.** See the security finding — this is the single most
    important fact in this study.
  - Not paginated and not filterable — the whole table comes back every time.
    68 KB today; it will grow.
  - Ids are sparse (2–70 with 18 gaps). `is_active` is `true` for all 52 —
    deactivation is not being used, so "active user count" from this endpoint
    is really "row count".
  - `main_groups` is `[]` for some users who still have a singular
    `main_group` — 1 user today. Treat empty-plural-with-nonempty-singular as
    "scope never migrated", not "no scope".
  - 12 users have `category: null`, 10 have `company: null`. Group-bys need a
    null bucket.

---

### `/api/auth/users/{id}/` (PUT)

- **command**: —
- **verdict**: exclude
- **exclusion reason**: write verb (PUT — edits an existing OMS login,
  including its `password`)

---

### `/api/auth/users/{id}/page-permissions/`

- **command**: `account user-page-permissions`  (shipped)
- **verdict**: **publish the GET only**
- **exclusion reason** (for the other verb): **this URL serves GET *and* PUT.**
  `updatePagePermissions:(e,t)=>Y.put('/auth/users/'+e+'/page-permissions/',
  {extra_pages:t})` (bundle @806535). **The PUT is excluded — it grants and
  revokes access to admin screens.** The exclusion must be keyed on
  *path + verb*; an exclusion keyed on path alone would wrongly kill a
  working read, and a publication keyed on path alone would ship a permissions
  editor.
- **description**: Which extra admin screens a specific user has been granted
  beyond their role's defaults.
- **params**:
  - `id` — int, required, positional. User id from `account users`.
- **response**: `object`. `{success, data:{user_id, extra_pages:[string]}}`.
  `extra_pages` is a list of page **keys**. The full enum, read from the app's
  own `h7` table (bundle @1800430) — key → label → route:

  | key | label |
  |---|---|
  | `App_User` | App User |
  | `Sap_Sync` | SAP Sync |
  | `Party_Assignment` | Party Assignment |
  | `Party_Product_Assignment` | Party Product Assignment |
  | `Add_Scheme` | Add Scheme |
  | `Order_Flow_Settings` | Order Flow Settings |
  | `Product_Stock` | Stock |
  | `Reports` | Reports (routes to `/Daily_Report`) |
  | `Einvoice` | e-Invoice (IRN) |
  | `Ewaybill` | e-Way Bill |
  | `Device_Management` | Device Management |

- **evidence**: **four live GETs today, all HTTP 200**, ids taken from
  `account users`:
  - `62` (admin) → `{"user_id":62,"extra_pages":[]}`
  - `3` (manager) → `{"user_id":3,"extra_pages":[]}`
  - `21` (billing) → `["Party_Product_Assignment","Party_Assignment",
    "Add_Scheme","Sap_Sync"]`
  - `33` (billing) → the same four, different order
  Returns **401** unauthenticated (checked).
- **traps**:
  - **Empty ≠ no access.** Admins get every page from their role and always
    return `[]`. Only 5 of 52 users have any entry at all. Reading this endpoint
    alone will tell you an admin has no permissions.
  - The order of `extra_pages` is not stable between users; never diff two
    users' lists positionally.
  - The values are identical to the `extra_pages` already present on the
    matching row of `account users` — this endpoint is a convenience, not a
    separate source of truth.
  - Same URL serves the PUT. Anything generated from this study must not emit a
    write path for it.

---

### `/api/auth/users/{id}/parties/`

- **command**: `account user-parties`  (shipped)
- **verdict**: publish
- **description**: The customers a salesperson is allowed to raise orders for.
  The direct answer to "why can't this manager find that party in the dropdown".
- **params**:
  - `id` — int, required, positional. User id from `account users`.
  - `category` — string, optional, query. Enum `OIL` | `BEVERAGES` | `MART`.
    Source: the app sends it —
    `getUserParties:(e,t)=>Y.get('/auth/users/'+e+'/parties/',
    {params:t?{category:t}:undefined})` (bundle @804790). **It is accepted and
    then silently ignored by the server — see traps.** Document it; do not
    advertise it as working.
- **response**: `object`.
  `{success, data:{user:{id,username,name}, parties:[…], card_codes:[string],
  total_assigned:int}}`.
  Party fields: `id` (assignment-row id), `card_code`, `card_name`, `state`
  (code string), `main_group` (name string), `category`, `assigned_at`.
  `card_codes` is a flat convenience array of the same codes and has always
  matched `len(parties)` and `total_assigned` in every call I made.
- **evidence**: **seven live GETs today, all HTTP 200**:
  - `62` (admin, self) → `total_assigned: 0`, `parties: []`, `card_codes: []`
  - `3` (manager `prince`) → 15 parties, 2815 bytes
  - `4` (manager `harpreet`) → 15 parties, 2538 bytes
  - `21` (billing `sumit`) → 30 parties, 5681 bytes
  - `3?category=OIL` → 15 · `3?category=BEVERAGES` → 15 · `3?category=MART` → 15
  - `21?category=BEVERAGES` → 30
- **traps**:
  - **The `category` filter does not work on this endpoint.** User 3's 15
    parties are all `category: OIL`; asking for `BEVERAGES` or `MART` returns
    the same 15 OIL rows. User 21 behaves identically (30 rows regardless).
    The sibling endpoint `auth/parties/{card_code}/products/` filters correctly
    with the same param name, so this is a **backend defect**, not a param-name
    mistake on my part. Confidence: high — four calls, two users, three enum
    values, zero variation. A CLI that exposes `--category` here would be
    lying; expose it documented-as-ignored or not at all.
  - **A 0-row 200 is a data fact.** Admin 62 has no assigned parties because
    admins don't need them, not because the endpoint is broken.
  - `main_group` and `state` come back as **plain strings** here (`"ROI"`,
    `"DL"`), unlike the `{id,name}` objects on user records.
  - Assigned parties are not clean sales accounts. User 21's 30 include
    `ORGC000030 TARANDEEP SINGH IMPREST JWPL0346` (a staff imprest vendor) and
    parties under `main_group: BRANCH` (intercompany). Counting "customers per
    salesperson" off this without excluding `STAFF` / `BRANCH` overstates it.
  - **Served 200 with no Authorization header** (checked). See the security
    finding.

---

### `/api/devices/register/`

- **command**: —
- **verdict**: exclude
- **exclusion reason**: write verb (POST). This is the client-side half of the
  device registry: on every authenticated session the SPA mints a
  `crypto.randomUUID()` into `localStorage.device_id` and POSTs its platform,
  app version, build number, browser and OS to this path (bundle @275822), also
  sending `X-Device-Id`, `X-App-Version`, `X-Build-Number`, `X-Platform` and
  `X-App-Type` on every request thereafter. **It is telemetry/session
  enrolment, not push-notification enrolment** — web push is a different path
  entirely (`orders/web-push/subscribe/`, also a write, also excluded). Never
  called by the CLI; a GET here was never attempted.

---

### `/api/ui-config/admin/labels/`

- **command**: `account ui-label-config`  (NEW)
- **verdict**: **publish the GET only**
- **exclusion reason** (for the other verb): this path serves **GET and POST**.
  The POST creates a label override and is excluded. Path+verb keying required.
- **description**: The editable definitions behind OMS's renameable field
  labels — the admin view, with the description and the active flag.
- **params**: none observed.
- **response**: `object`. `{success, message:"UI labels fetched.", data:[{id,
  field_key, display_name, description, is_active, created_at, updated_at}]}`.
  Exactly **one** row live today: `field_key: "price_list"` → `"Price List"`,
  *"Unified price list field label shown on web and mobile."*, `is_active:
  true`, created 2026-07-24, updated 2026-07-29.
- **evidence**: live GET → HTTP 200, 293 bytes. Returns **401**
  unauthenticated (checked).
- **traps**:
  - One row is the whole feature today. It looks like the beginning of a
    label-override system, not a populated one. Don't build a command that
    implies a rich config surface.
  - Sibling `/api/ui-config/admin/labels/{id}/` is PUT/DELETE only — excluded.

---

### `/api/ui-config/admin/labels/{id}/`

- **command**: —
- **verdict**: exclude
- **exclusion reason**: write verb (PUT and DELETE only; no GET on this path)

---

### `/api/ui-config/labels/`

- **command**: `account ui-labels`  (NEW)
- **verdict**: publish
- **description**: The resolved label map the app renders with — what the UI
  currently calls each renameable field. Useful when a user's screenshot says
  something your data dictionary doesn't.
- **params**: none observed.
- **response**: `object` — **a bare `{key: label}` map with no `success`
  envelope**: `{"price_list": "Price List"}` today, 27 bytes.
- **evidence**: live GET → HTTP 200. Returns **401** unauthenticated (checked).
  Found via the shape-C lens: the path lives in a module const
  (``Eo=`/ui-config/labels/` ``, bundle @276460), cached into
  `localStorage.ui_labels`, which is why a `/api/`-anchored harvest missed it.
- **traps**:
  - **This is the only endpoint in the domain with no `{success, data}`
    envelope.** A generic unwrapper that assumes `data` will return nothing.
  - It is the *active* subset of `ui-config/admin/labels/`. If a label is set
    `is_active: false` it disappears here but stays in the admin list.

---

## Domain summary

**What this domain is.** `account` is OMS's identity and reference layer. Two
halves. The first is **who can see what**: `profile` (this token), `users`
(everyone), `roles`, and the two scoping endpoints — `user-parties` (which
customers a salesperson owns) and `user-page-permissions` (which admin screens
they were granted). The second is the **master data every other domain's fields
point at**: `categories` (OIL / BEVERAGES / MART), `companies` (Jivo Wellness /
Jivo Mart), `main-groups` (the 27 sales channels), `states` (the 27 territories
JIVO sells into) and `party-products` (which SKUs a customer may be sold). Bolted
on are the **device registry** (`/api/admin/devices/*` — 253 browsers and phones,
which app build each is on) and the **UI label config** (`/api/ui-config/*`, one
row today). When any other OMS command comes back with 0 rows or a 403,
`account profile` is where the reason is.

**Verdicts: 15 published, 14 excluded, 29 total.**
Published (all GET): `devices`, `device`, `device-analytics`, `categories`,
`companies`, `main-groups`, `party-products`, `profile`, `roles`, `states`,
`users`, `user-page-permissions`, `user-parties`, `ui-label-config`,
`ui-labels`.
Excluded: `auth/users/create`, `auth/users/{id}` (PUT), `auth/assign-parties`,
`auth/assign-parties/bulk-upload`, `auth/remove-party`,
`auth/bulk-party/assign-products`, `auth/party-product/{bulk-add,remove,
update-rate}`, `devices/register`, `ui-config/admin/labels/{id}` (PUT/DELETE),
and the three auth mutators `auth/{login,logout,refresh}` — never published,
never probed.
**Two published paths carry an excluded verb on the same URL**:
`auth/users/{id}/page-permissions/` (GET published, **PUT excluded** — it grants
admin screens) and `ui-config/admin/labels/` (GET published, POST excluded).
Exclusions here must be keyed on **path + verb**, never path alone.

**Domain-wide traps.**
1. **Singular scope fields are legacy; read the plurals.** `main_group` /
   `state` / `category` disagree with `main_groups[0]` / `states[0]` on real
   rows today. Every scope answer comes from the plural.
2. **`category` (OIL/BEVERAGES/MART) is not `branch` (OIL/BEVERAGE).** Singular
   vs plural, and MART has no branch at all. Substituting one for the other is
   the single easiest way to get a wrong OMS number.
3. **Three response envelopes in one domain.** Bare arrays (`categories`,
   `companies`, `roles`, `states`, `mainGroup`), `{success,data}` wrappers
   (`profile`, `users`, `user-parties`, `party-products`, `devices`), and one
   raw map with no envelope at all (`ui-config/labels`). The shipped spec
   declared `type: object` for all of them and was wrong about five.
4. **Reference-list ids are sparse and alphabetically ordered.** `mainGroup` is
   missing id 27, `states` is missing 18/19/20, `users` has 18 gaps. Never
   iterate an id range; never assume id order matches list order.
5. **`variety` and `sub_group` are inverted from plain English** on
   `party-products` — `sub_group` is the oil variety, `variety` is the grade.
6. **`extra_pages: []` on an admin means "everything", not "nothing".**
7. **Devices ≠ users.** 253 devices, 54 users; one person holds up to 4.
   `admin/devices/` is also the only paginated endpoint here (25 by default,
   capped at 100) — an unpaged command shows a tenth of the fleet.

**Backend defects — reproductions included. These are the OMS team's.**

**① CRITICAL — `GET /api/auth/users/list/` requires no authentication and
returns every user's password hash.**

```
$ curl -s "https://oms.jivo.in/api/auth/users/list/"        # no Authorization header, no cookie
HTTP 200, 68594 bytes
rows: 54
rows with a pbkdf2 hash: 54
sample: {"id":2,"username":"preshit","email":"preshit@gmail.com",
         "phone":"9999999999","role":"admin","is_superuser":true,
         "password":"pbkdf2_sha256$1000000$…"}
```

- Reproduced **twice from two independent hosts** — this MacBook and the
  Hostinger VPS (different IP, different network, no credentials of any kind).
  Both returned 54 rows and 54 `pbkdf2_sha256$1000000$…` hashes.
- Not a cache artifact: the anonymous response contained two accounts (`Taran`
  id 71, `Keshav` id 72) created **after** my authenticated call, and the 52
  overlapping hashes were byte-identical across both.
- **Exposed by this one URL, to anybody on the internet**: 54 usernames, 48
  distinct email addresses, 41 distinct phone numbers, full role and scope
  metadata, `is_superuser` flags (naming `preshit` as the superuser), and 54
  offline-crackable password hashes.
- **The leaking field is `password`**, on the row objects under `data[]`.
- The same `password` field is on **`GET /api/auth/profile/`** (the caller's own
  hash — authenticated, 401 without a token) and in the **login response**
  (`data.user.password`, confirmed in the captured login body). One user
  serializer is shared by all three, which is the likely root cause: a
  `ModelSerializer` with no `exclude`/`extra_kwargs` for `password`.
- Two mitigations that do **not** make this safe: the hashes are
  `pbkdf2_sha256` at 1,000,000 iterations (strong, but weak passwords still
  fall), and OMS logins are also SAP-adjacent identities.
- **Second unauthenticated endpoint, same class**:
  `GET /api/auth/users/{id}/parties/` also returns **200 with no token**,
  disclosing which named customers each named salesperson owns. Verified on
  user 3.
- The reference lists `auth/{categories,companies,mainGroup,states,roles}` are
  likewise open (200 unauthenticated) — low sensitivity, but the same missing
  permission class. `profile`, `page-permissions`, `party-products`,
  `admin/devices*` and `ui-config/*` all correctly return 401.
- Recommended to the OMS team, in order: drop `password` from the user
  serializer everywhere (login, profile, list); put `users/list` and
  `users/{id}/parties` behind authentication + an admin check; then **force a
  password reset for all 54 accounts**, because the hashes have been publicly
  reachable and there is no way to know for how long.

**② `category` is silently ignored on `GET /api/auth/users/{id}/parties/`.**
```
users/3/parties/                  -> total_assigned 15, categories {OIL}
users/3/parties/?category=OIL     -> total_assigned 15, categories {OIL}
users/3/parties/?category=BEVERAGES -> total_assigned 15, categories {OIL}   # expected 0
users/3/parties/?category=MART      -> total_assigned 15, categories {OIL}   # expected 0
users/21/parties/?category=BEVERAGES -> total_assigned 30, categories {OIL}  # expected 0
```
The app sends this param, and the sibling `auth/parties/{cc}/products/` honours
the identical param correctly (`?category=OIL` → 1, `?category=BEVERAGES` → 12,
none → 13). So the filter is dropped on the server for the users route only.

**③ `main_group` master has a duplicate.** `CALL CENTER` (id 8) and
`CALL CENTRE` (id 28) are the same channel. Any channel-mix report splits
tele-sales across two rows. Master-data fix, one merge.

**Durable JIVO business truths worth recording as corrections.**
- **OMS's `category` (OIL / BEVERAGES / MART) is the SAP-company selector, and
  it does not equal OMS's `branch` (OIL / BEVERAGE).** MART exists as a category
  and has no branch; OMS's HANA layer reaches Oil and Beverages only. Extends
  API-FACTS §2 and echoes C-0008 for ecom: each JIVO app sees a different slice
  of the three SAP companies, never all three.
- **On OMS party-product rows, `sub_group` is the oil variety and `variety` is
  the grade within it** — `variety:"EXTRA LIGHT", sub_group:"OLIVE"`. They
  mirror SAP `OITM.U_Sub_Group` / `U_Variety` exactly, so the existing SAP rules
  (C-0003, the `sap-olive-grade-field` note) apply verbatim to OMS. Anyone
  aggregating "olive sales" off `variety` gets the wrong answer.
- **`main_group` values `BRANCH`, `STAFF`, `STAFF CUSTOMER`, `FIXED ASSETS`,
  `COMPANY UNIT` and `REFERENCE` are not sales channels** and must be excluded
  from channel-mix and per-salesperson customer counts — the same exclusion
  discipline as C-0005's 23 intercompany card codes.

**What I could not verify.**
- **`basic_rate`'s real meaning.** I established what writes it and what reads
  it, but the observed values (mostly 0.0; ₹2.00 on a 15 LTR tin) are not
  consistent with a straight selling price. I did **not** cross-check a single
  row against `hana/item-price/`. Treat as a configured field, not a price.
- **Whether `/api/admin/devices/*` requires the `admin` role or the
  `Device_Management` page grant.** I only hold an admin token; I could not test
  a manager's. It is 401 unauthenticated, which is all I proved.
- **The 404 shape of `/api/admin/devices/{id}/`** — probing it needs an id that
  does not exist, which would be an invented value (rule 2). Not attempted.
- **Whether `/api/auth/users/list/` accepts any query parameter.** The app sends
  none; I invented none. Unproven resolves to excluded.
- **How long `users/list` has been unauthenticated.** I proved it is open now.
  I have no evidence about when it became open or whether it has been accessed.
