# ji.jivo.in sizing note (asked for "early") — 2026-08-22

## Verdict: it is NOT a missing CLI. It is factory-cli's own frontend.

Evidence, in order:

1. `curl -s https://ji.jivo.in/` -> 200, title `JI`,
   `<meta name="description" content="JI - Complete management system for Jivo Wellness.">`,
   favicon `/factoryLogoNew.png`, single module bundle `/assets/index-JG3vt8Qs.js` (1,027,790 bytes).
2. `curl -s https://factory.jivo.in/` -> 200 but **187 bytes of JSON**, not HTML:
   `{"message":"Welcome to the Accounts API","endpoints":{"login":"/login/", ...}}`.
   So `factory.jivo.in` is the **API origin only**; it serves no SPA.
3. In `ji`'s bundle: `mg={baseUrl:"https://factory.jivo.in/api/v1",timeout:3e4}` and the
   axios factory `Bt.create({baseURL:BU.apiBaseUrl||mg.baseUrl,...})`.
   IndexedDB name is `factoryManagementDB`.
4. The frozen endpoint registry `Ne={AUTH:{LOGIN:"/accounts/login/",...},VEHICLE:{...},...}`
   is present in ji's bundle — this is the same registry the jivo-rescrape skill describes
   for factory (`et`/`aI` on the July harvest).
5. `~/jivo-cli/factory-cli/research/API-FACTS.md:18` already records:
   `**Name:** jivo-factory (Jivo "JI" factory management system; frontend https://ji.jivo.in)`
   and `spec.yaml:5` describes the CLI as `(ji.jivo.in / factory.jivo.in)`.

## So the brief's premise is wrong

The brief says ji.jivo.in "has **no CLI in this repo at all**" and "may be the biggest
missing CLI we have." It is in fact the **best-covered** system in the repo:
`factory-cli`, spec v0.4.0, 455 endpoints, rescraped 2026-08-03 from this exact bundle.

## Does JIVO_USER / JIVO_PASS authenticate against it?

No — wrong credential pair. `JIVO_USER`/`JIVO_PASS` in the vault sit under
`[local] ~/jivo-cli/control-panel/.env` with `JIVO_BASE=http://103.89.45.75:9080`
(the Control Panel, a different system). The credentials that authenticate against the
factory/ji API are `JIVO_FACTORY_EMAIL` / `JIVO_FACTORY_PASSWORD`, posted to
`/api/v1/accounts/login/`, with tenant selected by the `Company-Code` header
(`JIVO_FACTORY_COMPANIES=JIVO_MART,JIVO_OIL,JIVO_BEVERAGES`).

## API surface size

The registry in ji's bundle yields 355 `UPPER_SNAKE:"/literal/"` entries on a bare grep
(before the template-function forms that Rule 4 warns are the ones usually captured, and
before recursing the 627 `assets/*.js` lazy chunks). factory-cli's shipped spec already
publishes 455 GET endpoints. Sizing: the *frontend* has no separate API of its own, so the
correct action for ji is **nothing new to build** — only the factory drift check
(system 4 of this run), which should harvest ji.jivo.in's bundle since that is where the
registry lives.
