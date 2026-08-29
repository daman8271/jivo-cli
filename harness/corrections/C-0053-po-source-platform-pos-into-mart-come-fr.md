---
id: C-0053
date: 2026-08-29
author: Daman
area: sales
severity: high
status: active
supersedes: C-0052
tags: [orders]
---

# PO source: platform POs into Mart come from ecom.jivo.in, MT and GT from OMS

## Wrong
Read 'Mart POs' as everything belonging to the Jivo Mart company. Wrong scope - OMS also carries Jivo Mart as a company (id 2), so company is not the thing that decides where a PO lives.

## Right
Daman's clarification 2026-08-29: it is the CHANNEL the PO arrives on, not the company. POs that reach Jivo Mart from the online platforms - quick-commerce (Blinkit, Zepto, Swiggy Instamart, BigBasket, Citymall, JioMart, Zomato) plus Amazon and Flipkart - come through ecom.jivo.in. MT (Modern Trade, organised retail chains) and GT (General Trade, kirana/distributor) POs come through OMS at oms.jivo.in. A Mart order arriving on an MT or GT lane is an OMS order, not an ecom one.

## Evidence
Ruling by Daman 2026-08-29, clarifying C-0052. Verified live the same day: ecom.jivo.in covers Amazon, Blinkit, Zepto, Swiggy, BigBasket, Flipkart, Citymall, JioMart, Zomato with PO commands 'platform pos', 'dashboard primary-po-litres', 'reports amazon-po'. OMS 'account companies' returns Jivo Mart (id 2) AND Jivo Wellness, and 'account main-groups' returns GT and MT - which is why company cannot be the discriminator.

## Rule
<!-- ONE line, imperative. This is the only part injected into every session.
     Keep it under ~200 chars. Write it so it is actionable without context. -->
POs by ARRIVAL CHANNEL, not company: q-commerce + Amazon + Flipkart into Mart = ecom.jivo.in (ecom CLI); MT and GT = OMS. Jivo Mart exists in both - the channel decides, never the company.
