---
id: C-0012
date: 2026-08-06
author: Daman
area: all
severity: high
status: active
supersedes: 
tags: [oms, sap, reporting]
---

# Source reports from SAP, never from OMS (OMS has no Mart)

## Wrong
Built report figures from OMS (its /api/hana/* endpoints), treating OMS as an equivalent source of business data because it mirrors SAP. Group totals produced this way looked complete and were not.

## Right
SAP is the source of truth for every report. OMS only mirrors SAP for Oil and Beverages — there is no MART branch at all — so any group-level or company-spanning figure sourced from OMS silently omits the whole of Mart. The same applies to the other app CLIs (ecom, factory): they are partial mirrors of SAP, useful for their own operational data, never authoritative for a financial or sales report. Pull reports with sapb1 (Service Layer) or hana-sql (direct SQL), and name the company.

## Evidence
Measured live 2026-08-06 from JIVO201. SAP customers (sapb1 query BusinessPartners --count --filter "CardType eq 'cCustomer'"): Oil 1172, Mart 939, Bev 1250. SAP non-cancelled invoices (hana-sql, OINV CANCELED='N'): Oil 30114, Mart 24694, Bev 5152. OMS /api/hana/* rejects any branch but OIL|BEVERAGE (400 'branch is required and must be one of: OIL, BEVERAGE' — see C-0010), and OMS branch=OIL all-customers returns 1172, identical to SAP Oil, confirming it is a mirror. Therefore Mart's 939 customers and 24694 invoices are wholly invisible to any OMS-sourced report.

## Rule
<!-- ONE line, imperative. This is the only part injected into every session.
     Keep it under ~200 chars. Write it so it is actionable without context. -->
Source every report from SAP (sapb1/hana-sql), never OMS/ecom/factory — they mirror SAP only partially: OMS has no MART branch, so an OMS-sourced report silently drops all Mart business.
