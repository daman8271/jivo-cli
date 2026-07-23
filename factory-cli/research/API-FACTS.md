---
title: Jivo Factory API Facts
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: reference
tags: [jivogpt, factory, api, research]
---

# jivo-factory — API facts (for printing-press)

> **Provenance — imported 2026-07-19; source snapshot 2026-06-30.** This note came from the JIVO_MART-only `daman8271/jivo-factory-intel` baseline. For the current three-company study and the live-verified 2026-07-19 state, use [[docs/factory/FACTORY_MAP|FACTORY_MAP]] and [[CLI/factory-cli/README|the current CLI guide]].

- **Name:** jivo-factory  (Jivo "JI" factory management system; frontend https://ji.jivo.in)
- **Base URL:** https://factory.jivo.in/api/v1
- **Backend:** Django REST Framework + SimpleJWT
- **Health check:** GET /accounts/me/  (200 when authed)

## Auth (bearer JWT)
- Login: `POST /accounts/login/`  body `{"email","password"}` -> `{"access","refresh","token":{access_expires_in:90000, refresh_expires_in:604800},"user":{...}}`
- Refresh: `POST /accounts/token/refresh/` body `{"refresh"}` -> `{"access"}`
- Header: `Authorization: Bearer <access>`
- access ~25h, refresh ~7d. Tokens stored 0600 at ~/.config/jivo-factory/.
- Env for login: JIVO_FACTORY_EMAIL / JIVO_FACTORY_PASSWORD (or --password-stdin). NEVER store the password.

## Company scope (REQUIRED on most endpoints)
- Header: `Company-Code: <CODE>`  -> missing => 403 `{"detail":"Company-Code header is missing."}`
- Companies: JIVO_MART (id 2, "Jivo Mart" = **Jivamart, our target**), JIVO_OIL (id 1), JIVO_BEVERAGES (id 3)
- Default company flag: configurable; CLI default = JIVO_MART.

## Read-only
- This CLI is READ-ONLY. Only GET endpoints. No POST/PUT/PATCH/DELETE commands except the internal login/refresh.

## Domains (35 Django apps / ~160 models)  — see model-inventory.txt
production_execution, gate_core, maintenance, barcode, quality_control, wms, person_gatein,
grpo, dispatch_plans, notifications, labour_count, raw_material_gatein, fixed_asset_gatein,
docking_admin, daily_needs_gatein, warehouse, vehicle_management, company, sales_planning_requirement,
maintenance_gatein, construction_gatein, accounts, driver_management, stock_dashboard,
ai_assistant, sap_plan_dashboard, non_moving_rm, inventory_age, weighment, security_checks.

## Endpoint inventory
- research/endpoints.txt = 210 candidate collection endpoints (trailing-slash GET).

Linked: [[docs/factory/FACTORY_MAP|FACTORY_MAP]] · [[docs/FACTORY_CLI_PLAN|FACTORY_CLI_PLAN]] · [[docs/READ_ONLY_LAW|READ_ONLY_LAW]]
