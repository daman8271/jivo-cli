---
title: "API Inventory"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: reference
tags: [jivogpt, exim, api]
---

# API Inventory

Base URL: `https://eximbe.jivo.in` · Auth: `Authorization: Bearer <access>`

## Read endpoints (safe GET — used by the CLI)

| Method | Path | Params | Category | Used by | Doc |
|---|---|---|---|---|---|
| `GET` | `/account/user/{id}/` | {id} | account | users | [[endpoints/account_user_id\|doc]] |
| `GET` | `/account/users/` | — | account | users | [[endpoints/account_users\|doc]] |
| `GET` | `/daily-price/db-list/` | date | daily-price | daily-price | [[endpoints/daily-price_db-list\|doc]] |
| `GET` | `/daily-price/highest-lowest/` | end_date, start_date | daily-price | daily-price | [[endpoints/daily-price_highest-lowest\|doc]] |
| `GET` | `/daily-price/range/` | from_date, to_date | daily-price | daily-price | [[endpoints/daily-price_range\|doc]] |
| `GET` | `/daily-price/trends/` | end_date, start_date | daily-price | daily-price, dashboard | [[endpoints/daily-price_trends\|doc]] |
| `GET` | `/dc/` | year | dc | domestic-2627, domestic-contracts | [[endpoints/dc\|doc]] |
| `GET` | `/dc/` | year | dc | domestic-2627 | [[endpoints/get_dc\|doc]] |
| `GET` | `/dc/dropdown/` | — | dc | domestic-contracts | [[endpoints/dc_dropdown\|doc]] |
| `GET` | `/director-inventorty/` | — | director-inventorty | director-dashboard | [[endpoints/director-inventorty\|doc]] |
| `GET` | `/exim-rates/fetch/` | — | exim-rates | exim-rates | [[endpoints/exim-rates_fetch\|doc]] |
| `GET` | `/item/fg/{item_code}/` | {item_code} | item | sync-finished-goods | [[endpoints/item_fg_item_code\|doc]] |
| `GET` | `/item/rm/{item_code}/` | {item_code} | item | sync-raw-material | [[endpoints/item_rm_item_code\|doc]] |
| `GET` | `/items/fg/` | — | items | sync-finished-goods | [[endpoints/items_fg\|doc]] |
| `GET` | `/items/rm/` | — | items | domestic-2627, sync-raw-material | [[endpoints/items_rm\|doc]] |
| `GET` | `/items/rm/summary/` | — | items | sync-raw-material | [[endpoints/items_rm_summary\|doc]] |
| `GET` | `/items/rm/varieties/` | — | items | sync-raw-material | [[endpoints/items_rm_varieties\|doc]] |
| `GET` | `/jivo-rate/range/` | from_date, to_date | jivo-rate | jivo-rates | [[endpoints/jivo-rate_range\|doc]] |
| `GET` | `/license/advance-license-export-lines/` | — | license | advance-license | [[endpoints/license_advance-license-export-lines\|doc]] |
| `GET` | `/license/advance-license-headers/` | — | license | advance-license | [[endpoints/license_advance-license-headers\|doc]] |
| `GET` | `/license/advance-license-import-lines/` | — | license | advance-license | [[endpoints/license_advance-license-import-lines\|doc]] |
| `GET` | `/license/advance-license-import-lines/dropdown/` | license_no | license | advance-license | [[endpoints/license_advance-license-import-lines_dropdown\|doc]] |
| `GET` | `/license/dfia-license-export-lines/dropdown/` | file_no | license | — | [[endpoints/license_dfia-license-export-lines_dropdown\|doc]] |
| `GET` | `/license/dfia-license-header/list/` | — | license | dfia-license | [[endpoints/license_dfia-license-header_list\|doc]] |
| `GET` | `/parties/` | — | parties | domestic-2627, stock-status, sync-vendor-data | [[endpoints/parties\|doc]] |
| `GET` | `/party/{card_code}/` | {card_code} | party | stock-status | [[endpoints/party_card_code\|doc]] |
| `GET` | `/rates/basic-rate/` | end_date, start_date | rates | our-rates | [[endpoints/rates_basic-rate\|doc]] |
| `GET` | `/rates/commodity/` | — | rates | market-rates, our-rates | [[endpoints/rates_commodity\|doc]] |
| `GET` | `/rates/market-rate/get/` | end_date, start_date | rates | market-rates, our-rates | [[endpoints/rates_market-rate_get\|doc]] |
| `GET` | `/rates/market-rate/latest/` | — | rates | market-rates, our-rates | [[endpoints/rates_market-rate_latest\|doc]] |
| `GET` | `/rates/packing/` | — | rates | our-rates | [[endpoints/rates_packing\|doc]] |
| `GET` | `/rates/rate-table/latest/` | — | rates | our-rates | [[endpoints/rates_rate-table_latest\|doc]] |
| `GET` | `/sap-sync/balance-sheet/` | — | sap-sync | dashboard, exim-account | [[endpoints/sap-sync_balance-sheet\|doc]] |
| `GET` | `/sap-sync/custa/balance-sheet/` | — | sap-sync | customer-outstanding | [[endpoints/sap-sync_custa_balance-sheet\|doc]] |
| `GET` | `/sap-sync/customer-aging-balance/` | — | sap-sync | customer-aging | [[endpoints/sap-sync_customer-aging-balance\|doc]] |
| `GET` | `/sap-sync/customer/balance/` | startDate, endDate | sap-sync | — | [[endpoints/sap_sync_customer_balance\|doc]] |
| `GET` | `/sap-sync/customer/ledger/` | cardCode | sap-sync | — | [[endpoints/sap_sync_customer_ledger\|doc]] |
| `GET` | `/sap-sync/finished-inventory/` | — | sap-sync | warehouse-inventory | [[endpoints/sap-sync_finished-inventory\|doc]] |
| `GET` | `/sap-sync/inventory/` | — | sap-sync | warehouse-inventory | [[endpoints/sap-sync_inventory\|doc]] |
| `GET` | `/sap-sync/monthly-planning/` | monthId | sap-sync | planning | [[endpoints/sap-sync_monthly-planning\|doc]] |
| `GET` | `/sap-sync/open-ap/` | — | sap-sync | open-aps | [[endpoints/sap-sync_open-ap\|doc]] |
| `GET` | `/sap-sync/open-ar/` | — | sap-sync | open-ars | [[endpoints/sap-sync_open-ar\|doc]] |
| `GET` | `/sap-sync/open-pos/` | — | sap-sync | open-pos | [[endpoints/sap-sync_open-pos\|doc]] |
| `GET` | `/sap-sync/planned-months/` | — | sap-sync | planning | [[endpoints/sap-sync_planned-months\|doc]] |
| `GET` | `/sap-sync/vendor/balance-sheet/` | — | sap-sync | vendor-outstanding | [[endpoints/sap-sync_vendor_balance-sheet\|doc]] |
| `GET` | `/sap-sync/vendor/ledger/` | cardCode | sap-sync | — | [[endpoints/sap_sync_vendor_ledger\|doc]] |
| `GET` | `/stock-status/` | status | stock-status | contracts, dashboard, stock-status | [[endpoints/stock-status\|doc]] |
| `GET` | `/stock-status/contractual-history/` | — | stock-status | contractual-history | [[endpoints/stock-status_contractual-history\|doc]] |
| `GET` | `/stock-status/debit-entries/` | — | stock-status | shortage-report | [[endpoints/stock-status_debit-entries\|doc]] |
| `GET` | `/stock-status/debit-insights/` | — | stock-status | shortage-report | [[endpoints/stock-status_debit-insights\|doc]] |
| `GET` | `/stock-status/stock-dashboard/` | rounding | stock-status | stock-dashboard | [[endpoints/stock-status_stock-dashboard\|doc]] |
| `GET` | `/stock-status/stock-insights/` | — | stock-status | stock-status | [[endpoints/stock-status_stock-insights\|doc]] |
| `GET` | `/stock-status/stock-logs/` | — | stock-status | stock-updation-logs | [[endpoints/stock-status_stock-logs\|doc]] |
| `GET` | `/stock-status/stock-summary/` | — | stock-status | — | [[endpoints/stock-status_stock-summary\|doc]] |
| `GET` | `/stock-status/vehicle-report/` | status | stock-status | director-dashboard, vehicle-report | [[endpoints/stock-status_vehicle-report\|doc]] |
| `GET` | `/stock-status/{id}/` | {id} | stock-status | stock-status | [[endpoints/stock-status_id\|doc]] |
| `GET` | `/sync_logs/` | — | sync_logs | sync-logs | [[endpoints/sync_logs\|doc]] |
| `GET` | `/tank/` | — | tank | tank-data, tank-monitoring | [[endpoints/tank\|doc]] |
| `GET` | `/tank/capacity-insights/` | — | tank | dashboard | [[endpoints/tank_capacity-insights\|doc]] |
| `GET` | `/tank/in-tank-items/` | — | tank | in-tank-breakdown | [[endpoints/tank_in-tank-items\|doc]] |
| `GET` | `/tank/item-wise-average/` | item_code | tank | in-tank-breakdown, tank-monitoring | [[endpoints/tank_item-wise-average\|doc]] |
| `GET` | `/tank/item-wise-summary/` | — | tank | stock-dashboard, tank-monitoring | [[endpoints/tank_item-wise-summary\|doc]] |
| `GET` | `/tank/items/` | — | tank | in-tank-breakdown, stock-status, tank-data | [[endpoints/tank_items\|doc]] |
| `GET` | `/tank/log/` | — | tank | tank-logs | [[endpoints/tank_log\|doc]] |
| `GET` | `/tank/tank-summary/` | — | tank | tank-data, tank-monitoring | [[endpoints/tank_tank-summary\|doc]] |
| `GET` | `/tank/{tank_code}/` | {tank_code} | tank | tank-data | [[endpoints/tank_tank_code\|doc]] |

## Write / sync endpoints (documented, NOT wired into CLI v1)

| Method | Path | Purpose | Doc |
|---|---|---|---|
| `POST` | `/account/login/` | Authenticate; returns access+refresh+permissions. | [[endpoints/account_login\|doc]] |
| `POST` | `/account/login/refresh/` | Exchange refresh token for a new access token. | [[endpoints/account_login_refresh\|doc]] |
| `POST` | `/account/logout/` | Invalidate the refresh token. | [[endpoints/account_logout\|doc]] |
| `POST` | `/account/register/` | Create a new user. | [[endpoints/account_register\|doc]] |
| `POST` | `/ai/chat/` | AI assistant chat over EXIM data. | [[endpoints/ai_chat\|doc]] |
| `GET` | `/daily-price/fetch/` | Fetch/refresh the latest daily commodity prices; returns status + preview. [RECLASSIFIED: pull-and-store / sync-trigger — writes data, excluded from read CLI] | [[endpoints/daily-price_fetch\|doc]] |
| `POST` | `/dc/contract/create/` | Create a domestic contract. | [[endpoints/dc_contract_create\|doc]] |
| `POST` | `/dc/freight/create/{id}/` | Add freight to a contract. | [[endpoints/dc_freight_create_id\|doc]] |
| `POST` | `/dc/loading/create/{id}/` | Add loading to a contract. | [[endpoints/dc_loading_create_id\|doc]] |
| `DELETE` | `/item/fg/{item_code}/` | Delete an FG item. | [[endpoints/delete_item_fg_item_code\|doc]] |
| `DELETE` | `/item/rm/{item_code}/` | Delete an RM item. | [[endpoints/delete_item_rm_item_code\|doc]] |
| `GET` | `/jivo-rate/fetch/` | Fetch/refresh latest JIVO pack rates; returns status + preview. [RECLASSIFIED: pull-and-store / sync-trigger — writes data, excluded from read CLI] | [[endpoints/jivo-rate_fetch\|doc]] |
| `POST` | `/license/advance-license-export-lines/create/` | Add export (SB) line. | [[endpoints/license_advance-license-export-lines_create\|doc]] |
| `POST` | `/license/advance-license-headers/` | Create advance-license header. | [[endpoints/post_license_advance-license-headers\|doc]] |
| `POST` | `/license/advance-license-import-lines/` | Add import (BOE) line. | [[endpoints/post_license_advance-license-import-lines\|doc]] |
| `POST` | `/license/dfia-license-header/create/` | Create DFIA header. | [[endpoints/license_dfia-license-header_create\|doc]] |
| `DELETE` | `/party/{card_code}/` | Delete a party. | [[endpoints/delete_party_card_code\|doc]] |
| `POST` | `/sap_sync/fg/items/` | Trigger SAP finished-goods master sync. | [[endpoints/sap_sync_fg_items\|doc]] |
| `GET` | `/sap_sync/open-grpos/` | Open GRPO sync read; may refresh SAP and is excluded from tooling. | [[endpoints/sap_sync_open-grpos\|doc]] |
| `POST` | `/sap_sync/party/{code}/` | Trigger SAP vendor/party sync. | [[endpoints/sap_sync_party_code\|doc]] |
| `POST` | `/sap_sync/rm/items/` | Trigger SAP raw-material master sync. | [[endpoints/sap_sync_rm_items\|doc]] |
| `POST` | `/stock-status/` | Create a stock-status record. | [[endpoints/post_stock-status\|doc]] |
| `POST` | `/stock-status/arrive-batch/` | Mark a batch arrived. | [[endpoints/stock-status_arrive-batch\|doc]] |
| `POST` | `/stock-status/dashboard-order/{id}/` | Reorder dashboard items. | [[endpoints/stock-status_dashboard-order_id\|doc]] |
| `POST` | `/stock-status/dispatch/` | Dispatch stock. | [[endpoints/stock-status_dispatch\|doc]] |
| `POST` | `/stock-status/move/` | Move stock between statuses/locations. | [[endpoints/stock-status_move\|doc]] |
| `POST` | `/stock-status/opening-stock/` | Set opening stock. | [[endpoints/stock-status_opening-stock\|doc]] |
| `PATCH` | `/stock-status/{id}/` | Update / soft-delete a stock row. | [[endpoints/patch_stock-status_id\|doc]] |
| `POST` | `/tank/` | Create a tank. | [[endpoints/post_tank\|doc]] |
| `POST` | `/tank/item/` | Create a tank item. | [[endpoints/tank_item\|doc]] |
| `PATCH` | `/tank/item/update-color/{id}/` | Update a tank item colour. | [[endpoints/tank_item_update-color_id\|doc]] |
| `POST` | `/tank/log/` | Create a tank inflow/outflow log. | [[endpoints/post_tank_log\|doc]] |
| `PATCH` | `/tank/update-capacity/{id}/` | Update tank capacity. | [[endpoints/tank_update-capacity_id\|doc]] |
| `PATCH` | `/tank/{tank_code}/` | Update a tank. | [[endpoints/patch_tank_tank_code\|doc]] |

Linked: [[CLI/exim/INDEX|INDEX]] · [[docs/EXIM_MAP|EXIM_MAP]] · [[docs/READ_ONLY_LAW|READ_ONLY_LAW]]
