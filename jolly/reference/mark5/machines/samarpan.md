# MARK V machine specification: Samarpan pouch

Reviewed 10 September 2026. Status: approved operating inputs for design; no
engine change. Confidence: high in machine identity, running-rate range and
ability to run singly or with Hitech. Exact pack/film mapping and attribution of
generic MES pouch records require specific source identity.

Authority: [WORKING-RULES.md](../WORKING-RULES.md), M5-R01 and M5-A01. Daman
adopted the revised PDF figures as actual operating inputs. The later Speeds
note controls over the earlier 35–40/min transcript fragment.

## Operating specification

| Field | MARK V rule | Source anchor |
|---|---|---|
| Physical identity | **Samarpan is a separate pouch machine from Hitech** | PDF p52, 38:33–38:37 and 39:17 |
| Running speed | **30–35 pouches/min = 1,800–2,100 pouches/hour** | PDF p2; p12 N1; p52, 38:48–39:01 |
| Single operation | Samarpan can run on its own | PDF p12 N1; p52, 39:12 |
| Concurrent operation | Hitech and Samarpan can run together; reported preference is together | PDF p12 N1; p52, 39:07–39:17 |
| Pack/film coverage | Pouch route; no complete pack-weight or film compatibility list supplied | PDF p2 |
| Changeover and crew | No Samarpan-specific setup duration, flushing volume or complete crew supplied | Revised tables p3 and notes pp12–14 |

Keep both speed endpoints until an explicit scheduling choice selects a value
or presents bounded scenarios. Do not silently select 1,800, 1,950 or 2,100/hour.
These are running rates, not measured saleable full-shift output. Do not restore
35–40/min or add an inherited efficiency multiplier.

## Routing and units

- Treat Samarpan and Hitech as two physical planning resources. Their individual
  capacities must replace the old one-machine pouch abstraction, rather than
  being added beside an independently scheduled aggregate pouch line.
- Keep each product's verified pouch/film recipe, physical fill quantity and
  sales-unit conversion. The PDF does not assign the speed to every pouch size,
  1 L, or 700 g, and does not establish that 700 g equals 0.7 L. Do not turn
  1,800–2,100 pouches/hour into litres/hour without a verified litres-per-pouch
  conversion for that SKU.
- `site-mark4/lib/model.ts:31–43` identifies pouch recipes from pouch/film/
  laminate component names. `Product` has `fillLitres`, `containersPerPiece`
  and `bom` (`types.ts:36–42`), but no machine-specific pouch-film compatibility
  field. This coarse container classification cannot alone prove suitability
  for both machines.
- `rules.ts:77` currently collapses every pouch rate lookup to `POUCH` and
  divides container capacity by `containersPerPiece`. Preserve physical versus
  sales-unit arithmetic, while requiring the source to establish container
  count. A film coefficient in kg is not a count of pouches; the normalizer's
  default one-container value does not prove a combo pack contains one pouch.
- Preserve recipe/identity holds, actual material availability and warehouse
  limits. Shared film, oil and carton stocks remain one ledger when both
  machines operate. A second machine cannot consume the same material twice
  without reservation or count the same demand as two separate obligations.

## Current code and observation boundary

MARK IV's `LINE_IDS` schedules only `Pouch Machine`; its speed entry identifies
that resource as Hitech at the older 1,800/hour. `Pouch Samarpan` exists only as
a `null` speed with status `not separately scheduled` (`rules.ts:3,63–64`).
The model's line description explicitly says Hitech only (`model.ts:262`).

The source pipeline also carries a generic pouch identity:

- `collect_factory_now.py:22,70–74` iterates a list containing only `Pouch
  Machine` and matches actual records by exact `line_name`.
- `serve_inputs.py:137–143` retains that generic line in actual runs and
  deduplicates by source run ID. At lines 155–162, machine configuration names
  Hitech and Samarpan become `POUCH-Hitech` and `POUCH-Samarpan` rate evidence;
  that configuration distinction is not itself a mapping of an actual run.
- `revision_input.py:10` similarly recognizes only the generic pouch line.

Before attributing actual output, running state or labour to either physical
machine, use a source machine/config identifier whose meaning is established.
If a run only says `Pouch Machine`, retain it once as pouch output with machine
unspecified. Do not clone it onto both rows, arbitrarily label it Hitech, split
its output by rated speed, or show both machines running from one observation.
This is verified code behavior; live MES identity coverage was not queried in
this machine study.

## Setup, shared resources and practical effect

Concurrent filling is supported by the source. It does not supply two full
crews, unrestricted shared packing capacity or a ruling that both machines may
occupy the existing one-night-line allocation simultaneously. Represent these
as explicit roster/resource choices when designing the scheduler.

Do not substitute JP or Clear Pack changeover/flushing values, nor mark
Samarpan setup as measured zero. Any temporary setup policy must be labelled
and distinct from the approved running rate. M5-A01 reuse governs flushing if
applicable, but supplies neither a Samarpan flushing quantity nor duration.

For one uninterrupted hour with both machines fully supplied and staffed,
the two running rates sum to **3,000–3,300 physical pouches**: Hitech 1,200 plus
Samarpan 1,800–2,100. This is arithmetic capacity, not guaranteed packed output
or a combined litres/hour rate. A pair summary must sum actual individual
allocations, rather than create a third productive resource.

## Meaningful acceptance tests for implementation

1. Samarpan retains 1,800–2,100/hour with an explicit range policy; Hitech keeps
   its separate 1,200/hour value. No legacy aggregate line adds extra capacity.
2. Samarpan can schedule alone when Hitech is disabled. Both can fill in an
   explicitly feasible shared-resource scenario, consuming shared inventory
   and residual demand only once; any night allocation follows its documented
   policy rather than treating the pair as one machine automatically.
3. A weight-labelled pouch without verified litre conversion does not invent
   litres/hour. Multi-pouch sales units divide physical throughput correctly;
   film mass coefficients cannot become pouch counts.
4. A generic MES run appears once with unspecified physical machine. A source
   run carrying a verified Samarpan identity appears on Samarpan only. Repeated
   observations of the same source run do not duplicate output or labour.
5. Bottle/tin/drum recipes cannot reach Samarpan merely by product-name matching;
   unresolved film compatibility and required-material shortages remain visible.
6. Missing setup/crew values remain unknown or explicitly assumed; they never
   silently become measured zero, JP's 5–6 hours, or a fabricated flushing loss.

Source PDF: `/Users/damanpreetsingh/Documents/Codex/2026-09-09/make/outputs/Machine_Changeover_Planning_Red_Notes_Edition.pdf`.
SHA-256 checked in this session: `b3388f02852783347fa04f9d23e1a9260d46477f7132d65464bdbc7238636fe3`.
Pages 2, 4, 12 and 51–52 were read directly in bounded text extraction; p4 is
general reconciliation and adds no Samarpan-specific override. See
[PDF-REVIEW-2026-09-10.md](../PDF-REVIEW-2026-09-10.md).
