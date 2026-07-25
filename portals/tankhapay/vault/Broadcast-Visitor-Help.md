---
tags: [tankhapay, section, broadcast-visitor-help]
---
# Broadcast, Visitor Management & Help/Support

Three small employer utilities bundled together: **Broadcast** — push-notification campaigns and
targeted alerts to employees (`NotificationApi/*`); **Visitor management** — the front-desk
visitor/visiting-card log (`visitor/*`); and **Help & Support** — the employer's helpdesk tickets and
their trails (`TpHelpAndSupportApi/*`). The reads list campaigns/audiences, visitors and tickets; the
writes create/notify/check-in/OTP. AES-encrypted POST ([[Encryption-Scheme]]); one JWT
([[Auth-and-Access]]). 12 reads, 11 writes.

## Read endpoints (in-scope for the CLI)

| Command (`broadcast …`) | Backend | Request payload keys | Returns |
|---|---|---|---|
| `campaigns-details` | business | account ctx | push-notification campaigns |
| `unique-campaign-details` | business | `customerAccountId`, `campaignId` | one campaign's detail |
| `target-audience` | business | `customerAccountId`, `campaignId` | a campaign's target audience |
| `audience-list` | business | account ctx | saved audiences |
| `tp-alerts-by-date-filter` | business | `actionType`, `emp_id`, `alertUserType`, `productTypeId`, `fromDate` | alerts by date |
| `tickets` | business | `fromDate`, `toDate`, `ticketStatus`, `orgUnitId` | help/support tickets |
| `all-queries-tickets` | business | `action`, `fromDate`, `toDate` | all queries + tickets |
| `ticket-trail` | business | `ticketId`, `productTypeId`, `customerAccountId` | one ticket's conversation trail |
| `visitor-list` | business | `p_fromdt`, `p_todt`, `p_keyword`, `p_pageindex`, `p_pagesize`, `p_accountid` | visitor log (paged) |
| `visitor-summary` | business | `p_fromdt`, `p_todt`, `p_keyword`, `p_pageindex`, `p_pagesize`, `p_accountid` | visitor counts summary |
| `visitor-card-details` | business | `p_fromdt`, `p_todt`, `p_keyword`, `p_pageindex`, `p_pagesize`, `p_accountid` | visiting-card detail rows |
| `visiting-card-list` | business | `p_action`, `p_keyword`, `p_accountid` | visiting-card list |

### Account context — note the `p_` convention
The **visitor** reads use a distinct **`p_`-prefixed** parameter convention (`p_accountid` = **2719**,
`p_fromdt`/`p_todt` = `DD/MM/YYYY`, `p_pageindex`/`p_pagesize` for paging, `p_keyword` search). The
CLI's auto-context injects the plain `accountId`; supply the `p_*` params explicitly with `--set`
(e.g. `--set p_accountid=@accountId --set p_pageindex=0 --set p_pagesize=50`). Notification/ticket
reads use the normal `customerAccountId`/`productTypeId`.

## Write endpoints (documented, OUT OF SCOPE)

```
notifications : NotificationApi/{AddEditPushNotifications, ChangeApprovalStatusForCampaign}
help/support  : TpHelpAndSupportApi/{CreateTicketTrail, UpdateTicketstatus}
visitor       : visitor/{saveVisitor, Update_visitor, save_visitor_card, check_in_out_visitor,
    update_blacklist_visitor, send_visitor_otp, verify_visitor_otp}
```
UNKNOWN (not wired): `TpHelpAndSupportApi/readTicketInternalDepartment`.

## CLI command mapping

```
tankhapay-portal broadcast tickets --set fromDate=… --set toDate=… --set ticketStatus=Open
tankhapay-portal broadcast ticket-trail --set ticketId=…
tankhapay-portal broadcast visitor-list --set p_accountid=@accountId --set p_fromdt=01/07/2026 --set p_todt=31/07/2026 --set p_pageindex=0 --set p_pagesize=50
tankhapay-portal broadcast campaigns-details
```

---
[[00-TankhaPay-Atlas]] · [[Encryption-Scheme]] · [[Auth-and-Access]] · [[Backends-and-Environment]] · [[Read-Only-Guardrails]] · [[Proven-Login-Recipe]] · [[Pages-and-Routes]]

Siblings: [[Dashboard]] · [[Employee-Management]] · [[Attendance]] · [[Leave-Management]] · [[Payouts]] · [[Approvals]] · [[Accounts-Taxes]] · [[Reports]] · [[Recruit-ATS]] · [[Masters-Config]] · [[Org-User-Management]] · [[Contract-Labour-Inventory]] · [[Training-Performance]]
