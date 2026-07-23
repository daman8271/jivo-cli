---
title: JivoGPT CLI Hub
created: 2026-07-19
updated: 2026-07-20
project: jivogpt
type: hub
tags: [jivogpt, cli, connectors, read-only]
---

# JivoGPT CLI Hub

Every JivoGPT command-line connector now lives under this single `CLI/` folder. Each workspace remains complete—source, executable, tests, specs, operator docs, and local safeguards moved together. Factory and jivo-scrape also consume one released [[CLI/product-identity/README|Product Identity Bridge]] so the same product is resolved from exact source identities rather than names.

> ⛔ All six connectors are governed by [[docs/READ_ONLY_LAW|READ_ONLY_LAW]]. They may read production data, but they must never create, update, delete, dispatch, sync, or otherwise mutate JIVO business data.

## CLI directory

| CLI | Workspace | Runtime and surface | Primary docs |
|---|---|---|---|
| **Ecom** | `CLI/ecom-cli/` | Go / Printing Press · 138 GET commands | [[CLI/ecom-cli/README|Guide]] · [[docs/ecom/ECOM_MAP|Map]] |
| **EXIM** | `CLI/exim/` | Go / Printing Press plus guarded workspace wrapper · 65 safe GET commands | [[CLI/exim/README|Guide]] · [[docs/EXIM_MAP|Map]] |
| **Factory** | `CLI/factory-cli/` | Go / Printing Press · 183 API GET commands plus local exact-product commands across Mart, Oil, and Beverages | [[CLI/factory-cli/README|Guide]] · [[docs/factory/FACTORY_MAP|Map]] |
| **OMS** | `CLI/oms-cli/` | Go / Printing Press · 73 specified GET entries, 72 registered endpoint commands | [[CLI/oms-cli/README|Guide]] · [[docs/oms/OMS_MAP|Map]] |
| **JSAP** | `CLI/jsap-cli/` | Python · 146 read commands across 13 groups | [[CLI/jsap-cli/README|Guide]] · [[docs/jsap/JSAP_MAP|Map]] |
| **jivo-scrape** (ex jivo-desk, renamed 2026-07-19) | `CLI/jivo-scraping-cli/` | Python · 14 read commands — 8 operational + exact `product` group + 5 archive commands (`history`/`asof`/`runs`/`vault`/`reports`) over any ecom-intel checkout | [[CLI/jivo-scraping-cli/README|Guide]] · [[docs/SCRAPING_CLI|Map]] |

## Shared product identity

`CLI/product-identity/v1/product-identity-map.json` is the single released bridge used by both Factory and jivo-scrape. Its authoritative keys are `platform + listing_id` on the scraper side and `company + SAP schema + item_code` on the Factory side. The current release accounts for 333 distinct listings, 334 price-group membership rows, and 1,906 observed Factory FG/FB/SL items. Both consumers require the pinned detached `release-attestation.json` and recompute all six evidence-file hashes. Run the independent verifier before consuming a refreshed release:

```bash
python3 CLI/product-identity/tools/verify_map.py --json
```

See [[CLI/product-identity/README|Product Identity Bridge]] and [[Connections/FACTORY__JIVO_DESK|Factory to Jivo Desk Connection]] for scope and safety boundaries.

## Entry points

Run a CLI from the repository root with its workspace path:

```bash
./CLI/ecom-cli/jivo-ecom-pp-cli --help
./CLI/exim/exim --help
./CLI/factory-cli/jivo-factory-pp-cli --help
./CLI/oms-cli/oms-pp-cli --help
./CLI/jsap-cli/jsap-cli --help
CLI/jivo-scraping-cli/bin/jivo-scrape --help
```

Credentials remain consolidated in the JivoGPT root `.env`; generated state and token caches remain inside their existing protected locations. See [[docs/DATA_SOURCES|DATA_SOURCES]] for connector roles and [[Connections/CONNECTIONS_MOC|CONNECTIONS_MOC]] for joins between them.

Linked: [[/README|JivoGPT]] · [[CLI/product-identity/README|Product Identity Bridge]] · [[docs/READ_ONLY_LAW|READ_ONLY_LAW]] · [[docs/DATA_SOURCES|DATA_SOURCES]] · [[Connections/CONNECTIONS_MOC|CONNECTIONS_MOC]]
