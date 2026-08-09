---
version: 1
slug: "distribution-web-index-html"
primary_target: "distribution/web/index.html"
related_targets: []
---

# Surface: Distribution bundle composer (single page)

**Scope & mode:** Operate. One screen served locally by the distribution Go binary. Daman (later a dept head) composes a toolkit bundle: tick tools → pick target OS → download one zip.

**Audience & job:** The composer knows the toolkit; the job is selection and dispatch, done in under a minute, often repeatedly. Recipients never see this surface — they get the zip.

**Task & content:** 12 components / 21 tools from `distribution/manifest.json` (never hardcoded), grouped (SAP & books / Ops systems / Seller portals / Desk tools). Per row: tick, name, one-line plain-language description, per-OS availability, approx size, warning marks (no binary for chosen OS, known-dead credential). Platform plates: MAC / WINDOWS. Dispatch slip (right, sticky): live list of what's ticked — tools, env files by name, total size, README note — with DISPATCH (download) as its stamp; slip is the primary feedback channel.

**Chosen direction:** The Godown Load Board (see distribution/DESIGN.md). Memorable moment: the paper slip typing itself as you tick, then the stamp press on DISPATCH.

**States that matter:** empty selection (slip shows a blank pad + hint), missing-binary-for-OS (red chalk note, row still tickable with warning carried to slip), bundle building (stamp pressed, progress line on slip), bundle failed (wet-rag wipe + error line on slip), bundle ready (download starts; slip notes the zip name).

**Constraints:** No auth. No CDN/network dependency at serve time — everything embedded in the Go binary. No credentials or env values in the DOM; filenames only. API: GET /api/manifest, POST /api/bundle {components[], os} → zip stream (reconcile with Atlas plan). No page horizontal scroll; slip drops below board <900px.

**Resolved during build:** display face = tracked 800-weight system caps + hand-drawn SVG chalk rule (no webfont, offline rule holds); missing binaries skip-with-warning (Atlas D2), surfaced as row chalk notes and slip warnings. Successful dispatch stamps a red-ink DISPATCHED impression on the slip (the memorable moment, shipped).
