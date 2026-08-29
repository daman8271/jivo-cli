---
id: C-0052
date: 2026-08-29
author: Daman
area: sales
severity: high
status: active
supersedes: 
tags: [orders]
---

# PO source: Mart POs come from ecom.jivo.in, MT and GT from OMS

## Wrong
Treated SAP as the place to look for purchase orders regardless of channel, and had no rule for which upstream system owns a PO before it reaches SAP.

## Right
Daman's ruling 2026-08-29: POs are sourced per channel. Mart POs come through ecom.jivo.in (the ecom CLI - platform pos, dashboard primary-po-litres, reports amazon-po; covers Amazon, Blinkit, Zepto, Swiggy, BigBasket, Flipkart, Citymall, JioMart, Zomato). MT (Modern Trade) and GT (General Trade) POs come through OMS (oms.jivo.in). Go to the owning system for the PO; do not assume SAP or one single source.

## Evidence
Ruling by Daman 2026-08-29. Both systems verified live the same day: 'ecom doctor' = API reachable, credentials valid, base_url https://ecom.jivo.in, with PO commands 'platform pos', 'dashboard primary-po-litres', 'reports amazon-po' (10,247 rows). 'oms-pp-cli account main-groups' returns GT and MT among 27 channels, and 'account companies' returns Jivo Mart (id 2) and Jivo Wellness, base_url https://oms.jivo.in.

## Rule
<!-- ONE line, imperative. This is the only part injected into every session.
     Keep it under ~200 chars. Write it so it is actionable without context. -->
POs by channel: Mart = ecom.jivo.in (ecom CLI); MT and GT = OMS (oms.jivo.in). Go to the owning system for a PO, never assume one source.
