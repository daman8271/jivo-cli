---
id: C-0031
date: 2026-08-25
author: Daman
area: accounts
severity: high
status: active
supersedes: 
tags: [login]
---

# 'Fail to NONE-SSO login from SLD' is a WRONG PASSWORD

## Wrong
Read SAP's 'Fail to NONE-SSO login from SLD' as a licence/company-assignment block — concluded USER05 was 'Oil-only' and told the operator an SAP admin had to assign the user to the Beverages company before any Beverages entry could be made in their name.

## Right
That message is what the Service Layer returns for a BAD PASSWORD against that company DB. SAP passwords at JIVO are PER COMPANY DB for the same user code. USER05 with the Oil password failed on Beverages with this exact error; USER05 with the Beverages password (supplied by Daman) logged in immediately and created payment draft DocEntry 296 there. The user was never unassigned.

## Evidence
sapb1 doctor, host 138.252.101.222:50000, same user5.env credentials: USER05 -> JIVO_OIL_HANADB = connected; USER05 + Oil pw -> JIVO_BEVERAGES_HANADB = 'Fail to NONE-SSO login from SLD'; USER05 + Beverages pw '1234' -> JIVO_BEVERAGES_HANADB = connected, then created PaymentDrafts DocEntry 296 / DocNum 826468050.

## Rule
<!-- ONE line, imperative. This is the only part injected into every session.
     Keep it under ~200 chars. Write it so it is actionable without context. -->
'Fail to NONE-SSO login from SLD' means the password is wrong FOR THAT COMPANY DB, not that the user lacks a licence — SAP passwords differ per company; ask for that company's password before declaring a user blocked.
