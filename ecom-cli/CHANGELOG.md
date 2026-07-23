---
title: "Changelog"
created: 2026-07-19
updated: 2026-07-19
project: jivogpt
type: changelog
tags: [jivogpt, ecom-cli, changelog]
---

# Changelog

This file is maintained by printing-press-library release automation. Do not hand-edit release sections in normal PRs.

## 2026-07-19 — JivoGPT import & expansion (unreleased)

- Imported into the JivoGPT monorepo at `~/jivogpt/CLI/ecom-cli` as read-only Data Source #1.
- Expanded the read surface from **44 → 138** GET endpoints via `cli-printing-press generate`
  from an amended `spec.yaml`. New resource groups: `reports`, `sap` (SAP HANA distributor/
  inventory/invoice reads), `shipment` (Amazon Shipment Planner — access-gated, 403 without
  the permission), `upload`, `uploads`, `chatbot`; extended `dashboard` (realise-*, state-sales
  drill-downs, lead-time, expiry-alert POs), `notifications`, and `platform` (ads/brandfund/
  landing-rate families, cross-platform summaries). MCP tool count 44 → 138.
- **RULE 0:** removed the generic `import` write command (the only POST-to-source path).
  See `.printing-press-patches/0001-remove-import-write-command.md`.

Linked: [[docs/ecom/ECOM_MAP|ECOM_MAP]] · [[docs/READ_ONLY_LAW|READ_ONLY_LAW]] · [[/README|JivoGPT]]
