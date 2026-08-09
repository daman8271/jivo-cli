# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Primary: Daman (owner of the jivo-cli toolkit) composing tool bundles to hand to JIVO staff. Secondary, later: a department head doing the same. Recipients are JIVO office operators (Accounts, Sales, E-com, Factory teams — "many people", per Daman 2026-08-10) who receive a zip, not the site. *(Inferred from session brief + repo docs; interview waived by user's instruction to proceed.)*

## Product Purpose

The jivo-cli repo is JIVO's data toolkit: ~12 CLI tools answering live business questions (SAP books, HANA SQL, e-com, orders, factory, imports, field sales, seller portals). The **distribution surface** exists so a working subset of that toolkit can be handed to a person in one zip — binaries plus the credential files each tool actually reads, laid out so it works on first run. Success: recipient unzips, follows a short README, and their first `doctor`/`--help` runs green without a technical person present.

## Positioning

Unlike a shared drive of binaries or a git checkout, a bundle is *composed* — only the tools this person should have, with env files pre-placed where each tool's own resolution logic looks for them (a fact map no generic packager has: it was extracted from each tool's source).

## Operating Context

Site runs locally (Daman's Mac; later office/VPS boxes) served by a single Go binary. No public deploy — bundles contain live credentials. Recipients run tools on office Windows PCs or Macs; SAP/HANA need office LAN, FortiClient VPN, or fleet tunnels. Source of truth for what's bundlable: `distribution/manifest.json` (14-agent inventory, 2026-08-10).

## Capabilities and Constraints

- Select components via checkboxes; pick target OS (windows / mac-arm64 in v1); download one zip.
- Env files baked in at bundle time from their authoritative repo locations; some tools' configs live outside the repo (~/.config/... , ~/.postsql/) and get templates + instructions instead.
- Explicitly NO auth/permissions layer in v1 (Daman's call, 2026-08-10 — do not add one).
- Generated zips and staging are never committed to git.
- CLIs themselves are never modified by bundling.
- Undecided: whether missing-platform binaries are cross-compiled on demand or skipped with a warning (Atlas plan will settle).

## Brand Commitments

JIVO is an edible-oils company (olive/canola/mustard); the toolkit is an internal ops tool, INR-denominated, Indian-market. No formal brand kit exists in this repo. Daman's standing taste: plain language, no jargon, dense and fast over decorative. *(Inferred.)*

## Evidence on Hand

- `distribution/manifest.json` — full inventory: 12 components, 21 tools, binaries per OS, env resolution semantics read from source, zip gotchas, install lessons from two real machine onboardings (Karanpreet 2026-08-08, Avtar/JIVO201 2026-08-06).
- `sap-b1/accounts-kit/SETUP.md` — the proven manual onboarding doc this site supersedes.
- No testimonials/marketing evidence — this is an internal Operate tool; none should be fabricated.

## Product Principles

1. The zip must work on first run — every layout decision defers to how each tool actually resolves its config, not to tidiness.
2. Composition over completeness — giving someone less is a feature, not a failure.
3. Credentials are cargo, never exhaust — they ride inside zips deliberately and never leak into git, logs, or URLs.
4. The manifest is the single source of truth — UI and bundler both read it; nothing is hardcoded twice.
5. One binary, no ceremony — runs anywhere in the fleet with `./distribution-site`, no DB, no build pipeline at serve time.
