---
title: Read-Only Guardrails
created: 2026-07-24
updated: 2026-07-24
project: jivo-cli
type: reference
tags: [blinkit, read-only, safety]
---
# Read-Only Guardrails (BINDING)
During the whole Blinkit study & CLI build: **only** navigate, read, screenshot, and capture GET/read API traffic. NEVER click create / edit / save / delete / launch / submit / upload / pause-campaign / change-budget. Login (OTP / magic-link) is the one allowed write, exactly like every [[00-Blinkit-Atlas]] CLI. Generating a report export (async) is borderline — allowed only when explicitly needed, since it just queues a read. See jivo-cli READ-ONLY LAW.
